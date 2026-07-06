# Author: Tom Sapletta · Part of the ifURI solution.
"""The operator control console behind the /work view.

Three legible surfaces for a human watching the autonomous loop:

* **Operations to confirm** — a durable queue of proposed operations (each a URI
  process + the shell command that realises it). The human confirms or rejects
  each one in the browser; a confirm starts a background run (durable record in
  the Runs panel). Nothing executes that the operator did not approve.
* **URI activity** — the live feed of URI processes urirun is actually running,
  read from the twin step-event hub: what it is doing, right now, by URI.
* **Shell console** — an operator shell so the human can look around the host the
  loop runs on. Read-only surfaces elsewhere; this is the deliberate escape hatch.

Everything is best-effort and degrades to empty rather than raising, matching the
other /work data modules (work_queue, work_runs).
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

_OPS_FILE_ENV = "URIRUN_WORK_OPS_FILE"
_SHELL_ENV = "URIRUN_WORK_SHELL"          # "0" disables the shell console
_SHELL_TIMEOUT_ENV = "URIRUN_WORK_SHELL_TIMEOUT"


# ---------------------------------------------------------------- operations queue

def ops_file() -> Path:
    p = Path(os.environ.get(_OPS_FILE_ENV) or "~/.urirun/host-dashboard/work-ops.json").expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _load() -> list[dict]:
    f = ops_file()
    if not f.is_file():
        return []
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:  # noqa: BLE001 - a corrupt queue is an empty queue, never an error
        return []


def _save(ops: list[dict]) -> None:
    ops_file().write_text(json.dumps(ops, indent=1), encoding="utf-8")


def add_ops(items: list[dict]) -> dict[str, Any]:
    """Append proposed operations to the confirm queue (the loop/agent's seam).

    Each item: {uri, title, desc, cmd}. An id and pending status are assigned here.
    De-duplicates on (uri, cmd) so re-seeding the same plan does not pile up."""
    ops = _load()
    seen = {(o.get("uri"), o.get("cmd")) for o in ops}
    added = 0
    for it in items or []:
        key = (it.get("uri"), it.get("cmd"))
        if key in seen or not it.get("cmd"):
            continue
        seen.add(key)
        ops.append({"id": f"op-{int(time.time() * 1000)}-{added}", "uri": it.get("uri") or "",
                    "title": it.get("title") or "", "desc": it.get("desc") or "",
                    "cmd": it.get("cmd"), "status": "pending", "run": None,
                    "created": time.time()})
        added += 1
    _save(ops)
    return {"ok": True, "added": added, "total": len(ops)}


def _runs_by_id() -> dict:
    try:
        from .work_runs import list_runs
        return {r.get("id"): r for r in list_runs(tail_lines=1)}
    except Exception:  # noqa: BLE001
        return {}


def _reflect(op: dict, runs: dict) -> dict:
    """A confirmed op mirrors its run: running / exit 0 → done / else failed."""
    r = runs.get(op.get("run"))
    if op.get("status") == "running" and r is not None:
        if r.get("running"):
            return op
        op = {**op, "status": "done" if r.get("exit") == 0 else "failed"}
    return op


def list_ops() -> list[dict]:
    """The confirm queue, pending first, each confirmed op reflecting its run outcome."""
    runs = _runs_by_id()
    ops = [_reflect(o, runs) for o in _load()]
    order = {"pending": 0, "running": 1, "failed": 2, "done": 3, "rejected": 4}
    ops.sort(key=lambda o: (order.get(o.get("status"), 5), -(o.get("created") or 0)))
    return ops


def _set_status(op_id: str, **changes: Any) -> dict | None:
    ops = _load()
    hit = None
    for o in ops:
        if o.get("id") == op_id:
            o.update(changes)
            hit = o
    if hit is not None:
        _save(ops)
    return hit


def confirm_op(project: Any, op_id: str) -> dict[str, Any]:
    """Confirm a pending op → run its command in the background with a durable record."""
    op = next((o for o in _load() if o.get("id") == op_id), None)
    if op is None:
        return {"ok": False, "error": f"no operation {op_id}"}
    if op.get("status") != "pending":
        return {"ok": False, "error": f"operation {op_id} is {op.get('status')}, not pending"}
    from .work_runs import start_run
    meta = start_run(project, op.get("uri") or op_id, op["cmd"], label=op.get("title") or "")
    _set_status(op_id, status="running", run=meta["id"])
    return {"ok": True, "started": True, "op": op_id, "run": meta["id"], "log": meta["log"]}


def reject_op(op_id: str) -> dict[str, Any]:
    op = _set_status(op_id, status="rejected")
    return {"ok": op is not None, "op": op_id} if op else {"ok": False, "error": f"no operation {op_id}"}


# ---------------------------------------------------------------- URI activity feed

def uri_activity(limit: int = 40) -> list[dict]:
    """What urirun is running, by URI: recent twin step events (newest first)."""
    try:
        from .twin_bridge import TWIN_EVENT_HUB
        events = [e for e in TWIN_EVENT_HUB.replay_since(0)
                  if isinstance(e, dict) and e.get("uri") == "twin://monitor/event"]
    except Exception:  # noqa: BLE001
        return []
    rows = []
    for e in events[-int(limit):]:
        rows.append({"uri": e.get("step_uri"), "narration": e.get("narration"),
                     "status": e.get("status"), "category": e.get("category"),
                     "degraded": e.get("degraded")})
    rows.reverse()
    return rows


# ---------------------------------------------------------------- shell console

def shell_enabled() -> bool:
    return str(os.environ.get(_SHELL_ENV, "1")).strip().lower() not in ("0", "false", "no", "off")


def run_shell(project: Any, cmd: str, timeout: float | None = None) -> dict[str, Any]:
    """Run one shell command in the project dir and return its combined output.

    The operator's own shell, on the host the loop runs on — deliberately powerful,
    so it is gated by URIRUN_WORK_SHELL and bounded by a timeout."""
    if not shell_enabled():
        return {"ok": False, "error": "shell console disabled (URIRUN_WORK_SHELL=0)"}
    cmd = str(cmd or "").strip()
    if not cmd:
        return {"ok": False, "error": "empty command"}
    to = float(timeout or os.environ.get(_SHELL_TIMEOUT_ENV) or 30)
    try:
        cp = subprocess.run(["bash", "-lc", cmd], cwd=str(project), capture_output=True,
                            text=True, timeout=to)  # noqa: S603 - operator console, gated + bounded
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timed out after {to:g}s", "cmd": cmd}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "cmd": cmd}
    out = (cp.stdout or "") + (cp.stderr or "")
    truncated = len(out) > 20000
    return {"ok": True, "cmd": cmd, "exit": cp.returncode,
            "out": out[-20000:] if truncated else out, "truncated": truncated}
