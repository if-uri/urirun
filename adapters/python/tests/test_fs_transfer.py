from __future__ import annotations

import tempfile
from pathlib import Path

from urirun.host.fs_transfer import (
    fs_file_transfer_binding,
    fs_file_transfer_fallback_bindings,
    node_has_route,
    route_key,
)


# ─── route_key ───────────────────────────────────────────────────────────────

def test_route_key_extracts_scheme_and_path():
    assert route_key("fs://node/file/query/read-b64") == ("fs", "file/query/read-b64")


def test_route_key_no_path():
    assert route_key("fs://node") == ("fs", "")


def test_route_key_bad_uri_returns_original():
    assert route_key("not-a-uri") == ("not-a-uri", "")


# ─── node_has_route ──────────────────────────────────────────────────────────

def test_node_has_route_found():
    routes = [
        {"uri": "fs://laptop/file/query/read-b64"},
        {"uri": "fs://laptop/file/command/write-b64"},
    ]
    # host-segment is ignored: only scheme+path matters
    assert node_has_route(routes, "fs://otherhost/file/query/read-b64") is True


def test_node_has_route_not_found():
    routes = [{"uri": "fs://laptop/file/query/read-b64"}]
    assert node_has_route(routes, "fs://laptop/file/command/write-b64") is False


def test_node_has_route_empty():
    assert node_has_route([], "fs://n/file/query/read-b64") is False


# ─── fs_file_transfer_binding ────────────────────────────────────────────────

def test_binding_read_route_uses_read_b64_export():
    b = fs_file_transfer_binding("fs://node/file/query/read-b64")
    assert b["python"]["export"] == "read_b64"
    assert "max_bytes" in b["inputSchema"]["properties"]
    assert b["inputSchema"]["required"] == ["path"]


def test_binding_write_route_uses_write_b64_export():
    b = fs_file_transfer_binding("fs://node/file/command/write-b64")
    assert b["python"]["export"] == "write_b64"
    assert "bytes_b64" in b["inputSchema"]["properties"]
    assert "path" in b["inputSchema"]["required"]
    assert "bytes_b64" in b["inputSchema"]["required"]


def test_binding_kind_is_local_function_subprocess():
    b = fs_file_transfer_binding("fs://n/file/query/read-b64")
    assert b["kind"] == "local-function"
    assert b["adapter"] == "local-function-subprocess"


# ─── fs_file_transfer_fallback_bindings ──────────────────────────────────────

def test_fallback_bindings_filters_non_transfer_uris():
    uris = [
        "fs://node/file/query/read-b64",
        "fs://node/file/command/write-b64",
        "env://node/runtime/query/health",   # not a transfer URI
    ]
    result = fs_file_transfer_fallback_bindings(uris)
    assert set(result["bindings"]) == {
        "fs://node/file/query/read-b64",
        "fs://node/file/command/write-b64",
    }


def test_fallback_bindings_empty_when_no_transfer_uris():
    result = fs_file_transfer_fallback_bindings(["env://n/runtime/query/health"])
    assert result["bindings"] == {}
    assert result["version"] == "urirun.bindings.v2"


# ─── read_b64 / write_b64 (filesystem I/O) ───────────────────────────────────

def test_write_then_read_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = str(Path(tmpdir) / "file.txt")
        content = b"hello world"
        encoded = base64.b64encode(content).decode()

        wr = write_b64(path=path, bytes_b64=encoded)
        assert wr["ok"] is True

        rd = read_b64(path=path)
        assert rd["ok"] is True
        decoded = base64.b64decode(rd["bytes_b64"])
        assert decoded == content


def test_write_fails_when_overwrite_false_and_file_exists():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = str(Path(tmpdir) / "existing.txt")
        Path(path).write_bytes(b"existing")
        encoded = base64.b64encode(b"new").decode()
        result = write_b64(path=path, bytes_b64=encoded, overwrite=False)
        assert result["ok"] is False


def test_read_missing_file_returns_error():
    result = read_b64(path="/nonexistent/path/file.txt")
    assert result["ok"] is False
