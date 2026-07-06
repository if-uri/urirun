# Author: Tom Sapletta · Part of the ifURI solution.
"""Thin bridge from the /work dashboard to the ``cron://`` connector.

The scheduling logic (crontab CRUD, upcoming-runs calendar, iCalendar / Google-CSV export)
lives in ``urirun-connector-cron`` — a URI-native connector — so it is one source of truth,
testable and reusable off the dashboard. This module just forwards, and degrades to a clear
"install the connector" message if it is not present. Writing crontab is a persistent-config
change: it is always driven by the human clicking in the panel, never by the loop.
"""
from __future__ import annotations

from typing import Any


def _conn():
    from urirun_connector_cron import core  # lazy: optional connector
    return core


def _missing() -> dict[str, Any]:
    return {"ok": False, "error": "install urirun-connector-cron (pip install -e urirun-connector-cron)"}


def state() -> dict[str, Any]:
    try:
        c = _conn()
        return {"ok": True, "entries": c._entries(), "calendar": c._calendar(7)}
    except ImportError:
        return _missing()
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def add_entry(schedule: str, command: str, label: str = "") -> dict[str, Any]:
    try:
        return _conn().entry_command_add(schedule=schedule, command=command, label=label)
    except ImportError:
        return _missing()


def edit_entry(cid: str, *, schedule: str = "", command: str = "", label: str | None = None) -> dict[str, Any]:
    try:
        return _conn().entry_command_edit(id=cid, schedule=schedule, command=command, label=label)
    except ImportError:
        return _missing()


def remove_entry(cid: str) -> dict[str, Any]:
    try:
        return _conn().entry_command_remove(id=cid)
    except ImportError:
        return _missing()


def export(fmt: str, *, id: str = "", mode: str = "rrule", days: int = 30) -> dict[str, Any]:
    try:
        c = _conn()
        return c.export_query_google_csv(days=int(days)) if fmt == "gcsv" \
            else c.export_query_ics(id=id, mode=mode, days=int(days))
    except ImportError:
        return _missing()
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def action(payload: dict) -> dict[str, Any]:
    """POST dispatch: {action: add|edit|remove, …}."""
    act = str((payload or {}).get("action") or "").strip()
    if act == "add":
        return add_entry(str(payload.get("schedule") or ""), str(payload.get("command") or ""),
                         str(payload.get("label") or ""))
    if act == "edit":
        return edit_entry(str(payload.get("id") or ""), schedule=str(payload.get("schedule") or ""),
                          command=str(payload.get("command") or ""), label=payload.get("label"))
    if act == "remove":
        return remove_entry(str(payload.get("id") or ""))
    return {"ok": False, "error": f"unknown action {act!r}"}
