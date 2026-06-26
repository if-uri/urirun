from __future__ import annotations

import json
import pytest
from urirun.node.flow import (
    _dig_path,
    _flow_intents,
    _uri_matches_template,
    _uri_segments,
    first_url,
    json_from_text,
    nl_key,
    requested_folder_path,
    resolve_step_payload,
)


# ─── first_url ───────────────────────────────────────────────────────────────

def test_first_url_extracts_https():
    assert first_url("check https://example.com/page now") == "https://example.com/page"


def test_first_url_extracts_http():
    assert first_url("open http://localhost:3000") == "http://localhost:3000"


def test_first_url_returns_none_when_absent():
    assert first_url("restart the phone scanner") is None


def test_first_url_returns_first_only():
    result = first_url("go to https://a.com and then https://b.com")
    assert result == "https://a.com"


# ─── nl_key ──────────────────────────────────────────────────────────────────

def test_nl_key_lowercases():
    assert nl_key("HELLO WORLD") == "hello world"


def test_nl_key_strips_diacritics():
    result = nl_key("zażółć gęślą jaźń")
    assert "ż" not in result
    assert "ę" not in result


def test_nl_key_collapses_whitespace():
    assert nl_key("  foo   bar  ") == "foo bar"


# ─── requested_folder_path ───────────────────────────────────────────────────

def test_requested_folder_path_downloads():
    assert requested_folder_path("list the downloads folder") == "~/Downloads"
    assert requested_folder_path("pobrane pliki") == "~/Downloads"


def test_requested_folder_path_default():
    assert requested_folder_path("show processes") == "."


# ─── _flow_intents ───────────────────────────────────────────────────────────

def test_flow_intents_screen():
    intents = _flow_intents("take a screenshot")
    assert intents["screen"] is True


def test_flow_intents_browser():
    intents = _flow_intents("open the browser and go to url")
    assert intents["browser"] is True


def test_flow_intents_health():
    intents = _flow_intents("check runtime health")
    assert intents["health"] is True


def test_flow_intents_default_processes():
    intents = _flow_intents("co jest uruchomione")
    # No known word → defaults to processes=True
    assert intents["processes"] is True


def test_flow_intents_invoices():
    intents = _flow_intents("znajdz faktury z maja")
    assert intents["invoices"] is True


# ─── _uri_segments ───────────────────────────────────────────────────────────

def test_uri_segments_basic():
    scheme, segs = _uri_segments("kvm://laptop/display/query/info")
    assert scheme == "kvm"
    assert segs == ["laptop", "display", "query", "info"]


def test_uri_segments_no_path():
    scheme, segs = _uri_segments("env://node")
    assert scheme == "env"
    assert segs == ["node"]


# ─── _uri_matches_template ───────────────────────────────────────────────────

def test_uri_matches_template_exact():
    assert _uri_matches_template("kvm://laptop/display/query/info",
                                  "kvm://laptop/display/query/info") is True


def test_uri_matches_template_with_param():
    assert _uri_matches_template("kvm://laptop/display/query/info",
                                  "kvm://{host}/display/query/info") is True


def test_uri_matches_template_different_scheme():
    assert _uri_matches_template("env://laptop/x", "kvm://laptop/x") is False


def test_uri_matches_template_different_length():
    assert _uri_matches_template("kvm://laptop/a/b", "kvm://laptop/a") is False


def test_uri_matches_template_multi_param():
    assert _uri_matches_template("kvm://n1/window/cmd1/fire",
                                  "kvm://{host}/{id}/{verb}/fire") is True


# ─── json_from_text ──────────────────────────────────────────────────────────

def test_json_from_text_plain():
    result = json_from_text('{"steps": [{"uri": "env://n/x"}]}')
    assert result["steps"][0]["uri"] == "env://n/x"


def test_json_from_text_fenced():
    text = "Sure!\n```json\n{\"task\": \"done\"}\n```\n"
    result = json_from_text(text)
    assert result["task"] == "done"


def test_json_from_text_embedded():
    text = "Here is the flow: {\"ok\": true} done."
    result = json_from_text(text)
    assert result["ok"] is True


def test_json_from_text_invalid_raises():
    with pytest.raises(json.JSONDecodeError):
        json_from_text("not json at all")


# ─── _dig_path ───────────────────────────────────────────────────────────────

def test_dig_path_nested_dict():
    data = {"a": {"b": {"c": 42}}}
    assert _dig_path(data, "a.b.c") == 42


def test_dig_path_list_index():
    data = {"items": [{"name": "first"}, {"name": "second"}]}
    assert _dig_path(data, "items.0.name") == "first"
    assert _dig_path(data, "items.1.name") == "second"


def test_dig_path_missing_key_raises():
    with pytest.raises(KeyError):
        _dig_path({"a": 1}, "a.b")


# ─── resolve_step_payload ────────────────────────────────────────────────────

def test_resolve_step_payload_from_reference():
    payload = {"slug_from": "step1.result.slug"}
    results = {"step1": {"result": {"slug": "my-slug"}}}
    resolved = resolve_step_payload(payload, results)
    assert resolved["slug"] == "my-slug"
    assert "slug_from" not in resolved


def test_resolve_step_payload_passthrough():
    payload = {"query": "hello", "limit": 10}
    resolved = resolve_step_payload(payload, {})
    assert resolved == payload


def test_resolve_step_payload_mixed():
    payload = {"text_from": "prev.result.text", "limit": 5}
    results = {"prev": {"result": {"text": "extracted"}}}
    resolved = resolve_step_payload(payload, results)
    assert resolved["text"] == "extracted"
    assert resolved["limit"] == 5


def test_resolve_step_payload_none_safe():
    assert resolve_step_payload(None, {}) == {}
