# Author: Tom Sapletta · Part of the ifURI solution.
"""autonomy_mode — przełącznik KTO steruje autonomią: llm (API) vs human (UI-approval)."""
from __future__ import annotations

from urirun.host import autonomy_mode as am


def test_default_is_human(tmp_path, monkeypatch):
    monkeypatch.delenv("URIRUN_AUTONOMY_MODE", raising=False)
    monkeypatch.setattr(am, "_FILE", tmp_path / "mode")  # absent → safe default
    assert am.get_mode() == "human"
    assert am.is_llm() is False


def test_env_override_wins(monkeypatch):
    monkeypatch.setenv("URIRUN_AUTONOMY_MODE", "llm")
    assert am.get_mode() == "llm"
    assert am.is_llm() is True


def test_set_mode_persists(tmp_path, monkeypatch):
    monkeypatch.delenv("URIRUN_AUTONOMY_MODE", raising=False)
    f = tmp_path / "mode"
    monkeypatch.setattr(am, "_FILE", f)
    assert am.set_mode("llm")["ok"] is True
    assert f.read_text() == "llm"
    assert am.get_mode() == "llm"


def test_invalid_mode_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(am, "_FILE", tmp_path / "mode")
    r = am.set_mode("banana")
    assert r["ok"] is False and "error" in r
