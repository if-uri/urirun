from __future__ import annotations

from urirun.node.server import (
    _apply_deploy_allow,
    _apply_deploy_env,
    _parse_sse_query,
    _sse_event_matches,
    _sse_frame,
    _registry_to_bindings,
    resolve_admin_token,
)


# ─── _parse_sse_query ────────────────────────────────────────────────────────

def test_parse_sse_query_basic():
    params = _parse_sse_query("scheme=env&run=r1")
    assert params["scheme"] == "env"
    assert params["run"] == "r1"


def test_parse_sse_query_url_encoded():
    params = _parse_sse_query("last_event_id=42&scheme=env%3A%2F%2F")
    assert params["last_event_id"] == "42"
    assert params["scheme"] == "env://"


def test_parse_sse_query_empty():
    assert _parse_sse_query("") == {}


def test_parse_sse_query_no_value_key_skipped():
    params = _parse_sse_query("scheme=env&novalue")
    assert params["scheme"] == "env"
    assert "novalue" not in params


# ─── _sse_event_matches ──────────────────────────────────────────────────────

def test_sse_event_matches_no_filter():
    ev = {"uri": "env://laptop/x", "run": "r1"}
    assert _sse_event_matches(ev, set(), set()) is True


def test_sse_event_matches_scheme_filter():
    ev = {"uri": "env://laptop/x"}
    assert _sse_event_matches(ev, {"env"}, set()) is True
    assert _sse_event_matches(ev, {"kvm"}, set()) is False


def test_sse_event_matches_run_filter():
    ev = {"uri": "env://x", "run": "run-42"}
    assert _sse_event_matches(ev, set(), {"run-42"}) is True
    assert _sse_event_matches(ev, set(), {"other-run"}) is False


def test_sse_event_matches_both_filters():
    ev = {"uri": "env://laptop/x", "run": "r1"}
    assert _sse_event_matches(ev, {"env"}, {"r1"}) is True
    assert _sse_event_matches(ev, {"kvm"}, {"r1"}) is False


# ─── _sse_frame ──────────────────────────────────────────────────────────────

def test_sse_frame_format():
    ev = {"_id": 5, "event": "run", "uri": "env://n/x"}
    frame = _sse_frame(ev)
    assert frame.startswith(b"id: 5\n")
    assert b"data:" in frame
    assert frame.endswith(b"\n\n")
    assert b"_id" not in frame  # _id is excluded from payload


def test_sse_frame_json_payload():
    import json
    ev = {"_id": 1, "event": "done", "ok": True}
    frame = _sse_frame(ev)
    data_line = [l for l in frame.decode().splitlines() if l.startswith("data:")][0]
    payload = json.loads(data_line[5:])
    assert payload["event"] == "done"
    assert "_id" not in payload


# ─── _apply_deploy_env ───────────────────────────────────────────────────────

def test_apply_deploy_env_sets_env(monkeypatch):
    monkeypatch.delenv("MY_TEST_VAR_XYZ", raising=False)
    summary = {"env": []}
    _apply_deploy_env({"MY_TEST_VAR_XYZ": "hello"}, summary)
    import os
    assert os.environ.get("MY_TEST_VAR_XYZ") == "hello"
    assert "MY_TEST_VAR_XYZ" in summary["env"]


def test_apply_deploy_env_blocks_denied_keys(monkeypatch):
    import os
    original_path = os.environ.get("PATH", "")
    summary = {"env": []}
    _apply_deploy_env({"PATH": "/evil"}, summary)
    assert os.environ.get("PATH") == original_path
    assert "PATH" not in summary["env"]


def test_apply_deploy_env_none_safe():
    summary = {"env": []}
    _apply_deploy_env(None, summary)
    assert summary["env"] == []


# ─── _apply_deploy_allow ─────────────────────────────────────────────────────

def test_apply_deploy_allow_replaces():
    state = {"allow": ["env://"]}
    summary = {}
    _apply_deploy_allow(state, {"allow": ["kvm://", "fs://"]}, summary)
    assert state["allow"] == ["kvm://", "fs://"]


def test_apply_deploy_allow_merge():
    state = {"allow": ["env://"]}
    summary = {}
    _apply_deploy_allow(state, {"allow": ["fs://"], "merge": True}, summary)
    assert "env://" in state["allow"]
    assert "fs://" in state["allow"]
    assert summary.get("allowMerged") is True


def test_apply_deploy_allow_no_allow_noop():
    state = {"allow": ["env://"]}
    summary = {}
    _apply_deploy_allow(state, {}, summary)
    assert state["allow"] == ["env://"]


# ─── resolve_admin_token ─────────────────────────────────────────────────────

def test_resolve_admin_token_explicit():
    assert resolve_admin_token("mytoken", None, False) == "mytoken"


def test_resolve_admin_token_config():
    assert resolve_admin_token(None, "cfgtoken", False) == "cfgtoken"


def test_resolve_admin_token_env(monkeypatch):
    monkeypatch.setenv("URIRUN_NODE_TOKEN", "envtoken")
    assert resolve_admin_token(None, None, False) == "envtoken"


def test_resolve_admin_token_none_when_disabled(monkeypatch):
    monkeypatch.delenv("URIRUN_NODE_TOKEN", raising=False)
    assert resolve_admin_token(None, None, False) is None


# ─── _registry_to_bindings ───────────────────────────────────────────────────

def test_registry_to_bindings_extracts_uri():
    registry = {
        "index": {
            "env://n/x": {
                "uri": "env://n/x",
                "routeEntry": {"kind": "query", "config": {"argv": ["python", "x.py"]}},
            }
        }
    }
    bindings = _registry_to_bindings(registry)
    assert "env://n/x" in bindings
    binding = bindings["env://n/x"]
    assert binding["uri"] == "env://n/x"
    assert binding["kind"] == "query"
    assert binding["argv"] == ["python", "x.py"]


def test_registry_to_bindings_empty():
    assert _registry_to_bindings({}) == {}
    assert _registry_to_bindings({"index": {}}) == {}
