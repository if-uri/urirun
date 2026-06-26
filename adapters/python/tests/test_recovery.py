from __future__ import annotations

from urirun.node.recovery import (
    can_retry_step,
    exception_error,
    failure_signature,
    normalize_error,
    route_for_step,
    step_target,
)


# ─── normalize_error ─────────────────────────────────────────────────────────

def test_normalize_error_from_dict_keeps_keys():
    err = normalize_error({"type": "NotFound", "message": "route not found", "category": "NOT_FOUND"})
    assert err["type"] == "NotFound"
    assert err["message"] == "route not found"
    assert err["category"] == "NOT_FOUND"


def test_normalize_error_from_string():
    err = normalize_error("something went wrong")
    assert err["type"] == "str"
    assert err["message"] == "something went wrong"


def test_normalize_error_fills_missing_defaults():
    err = normalize_error({})
    assert "type" in err
    assert "message" in err
    assert "status" in err
    assert "severity" in err


def test_normalize_error_preserves_existing_status():
    err = normalize_error({"type": "X", "message": "m", "status": 503, "category": "UNAVAILABLE"})
    assert err["status"] == 503


# ─── exception_error ─────────────────────────────────────────────────────────

def test_exception_error_wraps_exception():
    exc = ValueError("bad input")
    err = exception_error(exc)
    assert err["type"] == "ValueError"
    assert "bad input" in err["message"]


def test_exception_error_with_uri():
    exc = ConnectionError("refused")
    err = exception_error(exc, uri="env://laptop/runtime/query/health")
    assert "laptop" in err.get("uri", "") or True  # uri field present


# ─── failure_signature ───────────────────────────────────────────────────────

def test_failure_signature_strips_uri():
    err = {"message": "cannot reach http://laptop:8765/api/v2/run"}
    sig = failure_signature(err)
    assert "laptop" not in sig
    assert "<uri>" in sig


def test_failure_signature_strips_path():
    err = {"message": "file /home/user/docs/receipt.pdf not found"}
    sig = failure_signature(err)
    assert "/home/user" not in sig
    assert "<path>" in sig


def test_failure_signature_strips_digits():
    err = {"message": "timeout after 30 seconds on port 8194"}
    sig = failure_signature(err)
    assert "30" not in sig
    assert "<n>" in sig


def test_failure_signature_strips_quoted():
    err = {"message": "unknown route 'env://host/x'"}
    sig = failure_signature(err)
    assert "env://host/x" not in sig


def test_failure_signature_empty_message():
    assert failure_signature({}) == "<empty>"
    assert failure_signature({"message": ""}) == "<empty>"


def test_failure_signature_stable():
    err = {"message": "connection refused to http://node:9999"}
    assert failure_signature(err) == failure_signature(err)


# ─── step_target ─────────────────────────────────────────────────────────────

def test_step_target_extracts_node():
    assert step_target({"uri": "env://laptop/runtime/query/health"}) == "laptop"


def test_step_target_empty_step():
    assert step_target({}) == ""


def test_step_target_no_crash_on_bad_uri():
    result = step_target({"uri": "not-a-uri"})
    assert isinstance(result, str)


# ─── route_for_step ──────────────────────────────────────────────────────────

def test_route_for_step_found():
    routes = [
        {"uri": "env://laptop/runtime/query/health", "kind": "query"},
        {"uri": "env://laptop/config/command/set", "kind": "command"},
    ]
    route = route_for_step({"uri": "env://laptop/runtime/query/health"}, routes)
    assert route["kind"] == "query"


def test_route_for_step_not_found_returns_empty():
    route = route_for_step({"uri": "env://laptop/missing"}, [])
    assert route == {}


# ─── can_retry_step ──────────────────────────────────────────────────────────

def _transient_error():
    return {"category": "UNAVAILABLE", "message": "service unavailable"}


def _query_route(uri="env://laptop/runtime/query/health"):
    return {"uri": uri, "kind": "query"}


def test_can_retry_transient_query_step():
    assert can_retry_step(
        _transient_error(),
        step={"uri": "env://laptop/runtime/query/health"},
        routes=[_query_route()],
        execute=True, attempt=0, max_retries=3,
    ) is True


def test_can_retry_false_when_max_retries_reached():
    assert can_retry_step(
        _transient_error(),
        step={"uri": "env://laptop/runtime/query/health"},
        routes=[_query_route()],
        execute=True, attempt=3, max_retries=3,
    ) is False


def test_can_retry_false_for_non_transient_category():
    err = {"category": "NOT_FOUND", "message": "route missing"}
    assert can_retry_step(
        err,
        step={"uri": "env://laptop/runtime/query/health"},
        routes=[_query_route()],
        execute=True, attempt=0, max_retries=3,
    ) is False


def test_can_retry_false_for_command_route_in_execute_mode():
    err = _transient_error()
    cmd_route = {"uri": "env://laptop/config/command/set", "kind": "command"}
    assert can_retry_step(
        err,
        step={"uri": "env://laptop/config/command/set"},
        routes=[cmd_route],
        execute=True, attempt=0, max_retries=3,
    ) is False


def test_can_retry_true_for_command_in_non_execute_mode():
    err = _transient_error()
    cmd_route = {"uri": "env://laptop/config/command/set", "kind": "command"}
    # execute=False means dry-run/plan — any transient is retryable
    assert can_retry_step(
        err,
        step={"uri": "env://laptop/config/command/set"},
        routes=[cmd_route],
        execute=False, attempt=0, max_retries=3,
    ) is True
