# Author: Tom Sapletta · Part of the ifURI solution.
from __future__ import annotations

import pytest

from urirun_connectors_toolkit.connector_sdk import manifest_routes


def _b(uri, label="do it"):
    return {"bindings": {uri: {"meta": {"label": label}}}}


def test_class_and_verb_parsed_from_uri():
    r = manifest_routes(_b("kvm://host/screen/query/capture"))[0]
    assert r["class"] == "query" and r["verb"] == "capture" and r["mutates"] is False
    assert "INVALID_ARGUMENT" in r["errors"]


def test_command_mutates_and_carries_command_errors():
    r = manifest_routes(_b("kvm://host/input/command/type"))[0]
    assert r["class"] == "command" and r["mutates"] is True
    assert "PERMISSION_DENIED" in r["errors"]


def test_summary_from_meta_label():
    r = manifest_routes(_b("x://host/a/query/read", label="Read a thing"))[0]
    assert r["summary"] == "Read a thing"


def test_unknown_class_is_rejected():
    with pytest.raises(ValueError, match="must be one of"):
        manifest_routes(_b("x://host/a/frobnicate/read"))


def test_routes_sorted_and_complete():
    b = {"bindings": {"z://host/a/query/x": {}, "a://host/b/command/y": {}}}
    routes = manifest_routes(b)
    assert [r["uri"] for r in routes] == ["a://host/b/command/y", "z://host/a/query/x"]
    assert all(set(r) >= {"uri", "class", "verb", "summary", "mutates", "errors"} for r in routes)
