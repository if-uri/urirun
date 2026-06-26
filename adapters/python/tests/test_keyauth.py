from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from urirun.node.keyauth import (
    _normalize,
    fingerprint,
    new_enroll_token,
    token_matches,
)


# ─── new_enroll_token ────────────────────────────────────────────────────────

def test_enroll_token_default_length():
    token = new_enroll_token()
    assert len(token) == 6


def test_enroll_token_custom_length():
    assert len(new_enroll_token(4)) == 4
    assert len(new_enroll_token(10)) == 10


def test_enroll_token_alphanumeric_uppercase():
    token = new_enroll_token(20)
    # All characters must be from the allowed alphabet (A-Z, 0-9, minus common confusables)
    assert all(ch.isalnum() for ch in token)
    assert token == token.upper()


def test_enroll_token_unique():
    tokens = {new_enroll_token() for _ in range(20)}
    assert len(tokens) > 1


# ─── token_matches ───────────────────────────────────────────────────────────

def test_token_matches_exact():
    assert token_matches("ABC123", "ABC123") is True


def test_token_matches_case_insensitive():
    assert token_matches("abc123", "ABC123") is True
    assert token_matches("ABC123", "abc123") is True


def test_token_matches_strips_leading_trailing_spaces():
    assert token_matches("  ABC123  ", "ABC123") is True
    assert token_matches("ABC123", "  ABC123  ") is True


def test_token_matches_wrong_value():
    assert token_matches("ABC123", "XYZ999") is False


def test_token_matches_none():
    assert token_matches(None, "ABC123") is False
    assert token_matches("ABC123", None) is False
    assert token_matches(None, None) is False


def test_token_matches_empty():
    assert token_matches("", "ABC123") is False
    assert token_matches("ABC123", "") is False


# ─── _normalize ──────────────────────────────────────────────────────────────

def test_normalize_strips_comment():
    key = "ssh-ed25519 AAAA... user@host"
    assert _normalize(key) == "ssh-ed25519 AAAA..."


def test_normalize_already_two_parts():
    key = "ssh-rsa BBBB..."
    assert _normalize(key) == "ssh-rsa BBBB..."


def test_normalize_single_word():
    assert _normalize("onlytype") == "onlytype"


# ─── fingerprint ─────────────────────────────────────────────────────────────

# Use a real Ed25519 public key (generated offline — no private key involved)
_TEST_ED25519_PUB = (
    "ssh-ed25519 "
    "AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GkZH "
    "test@test"
)


def test_fingerprint_format():
    fp = fingerprint(_TEST_ED25519_PUB)
    assert fp.startswith("SHA256:")
    assert len(fp) > 10


def test_fingerprint_stable():
    assert fingerprint(_TEST_ED25519_PUB) == fingerprint(_TEST_ED25519_PUB)


def test_fingerprint_invalid_raises():
    with pytest.raises((ValueError, Exception)):
        fingerprint("not-a-key")
