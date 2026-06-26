# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# flow:// — the plan made a first-class, URI-addressable node. A flow (the plan atom of a known-good
# run, stored as a named skill) becomes callable and referenceable in the SAME URI space as the facts
# and actions it operates on. That homoiconicity is the payoff: because a flow is dispatched by URI,
# a flow can dispatch another flow as a step — skill composition is uniform, not a special case.
#
#   flow://{node}/{name}/query/get     -> the named flow document (no execution)
#   flow://{node}/{name}/command/run   -> run a named flow (or an inline `flow=`) through the engine
#
# Rides the existing skill store (recall_skill) + run_flow_document — no new store, no new engine.
# Exposed as a urirun.bindings entry point so flow:// resolves like any connector.
from __future__ import annotations


def _memory():
    from urirun.node.twin_store import durable_memory  # noqa: PLC0415
    return durable_memory()


def _named_flow(name: str) -> dict | None:
    rec = _memory().recall_skill(name)
    if isinstance(rec, dict) and isinstance(rec.get("flow"), dict):
        return rec["flow"]
    return None


def _uri_flow_get(name: str = "") -> dict:
    """Handler for flow://<node>/<name>/query/get. Returns the named flow document, or found=False."""
    name = str(name or "").strip()
    if not name:
        return {"ok": False, "error": "flow name required"}
    flow = _named_flow(name)
    if flow is None:
        return {"ok": True, "found": False, "name": name}
    return {"ok": True, "found": True, "name": name, "flow": flow}


def _uri_flow_run(name: str = "", flow: dict | None = None, routes: list | None = None,
                  mesh: dict | None = None, execute: bool = True, rollback_on_failure: bool = False) -> dict:
    """Handler for flow://<node>/<name>/command/run.

    Runs a flow through the engine and returns its result. The flow is taken from the inline
    ``flow=`` payload when given, otherwise looked up as a named skill. ``mesh`` (or ``routes``)
    supplies the discovered registry the flow's steps dispatch against — a flow:// step inside the
    flow resolves back here, so flow-dispatches-flow composition needs no special handling."""
    flow_doc = flow if isinstance(flow, dict) and flow.get("steps") is not None else None
    if flow_doc is None:
        name = str(name or "").strip()
        if not name:
            return {"ok": False, "error": "flow name (or inline flow) required"}
        flow_doc = _named_flow(name)
        if flow_doc is None:
            return {"ok": False, "error": f"no flow named {name!r}", "found": False}
    if not isinstance(mesh, dict) or "routes" not in mesh:
        mesh = {"routes": list(routes or [])}
    from urirun.node.flow import run_flow_document  # noqa: PLC0415
    result = run_flow_document(flow_doc, mesh, execute=bool(execute),
                               rollback_on_failure=bool(rollback_on_failure))
    return {"ok": bool(result.get("ok")), "name": name or flow_doc.get("task", {}).get("id"),
            "result": result}


def _build_connector():
    try:
        import urirun  # noqa: PLC0415
        # NOTE: connector id must be unique — "flow" is already taken by the twin connector in
        # urirun.node.flow (scheme="twin"); reusing it would clobber one registration. The SCHEME
        # ("flow") is what routes, so a distinct id keeps both connectors intact.
        conn = urirun.connector("flow-run", scheme="flow")
        conn.handler("flow/query/get",
                     meta={"label": "Get a named flow document (the plan as a URI-addressable artifact)"})(_uri_flow_get)
        conn.handler("flow/command/run",
                     meta={"label": "Run a named (or inline) flow through the engine — flow dispatches flow"})(_uri_flow_run)
        return conn
    except Exception:  # noqa: BLE001 - connector registration is optional
        return None


_FLOW_CONN = _build_connector()


def flow_bindings() -> dict:
    """Entry-point binding document for the flow:// scheme (``urirun.bindings`` group)."""
    return _FLOW_CONN.bindings() if _FLOW_CONN is not None else {}


def register() -> bool:
    return _FLOW_CONN is not None
