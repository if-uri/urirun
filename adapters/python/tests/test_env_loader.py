# Author: Tom Sapletta · Part of the ifURI solution.
from __future__ import annotations

from pathlib import Path

from urirun.host import env_loader as el


def test_load_project_env_reads_urirun_dotenv(tmp_path, monkeypatch):
    root = tmp_path / "proj"
    (root / "urirun").mkdir(parents=True)
    (root / "urirun" / ".env").write_text("LLM_MODEL_DEVELOPER=openrouter/test/model\n", encoding="utf-8")
    monkeypatch.delenv("LLM_MODEL_DEVELOPER", raising=False)
    loaded = el.load_project_env(root)
    assert "LLM_MODEL_DEVELOPER" in loaded
    assert el.agent_model() == "openrouter/test/model"


def test_nxdo_model_strips_openrouter_prefix(monkeypatch):
    monkeypatch.setenv("KORU_NXDO_MODEL", "openrouter/google/gemini-2.5-flash")
    assert el.nxdo_model() == "google/gemini-2.5-flash"


def test_koru_ide_prefers_urirun_env(monkeypatch):
    monkeypatch.setenv("URIRUN_KORU_IDE", "aider")
    monkeypatch.setenv("KORU_TILLM_CLIENT", "claude")
    assert el.koru_ide() == "aider"
