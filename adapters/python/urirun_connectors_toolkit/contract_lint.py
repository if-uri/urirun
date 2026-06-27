# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
"""Static lint binding a handler's SIGNATURE to its contract — so the input shape can't be
hand-edited away from (or drift from) the declared contract.

A connector's input schema is DERIVED from each ``@conn.handler`` signature; the contract declares
``inp`` independently. ``contract_codegen`` generates the signature FROM ``inp`` so they start equal —
this lint keeps them equal: for every contracted route, every declared ``inp`` field must exist in the
live handler signature, with a compatible JSON type. (Extra handler params are allowed — a contract
may intentionally cover a subset; the gate is "no declared input is missing or mistyped".)

Run it from a connector's conformance test against ``urirun_bindings()`` (no hardware, always on):

    from urirun_connectors_toolkit.contract_lint import lint_handler_signatures
    assert not lint_handler_signatures(CONTRACTS, core.urirun_bindings())
"""
from __future__ import annotations

from typing import Any

# contract inp leaf token -> the JSON-schema "type" a signature-derived inputSchema carries
_TOKEN_JSON_TYPE = {
    "str": "string", "int": "integer", "num": "number",
    "bool": "boolean", "obj": "object", "list": "array",
}


def _base(tok: Any) -> str:
    return tok[1:] if isinstance(tok, str) and tok.startswith("?") else (tok if isinstance(tok, str) else "")


def _check_field_type(route: str, field: str, tok: Any, props: dict, problems: list[str]) -> None:
    if field not in props:
        problems.append(f"{route}: contract.inp declares {field!r} but the handler signature has no such param")
        return
    base = _base(tok)
    if not base or base.startswith(("const:", "enum:")):
        return  # literal/enum tokens don't map to a single JSON scalar type
    want = _TOKEN_JSON_TYPE.get(base)
    got = (props[field] or {}).get("type")
    if want and got and want != got:
        problems.append(f"{route}.{field}: contract type {base!r} (JSON {want!r}) != signature type {got!r}")


def lint_handler_signatures(contracts: dict, bindings_doc: dict, *, conn_uri=None) -> list[str]:
    """Return a list of contract↔signature problems ([] = clean).

    ``conn_uri`` maps a connector-local route path to its full URI (e.g. ``conn.uri``); omit it when
    contract keys are already full URIs (multi-scheme connectors).
    """
    bindings = bindings_doc.get("bindings", {})
    problems: list[str] = []
    for route, c in contracts.items():
        inp = getattr(c, "inp", None)
        if inp is None and isinstance(c, dict):
            inp = c.get("inp", {})
        uri = route if "://" in route else (conn_uri(route) if conn_uri else route)
        binding = bindings.get(uri)
        if binding is None:
            problems.append(f"{route}: contract has no live binding (route not served at {uri!r})")
            continue
        props = (binding.get("inputSchema") or {}).get("properties") or {}
        for field, tok in (inp or {}).items():
            _check_field_type(route, field, tok, props, problems)
    return problems
