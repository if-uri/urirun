from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
from urirun_runtime import access
from urirun_runtime import v2


ROOT = Path(__file__).resolve().parents[3]


def development_contract() -> dict:
    return {
        "schema_version": "aql.access.v1",
        "contract_id": "local-autonomy-development-v1",
        "environment": "development",
        "grants": [
            {
                "grant_id": "all-local-apps",
                "actor": "subactor:*",
                "actions": list(access.ACCESS_ACTIONS),
                "providers": ["*"],
                "capabilities": ["*"],
                "targets": ["*"],
                "max_credential_ttl_seconds": 86400,
                "max_cost": 100,
            }
        ],
    }


def requirement(**overrides) -> dict:
    value = {
        "schema_version": "access.requirement.v1",
        "actor": "subactor:desktop-test",
        "environment": "development",
        "environment_fingerprint": "lenovo-dev-01",
        "capability": "credential.acquire.browser",
        "provider": "browser",
        "target": "github.com",
        "requested_actions": ["ALLOW_DISCOVER", "ALLOW_ACQUIRE", "ALLOW_USE"],
        "effect": "credential_acquisition",
        "estimated_cost": 0,
        "max_credential_ttl_seconds": 1800,
    }
    value.update(overrides)
    return value


def test_standing_development_contract_allows_automatic_access() -> None:
    decision = access.evaluate_access(requirement(), development_contract())

    assert decision["decision"] == "ALLOW"
    assert decision["contract_id"] == "local-autonomy-development-v1"
    assert decision["grant_id"] == "all-local-apps"
    assert decision["human_required"] is False


def test_access_without_contract_returns_typed_authority_blocker() -> None:
    decision = access.evaluate_access(requirement(), None)

    assert decision == {
        "decision": "BLOCK",
        "code": "AQL_ALLOW_REQUIRED",
        "human_required": True,
        "required_actions": ["ALLOW_DISCOVER", "ALLOW_ACQUIRE", "ALLOW_USE"],
    }


def test_resolution_prefers_refresh_delegate_and_browser_acquisition() -> None:
    contract = development_contract()

    refresh = access.resolve_required_access(
        requirement(),
        contract,
        credential={
            "credential_handle": "cred-expired",
            "valid": False,
            "refreshable": True,
            "secret_value_visible": False,
        },
    )
    delegate = access.resolve_required_access(
        requirement(requested_actions=["ALLOW_DISCOVER", "ALLOW_DELEGATE"]),
        contract,
        credential={
            "credential_handle": "cred-parent",
            "valid": False,
            "parent_delegatable": True,
            "secret_value_visible": False,
        },
    )
    browser = access.resolve_required_access(
        requirement(),
        contract,
        credential=None,
        acquisition_methods=[
            {
                "type": "browser",
                "interactive_consent_required": False,
                "mfa_required": False,
            }
        ],
    )

    assert refresh["status"] == "AUTO_ACQUIRABLE"
    assert refresh["strategy"] == "refresh"
    assert delegate["status"] == "AUTO_ACQUIRABLE"
    assert delegate["strategy"] == "delegate"
    assert browser["status"] == "AUTO_ACQUIRABLE"
    assert browser["strategy"] == "browser"


def test_provider_consent_is_a_typed_step_not_generic_human_input() -> None:
    result = access.resolve_required_access(
        requirement(),
        development_contract(),
        acquisition_methods=[
            {
                "type": "oauth",
                "interactive_consent_required": True,
                "mfa_required": False,
            }
        ],
    )

    assert result["status"] == "PROVIDER_CONSENT_REQUIRED"
    assert result["human_uri"] == "human://founder/precondition/command/satisfy"
    assert result["scope"] == "per-env"


def test_execution_grant_is_bounded_and_contains_no_secret_value() -> None:
    decision = access.evaluate_access(requirement(), development_contract())
    grant = access.compile_execution_grant(
        requirement(),
        decision,
        plan_hash="sha256:abc",
        now=datetime(2026, 7, 19, 20, 0, tzinfo=timezone.utc),
        nonce="one-time-test-nonce",
    )

    assert grant["schema_version"] == "aql.execution-grant.v1"
    assert grant["parent_contract"] == "local-autonomy-development-v1"
    assert grant["valid_until"] == "2026-07-19T20:30:00Z"
    assert grant["nonce"] == "one-time-test-nonce"
    assert "secret" not in grant


def test_versioned_schemas_validate_requirement_contract_and_child_grant() -> None:
    contract = development_contract()
    req = requirement()
    decision = access.evaluate_access(req, contract)
    grant = access.compile_execution_grant(
        req,
        decision,
        plan_hash="sha256:contract-test",
        nonce="schema-test-nonce",
    )

    documents = (
        ("aql-access-v1.schema.json", contract),
        ("access-requirement-v1.schema.json", req),
        ("aql-execution-grant-v1.schema.json", grant),
    )
    for schema_name, document in documents:
        schema = json.loads((ROOT / "v2" / "spec" / schema_name).read_text())
        jsonschema.Draft202012Validator(schema).validate(document)


def test_opt_in_development_policy_is_unrestricted_for_local_automation() -> None:
    policy = json.loads(
        (ROOT / "examples" / "policies" / "development-autonomy.json").read_text()
    )

    assert policy["execute"]["allow"] == ["*://**"]
    assert "secret://browser/**" in policy["secretAllow"]
    decision = access.evaluate_access(requirement(), policy["access"]["contract"])
    assert decision["decision"] == "ALLOW"


def test_access_resolver_is_discoverable_and_executable_through_uri_routes() -> None:
    bindings = access.access_bindings()
    assert set(bindings["bindings"]) == {
        "access://host/requirement/query/evaluate",
        "access://host/requirement/query/resolve",
        "access://host/grant/command/compile",
    }
    registry = v2.compile_registry(bindings)
    policy = {"execute": {"allow": ["access://**"]}}
    evaluated = v2.run(
        "access://host/requirement/query/evaluate",
        registry,
        {"requirement": requirement(), "contract": development_contract()},
        mode="execute",
        policy=policy,
    )
    decision = evaluated["result"]["value"]
    assert decision["decision"] == "ALLOW"

    resolved = v2.run(
        "access://host/requirement/query/resolve",
        registry,
        {
            "requirement": requirement(),
            "contract": development_contract(),
            "acquisition_methods": [
                {
                    "type": "browser",
                    "interactive_consent_required": False,
                    "mfa_required": False,
                }
            ],
        },
        mode="execute",
        policy=policy,
    )
    assert resolved["result"]["value"]["status"] == "AUTO_ACQUIRABLE"
