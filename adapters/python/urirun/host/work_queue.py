# Author: Tom Sapletta · Part of the ifURI solution.
"""The queue panel data: is the autonomous loop (koru) running, and what is in the queue.

Answers "where can I see that it keeps going?" — koru's live status plus the planfile
ticket queue, so the /work dashboard shows continuous operation, not just a snapshot.
Everything is best-effort and read-only; missing tools degrade to empty, never an error.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

_PROJECT_ENV = "URIRUN_KORU_PROJECT"
_PLANFILE_ENV = "URIRUN_PLANFILE_BIN"


def _project() -> str:
    return os.environ.get(_PROJECT_ENV) or os.path.expanduser("~/github/if-uri")


def _planfile() -> str | None:
    b = os.environ.get(_PLANFILE_ENV) or shutil.which("planfile")
    if b:
        return b
    for c in ("~/github/if-uri/venv/bin/planfile", "~/github/semcod/koru/.venv/bin/planfile"):
        p = Path(c).expanduser()
        if p.is_file():
            return str(p)
    return None


def koru_status() -> dict[str, Any]:
    """Is the autonomous loop alive, and what was its last cycle line?"""
    project = _project()
    try:
        out = subprocess.run(["pgrep", "-af", "autonomous up"], capture_output=True, text=True, timeout=5).stdout
    except Exception:  # noqa: BLE001
        out = ""
    loops = [ln for ln in out.splitlines() if project in ln or "autonomous up" in ln]
    running = any(project in ln for ln in loops)
    last = ""
    log = Path(project) / ".planfile" / ".koru" / "queue.log"
    if not log.is_file():
        log = Path(project) / ".planfile" / ".koru" / "soak.log"
    if log.is_file():
        try:
            lines = [l for l in log.read_text(errors="replace").splitlines()
                     if "cycle=" in l or "queue:" in l or "QUEUE:" in l or "ticket" in l.lower()]
            last = lines[-1][-200:] if lines else ""
        except Exception:  # noqa: BLE001
            pass
    return {"running": running, "loops": len(loops), "project": project, "last_activity": last.strip()}


def tickets(limit: int = 40) -> list[dict[str, Any]]:
    """The planfile queue — every ticket with its status, newest work first."""
    pf = _planfile()
    if not pf:
        return []
    try:
        cp = subprocess.run([pf, "ticket", "list", "--format", "json"],
                            capture_output=True, text=True, timeout=15, cwd=_project())
        raw = cp.stdout
        data = json.loads(raw[raw.index("["):raw.rindex("]") + 1]) if "[" in raw else \
            json.loads(raw).get("tickets", [])
    except Exception:  # noqa: BLE001
        return []
    rows = []
    for t in data[:limit]:
        src = t.get("source") or {}
        rows.append({"id": t.get("id"), "name": t.get("name"), "status": t.get("status"),
                     "priority": t.get("priority"),
                     "source": src.get("tool") if isinstance(src, dict) else src,
                     "labels": t.get("labels") or t.get("label")})
    order = {"in_progress": 0, "claimed": 1, "waiting_input": 2, "open": 3, "done": 4, "blocked": 2}
    rows.sort(key=lambda r: order.get(r.get("status"), 5))
    return rows


def queue_state() -> dict[str, Any]:
    ts = tickets()
    counts: dict[str, int] = {}
    for t in ts:
        counts[t.get("status") or "?"] = counts.get(t.get("status") or "?", 0) + 1
    return {"koru": koru_status(), "tickets": ts, "counts": counts, "total": len(ts)}
