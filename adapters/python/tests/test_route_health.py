# Author: Tom Sapletta · Part of the ifURI solution.
"""route_health — grounding środowiskowy dla planera LLM (które trasy realnie działają na node)."""
from __future__ import annotations

from urirun.host import route_health as rh


def test_seed_grounding_block_for_lenovo():
    block = rh.grounding_block("lenovo")
    assert "ROUTE-HEALTH" in block
    assert "ODRADZANE" in block and "PREFEROWANE" in block and "ZASADA" in block


def test_unknown_node_is_empty():
    assert rh.route_health("nonexistent-node") == {}
    assert rh.grounding_block("nonexistent-node") == ""


def test_record_persists_and_reads_back(tmp_path, monkeypatch):
    monkeypatch.setattr(rh, "_STORE", tmp_path / "rh.json")
    rh.record("nodeX", {"env": "test-env", "preferred": [{"route": "a/b", "recipe": "do a"}]})
    assert (tmp_path / "rh.json").is_file()
    h = rh.route_health("nodeX")
    assert h["env"] == "test-env"
    assert any(p["route"] == "a/b" for p in h["preferred"])


def test_persisted_extends_seed_without_dropping_it(tmp_path, monkeypatch):
    monkeypatch.setattr(rh, "_STORE", tmp_path / "rh.json")
    rh.record("lenovo", {"preferred": [{"route": "new/route", "recipe": "x"}]})
    routes = {p["route"] for p in rh.route_health("lenovo")["preferred"]}
    assert "new/route" in routes            # learned finding
    assert "abs/command/click" in routes    # original seed knowledge kept


def test_merge_list_dedups_by_key():
    merged = rh._merge_list([{"route": "a"}], [{"route": "a"}, {"route": "b"}], "route")
    assert [m["route"] for m in merged] == ["a", "b"]
