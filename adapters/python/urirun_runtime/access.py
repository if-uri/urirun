"""AQL access contracts and autonomous credential-resolution decisions.

This module handles credential metadata and authority only. Secret values stay
inside providers and are materialized solely at an executor injection boundary.
"""

from __future__ import annotations

import fnmatch
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any


ACCESS_ACTIONS = (
    "ALLOW_DISCOVER",
    "ALLOW_ACQUIRE",
    "ALLOW_USE",
    "ALLOW_DELEGATE",
    "ALLOW_ROTATE",
    "ALLOW_REVOKE",
    "ALLOW_MUTATE",
    "ALLOW_SPEND",
    "ALLOW_ACCEPT_TERMS",
)
ACCESS_CONTRACT_VERSION = "aql.access.v1"
ACCESS_REQUIREMENT_VERSION = "access.requirement.v1"
EXECUTION_GRANT_VERSION = "aql.execution-grant.v1"
BINDINGS_VERSION = "urirun.bindings.v2"
HUMAN_AUTHORITY_URI = "human://founder/precondition/command/satisfy"
_CREDENTIAL_PUBLIC_FIELDS = {
    "authenticated",
    "credential_handle",
    "credential_type",
    "scopes",
    "expires_at",
    "refreshable",
    "delegatable",
    "parent_delegatable",
    "interactive_consent_required",
    "principal",
    "provider",
    "valid",
    "secret_value_visible",
    "evidence",
}


class AccessPolicyError(PermissionError):
    """A typed AQL access denial."""

    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(f"{code}{': ' + detail if detail else ''}")


def _patterns_match(value: str, patterns: str | list[str] | tuple[str, ...]) -> bool:
    if isinstance(patterns, str):
        patterns = (patterns,)
    return any(fnmatch.fnmatch(value, pattern) for pattern in patterns)


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _block(code: str, *, human_required: bool, **extra: Any) -> dict:
    return {"decision": "BLOCK", "code": code, "human_required": human_required, **extra}


def _matching_grant(requirement: dict, contract: dict) -> dict | None:
    requested = set(requirement.get("requested_actions") or [])
    for grant in contract.get("grants") or []:
        if not _patterns_match(requirement["actor"], grant.get("actor", "")):
            continue
        if not _patterns_match(requirement["provider"], grant.get("providers") or []):
            continue
        if not _patterns_match(requirement["capability"], grant.get("capabilities") or []):
            continue
        if not _patterns_match(requirement["target"], grant.get("targets") or []):
            continue
        if not requested.issubset(set(grant.get("actions") or [])):
            continue
        return grant
    return None


def evaluate_access(
    requirement: dict,
    contract: dict | None,
    *,
    now: datetime | None = None,
) -> dict:
    """Evaluate a standing AQL contract for one access requirement."""
    requested = list(dict.fromkeys(requirement.get("requested_actions") or []))
    required_fields = {"actor", "environment", "capability", "provider", "target"}
    if (
        requirement.get("schema_version") != ACCESS_REQUIREMENT_VERSION
        or not required_fields.issubset(requirement)
    ):
        return _block("AQL_REQUIREMENT_INVALID", human_required=False)
    if not contract:
        return _block(
            "AQL_ALLOW_REQUIRED",
            human_required=True,
            required_actions=requested,
        )
    if contract.get("schema_version") != ACCESS_CONTRACT_VERSION:
        return _block("AQL_CONTRACT_INVALID", human_required=True)
    environment = requirement.get("environment")
    if contract.get("environment") not in (environment, "*"):
        return _block("AQL_ENVIRONMENT_MISMATCH", human_required=True)
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    try:
        valid_until = _parse_timestamp(contract.get("valid_until"))
    except (TypeError, ValueError):
        return _block("AQL_CONTRACT_INVALID", human_required=True)
    if valid_until and current >= valid_until:
        return _block("AQL_CONTRACT_EXPIRED", human_required=True)
    if any(action not in ACCESS_ACTIONS for action in requested):
        return _block("AQL_ACTION_UNKNOWN", human_required=True)

    grant = _matching_grant(requirement, contract)
    if grant is None:
        return _block(
            "AQL_SCOPE_OR_ACTION_DENIED",
            human_required=True,
            required_actions=requested,
        )
    requested_ttl = int(requirement.get("max_credential_ttl_seconds") or 0)
    max_ttl = int(grant.get("max_credential_ttl_seconds") or requested_ttl or 0)
    if max_ttl and requested_ttl > max_ttl:
        return _block("AQL_CREDENTIAL_TTL_EXCEEDED", human_required=True)
    estimated_cost = float(requirement.get("estimated_cost") or 0)
    if "max_cost" in grant and estimated_cost > float(grant["max_cost"]):
        return _block("AQL_BUDGET_EXCEEDED", human_required=True)
    return {
        "decision": "ALLOW",
        "human_required": False,
        "contract_id": contract["contract_id"],
        "grant_id": grant["grant_id"],
        "allowed_actions": requested,
        "max_credential_ttl_seconds": max_ttl or requested_ttl,
        "environment_fingerprint": requirement.get("environment_fingerprint", ""),
    }


def require_access(requirement: dict, contract: dict | None) -> dict:
    """Return an ALLOW decision or raise a typed policy exception."""
    decision = evaluate_access(requirement, contract)
    if decision["decision"] != "ALLOW":
        raise AccessPolicyError(decision["code"])
    return decision


def _public_credential(credential: dict) -> dict:
    return {
        key: value
        for key, value in credential.items()
        if key in _CREDENTIAL_PUBLIC_FIELDS
    }


def resolve_required_access(
    requirement: dict,
    contract: dict | None,
    *,
    credential: dict | None = None,
    acquisition_methods: list[dict] | None = None,
) -> dict:
    """Classify the next autonomous access-resolution step without secret values."""
    decision = evaluate_access(requirement, contract)
    if decision["decision"] != "ALLOW":
        return {"status": decision["code"], "aql_decision": decision}
    public = _public_credential(credential or {})
    if credential and credential.get("valid"):
        return {"status": "READY", "credential": public, "aql_decision": decision}
    allowed = set(decision["allowed_actions"])
    if credential and credential.get("refreshable") and "ALLOW_ACQUIRE" in allowed:
        return {
            "status": "AUTO_ACQUIRABLE",
            "strategy": "refresh",
            "credential": public,
            "aql_decision": decision,
        }
    if credential and credential.get("parent_delegatable") and "ALLOW_DELEGATE" in allowed:
        return {
            "status": "AUTO_ACQUIRABLE",
            "strategy": "delegate",
            "credential": public,
            "aql_decision": decision,
        }
    for method in acquisition_methods or []:
        if method.get("mfa_required"):
            return {"status": "MFA_REQUIRED", "acquisition": method, "aql_decision": decision}
        if method.get("interactive_consent_required"):
            return {
                "status": "PROVIDER_CONSENT_REQUIRED",
                "acquisition": method,
                "human_uri": HUMAN_AUTHORITY_URI,
                "scope": "per-env",
                "aql_decision": decision,
            }
        if "ALLOW_ACQUIRE" in allowed:
            return {
                "status": "AUTO_ACQUIRABLE",
                "strategy": method["type"],
                "acquisition": method,
                "aql_decision": decision,
            }
    return {"status": "ROOT_CREDENTIAL_MISSING", "aql_decision": decision}


def _iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def compile_execution_grant(
    requirement: dict,
    decision: dict,
    *,
    plan_hash: str,
    now: datetime | None = None,
    nonce: str | None = None,
) -> dict:
    """Compile a short child grant from an already accepted standing contract."""
    if decision.get("decision") != "ALLOW":
        raise AccessPolicyError("AQL_EXECUTION_GRANT_DENIED")
    issued = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    ttl = min(
        int(requirement.get("max_credential_ttl_seconds") or 1800),
        int(decision.get("max_credential_ttl_seconds") or 1800),
    )
    return {
        "schema_version": EXECUTION_GRANT_VERSION,
        "grant_id": f"exec_{secrets.token_hex(8)}",
        "parent_contract": decision["contract_id"],
        "parent_grant": decision["grant_id"],
        "actor": requirement["actor"],
        "capability": requirement["capability"],
        "target": requirement["target"],
        "provider": requirement["provider"],
        "plan_hash": plan_hash,
        "environment_fingerprint": requirement.get("environment_fingerprint", ""),
        "issued_at": _iso_z(issued),
        "valid_until": _iso_z(issued + timedelta(seconds=ttl)),
        "nonce": nonce or secrets.token_urlsafe(18),
        "max_mutations": int(requirement.get("max_mutations") or 1),
        "rollback_required": bool(requirement.get("rollback_required", True)),
    }


def _evaluate_route(target: str, args: dict, payload: dict, descriptor: dict) -> dict:
    """URI handler for a standing-contract decision."""
    del target, args, descriptor
    return evaluate_access(payload["requirement"], payload.get("contract"))


def _resolve_route(target: str, args: dict, payload: dict, descriptor: dict) -> dict:
    """URI handler for selecting the next access-acquisition strategy."""
    del target, args, descriptor
    return resolve_required_access(
        payload["requirement"],
        payload.get("contract"),
        credential=payload.get("credential"),
        acquisition_methods=payload.get("acquisition_methods"),
    )


def _compile_grant_route(
    target: str,
    args: dict,
    payload: dict,
    descriptor: dict,
) -> dict:
    """URI handler compiling a bounded child grant from an ALLOW decision."""
    del target, args, descriptor
    return compile_execution_grant(
        payload["requirement"],
        payload["decision"],
        plan_hash=payload["plan_hash"],
        nonce=payload.get("nonce"),
    )


def _local_binding(export: str, input_schema: dict, label: str) -> dict:
    return {
        "kind": "local-function",
        "adapter": "local-function",
        "python": {
            "type": "python",
            "module": "urirun_runtime.access",
            "export": export,
        },
        "ref": globals()[export],
        "inputSchema": input_schema,
        "policy": {"allowExecute": True},
        "meta": {
            "label": label,
            "connector": "urirun-access-resolver",
            "secretValueVisible": False,
        },
    }


def access_bindings(target: str = "host") -> dict:
    """Expose AQL evaluation, access resolution and child grants as URI routes."""
    object_schema = {"type": "object"}
    evaluate_schema = {
        "type": "object",
        "properties": {
            "requirement": object_schema,
            "contract": {"type": ["object", "null"]},
        },
        "required": ["requirement"],
        "additionalProperties": False,
    }
    resolve_schema = {
        "type": "object",
        "properties": {
            "requirement": object_schema,
            "contract": {"type": ["object", "null"]},
            "credential": {"type": ["object", "null"]},
            "acquisition_methods": {
                "type": "array",
                "items": {"type": "object"},
            },
        },
        "required": ["requirement"],
        "additionalProperties": False,
    }
    grant_schema = {
        "type": "object",
        "properties": {
            "requirement": object_schema,
            "decision": object_schema,
            "plan_hash": {"type": "string", "minLength": 1},
            "nonce": {"type": "string", "minLength": 1},
        },
        "required": ["requirement", "decision", "plan_hash"],
        "additionalProperties": False,
    }
    return {
        "version": BINDINGS_VERSION,
        "bindings": {
            f"access://{target}/requirement/query/evaluate": _local_binding(
                "_evaluate_route", evaluate_schema, "Evaluate a standing AQL access contract"
            ),
            f"access://{target}/requirement/query/resolve": _local_binding(
                "_resolve_route", resolve_schema, "Resolve the next access-acquisition step"
            ),
            f"access://{target}/grant/command/compile": _local_binding(
                "_compile_grant_route", grant_schema, "Compile a bounded child execution grant"
            ),
        },
    }
