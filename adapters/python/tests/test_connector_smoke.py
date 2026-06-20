"""Tests for `urirun connectors smoke`."""

from __future__ import annotations

import json

from urirun import connector_smoke


def _doc(argv):
    return {
        "version": "urirun.bindings.v2",
        "bindings": {
            "test://host/echo/query/run": {
                "adapter": "argv-template",
                "argv": argv,
                "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}},
                "kind": "command",
                "meta": {"connector": "test"},
                "uri": "test://host/echo/query/run",
            }
        },
    }


def _write(tmp_path, doc):
    path = tmp_path / "bindings.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return str(path)


def test_smoke_validate_compile_mcp_a2a(tmp_path):
    result = connector_smoke.smoke(_write(tmp_path, _doc(["true"])))
    assert result["ok"] is True
    assert result["stages"] == ["validate", "compile", "mcp", "a2a"]
    assert result["routes"] == ["test://host/echo/query/run"]
    assert result["mcpTools"] == 1
    assert result["a2aSkills"] >= 1


def test_smoke_invalid_bindings_fails_at_validate(tmp_path):
    bad = _doc(["x", "{missing}"])  # placeholder with no schema property
    result = connector_smoke.smoke(_write(tmp_path, bad))
    assert result["ok"] is False
    assert result["stage"] == "validate"
    assert result["errors"]


def test_smoke_run_executes_route(tmp_path):
    result = connector_smoke.smoke(
        _write(tmp_path, _doc(["true"])),
        run_uri="test://host/echo/query/run",
        payload="{}",
        allow="test://*",
    )
    assert result["ok"] is True
    assert result["run"]["uri"] == "test://host/echo/query/run"
    assert result["run"]["ok"] is True
    assert "run" in result["stages"]


def test_smoke_run_failure_marks_not_ok(tmp_path):
    # `false` exits non-zero -> run stage fails -> overall not ok
    result = connector_smoke.smoke(
        _write(tmp_path, _doc(["false"])),
        run_uri="test://host/echo/query/run",
        allow="test://*",
    )
    assert result["ok"] is False
    assert result["run"]["ok"] is False


def test_smoke_command_returns_exit_code(tmp_path, capsys):
    import argparse

    args = argparse.Namespace(
        bindings=_write(tmp_path, _doc(["true"])),
        run=None, payload="{}", allow=None, name="test",
    )
    rc = connector_smoke.smoke_command(args)
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True
