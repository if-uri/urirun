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
        now = time.time()
        ops.append({"id": f"op-{int(now * 1000)}-{added}", "uri": it.get("uri") or "",
                    "title": it.get("title") or "", "desc": it.get("desc") or "",
                    "cmd": it.get("cmd"), "llm": it.get("llm") or "",  # który LLM uczestniczy
                    "status": "pending", "run": None, "created": now, "updated": now})
        added += 1
    _save(ops)
    return {"ok": True, "added": added, "total": len(ops)}


def _runs_by_id() -> dict:
    try:
        from .work_runs import list_runs
        return {r.get("id"): r for r in list_runs(tail_lines=1)}
    except Exception:  # noqa: BLE001
        return {}


def list_ops() -> list[dict]:
    """The confirm queue, pending first. A running op whose run has finished is transitioned
    to done/failed AND stamped ``updated`` here, so the panel shows when it last changed."""
    runs = _runs_by_id()
    ops = _load()
    changed = False
    for o in ops:
        if o.get("status") == "running":
            r = runs.get(o.get("run"))
            if r is not None and not r.get("running"):
                o["status"] = "done" if r.get("exit") == 0 else "failed"
                o["updated"] = time.time()
                changed = True
    if changed:
        _save(ops)
    order = {"pending": 0, "running": 1, "failed": 2, "done": 3, "rejected": 4}
    ops.sort(key=lambda o: (order.get(o.get("status"), 5), -(o.get("updated") or o.get("created") or 0)))
    return ops


def _set_status(op_id: str, **changes: Any) -> dict | None:
    ops = _load()
    hit = None
    for o in ops:
        if o.get("id") == op_id:
            o.update(changes, updated=time.time())  # every status change is time-stamped
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

import datetime as _dt
import re as _re

_KLINE = _re.compile(r"^\[(\d\d:\d\d:\d\d)\]\s*koru\s*[^\s]?\s*([A-Z]+):\s*(.*)$")
_BACKTICK = _re.compile(r"`([^`]+)`")
_KORU_LOG_STALE_SECONDS = 1500  # koru cycles can sleep 900s; stale after ~25 min without a heartbeat.


def _utc_to_local(hhmmss: str) -> str:
    """koru zapisuje log w UTC — konwertuj HH:MM:SS na czas lokalny operatora (widz nie liczy w głowie)."""
    if not hhmmss:
        return hhmmss
    try:
        h, m, s = (int(x) for x in hhmmss.split(":"))
        today = _dt.datetime.now().date()
        utc = _dt.datetime(today.year, today.month, today.day, h, m, s, tzinfo=_dt.timezone.utc)
        return utc.astimezone().strftime("%H:%M:%S")
    except Exception:  # noqa: BLE001
        return hhmmss


def _koru_line(ln: str) -> dict:
    """Parse one koru log line into {time, type, text} — realne komendy czytelnie."""
    m = _KLINE.match(ln)
    if not m:
        return {"time": "", "type": "LOG", "text": ln.strip()[-240:]}
    t, typ, rest = m.groups()
    t = _utc_to_local(t)
    text = rest
    if typ == "OBS":
        av = _re.search(r'argv_text="([^"]*)"', rest)
        surf = _re.search(r"surface=(\S+)", rest)
        op = _re.search(r"operation=(\S+)", rest)
        if av:
            text = f"{surf.group(1) if surf else ''}·{op.group(1) if op else ''}  $ {av.group(1)}"
        else:
            corr = _re.search(r"corr=(\S+)", rest)
            text = f"{surf.group(1) if surf else ''} {corr.group(1) if corr else rest}"
    else:
        bt = _BACKTICK.search(rest)
        if bt:
            text = "$ " + bt.group(1)
    return {"time": t, "type": typ, "text": text.strip()[:240]}


def _coalesce(rows: list[dict]) -> list[dict]:
    """Zwiń IDENTYCZNE linie (ten sam typ+tekst) w jedną: {count, first, last}. koru wypluwa
    te same komendy/decyzje w kółko między cyklami — pokazujemy każdą RAZ, z licznikiem ×N,
    a najświeższą aktywność bąbelkujemy na koniec (czytelny podgląd „co się teraz dzieje")."""
    seen: dict[tuple, dict] = {}
    order: list[tuple] = []
    for r in rows:
        text = (r.get("text") or "").strip()
        if not text:
            continue  # pomiń puste linie
        key = (r.get("type"), text)
        e = seen.get(key)
        if e is None:
            e = {**r, "count": 1, "first": r.get("time", ""), "last": r.get("time", "")}
            seen[key] = e
            order.append(key)
        else:
            e["count"] += 1
            e["last"] = r.get("time") or e["last"]
            order.remove(key)
            order.append(key)  # najświeższe wystąpienie → na koniec
    return [seen[k] for k in order]


def _local_ts(ts: float | None = None) -> str:
    try:
        return _dt.datetime.fromtimestamp(ts or time.time()).astimezone().isoformat(timespec="seconds")
    except Exception:  # noqa: BLE001
        return ""


def _short_age(seconds: float | None) -> str:
    if seconds is None:
        return "?"
    if seconds < 120:
        return f"{int(seconds)}s"
    if seconds < 7200:
        return f"{int(seconds // 60)}min"
    return f"{seconds / 3600:.1f}h"


def _control_row(text: str) -> dict:
    now = _dt.datetime.now().strftime("%H:%M:%S")
    return {"time": now, "type": "CTRL", "text": text[:240], "count": 1, "first": now, "last": now}


def koru_log_tail(limit: int = 200) -> dict:
    """Ostatnie linie realnego logu koru, plus grounding źródła.

    The UI used to show an old ``queue.log`` as if it was live.  Return freshness
    and controller state with every poll so the panel can verify what it is
    looking at instead of trusting a non-moving file.
    """
    try:
        from . import ticket_meta
        from .work_queue import _loop_controller_active, _project, koru_status
        project = _project()
        log = ticket_meta.koru_log_path(_project())
        ku = koru_status()
        loop_controller = _loop_controller_active()
    except Exception:  # noqa: BLE001
        return {"lines": [], "log": None, "source": None, "status": "unavailable", "live": False}

    running = bool(ku.get("running"))
    controller = "koru" if running else ("loop://" if loop_controller else None)
    base: dict[str, Any] = {
        "log": str(log) if log else None,
        "source": str(log) if log else None,
        "project": project,
        "server_time": _local_ts(),
        "controller": controller,
        "koru_running": running,
        "loop_controller": loop_controller,
        "stale_after_seconds": _KORU_LOG_STALE_SECONDS,
    }
    if not log:
        text = f"brak queue.log/soak.log; aktywny kontroler: {controller or 'brak'}"
        return {**base, "lines": [_control_row(text)], "status": "missing", "live": False,
                "stale": False, "source_age_seconds": None, "source_mtime": None, "source_mtime_local": None}

    source_age: float | None = None
    source_mtime: float | None = None
    try:
        source_mtime = log.stat().st_mtime
        source_age = max(0.0, time.time() - source_mtime)
    except OSError:
        pass
    stale = source_age is not None and source_age > _KORU_LOG_STALE_SECONDS
    live = running and not stale
    status = "live" if live else ("stale" if stale else ("stopped" if not running else "idle"))
    rows = _coalesce([_koru_line(l) for l in ticket_meta._tail(log, int(limit))])
    if not live:
        if loop_controller and not running:
            text = (f"queue.log nie jest aktywnym kontrolerem; ostatnia zmiana {_short_age(source_age)} temu; "
                    "aktywny kontroler: loop:// (cron /api/work/loop)")
        elif stale:
            text = f"brak świeżego heartbeatu koru przez {_short_age(source_age)}; ostatnia zmiana: {_local_ts(source_mtime)}"
        elif not running:
            text = f"koru nie działa; ostatnia zmiana logu {_short_age(source_age)} temu; kontroler: {controller or 'brak'}"
        else:
            text = f"źródło logu: {log.name}; status: {status}"
        rows.append(_control_row(text))
    return {
        **base,
        "lines": rows,
        "status": status,
        "live": live,
        "stale": stale,
        "source_age_seconds": round(source_age) if source_age is not None else None,
        "source_mtime": source_mtime,
        "source_mtime_local": _local_ts(source_mtime) if source_mtime is not None else None,
    }


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
