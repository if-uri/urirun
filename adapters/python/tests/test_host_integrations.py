from __future__ import annotations

import pytest
from urirun.host.host_integrations import (
    _list_param,
    _planfile_action,
    _planfile_project,
    _simulate_planfile,
    _ticket_id,
)


# ─── _list_param ─────────────────────────────────────────────────────────────

def test_list_param_none():
    assert _list_param(None) == []


def test_list_param_list():
    assert _list_param(["a", "b"]) == ["a", "b"]


def test_list_param_csv_string():
    assert _list_param("foo, bar, baz") == ["foo", "bar", "baz"]


def test_list_param_single_string():
    assert _list_param("only") == ["only"]


def test_list_param_int_in_list():
    assert _list_param([1, 2, 3]) == ["1", "2", "3"]


# ─── _ticket_id ──────────────────────────────────────────────────────────────

def test_ticket_id_from_payload():
    assert _ticket_id({"ticket_id": "T-1"}, []) == "T-1"
    assert _ticket_id({"id": "T-2"}, []) == "T-2"


def test_ticket_id_from_args():
    assert _ticket_id({}, ["list", "T-3"]) == "T-3"


def test_ticket_id_missing_raises():
    with pytest.raises(ValueError, match="ticket_id is required"):
        _ticket_id({}, [])


# ─── _planfile_action ────────────────────────────────────────────────────────

def _ctx(package="planfile", resource="tickets", operation="query", args=None):
    return {
        "descriptor": {"package": package, "normalized": f"planfile://host/{resource}/{operation}"},
        "translation": {"resource": resource, "operation": operation, "args": args or []},
    }


def test_planfile_action_from_args():
    assert _planfile_action(_ctx(args=["list"])) == "list"


def test_planfile_action_list_default():
    assert _planfile_action(_ctx(resource="tickets", operation="query")) == "list"


def test_planfile_action_dsl():
    ctx = _ctx(resource="dsl", operation="command")
    assert _planfile_action(ctx) == "dsl"


def test_planfile_action_no_args_no_known_raises():
    with pytest.raises(ValueError):
        _planfile_action(_ctx(resource="unknown", operation="command"))


# ─── _planfile_project ───────────────────────────────────────────────────────

def test_planfile_project_from_payload():
    ctx = {"routeEntry": {"config": {}}, "params": {}}
    assert _planfile_project(ctx, {"project": "/my/project"}) == "/my/project"


def test_planfile_project_from_config():
    ctx = {"routeEntry": {"config": {"project": "/conf/proj"}}, "params": {}}
    assert _planfile_project(ctx, {}) == "/conf/proj"


def test_planfile_project_default():
    ctx = {"routeEntry": {"config": {}}, "params": {}}
    assert _planfile_project(ctx, {}) == "."


# ─── _simulate_planfile ──────────────────────────────────────────────────────

def test_simulate_planfile_fields():
    ctx = {
        "descriptor": {"normalized": "planfile://host/tickets/query"},
        "routeEntry": {"config": {}},
        "params": {},
    }
    result = _simulate_planfile(ctx, "list", {"sprint": "current"}, ".")
    assert result["simulated"] is True
    assert result["action"] == "list"
    assert result["type"] == "planfile-task"
    assert result["payload"] == {"sprint": "current"}
