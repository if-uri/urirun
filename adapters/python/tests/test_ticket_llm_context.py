"""ticket_llm_context — pierwszy prompt ze środowiskiem i katalogiem URI."""
from __future__ import annotations

from urirun_runtime import ticket_llm_context as tlc


def test_first_prompt_includes_environment_ticket_and_catalog(monkeypatch, tmp_path):
    monkeypatch.setenv("URIRUN_KORU_PROJECT", str(tmp_path))
    tpl = tmp_path / "compose/uri-runtime/environment.uri-topology.yaml"
    tpl.parent.mkdir(parents=True)
    tpl.write_text(
        "uri_runtime_environment:\n  addressing_rules:\n    - lenovo POST /run\n",
        encoding="utf-8",
    )
    prompt = tlc.build_first_system_prompt(
        ticket={"id": "IFURI-1", "name": "Send signal", "labels": ["signal", "kvm"]},
        node="lenovo",
    )
    assert "URI RUNTIME" in prompt or "lenovo POST" in prompt
    assert "IFURI-1" in prompt
    assert "DOSTĘPNE PROCESY URI" in prompt
    assert "kvm://host" in prompt


def test_save_and_load_llm_turns(tmp_path, monkeypatch):
    monkeypatch.setenv("URIRUN_JOURNAL_DIR", str(tmp_path))
    tlc.save_llm_turn("T-1", role="system", phase="first-prompt-environment", content="env block")
    tlc.save_llm_turn("T-1", role="tool", phase="runtime", content='{"ok": false}')
    turns = tlc.load_llm_turns("T-1")
    assert len(turns) == 2
    hist = tlc.format_turns_for_llm("T-1")
    assert "HISTORIA KONWERSACJI" in hist
    assert "env block" in hist
