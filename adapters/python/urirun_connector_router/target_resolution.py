from __future__ import annotations


def _node_name(target: str) -> str:
    value = str(target or "").strip()
    return value.removeprefix("node:")


def selected_nodes_from_targets(nodes: list[str], targets: list[str] | None = None) -> list[str]:
    out: list[str] = []
    for node in nodes or []:
        value = _node_name(node)
        if value and value != "host" and value not in out:
            out.append(value)
    for target in targets or []:
        raw = str(target or "").strip()
        if not raw.startswith("node:"):
            continue
        value = _node_name(raw)
        if value and value != "host" and value not in out:
            out.append(value)
    return out


def prompt_says_local(prompt: str) -> bool:
    text = str(prompt or "").casefold()
    return any(token in text for token in (
        "local", "localhost", "host", "ten komputer", "lokalnie", "mój komputer", "moj komputer",
    ))


def _prompt_says_remote(prompt: str) -> bool:
    text = str(prompt or "").casefold()
    return any(token in text for token in ("remote", "zdaln", "zdalny", "zdalnym"))


def target_selection_explicit(payload: dict) -> bool:
    return bool((payload or {}).get("target_explicit"))


def apply_host_default_when_no_node_in_prompt(
    prompt: str,
    selected_nodes: list[str],
    selected_targets: list[str],
    alias_map: dict | None = None,
) -> tuple[list[str], list[str]]:
    aliases = {str(k).casefold() for k in (alias_map or {})}
    text = str(prompt or "").casefold()
    if _prompt_says_remote(prompt) or (aliases and any(alias and alias in text for alias in aliases)):
        return selected_nodes, selected_targets
    if selected_nodes or selected_targets:
        return [], ["host"]
    return [], ["host"]


def resolve_selected_targets(
    payload: dict,
    prompt: str,
    alias_map: dict | None = None,
) -> tuple[list[str], list[str], list[str], list[str]]:
    raw_nodes = [str(item).strip() for item in ((payload or {}).get("nodes") or []) if str(item).strip()]
    raw_targets = [str(item).strip() for item in ((payload or {}).get("targets") or []) if str(item).strip()]
    text = str(prompt or "").casefold()
    aliases = alias_map or {}
    mentioned = []
    for alias, node in aliases.items():
        if str(alias).casefold() in text and str(node) not in mentioned:
            mentioned.append(str(node))
    if target_selection_explicit(payload):
        selected_nodes = list(dict.fromkeys(raw_nodes + selected_nodes_from_targets([], raw_targets)))
        selected_targets = list(dict.fromkeys(raw_targets or [f"node:{name}" for name in selected_nodes]))
    elif mentioned:
        selected_nodes = mentioned
        selected_targets = [f"node:{name}" for name in selected_nodes]
    else:
        selected_nodes, selected_targets = [], ["host"]
    return raw_nodes, raw_targets, selected_nodes, selected_targets


def rebuild_node_targets(
    selected: list[str],
    discovered_names: list[str],
    *,
    has_local: bool,
    existing_remote: set[str] | None = None,
) -> list[str]:
    existing_remote = existing_remote or set()
    out: list[str] = []
    if has_local:
        out.append("host")
    for target in selected:
        if target not in out:
            out.append(target)
    for name in discovered_names:
        if name in existing_remote:
            continue
        target = f"node:{name}"
        if target not in out:
            out.append(target)
    return out


def inactive_node_urls(nodes: list[dict], active_names: set[str]) -> set[str]:
    urls = set()
    for node in nodes:
        if not node.get("reachable"):
            continue
        if str(node.get("name") or "") in active_names:
            continue
        url = str(node.get("url") or "")
        if url:
            urls.add(url)
    return urls


def route_targets_active(route: dict, active_names: set[str], *, include_host: bool) -> bool:
    node = str(route.get("node") or "")
    if node == "host":
        return include_host
    return node in active_names


def filter_mesh_for_targets(discovered: dict, targets: list[str]) -> dict:
    include_host = "host" in targets
    active_names = {_node_name(target) for target in targets if target != "host"}
    nodes = list(discovered.get("nodes") or [])
    inactive_urls = inactive_node_urls(nodes, active_names)
    routes = [
        route for route in discovered.get("routes") or []
        if route_targets_active(route, active_names, include_host=include_host)
    ]
    service_map = {
        key: value for key, value in (discovered.get("serviceMap") or {}).items()
        if not value or value not in inactive_urls
    }
    if routes == (discovered.get("routes") or []) and service_map == (discovered.get("serviceMap") or {}):
        return discovered
    out = dict(discovered)
    out["routes"] = routes
    out["serviceMap"] = service_map
    return out


def with_local_host_routes(discovered: dict, targets: list[str], local_routes: list[dict]) -> dict:
    if "host" not in targets or not local_routes:
        return discovered
    seen = {route.get("uri") for route in discovered.get("routes") or []}
    merged = list(discovered.get("routes") or [])
    for route in local_routes:
        uri = route.get("uri")
        if uri not in seen:
            merged.append(route)
            seen.add(uri)
    if merged == (discovered.get("routes") or []):
        return discovered
    out = dict(discovered)
    out["routes"] = merged
    out["localHostRoutes"] = local_routes
    return out
