# Author: Tom Sapletta · Part of the ifURI solution.
"""Cienki most z dashboardu do connectora ``watch://`` (watchdog zapętleń koru).

Logika (detekcja stagnacji, rootcause, przerwanie pętli, eskalacja) mieszka w
``urirun-connector-watchdog``. Tu tylko forward + degradacja, gdy connectora brak.
``unstick`` mutuje ticket → inicjuje człowiek klikając w panelu.
"""
from __future__ import annotations

from typing import Any


def _conn():
    from urirun_connector_watchdog import core
    return core


def _project() -> str:
    from .work_queue import _project as p
    return p()


def detect() -> dict[str, Any]:
    """Zapętlenia z logu + in_progress tickety BEZ dowodów postępu (pusty/kłamliwy claim),
    scalone w jedną listę alertów dla panelu."""
    try:
        c, proj = _conn(), _project()
        d = c.detect(project=proj)
        v = c.verify_progress(project=proj)
    except ImportError:
        return {"ok": False, "error": "install urirun-connector-watchdog", "stuck": [], "count": 0}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "stuck": [], "count": 0}
    stuck = list(d.get("stuck", []))
    seen = {s["id"] for s in stuck}
    for cl in v.get("unverified", []):
        if cl["id"] in seen:
            continue
        ev = cl.get("evidence", {})
        stuck.append({"id": cl["id"], "category": cl["verdict"], "rootcause": cl["why"],
                      "action": "in_progress bez pokrycia — oznacz blocked + eskaluj albo wznów realnie",
                      "streak": ev.get("streak", 0), "drive_failed": ev.get("drive_failed", 0)})
    return {"ok": True, "stuck": stuck, "count": len(stuck),
            "dead_loops": sum(1 for t in stuck if t.get("dead_loop")),
            "claims": v.get("claims", []), "project": _project()}


def action(payload: dict) -> dict[str, Any]:
    act = str((payload or {}).get("action") or "").strip()
    try:
        c = _conn()
    except ImportError:
        return {"ok": False, "error": "install urirun-connector-watchdog"}
    if act == "unstick":
        return c.ticket_command_unstick(id=str(payload.get("id") or ""), project=_project())
    if act == "circuit-break":
        return c.loop_command_circuit_break(id=str(payload.get("id") or ""), project=_project())
    if act == "sweep":
        return c.loop_command_sweep(project=_project(), apply=bool(payload.get("apply")))
    return {"ok": False, "error": f"unknown action {act!r}"}
