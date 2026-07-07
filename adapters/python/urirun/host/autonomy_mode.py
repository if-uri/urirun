# Author: Tom Sapletta · Part of the ifURI solution.
"""autonomy_mode — przełącznik KTO steruje autonomią: LLM (API) czy CZŁOWIEK (UI).

`llm`   — pełna autonomia: bezpieczne decyzje (safe-auto) wykonują się przez API/LLM bez pytania.
`human` — kontrola operatora: KAŻDA decyzja (nawet safe-auto) czeka na zatwierdzenie w UI /work.

Stan trzymany w pliku (widzą go i dashboard, i pętla loop:// — jedno źródło prawdy). Domyślnie
`human` (bezpiecznie). Loop czyta `is_llm()` i degraduje run-agent→agent-gated w trybie human.
"""
from __future__ import annotations

import os
from pathlib import Path

_FILE = Path(os.environ.get("URIRUN_AUTONOMY_MODE_FILE")
             or "~/.urirun/host-dashboard/autonomy-mode").expanduser()
_VALID = ("llm", "human")


def get_mode() -> str:
    env = (os.environ.get("URIRUN_AUTONOMY_MODE") or "").strip().lower()
    if env in _VALID:
        return env
    try:
        m = _FILE.read_text().strip().lower()
        return m if m in _VALID else "human"
    except OSError:
        return "human"


def set_mode(mode: str) -> dict:
    m = (mode or "").strip().lower()
    if m not in _VALID:
        return {"ok": False, "error": f"mode musi być {_VALID}"}
    try:
        _FILE.parent.mkdir(parents=True, exist_ok=True)
        _FILE.write_text(m, encoding="utf-8")
    except OSError as exc:
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "mode": m}


def is_llm() -> bool:
    """True = LLM steruje (safe-auto wykonuje się); False = człowiek (wszystko przez UI-approval)."""
    return get_mode() == "llm"
