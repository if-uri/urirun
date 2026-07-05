# Author: Tom Sapletta · Part of the ifURI solution.
"""Guard the /work Runs panel substrate: durable run records with progress + logs.

Every Approve on the work view must leave a trackable record (meta + log + exit code)
so the dashboard can show WHAT ran, whether it is STILL running, and its output —
the user-facing contract behind /api/work/runs.
"""
import json
import time

import pytest

from urirun.host import work_runs


@pytest.fixture()
def runs_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("URIRUN_WORK_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setattr(work_runs, "_LEGACY_GLOB", str(tmp_path / "legacy" / "none-*.log"))
    return tmp_path / "runs"


def _wait_finished(run_id, timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        row = next((r for r in work_runs.list_runs() if r["id"] == run_id), None)
        if row and not row["running"]:
            return row
        time.sleep(0.1)
    raise AssertionError("run did not finish in time")


def test_start_run_records_meta_log_and_exit(runs_dir, tmp_path):
    meta = work_runs.start_run(tmp_path, "release://x/command/publish",
                               "echo hello-panel; exit 0", label="publishing x")
    assert meta["id"].endswith("release___x_command_publish")
    row = _wait_finished(meta["id"])
    assert row["exit"] == 0 and row["uri"] == "release://x/command/publish"
    assert "hello-panel" in row["tail"]
    assert row["label"] == "publishing x"
    saved = json.loads((runs_dir / f"{meta['id']}.json").read_text())
    assert saved["pid"] == meta["pid"]


def test_failed_run_reports_nonzero_exit(runs_dir, tmp_path):
    meta = work_runs.start_run(tmp_path, "deploy://y", "echo boom >&2; exit 3")
    row = _wait_finished(meta["id"])
    assert row["exit"] == 3 and row["running"] is False
    assert "boom" in row["tail"]


def test_tail_strips_ansi_and_collapses_progress_bars(runs_dir, tmp_path):
    log = work_runs.runs_dir() / "x.log"
    log.write_text("plain\n\x1b[35m 16%\x1b[0m bar\rdone 100%\n", encoding="utf-8")
    tail = work_runs._clean_tail(log, 10)
    assert "\x1b" not in tail and "16%" not in tail
    assert "plain" in tail and "done 100%" in tail


def test_list_runs_newest_first_and_corrupt_meta_skipped(runs_dir, tmp_path):
    a = work_runs.start_run(tmp_path, "a://1", "true")
    time.sleep(1.1)  # run ids are second-granular; force distinct started stamps
    b = work_runs.start_run(tmp_path, "b://2", "true")
    (work_runs.runs_dir() / "zz-corrupt.json").write_text("{not json", encoding="utf-8")
    _wait_finished(a["id"]), _wait_finished(b["id"])
    ids = [r["id"] for r in work_runs.list_runs()]
    assert ids == [b["id"], a["id"]]
