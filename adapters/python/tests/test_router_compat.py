from __future__ import annotations

import types

import urirun


def test_router_effect_of_patch_uses_effect_of_route(monkeypatch):
    package = types.ModuleType("urirun_connector_router")
    routing = types.SimpleNamespace(effect_of_route=lambda uri: "ok:" + uri)
    package.routing = routing
    assert not hasattr(routing, "effect_of")

    monkeypatch.setitem(__import__("sys").modules, "urirun_connector_router", package)
    urirun._patch_router_effect_of()

    assert routing.effect_of("x://host/a/query/b") == "ok:x://host/a/query/b"
    assert routing.execution_layers({}) == ["host", "node"]
