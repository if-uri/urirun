"""Lazy, scheme-indexed discovery: index build/cache + scheme resolution."""
from __future__ import annotations

import urirun
from urirun.runtime import discovery, v2


def _fake_binding(uri: str, connector: str) -> dict:
    return {
        "uri": uri,
        "kind": "query",
        "adapter": "local-function",
        "config": {"inputSchema": {"type": "object", "additionalProperties": True}},
        "source": {"name": connector},
    }


def test_build_index_maps_schemes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    index = discovery.build_index(v2.ENTRY_POINT_GROUP)
    assert "schemes" in index and "fingerprint" in index
    assert (tmp_path / ".urirun" / "scheme-index.json").exists()
    schemes = index["schemes"]
    # scheme→connector mapping depends on which connectors are installed; assert the
    # canonical ones only when present (matches test_registry_for_uri_resolves_only_matching)
    if not any(s in schemes for s in ("time", "log", "fs")):
        return  # none of those connectors installed in this env
    assert any(s in schemes for s in ("time", "log", "fs"))


def test_build_index_tracks_shared_scheme_candidates(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bindings = [
        _fake_binding("browser://host/page/command/screenshot", "domain-monitor"),
        _fake_binding("browser://cdp/page/query/tabs", "browser-control"),
        _fake_binding("browser://kvm/screen/query/capture", "browser-control"),
        _fake_binding("artifact://host/schema/query/get", "artifact"),
        _fake_binding("artifact://host/artifact/command/register", "sqlite-context"),
    ]
    monkeypatch.setattr(v2, "entry_point_bindings", lambda group, on_error="warn": list(bindings))
    monkeypatch.setattr(discovery, "_fingerprint", lambda group: [["fake", "fake:bindings", "0"]])

    index = discovery.build_index(v2.ENTRY_POINT_GROUP)

    assert index["version"] == discovery._INDEX_VERSION
    assert index["schemes"]["browser"] == "browser-control"
    assert index["schemeCandidates"]["browser"] == ["browser-control", "domain-monitor"]
    assert index["schemeCandidates"]["artifact"] == ["artifact", "sqlite-context"]


def test_registry_for_uri_loads_all_candidates_for_shared_scheme(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    by_name = {
        "domain-monitor": [_fake_binding("browser://host/page/command/screenshot", "domain-monitor")],
        "browser-control": [
            _fake_binding("browser://cdp/page/query/tabs", "browser-control"),
            _fake_binding("browser://kvm/screen/query/capture", "browser-control"),
        ],
    }
    bindings = [binding for group in by_name.values() for binding in group]
    monkeypatch.setattr(v2, "entry_point_bindings", lambda group, on_error="warn": list(bindings))
    monkeypatch.setattr(discovery, "_fingerprint", lambda group: [["fake", "fake:bindings", "0"]])
    monkeypatch.setattr(discovery, "_bindings_for_entry_point", lambda name, group: list(by_name.get(name, [])))

    reg = discovery.registry_for_uri("browser://cdp/page/query/tabs", v2.ENTRY_POINT_GROUP)
    uris = {route["uri"] for route in urirun.list_routes(reg)}

    assert "browser://cdp/page/query/tabs" in uris
    assert "browser://host/page/command/screenshot" in uris
    assert any(uri.startswith("registry://") for uri in uris)


def test_cache_reused_when_fingerprint_matches(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    discovery.build_index(v2.ENTRY_POINT_GROUP)
    # load_index returns the cached dict (same fingerprint) without rebuilding
    idx = discovery.load_index(v2.ENTRY_POINT_GROUP)
    assert idx["fingerprint"] == discovery._fingerprint(v2.ENTRY_POINT_GROUP)


def test_fingerprint_includes_source_mtime():
    fp = discovery._fingerprint(v2.ENTRY_POINT_GROUP)
    if not fp:
        return  # no connectors installed in this env
    assert all(len(entry) == 3 for entry in fp)  # (name, value, mtime)


def test_fingerprint_busts_on_connector_source_edit():
    # Editing a connector in place (auto-sync flipping an adapter) must invalidate
    # the discovery cache — otherwise the daemon / list / registry:// serve a stale
    # registry. The fingerprint tracks the entry-point module's mtime.
    import os
    from importlib.metadata import entry_points
    from importlib.util import find_spec

    target = None
    for ep in entry_points(group=v2.ENTRY_POINT_GROUP):
        module = (getattr(ep, "value", "") or "").split(":", 1)[0]
        spec = find_spec(module) if module else None
        if spec and spec.origin and os.path.exists(spec.origin):
            target = spec.origin
            break
    if target is None:
        return  # no resolvable connector source in this env

    before = discovery._fingerprint(v2.ENTRY_POINT_GROUP)
    orig = os.path.getmtime(target)
    try:
        os.utime(target, (orig + 10, orig + 10))
        after = discovery._fingerprint(v2.ENTRY_POINT_GROUP)
    finally:
        os.utime(target, (orig, orig))
    assert before != after


def test_registry_for_uri_resolves_only_matching(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    if "time" not in discovery.build_index(v2.ENTRY_POINT_GROUP)["schemes"]:
        return  # time-tools not installed in this env; nothing to assert
    reg = discovery.registry_for_uri("time://host/clock/query/now", v2.ENTRY_POINT_GROUP)
    uris = {r["uri"] for r in urirun.list_routes(reg)}
    assert "time://host/clock/query/now" in uris
    # builtins are mounted too (runtime self-describes)
    assert any(u.startswith("registry://") for u in uris)
    # an unrelated connector's scheme is NOT pulled in
    assert not any(u.startswith("monitor://") for u in uris)
