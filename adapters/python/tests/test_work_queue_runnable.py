"""runnable_summary — /work visibility: servable vs frozen vs waiting vs dependency-blocked,
built on planfile's runnability contract (`ticket next --debug`)."""
from __future__ import annotations

import json
import types

from urirun.host import work_queue as wq


def test_bucket_skip_maps_each_reason():
    assert wq._bucket_skip("autonomy-frontier") == "frozen"
    assert wq._bucket_skip("goal-frozen") == "frozen"
    assert wq._bucket_skip("actor:human") == "waiting"
    assert wq._bucket_skip("waiting:node") == "waiting"
    assert wq._bucket_skip("needs-human:pypi-token") == "waiting"
    assert wq._bucket_skip("blocked_by:IFURI-9") == "dependency_blocked"
    assert wq._bucket_skip("exec_state:blocked") == "other"


def test_runnable_summary_splits_queue(monkeypatch):
    report = {
        "selected": "IFURI-219",
        "servable": ["IFURI-219", "IFURI-220"],
        "skipped": [
            {"id": "IFURI-224", "reason": "autonomy-frontier"},
            {"id": "IFURI-036", "reason": "waiting:node"},
            {"id": "IFURI-043", "reason": "needs-human:pypi-token"},
            {"id": "IFURI-079", "reason": "blocked_by:IFURI-201"},
            {"id": "IFURI-204", "reason": "exec_state:blocked"},
        ],
    }
    monkeypatch.setattr(wq, "_planfile", lambda: "/fake/planfile")
    monkeypatch.setattr(wq.subprocess, "run",
                        lambda *a, **k: types.SimpleNamespace(stdout=json.dumps(report), stderr="", returncode=0))
    s = wq.runnable_summary()
    assert s["selected"] == "IFURI-219" and s["servable"] == ["IFURI-219", "IFURI-220"]
    assert [r["id"] for r in s["frozen"]] == ["IFURI-224"]
    assert {r["id"] for r in s["waiting"]} == {"IFURI-036", "IFURI-043"}
    assert [r["id"] for r in s["dependency_blocked"]] == ["IFURI-079"]
    assert [r["id"] for r in s["other"]] == ["IFURI-204"]


def test_runnable_summary_degrades_without_planfile(monkeypatch):
    monkeypatch.setattr(wq, "_planfile", lambda: None)
    s = wq.runnable_summary()
    assert s["selected"] is None and s["servable"] == [] and "error" in s
