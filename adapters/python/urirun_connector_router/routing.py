from __future__ import annotations

import hashlib

from urirun.runtime import _registry as reglib, v2


UNSAFE_URI_PARTS = (
    "/terminal/command/run",
    "/command/exec",
    "://sudo",
    "/command/install",
    "/command/upgrade",
)

_CONNECTOR_REQUIRED_ADAPTERS = frozenset({
    "configured-camera", "configured-media", "configured-ssh", "configured-files",
})
_EXTERNAL_ADAPTERS = frozenset({
    "configured-api", "fetch", "argv-template", "shell-template",
})
_READONLY_VERBS = ("/query/", "/info/", "/status/")


def parse_uri(uri: str) -> dict:
    return reglib.parse_uri(uri)


def uri_is_denied(uri: str) -> bool:
    return any(part in uri for part in UNSAFE_URI_PARTS)


def route_class(route: dict) -> str:
    adapter = str(route.get("adapter") or "")
    if adapter in _CONNECTOR_REQUIRED_ADAPTERS:
        return "connector_required"
    if adapter in _EXTERNAL_ADAPTERS:
        return "external"
    uri = str(route.get("uri") or "")
    if any(verb in uri for verb in _READONLY_VERBS):
        return "metadata"
    return "executable"


def route_is_safe(uri: str, declared: bool | None = None) -> bool:
    return bool(uri and declared is not False and not uri_is_denied(uri))


def routes_from_registry(registry: dict, source: str = "built-in") -> list[dict]:
    routes = []
    for item in reglib.flatten_registry_document(registry):
        entry = item["routeEntry"]
        config = entry.get("config") or {}
        meta = entry.get("meta") or {}
        declared = config.get("safe", meta.get("safe"))
        descriptor = {
            "uri": item["uri"],
            "kind": entry.get("kind"),
            "adapter": entry.get("adapter"),
            "safe": route_is_safe(item["uri"], declared),
            "title": meta.get("label") or meta.get("title") or item["uri"],
            "source": source,
            "inputSchema": config.get("inputSchema") or entry.get("inputSchema") or {"type": "object"},
        }
        descriptor["routeClass"] = route_class(descriptor)
        routes.append(descriptor)
    return sorted(routes, key=lambda item: item["uri"])


def registry_fingerprint(routes: list[dict]) -> str:
    items = sorted((r.get("uri", ""), r.get("kind", "")) for r in routes)
    return hashlib.sha256(repr(items).encode("utf-8")).hexdigest()[:16]


def safe_route(route: dict) -> bool:
    return route_is_safe(str(route.get("uri", "")), route.get("safe"))


def route_target(uri: str) -> str:
    return parse_uri(uri)["target"]


def binding_for_remote_route(route: dict) -> dict:
    return {
        "kind": "service",
        "adapter": "http-service",
        "inputSchema": route.get("inputSchema") or {"type": "object"},
        "meta": {
            "label": route.get("title") or route.get("uri"),
            "node": route.get("node"),
            "sourceAdapter": route.get("adapter"),
        },
    }


def registry_from_routes(routes: list[dict]) -> dict:
    bindings = {route["uri"]: binding_for_remote_route(route) for route in routes if safe_route(route)}
    return v2.compile_registry({"version": v2.VERSION, "bindings": bindings}, on_conflict="keep")


def target_nodes(prompt: str, nodes: list[dict], explicit: list[str] | None = None) -> list[str]:
    reachable = [node["name"] for node in nodes if node.get("reachable")]
    if explicit:
        selected = [name for name in explicit if name in reachable]
        return selected or explicit
    lowered = prompt.lower()
    mentioned = [name for name in reachable if name.lower() in lowered]
    return mentioned or reachable


def route_targets_for_nodes(routes: list[dict], node_names: list[str]) -> list[str]:
    all_targets: list[str] = []
    by_node: dict[str, list[str]] = {}
    for route in routes:
        try:
            target = route_target(str(route.get("uri") or ""))
        except Exception:
            continue
        if target not in all_targets:
            all_targets.append(target)
        node = str(route.get("node") or "")
        if node:
            by_node.setdefault(node, [])
            if target not in by_node[node]:
                by_node[node].append(target)

    expanded: list[str] = []
    for name in node_names:
        candidates = by_node.get(name) or ([name] if name in all_targets else [])
        for target in candidates or [name]:
            if target not in expanded:
                expanded.append(target)
    return expanded


def diagnose_plan(steps: list[dict], mesh: dict, probe: bool = False) -> dict:
    routes = mesh.get("routes") or []
    served = {str(route.get("uri") or ""): route for route in routes}
    blocked = []
    for index, step in enumerate(steps):
        uri = str(step.get("uri") or "")
        if not uri:
            continue
        route = served.get(uri)
        if route is None:
            blocked.append({"index": index, "uri": uri, "blockedAt": "routing", "reason": "route not served"})
        elif not safe_route(route):
            blocked.append({"index": index, "uri": uri, "blockedAt": "safety", "reason": "route is not safe"})
    return {"ok": not blocked, "blockedSteps": blocked, "probe": bool(probe)}


def diagnose_targets(
    selected_nodes: list[str],
    selected_targets: list[str],
    discovered: dict,
    probe: bool = False,
) -> dict:
    node_map = {
        str(node.get("name") or ""): node
        for node in (discovered.get("nodes") or [])
    }
    reachable = {
        str(node.get("name") or "")
        for node in (discovered.get("nodes") or [])
        if node.get("reachable")
    }
    requested = set(selected_nodes or [])
    requested.update(str(t).removeprefix("node:") for t in (selected_targets or []) if str(t).startswith("node:"))
    nodes = []
    for name in sorted(requested):
        if not name:
            continue
        ok = name in reachable
        known = name in node_map
        klass = "unreachable" if known else "no-node-url"
        nodes.append({
            "node": name,
            "ok": ok,
            "status": "ok" if ok else ("uri-process-unreachable" if known else "missing-node-url"),
            "remediationClass": "" if ok else klass,
            "remediation": {} if ok else {
                "class": klass,
                "status": "uri-process-unreachable" if known else "missing-node-url",
                "message": f"Node '{name}' is not reachable." if known else f"Node '{name}' has no configured URL.",
                "humanAction": (
                    f"Start the node and pass --node-url {name}=http://<ip>:8765, "
                    f"or add it to the mesh config."
                ) if not known else f"Start node '{name}' and keep urirun node serve running.",
                "command": f"urirun node serve --name {name}",
            },
        })
    offline = [item["node"] for item in nodes if not item["ok"]]
    return {"ok": not offline, "nodes": nodes, "offlineNodes": offline, "probe": bool(probe)}


def accept_plan(steps: list[dict], mesh: dict, probe: bool = False) -> dict:
    routes = mesh.get("routes") or []
    route_nodes = {str(route.get("uri") or ""): str(route.get("node") or "") for route in routes}
    runs_on = {}
    violations = []
    for step in steps:
        uri = str(step.get("uri") or "")
        node = route_nodes.get(uri)
        if node:
            runs_on[uri] = node
        else:
            violations.append({"uri": uri, "blockedAt": "routing", "reason": "route not served"})
    report = {"ok": not violations, "runsOnByStep": runs_on, "probe": bool(probe)}
    return {"accepted": not violations, "violations": violations, "report": report}
