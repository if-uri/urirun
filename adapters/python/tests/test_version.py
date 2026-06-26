from __future__ import annotations

from urirun.node._version import (
    _vtuple,
    current_version,
    version_line,
    version_status,
)


# ─── _vtuple ─────────────────────────────────────────────────────────────────

def test_vtuple_simple():
    assert _vtuple("1.2.3") == (1, 2, 3)


def test_vtuple_single():
    assert _vtuple("5") == (5,)


def test_vtuple_pre_release():
    # "1.0.0a1" → extracts digits only: "1", "0", "0", "1"
    t = _vtuple("1.0.0a1")
    assert t[0] == 1
    assert t[1] == 0


def test_vtuple_ordering():
    assert _vtuple("1.2.10") > _vtuple("1.2.9")
    assert _vtuple("2.0.0") > _vtuple("1.99.99")


# ─── current_version ─────────────────────────────────────────────────────────

def test_current_version_returns_string():
    v = current_version()
    assert isinstance(v, str)
    assert v  # non-empty


def test_current_version_not_crashes():
    # Must not raise even if package metadata is missing
    result = current_version()
    assert result in ("unknown",) or "." in result


# ─── version_status ──────────────────────────────────────────────────────────

def test_version_status_no_check():
    status = version_status(check_latest=False)
    assert "version" in status
    assert status["latest"] is None
    assert status["status"] == "unknown"


def test_version_status_keys():
    status = version_status(check_latest=False)
    assert set(status) >= {"version", "latest", "status"}


# ─── version_line ────────────────────────────────────────────────────────────

def test_version_line_offline():
    line = version_line(check_latest=False)
    assert "urirun" in line
    assert "offline" in line or "unknown" in line


def test_version_line_contains_version_number():
    line = version_line(check_latest=False)
    v = current_version()
    if v != "unknown":
        assert v in line
