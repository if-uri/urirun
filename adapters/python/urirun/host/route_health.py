# Author: Tom Sapletta · Part of the ifURI solution.
"""route_health — grounding ŚRODOWISKOWY dla planerów LLM: KTÓRE trasy realnie działają na node.

Registry mówi CO można (wszystkie route'y). To mówi CO TU DZIAŁA: które trasy lądują, które
zawodzą i czym je zastąpić, plus zasady (ok≠efekt). Bez tego LLM planuje poprawnie-ale-naiwnie
(np. window/command/focus, którego atspi nie obsłuży na Electronie). Z tym — planuje WYKONALNIE.

Źródło: seed (twarda wiedza z pamięci `kvm-keyboard-batch-solved`) scalony z persystentnym
storem (findings/uczenie). `grounding_block(node)` → tekst do wstrzyknięcia w prompt planera.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_STORE = Path(os.environ.get("URIRUN_ROUTE_HEALTH")
              or "~/.urirun/host-dashboard/route-health.json").expanduser()

# Twarda wiedza empiryczna (zweryfikowana 2026-07-06 wysyłką Signal). Persystentny store ją nadpisuje/rozszerza.
_SEED: dict[str, dict] = {
    "lenovo": {
        "env": "Wayland/GNOME, single-monitor 1920x1080 scale 1.0; Signal/Chrome = Electron",
        "deprecated": [
            {"route": "window/command/focus", "why": "atspi NIE widzi okien Electron (Signal/Chrome)"},
            {"route": "ui/command/click", "why": "atspi ślepy + vision-OCR zawodzi na polu compose"},
            {"route": "ui/query/find", "why": "j.w. — nie zlokalizuje elementów Electron"},
            {"route": "input/command/key", "why": "pojedynczy klawisz gubiony (uinput tworzone per-call, warmup 1.2s)"},
            {"route": "abs/command/click (po fokusie apki, osobne wywołanie)",
             "why": "re-triggeruje GNOME overview; kursor przy hot-corner. Pikselowy klik konkretnego elementu zawodzi"},
            {"route": "cdp/session/ensure",
             "why": "otwiera CZYSTE okno Chrome (wymaga logowania) — NIE Twoja zalogowana sesja. Dla istniejącego zalogowanego LinkedIn: NIE używaj, fokusuj istniejący Chrome przez task/command/run"},
        ],
        "preferred": [
            {"route": "task/command/run", "recipe": "batch = jedno CIEPŁE uinput; klawisze/kombinacje działają. "
             "Fokus apki: steps=[{op:click,x:3,y:3}(hot-corner), {op:type,text:'<app>'}, {op:key,keys:'return'}]"},
            {"route": "abs/command/click", "recipe": "atomowy stabilny klik; współrzędne EKRANU 1:1 = 1920x1080"},
            {"route": "screen/query/capture", "recipe": "po KAŻDEJ mutacji → weryfikuj (ok≠efekt)"},
            {"route": "cdp/page/command/dom-click",
             "recipe": "DLA PRZEGLĄDAREK: klik elementu po selektorze CSS (np. Start a post) — omija piksele i overview; wymaga Chrome z remote-debugging, ale nie 'ensure' gdy liczy się istniejąca sesja użytkownika"},
        ],
        "principles": [
            "ok:true z komendy != efekt na ekranie → capture+verify po każdej mutacji",
            "potwierdź treść w polu PRZED wysłaniem (verify-before-submit)",
            "type-verified NIE wdrożony na tym node (IFURI-059) → verify orkiestruj z hosta",
            "jeśli browser/query/sessions pokazuje zalogowany profil bez CDP, NIE uruchamiaj cdp/session/ensure jako 'naprawy' — to inna, throwaway sesja",
        ],
    }
}


def _merge_list(seed_items: list[Any], persisted_items: list[Any], key: str) -> list[Any]:
    merged: list[Any] = []
    seen: set[Any] = set()
    for item in [*(seed_items or []), *(persisted_items or [])]:
        marker = item.get(key) if isinstance(item, dict) else item
        if marker in seen:
            continue
        seen.add(marker)
        merged.append(item)
    return merged


def _merge_health(seed: dict[str, Any], persisted: dict[str, Any]) -> dict[str, Any]:
    if not seed:
        return persisted or {}
    if not persisted:
        return seed or {}
    merged = {**seed, **persisted}
    merged["deprecated"] = _merge_list(seed.get("deprecated") or [], persisted.get("deprecated") or [], "route")
    merged["preferred"] = _merge_list(seed.get("preferred") or [], persisted.get("preferred") or [], "route")
    merged["principles"] = _merge_list(seed.get("principles") or [], persisted.get("principles") or [], "")
    return merged


def _load() -> dict:
    try:
        return json.loads(_STORE.read_text()) if _STORE.is_file() else {}
    except Exception:  # noqa: BLE001
        return {}


def route_health(node: str = "") -> dict[str, Any]:
    """Zdrowie tras dla node (persystentny store nadpisuje seed). {} jeśli nieznane."""
    persisted = _load()
    return _merge_health(_SEED.get(node) or {}, persisted.get(node) or {})


def record(node: str, health: dict) -> dict:
    """Ucz się: zapisz/zaktualizuj zdrowie tras node (findings/refleksja mogą wołać)."""
    data = _load()
    data[node] = _merge_health(route_health(node), health)
    try:
        _STORE.parent.mkdir(parents=True, exist_ok=True)
        _STORE.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    return data[node]


def grounding_block(node: str = "") -> str:
    """Tekst do wstrzyknięcia w prompt planera obok registry. Pusty gdy brak wiedzy o node."""
    h = route_health(node)
    if not h:
        return ""
    out = [f"# ROUTE-HEALTH node '{node}' ({h.get('env', '')}) — planuj TYLKO wykonalnie:"]
    for d in h.get("deprecated", []):
        out.append(f"#   ODRADZANE {d['route']} — {d['why']}")
    for p in h.get("preferred", []):
        out.append(f"#   PREFEROWANE {p['route']} — {p['recipe']}")
    for pr in h.get("principles", []):
        out.append(f"#   ZASADA: {pr}")
    return "\n".join(out)
