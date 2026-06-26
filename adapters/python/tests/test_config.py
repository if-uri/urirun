from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from urirun.node.config import (
    _coerce_node_url,
    _node_name_from_url,
    add_node,
    default_host_config,
    host_config_path,
    init_host,
    load_host_config,
    save_host_config,
)


# ─── default_host_config ─────────────────────────────────────────────────────

def test_default_host_config_structure():
    cfg = default_host_config(name="testhost")
    assert cfg["host"]["name"] == "testhost"
    assert "nodes" in cfg
    assert isinstance(cfg["nodes"], list)


def test_default_host_config_uses_hostname_when_no_name():
    import socket
    cfg = default_host_config()
    assert cfg["host"]["name"] == socket.gethostname()


# ─── host_config_path ────────────────────────────────────────────────────────

def test_host_config_path_uses_given_path(tmp_path):
    p = host_config_path(str(tmp_path / "custom.json"))
    assert str(p).endswith("custom.json")


# ─── load_host_config / save_host_config ─────────────────────────────────────

def test_load_missing_config_returns_default(tmp_path):
    p = str(tmp_path / "nonexistent.json")
    cfg = load_host_config(p)
    assert "host" in cfg
    assert cfg["nodes"] == []


def test_save_then_load_roundtrip(tmp_path):
    p = str(tmp_path / "config.json")
    cfg = default_host_config(name="mybox")
    save_host_config(cfg, p)
    loaded = load_host_config(p)
    assert loaded["host"]["name"] == "mybox"


def test_load_fills_missing_fields(tmp_path):
    p = Path(tmp_path) / "sparse.json"
    p.write_text('{"host": {"name": "x"}}', encoding="utf-8")
    loaded = load_host_config(str(p))
    assert "nodes" in loaded
    assert "version" in loaded


# ─── init_host ───────────────────────────────────────────────────────────────

def test_init_host_writes_config(tmp_path):
    p = str(tmp_path / "init.json")
    cfg = init_host(p, name="inithost")
    assert cfg["host"]["name"] == "inithost"
    assert Path(p).exists()


# ─── add_node ────────────────────────────────────────────────────────────────

def test_add_node_adds_entry(tmp_path):
    p = str(tmp_path / "c.json")
    init_host(p, name="host")
    add_node(p, "laptop", "http://laptop:8765")
    cfg = load_host_config(p)
    names = [n["name"] for n in cfg["nodes"]]
    assert "laptop" in names


def test_add_node_replaces_existing_name(tmp_path):
    p = str(tmp_path / "c.json")
    init_host(p, name="host")
    add_node(p, "laptop", "http://laptop:8765")
    add_node(p, "laptop", "http://laptop-new:9000")
    cfg = load_host_config(p)
    nodes = [n for n in cfg["nodes"] if n["name"] == "laptop"]
    assert len(nodes) == 1
    assert "9000" in nodes[0]["url"]


def test_add_node_sorted_alphabetically(tmp_path):
    p = str(tmp_path / "c.json")
    init_host(p, name="host")
    add_node(p, "zoo-node", "http://zoo:8765")
    add_node(p, "alpha-node", "http://alpha:8765")
    cfg = load_host_config(p)
    names = [n["name"] for n in cfg["nodes"]]
    assert names == sorted(names)


# ─── _coerce_node_url ────────────────────────────────────────────────────────

def test_coerce_node_url_full_url():
    assert _coerce_node_url("http://laptop:8765") == "http://laptop:8765"


def test_coerce_node_url_host_with_port():
    assert _coerce_node_url("laptop:9000") == "http://laptop:9000"


def test_coerce_node_url_host_without_port():
    result = _coerce_node_url("laptop")
    assert result.startswith("http://laptop:")


def test_coerce_node_url_empty_raises():
    with pytest.raises(ValueError):
        _coerce_node_url("")


def test_coerce_node_url_strips_trailing_slash():
    assert _coerce_node_url("http://laptop:8765/") == "http://laptop:8765"


# ─── _node_name_from_url ─────────────────────────────────────────────────────

def test_node_name_from_url_simple():
    name = _node_name_from_url("http://laptop:8765", 1)
    assert "laptop" in name


def test_node_name_from_url_includes_port():
    name = _node_name_from_url("http://laptop:9000", 1)
    assert "9000" in name


def test_node_name_from_url_bad_url_uses_index():
    name = _node_name_from_url("not-a-url", 3)
    assert name  # must not crash; fallback is fine
