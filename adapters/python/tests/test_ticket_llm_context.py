"""ticket_llm_context — pierwszy prompt ze środowiskiem i katalogiem URI."""
from __future__ import annotations

import json

from urirun_runtime import ticket_llm_context as tlc


def test_live_uri_process_schemas_from_routes(monkeypatch):
    sample = [
        {
            "uri": "kvm://host/ui/command/type-verified",
            "title": "Type with OCR verify",
            "effect": "mutate",
            "safe": True,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "default": ""},
                    "submit": {"type": "boolean", "default": False},
                    "draft_expect": {"type": "string"},
                },
                "required": ["text"],
            },
        }
    ]

    def fake_fetch(node, *, node_url=""):
        return sample

    monkeypatch.setattr(tlc, "fetch_routes_from_node", fake_fetch)
    block = tlc.build_live_uri_process_schemas("lenovo")
    assert "kvm://host/ui/command/type-verified" in block
    assert '"submit"' in block
    assert '"draft_expect"' in block
    assert "Type with OCR verify" in block


def test_first_prompt_includes_live_route_schemas(monkeypatch, tmp_path):
    monkeypatch.setenv("URIRUN_KORU_PROJECT", str(tmp_path))
    tpl = tmp_path / "compose/uri-runtime/environment.uri-topology.yaml"
    tpl.parent.mkdir(parents=True)
    tpl.write_text("uri_runtime_environment:\n  addressing_rules:\n  - lenovo\n", encoding="utf-8")

    monkeypatch.setattr(
        tlc,
        "fetch_routes_from_node",
        lambda node, **kw: [{
            "uri": "kvm://host/ui/command/type-verified",
            "title": "type-verified",
            "inputSchema": {"properties": {"text": {"type": "string"}}},
        }],
    )
    prompt = tlc.build_first_system_prompt(ticket={"id": "T-1"}, node="lenovo")
    assert "URI-PROCESY WĘZŁA" in prompt
    assert "type-verified" in prompt
    assert '"text"' in prompt


def test_offline_route_schemas_fallback(monkeypatch, tmp_path):
    root = tmp_path / "urirun-llm-runtime"
    jdir = root / "docs" / "llm"
    jdir.mkdir(parents=True)
    snap = jdir / "route_schemas_lenovo.json"
    snap.write_text(json.dumps({
        "routes": [{
            "uri": "kvm://host/ui/command/type-verified",
            "title": "type-verified",
            "inputSchema": {"properties": {"text": {"type": "string"}, "x": {"type": "integer"}}},
        }]
    }), encoding="utf-8")
    monkeypatch.setenv("URIRUN_LLM_RUNTIME_ROOT", str(root))
    monkeypatch.setattr(tlc, "_node_base_url", lambda n: "http://127.0.0.1:1")
    routes = tlc.fetch_routes_from_node("lenovo")
    assert any(r.get("uri") == "kvm://host/ui/command/type-verified" for r in routes)


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
    assert "urirun:processes" in prompt


def test_save_and_load_llm_turns(tmp_path, monkeypatch):
    monkeypatch.setenv("URIRUN_JOURNAL_DIR", str(tmp_path))
    tlc.save_llm_turn("T-1", role="system", phase="first-prompt-environment", content="env block")
    tlc.save_llm_turn("T-1", role="tool", phase="runtime", content='{"ok": false}')
    turns = tlc.load_llm_turns("T-1")
    assert len(turns) == 2
    hist = tlc.format_turns_for_llm("T-1")
    assert "HISTORIA KONWERSACJI" in hist
    assert "env block" in hist
