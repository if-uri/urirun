from __future__ import annotations

import pytest
from urirun.host.task_planner import (
    _json_from_text,
    _short_name,
    _unique,
    is_ambiguous,
    is_destructive,
    normalize_text,
    slug,
)


# ─── normalize_text ──────────────────────────────────────────────────────────

def test_normalize_text_lowercases():
    assert normalize_text("HELLO WORLD") == "hello world"


def test_normalize_text_strips_diacritics():
    result = normalize_text("zażółć gęślą jaźń")
    assert "ż" not in result
    assert "ę" not in result


def test_normalize_text_collapses_whitespace():
    assert normalize_text("  foo   bar  ") == "foo bar"


# ─── slug ────────────────────────────────────────────────────────────────────

def test_slug_basic():
    assert slug("Check domain status") == "check-domain-status"


def test_slug_strips_special_chars():
    assert slug("foo@bar!baz") == "foo-bar-baz"


def test_slug_fallback():
    assert slug("") == "task"
    assert slug("!!!!") == "task"


# ─── is_ambiguous ────────────────────────────────────────────────────────────

def test_ambiguous_few_words():
    assert is_ambiguous("do it") is True
    assert is_ambiguous("yes") is True


def test_ambiguous_enough_words():
    assert is_ambiguous("restart the phone scanner service") is False


def test_ambiguous_known_phrase():
    # very short prompts that match AMBIGUOUS_PHRASES
    assert is_ambiguous("ok") is True


# ─── is_destructive ──────────────────────────────────────────────────────────

def test_destructive_delete_keyword():
    assert is_destructive("delete all files on the server") is True


def test_destructive_drop_database():
    assert is_destructive("drop the production database") is True


def test_destructive_normal_prompt():
    assert is_destructive("list all running services") is False
    assert is_destructive("check domain status for example.com") is False


# ─── _unique ─────────────────────────────────────────────────────────────────

def test_unique_removes_duplicates():
    assert _unique(["a", "b", "a", "c"]) == ["a", "b", "c"]


def test_unique_preserves_order():
    assert _unique(["b", "a", "c", "b"]) == ["b", "a", "c"]


def test_unique_filters_empty():
    assert _unique(["a", "", "b", ""]) == ["a", "b"]


# ─── _short_name ─────────────────────────────────────────────────────────────

def test_short_name_daily_domains():
    name = _short_name("check daily", ["example.com", "foo.com"], daily=True)
    assert "Daily domain check" in name
    assert "example.com" in name


def test_short_name_domains_no_daily():
    name = _short_name("check domains", ["example.com"], daily=False)
    assert "Check domain" in name


def test_short_name_plain_prompt():
    name = _short_name("restart the phone scanner", [], daily=False)
    assert "Restart" in name


def test_short_name_truncated():
    long = "a " * 100
    name = _short_name(long, [], daily=False)
    assert len(name) <= 120


# ─── _json_from_text ─────────────────────────────────────────────────────────

def test_json_from_text_plain():
    result = _json_from_text('{"ok": true, "count": 3}')
    assert result == {"ok": True, "count": 3}


def test_json_from_text_fenced_block():
    text = '```json\n{"name": "test"}\n```'
    result = _json_from_text(text)
    assert result["name"] == "test"


def test_json_from_text_embedded():
    text = 'Here is the result: {"value": 42} done.'
    result = _json_from_text(text)
    assert result["value"] == 42


def test_json_from_text_invalid_raises():
    import json
    with pytest.raises(json.JSONDecodeError):
        _json_from_text("not json")
