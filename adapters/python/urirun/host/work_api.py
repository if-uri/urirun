# Author: Tom Sapletta · Part of the ifURI solution.
"""Samodokumentujące API strony /work — katalog KAŻDEJ akcji sterowalnej przez HTTP.

Cel: całą stronę /work (i każdą jej akcję z UI) da się wykonać przez API bez klikania —
GET ``/api/work/actions`` zwraca pełny katalog (ścieżka, metoda, parametry, opis), a zwykłe
endpointy ``/api/work/*`` wykonują. Dzięki temu klient (skrypt, agent, inny node) steruje
panelem programowo tak samo jak człowiek myszką.
"""
from __future__ import annotations

from typing import Any

_BASE = "/api/work"

# (metoda, ścieżka, {param: opis}, opis-akcji)
_CATALOG: list[dict[str, Any]] = [
    {"method": "GET", "path": f"{_BASE}/status", "params": {}, "desc": "Werdykt ciągłości: OK/AT_RISK/STOPPED + koru + liczniki"},
    {"method": "GET", "path": f"{_BASE}/queue", "params": {}, "desc": "Kolejka koru: tickety wzbogacone (llm/node/procesy/schedule)"},
    {"method": "GET", "path": f"{_BASE}/runs", "params": {"tail": "int"}, "desc": "Rekordy biegów (approve/agent) + logi"},
    {"method": "GET", "path": f"{_BASE}/ops", "params": {}, "desc": "Operacje do zatwierdzenia"},
    {"method": "GET", "path": f"{_BASE}/uri-log", "params": {"limit": "int"}, "desc": "Feed twin://monitor/event"},
    {"method": "GET", "path": f"{_BASE}/koru-log", "params": {"tail": "int"}, "desc": "Realny log koru, powtórki zwinięte ×N (czas lokalny)"},
    {"method": "GET", "path": f"{_BASE}/ticket/detail", "params": {"id": "str"}, "desc": "Pełne procesy + edytowalna meta ticketu"},
    {"method": "GET", "path": f"{_BASE}/cron", "params": {}, "desc": "Wpisy cron + kalendarz nadchodzących uruchomień"},
    {"method": "GET", "path": f"{_BASE}/cron/export", "params": {"fmt": "ics|gcsv", "id": "str", "mode": "rrule|events"}, "desc": "Eksport harmonogramu (.ics / Google CSV)"},
    {"method": "GET", "path": f"{_BASE}/watchdog", "params": {}, "desc": "Wykryte zapętlenia + rootcause + dead_loop/cycles"},
    {"method": "GET", "path": f"{_BASE}/agents", "params": {}, "desc": "Dostępne narzędzia AI (executor agent://)"},
    {"method": "POST", "path": f"{_BASE}/ops/confirm", "params": {"id": "str"}, "desc": "Zatwierdź operację → uruchom (Runs)"},
    {"method": "POST", "path": f"{_BASE}/ops/reject", "params": {"id": "str"}, "desc": "Odrzuć operację"},
    {"method": "POST", "path": f"{_BASE}/shell", "params": {"cmd": "str"}, "desc": "Konsola shell (gated URIRUN_WORK_SHELL)"},
    {"method": "POST", "path": f"{_BASE}/ticket", "params": {"id": "str", "action": "unblock|start|done|block|ready|note", "note": "str"}, "desc": "Akcja na ticketcie (status/notatka)"},
    {"method": "POST", "path": f"{_BASE}/ticket/edit", "params": {"id": "str", "name": "str", "description": "str", "llm": "str", "node": "str", "allow": "str", "deny": "str", "schedule": "str"}, "desc": "Edytuj ticket (tekst→planfile, reszta→meta)"},
    {"method": "POST", "path": f"{_BASE}/cron", "params": {"action": "add|edit|remove", "schedule": "str", "command": "str", "label": "str", "id": "str"}, "desc": "CRUD wpisów cron"},
    {"method": "POST", "path": f"{_BASE}/watchdog", "params": {"action": "unstick|circuit-break|sweep", "id": "str", "apply": "bool"}, "desc": "Przerwij pętlę / circuit-break (diagnoza) / sweep"},
    {"method": "POST", "path": f"{_BASE}/agents", "params": {"action": "run-ticket", "id": "str", "agent": "claude|codex|auto"}, "desc": "Wykonaj ticket REALNYM agentem (claude -p) → Runs"},
    {"method": "POST", "path": f"{_BASE}/koru", "params": {"lane": "str"}, "desc": "Uruchom/kontynuuj pętlę koru"},
]

# op → (metoda, ścieżka) dla unijnego dispatchera POST /api/work/action
_OPS = {
    "ops.confirm": ("POST", f"{_BASE}/ops/confirm"), "ops.reject": ("POST", f"{_BASE}/ops/reject"),
    "shell": ("POST", f"{_BASE}/shell"), "ticket": ("POST", f"{_BASE}/ticket"),
    "ticket.edit": ("POST", f"{_BASE}/ticket/edit"), "cron": ("POST", f"{_BASE}/cron"),
    "watchdog": ("POST", f"{_BASE}/watchdog"), "agents": ("POST", f"{_BASE}/agents"),
    "koru": ("POST", f"{_BASE}/koru"),
}


def catalog() -> dict[str, Any]:
    return {"ok": True, "base": _BASE, "actions": _CATALOG, "ops": sorted(_OPS),
            "hint": "GET dowolnej ścieżki czyta stan; POST wykonuje akcję. "
                    "Unijny: POST /api/work/action {op, ...params}."}


def op_path(op: str) -> str | None:
    """op (np. 'watchdog', 'agents') → ścieżka POST, dla unijnego dispatchera."""
    t = _OPS.get(op)
    return t[1] if t else None
