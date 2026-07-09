# Author: Tom Sapletta · Part of the ifURI solution.
"""Load canonical ``<project>/urirun/.env`` into the process environment.

All autonomy paths (dashboard, agent://, koru, loop) should call
``load_project_env`` so model/API choices come from one file the operator controls.
Already-set shell variables always win (the file never clobbers the real environment).
"""
from __future__ import annotations

import os
from pathlib import Path

_MODEL_KEYS = (
    "URIRUN_AGENT_MODEL",
    "LLM_MODEL_DEVELOPER",
    "LLM_MODEL",
    "URIRUN_LLM_MODEL",
)


def _load_path(path: Path) -> list[str]:
    if not path.is_file():
        return []
    loaded: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = val.strip().strip('"').strip("'")
        loaded.append(key)
    return loaded


def project_root(project: str | os.PathLike | None = None) -> Path:
    return Path(project or os.environ.get("URIRUN_KORU_PROJECT") or "~/github/if-uri").expanduser()


def urirun_env_file(project: str | os.PathLike | None = None) -> Path:
    return project_root(project) / "urirun" / ".env"


def load_project_env(project: str | os.PathLike | None = None) -> list[str]:
    """Load ``urirun/.env`` then optional ``<project>/.env``; return keys newly set."""
    root = project_root(project)
    keys: list[str] = []
    keys.extend(_load_path(root / "urirun" / ".env"))
    keys.extend(_load_path(root / ".env"))
    return keys


def agent_model() -> str:
    """OpenRouter/litellm model id for ticket/agent work (aider, planning, chat)."""
    for key in _MODEL_KEYS:
        value = os.environ.get(key, "").strip()
        if value:
            return value
    return ""


def default_agent() -> str:
    """Headless agent id for agent:// (aider|claude|codex|…); ``auto`` = connector preference."""
    return (os.environ.get("URIRUN_AGENT_DEFAULT") or "auto").strip() or "auto"


def koru_ide() -> str:
    """Shell LLM client koru drives via tillm (--ide)."""
    for key in ("URIRUN_KORU_IDE", "KORU_TILLM_CLIENT", "KORU_AUTOPILOT_IDE"):
        value = os.environ.get(key, "").strip()
        if value and value.lower() != "auto":
            return value
    return "aider"


def nxdo_model() -> str:
    """Model id for nxdo plan (-m flag, without openrouter/ prefix when using OpenRouter base)."""
    raw = (
        os.environ.get("KORU_NXDO_MODEL")
        or os.environ.get("LLM_MODEL_PLANNER")
        or os.environ.get("LLM_MODEL")
        or "google/gemini-2.5-flash"
    ).strip()
    if raw.startswith("openrouter/"):
        return raw.split("/", 1)[1]
    return raw
