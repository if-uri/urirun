from __future__ import annotations

import json
import tempfile
from pathlib import Path

from urirun.node._util import (
    _parse_json_option,
    json_load,
    json_write,
    now_id,
    slug,
)


# ─── now_id ──────────────────────────────────────────────────────────────────

def test_now_id_is_numeric_string():
    result = now_id()
    assert result.isdigit()
    assert int(result) > 0


def test_now_id_monotonically_non_decreasing():
    a, b = now_id(), now_id()
    assert int(b) >= int(a)


# ─── slug ────────────────────────────────────────────────────────────────────

def test_slug_lowercases():
    assert slug("HELLO WORLD") == "hello_world"


def test_slug_replaces_special_chars():
    assert slug("foo-bar.baz") == "foo_bar_baz"


def test_slug_strips_leading_trailing_underscores():
    assert slug("  hello  ") == "hello"


def test_slug_truncates_to_64():
    long = "a" * 100
    result = slug(long)
    assert len(result) <= 64


def test_slug_empty_returns_step():
    assert slug("") == "step"
    assert slug("!@#$%") == "step"


# ─── _parse_json_option ──────────────────────────────────────────────────────

def test_parse_json_option_none_returns_default():
    assert _parse_json_option(None) is None
    assert _parse_json_option(None, default=[]) == []


def test_parse_json_option_parses_dict():
    result = _parse_json_option('{"key": "value"}')
    assert result == {"key": "value"}


def test_parse_json_option_parses_list():
    result = _parse_json_option("[1, 2, 3]")
    assert result == [1, 2, 3]


def test_parse_json_option_invalid_raises():
    import pytest
    with pytest.raises(json.JSONDecodeError):
        _parse_json_option("not-json")


# ─── json_load / json_write ──────────────────────────────────────────────────

def test_json_write_then_read_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "sub" / "data.json"
        data = {"ok": True, "count": 42, "items": ["a", "b"]}
        json_write(path, data)
        assert path.exists()
        loaded = json_load(path)
        assert loaded == data


def test_json_write_creates_parent_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "a" / "b" / "c" / "out.json"
        json_write(path, {"x": 1})
        assert path.exists()


def test_json_write_uses_utf8():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "unicode.json"
        json_write(path, {"msg": "zażółć gęślą jaźń"})
        content = path.read_text(encoding="utf-8")
        assert "zażółć" in content


def test_json_write_is_indented():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "pretty.json"
        json_write(path, {"a": 1})
        content = path.read_text()
        assert "\n" in content
