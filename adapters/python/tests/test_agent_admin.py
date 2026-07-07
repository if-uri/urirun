# Author: Tom Sapletta · Part of the ifURI solution.
"""agent_admin: koru pędzi headless bez człowieka → agent musi ZAPISYWAĆ bez pytania o zgodę
(--dangerously-skip-permissions), inaczej stalluje na promptach. Domyślnie autonomous ON,
opt-out URIRUN_AGENT_AUTONOMOUS=0, explicit _autonomous wygrywa."""
from __future__ import annotations

from urirun.host import agent_admin as aa


def test_autonomous_default_on_by_default(monkeypatch):
    monkeypatch.delenv("URIRUN_AGENT_AUTONOMOUS", raising=False)
    assert aa._autonomous_default(None) is True


def test_autonomous_opt_out(monkeypatch):
    monkeypatch.setenv("URIRUN_AGENT_AUTONOMOUS", "0")
    assert aa._autonomous_default(None) is False


def test_autonomous_explicit_overrides_env(monkeypatch):
    monkeypatch.setenv("URIRUN_AGENT_AUTONOMOUS", "0")
    assert aa._autonomous_default(True) is True
    monkeypatch.delenv("URIRUN_AGENT_AUTONOMOUS", raising=False)
    assert aa._autonomous_default(False) is False


def test_agent_cmd_claude_autonomous_adds_skip_flag():
    cmd = aa._agent_cmd("/opt/claude", "claude", "Execute ticket X", True)
    assert "--dangerously-skip-permissions" in cmd
    assert "-p" in cmd


def test_agent_cmd_claude_supervised_no_flag():
    cmd = aa._agent_cmd("/opt/claude", "claude", "Execute ticket X", False)
    assert "--dangerously-skip-permissions" not in cmd


def test_agent_cmd_codex_uses_exec_never_skip_flag():
    cmd = aa._agent_cmd("/opt/codex", "codex", "Execute ticket X", True)
    assert "exec" in cmd and "--dangerously-skip-permissions" not in cmd
