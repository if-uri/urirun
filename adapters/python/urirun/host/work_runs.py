# Author: Tom Sapletta · Part of the ifURI solution.
"""Run records for approved work actions (the /work Runs panel).

Every Approve on the work view starts a background command. This module makes those
runs LEGIBLE: each run gets a durable record — meta JSON, a log file, an exit-code
file — under ``~/.urirun/host-dashboard/work-runs/``, so the dashboard can show
progress and logs while the command runs and after it finishes.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

_RUNS_DIR_ENV = "URIRUN_WORK_RUNS_DIR"
# ANSI CSI/escape sequences + stray control bytes (twine/rich progress bars).
_ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b[()][0-9A-B]|[\x00-\x08\x0b\x0c\x0e-\x1f]")
_LEGACY_GLOB = "/tmp/urirun_approve_*.log"  # pre-panel approve logs; shown read-only


def runs_dir() -> Path:
    d = Path(os.environ.get(_RUNS_DIR_ENV) or "~/.urirun/host-dashboard/work-runs").expanduser()
    d.mkdir(parents=True, exist_ok=True)
    return d


def start_run(project: Any, uri: str, cmd: str, label: str = "") -> dict:
    """Start ``cmd`` in the background with a durable run record; return its meta."""
    slug = "".join(c if c.isalnum() else "_" for c in uri)[:60]
    run_id = time.strftime("%Y%m%dT%H%M%S") + "-" + slug
    d = runs_dir()
    log, exitf = d / f"{run_id}.log", d / f"{run_id}.exit"
    proc = subprocess.Popen(  # noqa: S602 - cmd comes from the server-side plan, not the request
        ["bash", "-lc", f"cd {str(project)!r} && ( {cmd} ) > {str(log)!r} 2>&1; echo $? > {str(exitf)!r}"])
    meta = {"id": run_id, "uri": uri, "label": label, "cmd": cmd,
            "pid": proc.pid, "started": time.time(), "log": str(log)}
    (d / f"{run_id}.json").write_text(json.dumps(meta), encoding="utf-8")
    return meta


def _clean_tail(path: Path, lines: int) -> str:
    """Last ``lines`` of a log, with \\r-overwritten progress collapsed and ANSI stripped."""
    try:
        # bytes → decode: text mode would translate the bare \r we collapse on into \n
        text = path.read_bytes().decode("utf-8", errors="replace")
    except OSError:
        return ""
    rows = [_ANSI.sub("", seg.split("\r")[-1]).rstrip() for seg in text.split("\n")]
    return "\n".join(rows[-lines:])


def _pid_alive(pid: Any) -> bool:
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, TypeError, ValueError):
        return False


def _run_row(meta_file: Path, tail_lines: int) -> dict | None:
    try:
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - a corrupt record must not break the panel
        return None
    exitf = meta_file.with_suffix(".exit")
    exit_code: int | None = None
    if exitf.exists():
        try:
            exit_code = int(exitf.read_text(encoding="utf-8").strip() or 0)
        except ValueError:
            exit_code = -1
    log = Path(meta.get("log") or meta_file.with_suffix(".log"))
    return {"id": meta.get("id") or meta_file.stem, "uri": meta.get("uri"),
            "label": meta.get("label"), "cmd": meta.get("cmd"), "started": meta.get("started"),
            "running": exit_code is None and _pid_alive(meta.get("pid")),
            "exit": exit_code, "log": str(log), "tail": _clean_tail(log, tail_lines)}


def _legacy_rows(tail_lines: int) -> list[dict]:
    """Approve logs written before run records existed (flat /tmp files, no meta)."""
    import glob  # noqa: PLC0415
    rows = []
    for p in sorted(glob.glob(_LEGACY_GLOB)):
        lp = Path(p)
        try:
            st = lp.stat()
        except OSError:
            continue
        rows.append({"id": lp.stem, "uri": lp.stem.replace("urirun_approve_", ""),
                     "label": "", "cmd": None, "started": st.st_mtime,
                     "running": (time.time() - st.st_mtime) < 15, "exit": None,
                     "log": str(lp), "tail": _clean_tail(lp, tail_lines)})
    return rows


def list_runs(tail_lines: int = 120, limit: int = 20) -> list[dict]:
    """All known runs, newest first: durable records plus legacy /tmp approve logs."""
    rows = [r for r in (_run_row(mf, tail_lines) for mf in runs_dir().glob("*.json")) if r]
    rows += _legacy_rows(tail_lines)
    rows.sort(key=lambda r: r.get("started") or 0, reverse=True)
    return rows[:limit]
