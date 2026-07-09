"""Regression: environment_topology loads template and formats LLM block."""
from __future__ import annotations

from pathlib import Path

from urirun_runtime import environment_topology as et


def test_format_topology_includes_addressing_rules(monkeypatch, tmp_path):
    tpl = tmp_path / "compose/uri-runtime/environment.uri-topology.yaml"
    tpl.parent.mkdir(parents=True)
    tpl.write_text(
        "uri_runtime_environment:\n"
        "  addressing_rules:\n"
        "    - kvm://host na lenovo → POST /run na węźle\n"
        "  how_uri_processes_run: 'krok POST /run'\n",
        encoding="utf-8",
    )
    gen = tmp_path / "compose/uri-runtime/generated/environment.context.yaml"
    gen.parent.mkdir(parents=True)
    gen.write_text(
        "uri_runtime_environment:\n"
        "  generated_at: '2026-07-09T00:00:00Z'\n"
        "  live_nodes:\n"
        "    - {id: lenovo, base_url: 'http://192.168.188.201:8765', reachable: true, route_count: 59}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("URIRUN_KORU_PROJECT", str(tmp_path))
    monkeypatch.setenv("URIRUN_URI_TOPOLOGY_FILE", str(gen))

    text = et.format_topology_for_llm()
    assert "URI RUNTIME ENVIRONMENT" in text
    assert "kvm://host na lenovo" in text
    assert "lenovo" in text
    assert "192.168.188.201" in text


def test_topology_path_resolves_relative_to_project(monkeypatch, tmp_path):
    monkeypatch.setenv("URIRUN_KORU_PROJECT", str(tmp_path))
    monkeypatch.delenv("URIRUN_URI_TOPOLOGY_FILE", raising=False)
    p = et.topology_path()
    assert p == Path(tmp_path) / "compose/uri-runtime/generated/environment.context.yaml"
