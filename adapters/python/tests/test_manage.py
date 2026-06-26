from __future__ import annotations

import os

import pytest
from urirun.node.manage import (
    _classify_source,
    _connector_match,
)


# ─── _classify_source ────────────────────────────────────────────────────────

def test_classify_git_url():
    assert _classify_source("git+https://github.com/org/repo.git") == "git"
    assert _classify_source("git@github.com:org/repo.git") == "git"
    assert _classify_source("https://github.com/org/repo.git") == "git"


def test_classify_catalog_url():
    assert _classify_source("https://connectors.urirun.com/urirun-connector-foo") == "catalog"
    assert _classify_source("http://example.com/pkg") == "catalog"


def test_classify_local_path():
    assert _classify_source("/absolute/path/to/pkg") == "local"
    assert _classify_source("./relative/pkg") == "local"
    assert _classify_source("~/home/pkg") == "local"


def test_classify_catalog_name():
    assert _classify_source("urirun-connector-rtsp") == "catalog"
    assert _classify_source("my-custom-package") == "catalog"


# ─── _connector_match ────────────────────────────────────────────────────────

def test_connector_match_by_name():
    obj = {"name": "urirun-connector-rtsp", "id": "rtsp"}
    assert _connector_match(obj, "rtsp") is True
    assert _connector_match(obj, "urirun-connector-rtsp") is True


def test_connector_match_no_hit():
    obj = {"name": "urirun-connector-rtsp", "id": "rtsp"}
    assert _connector_match(obj, "mqtt") is False


def test_connector_match_non_dict():
    assert _connector_match("notadict", "rtsp") is False
    assert _connector_match(None, "rtsp") is False
