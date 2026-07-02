from __future__ import annotations

from copy import deepcopy

from urirun.runtime import _registry as reglib


def _route_by_uri(routes: list[dict]) -> dict[str, dict]:
    return {str(route.get("uri") or ""): route for route in routes}


def _target_from_uri(uri: str) -> str:
    try:
        return reglib.parse_uri(uri).get("target") or "host"
    except Exception:
        return "host"


def build_env_enum_inventories(flow: dict, routes: list[dict], **kwargs) -> dict:
    return kwargs.get("inventories") or {}


def _domain_options(inventories: dict, node: str, domain: str) -> list[dict]:
    inv = inventories.get(node) or inventories.get("host") or {}
    return list(((inv.get("domains") or {}).get(domain)) or [])


def _primary_value(options: list[dict], prompt: str) -> object | None:
    text = prompt.casefold()
    if "primary" in text or "glown" in text or "główn" in text:
        for option in options:
            if option.get("primary"):
                return option.get("value")
    return None


def _needs_selection(parameter: str, options: list[dict], flow: dict) -> dict:
    return {
        "ok": False,
        "kind": "needs-selection",
        "needsSelection": {"parameter": parameter, "options": options},
        "flow": flow,
    }


def _invalid(parameter: str, value: object, allowed: list[object], flow: dict) -> dict:
    return {
        "ok": False,
        "kind": "env-domain-invalid",
        "violation": {"parameter": parameter, "value": value, "allowed": allowed},
        "next": {"kind": "replan", "reason": "env-domain-invalid"},
        "flow": flow,
    }


def resolve_flow_env_enums(
    flow: dict,
    routes: list[dict],
    *,
    memory=None,
    inventories: dict | None = None,
    prompt: str = "",
) -> dict:
    out = deepcopy(flow)
    inventories = inventories or build_env_enum_inventories(out, routes)
    routes_by_uri = _route_by_uri(routes)
    for step in out.get("steps") or []:
        uri = str(step.get("uri") or "")
        route = routes_by_uri.get(uri) or {}
        domains = (((route.get("meta") or {}).get("contract") or {}).get("domains") or {})
        payload = step.setdefault("payload", {})
        node = _target_from_uri(uri)
        for parameter, spec in domains.items():
            if spec.get("type") != "enum":
                continue
            domain = str(spec.get("domain") or "")
            options = _domain_options(inventories, node, domain)
            allowed = [option.get("value") for option in options]
            empty_values = set(spec.get("emptyValues") or [])
            current = payload.get(parameter)
            if current not in (None, "") and current not in empty_values:
                if allowed and current not in allowed:
                    return _invalid(parameter, current, allowed, out)
                continue
            primary = _primary_value(options, prompt)
            if primary is not None:
                payload[parameter] = primary
                continue
            if len(options) == 1:
                payload[parameter] = options[0].get("value")
                continue
            if len(options) > 1:
                return _needs_selection(parameter, options, out)
    return {"ok": True, "flow": out}


def resolve_flow_env_enums_with_registry(
    flow: dict,
    routes: list[dict],
    registry: dict,
    **kwargs,
) -> dict:
    return resolve_flow_env_enums(flow, routes, **kwargs)
