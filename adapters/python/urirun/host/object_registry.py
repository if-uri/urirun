from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from .node_types import annotate_node_type, node_type_profile


PHONE_SCANNER_ROUTES = [
    "dashboard://host/phone-scanner/command/start",
    "dashboard://host/service/phone-scanner/command/restart",
    "service://host/phone-scanner/command/restart",
    "service://phone-scanner/command/restart",
    "scanner://page/camera/command/scan",
    "scanner://page/camera/command/best-pdf",
    "scanner://page/camera/command/autonomous",
]


def host_registry_routes(actions: list[dict]) -> list[dict]:
    routes = []
    for action in actions:
        if action.get("layer") not in {"host", "dashboard", "connector"}:
            continue
        routes.append({
            "uri": action.get("uri"),
            "kind": action.get("kind"),
            "title": action.get("label"),
            "source": action.get("where"),
            "safe": not bool(action.get("sideEffects")),
            "layer": action.get("layer"),
        })
    return routes


def host_object(project: str, routes: list[dict]) -> dict:
    return {
        "id": "host",
        "kind": "host",
        "label": "urirun host",
        "status": "local",
        "reachable": True,
        "url": str(Path(project).expanduser().resolve()),
        "routes": routes,
    }


def _uri_target(uri: str) -> str:
    if "://" not in uri:
        return ""
    rest = uri.split("://", 1)[1]
    return rest.split("/", 1)[0]


def _route_core_fields(route: dict, uri: str, owner: dict) -> dict:
    return {
        "uri": uri,
        "kind": route.get("kind") or "",
        "title": route.get("title") or route.get("label") or "",
        "source": route.get("source") or route.get("where") or route.get("adapter") or "registry",
        "adapter": route.get("adapter") or route.get("source") or "registry",
        "safe": route.get("safe"),
        "layer": route.get("layer") or "",
        "node": route.get("node") or "",
        "target": route.get("target") or route.get("node") or _uri_target(uri) or owner.get("id"),
    }


def route_owner_route(route: dict, owner: dict) -> dict:
    uri = str(route.get("uri") or "")
    return {
        **_route_core_fields(route, uri, owner),
        "ownerId": owner.get("id"),
        "ownerKind": owner.get("kind"),
        "ownerLabel": owner.get("label"),
    }


def dedupe_routes(routes: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for route in routes:
        key = "|".join(str(route.get(name) or "") for name in ("uri", "kind", "adapter"))
        if not route.get("uri") or key in seen:
            continue
        seen.add(key)
        out.append(route)
    return out


def _node_owner_dict(node: dict, name: str, typed_node: dict) -> dict:
    return {
        "id": f"node:{name}",
        "kind": "node",
        "label": f"urirun node: {name}",
        "status": "up" if node.get("reachable") else "down",
        "reachable": bool(node.get("reachable")),
        "url": node.get("url") or "",
        "type": typed_node.get("type") or "",
        "nodeType": typed_node.get("nodeType") or "",
        "typeLabel": typed_node.get("typeLabel") or "",
        "integrationLevel": typed_node.get("integrationLevel") or "",
        "transport": typed_node.get("transport") or "http",
        "runtime": typed_node.get("runtime") or "urirun-node",
        "apis": node.get("apis") if isinstance(node.get("apis"), list) else [],
        "capabilities": node.get("capabilities") if isinstance(node.get("capabilities"), list) else [],
        "error": node.get("error") or "",
    }


def _node_own_routes(node: dict, all_routes: list[dict], name: str) -> list[dict]:
    own = node.get("routes") if isinstance(node.get("routes"), list) else []
    if not own:
        own = [r for r in all_routes if r.get("node") == name or _uri_target(str(r.get("uri") or "")) == name]
    return own


def node_object(node: dict, all_routes: list[dict]) -> dict:
    typed_node = annotate_node_type(node)
    name = str(node.get("name") or "")
    owner = _node_owner_dict(node, name, typed_node)
    own_routes = _node_own_routes(node, all_routes, name)
    return {
        **owner,
        "routes": dedupe_routes([route_owner_route(route, owner) for route in own_routes]),
    }


def service_object(service: dict) -> dict:
    owner = {
        "id": service.get("id") or f"service:{service.get('name')}",
        "kind": "service",
        "label": service.get("label") or f"urirun service: {service.get('name')}",
        "status": service.get("status") or ("running" if service.get("reachable") else "stopped"),
        "reachable": bool(service.get("reachable")),
        "url": service.get("url") or "",
        "transport": service.get("transport") or "http",
        "runtime": service.get("runtime") or service.get("name") or "service",
    }
    routes = service.get("routes") if isinstance(service.get("routes"), list) else []
    route_rows = [
        route if isinstance(route, dict) else {"uri": route, "kind": "command", "adapter": "service"}
        for route in routes
    ]
    return {
        **owner,
        "routes": dedupe_routes([route_owner_route(route, owner) for route in route_rows]),
    }


def uri_objects(*, project: str, host_routes: list[dict], nodes: list[dict],
                services: list[dict], routes: list[dict]) -> list[dict]:
    host = host_object(project, dedupe_routes([
        route_owner_route(route, {"id": "host", "kind": "host", "label": "urirun host"})
        for route in host_routes
    ]))
    return [
        host,
        *[node_object(node, routes) for node in nodes if node.get("name")],
        *[service_object(service) for service in services],
    ]


def phone_scanner_contact(scanner_state: dict) -> dict:
    return {
        "id": "service:phone-scanner",
        "kind": "service",
        "name": "phone-scanner",
        "label": "urirun service: photo scanner",
        "url": scanner_state["url"],
        "status": scanner_state["status"],
        "reachable": scanner_state["reachable"],
        "routes": list(PHONE_SCANNER_ROUTES),
    }


def service_contacts(
    *,
    scanner_port: int,
    scanner_state: dict,
    service_entries: list[dict],
    phone_scanner_url: Callable[[int], str],
    phone_scanner_status: Callable[[int], dict],
) -> list[dict]:
    phone_scanner = phone_scanner_contact(scanner_state)
    contacts = [phone_scanner]
    for entry in service_entries:
        service_id = str(entry.get("service_id") or "")
        parsed = urlparse(service_id)
        port = int(parsed.port or scanner_port)
        service_url = phone_scanner_url(port)
        name = "phone-scanner" if port == scanner_port else f"service-{port}"
        alive = bool(entry.get("alive"))
        external = (
            {"status": "stopped", "reachable": False, "url": service_url}
            if alive
            else phone_scanner_status(port)
        )
        item = {
            **phone_scanner,
            "id": f"service:{name}",
            "name": name,
            "label": f"urirun service: {name}",
            "url": service_url if alive else external["url"],
            "bindUrl": service_id,
            "status": "running" if alive else external["status"],
            "reachable": alive or bool(external["reachable"]),
            "serverName": str(entry.get("server_name") or ""),
        }
        contacts = [contact for contact in contacts if contact.get("id") != item["id"]]
        contacts.append(item)
    return contacts


def annotate_node_tokens(nodes: list[dict], node_token_for: Callable[[str], Any]) -> list[dict]:
    for node in nodes:
        node_name = node.get("name")
        if not node_name:
            continue
        try:
            node["hasToken"] = bool(node_token_for(str(node_name)))
        except Exception:  # noqa: BLE001
            node["hasToken"] = False
    return nodes


def mirror_node_to_nodes_file(name: str, url: str) -> None:
    """Best-effort mirror to ~/.urirun/nodes.json so urifix can auto-repair node_url."""
    try:
        nodes_path = os.environ.get("URIRUN_NODES_FILE") or os.path.expanduser("~/.urirun/nodes.json")
        known: dict = {}
        if os.path.exists(nodes_path):
            with open(nodes_path, encoding="utf-8") as fh:
                loaded = json.load(fh)
            if isinstance(loaded, dict):
                inner = loaded.get("nodes")
                known = inner if isinstance(inner, dict) else loaded
        known[name] = url
        os.makedirs(os.path.dirname(nodes_path) or ".", exist_ok=True)
        with open(nodes_path, "w", encoding="utf-8") as fh:
            json.dump(known, fh, indent=2)
    except Exception:  # noqa: BLE001
        pass


def node_api_slug(value: Any, fallback: str) -> str:
    raw = str(value or "").strip().lower()
    slug = re.sub(r"[^a-z0-9_-]+", "-", raw).strip("-")
    return slug or fallback


def node_api_secret_ref(name: str, api_id: str) -> str:
    account = f"{node_api_slug(name, 'node')}/{node_api_slug(api_id, 'api')}"
    return f"secret://keyring/urirun-node-api/{account}#credential"


def store_node_api_secret(name: str, api_id: str, secret: str) -> tuple[str | None, str | None]:
    if not secret:
        return None, None
    try:
        import keyring
        account = f"{node_api_slug(name, 'node')}/{node_api_slug(api_id, 'api')}"
        keyring.set_password("urirun-node-api", account, secret)
        return node_api_secret_ref(name, api_id), None
    except Exception as exc:  # noqa: BLE001
        return None, f"could not store API credential securely (keyring): {exc}"


def extract_raw_secret(auth_data: dict, api: dict) -> str | None:
    return (
        auth_data.get("token")
        or auth_data.get("apiKey")
        or auth_data.get("password")
        or auth_data.get("secret")
        or api.get("token")
        or api.get("apiKey")
        or api.get("password")
        or api.get("secret")
    )


def extract_secret_ref(auth_data: dict, api: dict) -> str | None:
    return (
        auth_data.get("secretRef")
        or auth_data.get("ref")
        or auth_data.get("credentialRef")
        or api.get("secretRef")
        or api.get("credentialRef")
    )


def build_auth_extra_fields(auth_data: dict, api: dict) -> dict:
    extra: dict = {}
    for key in ("username", "header", "headerName", "queryParam", "scheme", "tokenUrl", "clientIdRef"):
        value = auth_data.get(key) if key in auth_data else api.get(key)
        if value not in (None, ""):
            extra[key] = value
    return extra


def normalize_node_api_auth(name: str, api_id: str, api: dict, auth: Any) -> tuple[dict, str | None]:
    auth_data = auth if isinstance(auth, dict) else {}
    raw_secret = extract_raw_secret(auth_data, api)
    secret_ref = extract_secret_ref(auth_data, api)
    auth_type = str(
        auth_data.get("type")
        or api.get("authType")
        or ("bearer" if raw_secret else ("ref" if secret_ref else "none"))
    ).strip().lower()
    if raw_secret:
        secret_ref, error = store_node_api_secret(name, api_id, str(raw_secret))
        if error:
            return {}, error
    if auth_type in {"", "none", "no", "false"} and not secret_ref:
        return {}, None
    out: dict = {"type": auth_type or "ref"}
    if secret_ref:
        out["secretRef"] = str(secret_ref)
    out.update(build_auth_extra_fields(auth_data, api))
    return out, None


def default_api_items(url: str, kind: str, payload: dict) -> list[dict]:
    return [{
        "id": "default",
        "label": "default API",
        "url": url,
        "kind": payload.get("protocol") or payload.get("apiKind") or ("web" if kind == "device" else "http"),
        "auth": payload.get("auth") if isinstance(payload.get("auth"), dict) else {},
    }]


def api_item_fields(item: dict, url: str, index: int) -> tuple[str, str, str]:
    api_id = node_api_slug(item.get("id") or item.get("name") or item.get("role"), f"api-{index}")
    api_url = str(item.get("url") or item.get("endpoint") or item.get("baseUrl") or url).strip()
    api_kind = str(item.get("kind") or item.get("protocol") or item.get("transport") or "http").strip().lower()
    return api_id, api_url, api_kind


def normalize_api_item(name: str, url: str, index: int, item: dict,
                       fallback_auth: Any) -> tuple[dict | None, str | None]:
    api_id, api_url, api_kind = api_item_fields(item, url, index)
    if not api_url:
        return None, None
    api: dict = {"id": api_id, "kind": api_kind, "url": api_url}
    for key in ("label", "role", "openapi", "basePath", "mount", "description"):
        if item.get(key) not in (None, ""):
            api[key] = item[key]
    auth, error = normalize_node_api_auth(name, api_id, item, item.get("auth") or fallback_auth)
    if error:
        return None, error
    if auth:
        api["auth"] = auth
    return api, None


def normalize_node_apis(name: str, url: str, kind: str | None, payload: dict) -> tuple[list[dict], str | None]:
    raw = payload.get("apis") or payload.get("interfaces") or payload.get("api")
    if isinstance(raw, dict):
        raw_items: list = [raw]
    elif isinstance(raw, list):
        raw_items = raw
    else:
        raw_items = []
    if not raw_items and kind in {"api", "device"}:
        raw_items = default_api_items(url, kind, payload)
    apis: list[dict] = []
    fallback_auth = payload.get("auth")
    for index, item in enumerate(raw_items, 1):
        if not isinstance(item, dict):
            continue
        api, error = normalize_api_item(name, url, index, item, fallback_auth)
        if error:
            return [], error
        if api is not None:
            apis.append(api)
    return apis, None


def derive_node_capabilities(payload: dict, apis: list[dict]) -> list[str]:
    raw = payload.get("capabilities")
    caps = [str(item).strip() for item in raw] if isinstance(raw, list) else []
    for api in apis:
        api_kind = str(api.get("kind") or "").lower()
        role = str(api.get("role") or "").lower()
        if api_kind in {"rtsp", "rtmp", "rtmps", "hls", "onvif"} or role == "camera":
            caps.append("camera")
        if api_kind in {"smb", "nfs", "nas", "sftp"}:
            caps.append("files")
        if api_kind in {"ssh", "sftp"}:
            caps.append("shell")
        if api_kind in {"http", "https", "rest", "openapi", "web", "panel"}:
            caps.append("api")
    return sorted({cap for cap in caps if cap})


def build_node_entry(
    name: str,
    url: str,
    kind: str | None,
    apis: list[dict] | None = None,
    capabilities: list[str] | None = None,
) -> dict:
    node: dict = {"name": name, "url": url, "kind": kind or None}
    if kind:
        profile = node_type_profile(kind)
        node.update({
            "kind": kind,
            "type": kind,
            "nodeType": kind,
            "typeLabel": profile.get("label") or kind,
            "transport": profile.get("transport") or "",
            "runtime": profile.get("runtime") or "",
            "integrationLevel": profile.get("integrationLevel") or "",
        })
    if apis:
        node["apis"] = apis
    if capabilities:
        node["capabilities"] = capabilities
    return node


def persist_node_to_config(
    node_config: Any,
    config: str | None,
    name: str,
    url: str,
    *,
    tags: list | None,
    apis: list | None,
    capabilities: list | None,
    meta: dict | None,
) -> tuple[dict | None, str | None]:
    try:
        updated = node_config.add_node(
            config, name, url,
            tags=tags, apis=apis or None, capabilities=capabilities or None, meta=meta,
        )
        return updated, None
    except Exception as exc:  # noqa: BLE001
        return None, f"could not persist node: {exc}"


def node_remove_from_mirror(name: str) -> bool:
    """Remove a node from the nodes.json urifix mirror; True if it was present (best-effort)."""
    try:
        nodes_path = os.environ.get("URIRUN_NODES_FILE") or os.path.expanduser("~/.urirun/nodes.json")
        if not os.path.exists(nodes_path):
            return False
        with open(nodes_path, encoding="utf-8") as fh:
            loaded = json.load(fh)
        inner = loaded.get("nodes") if isinstance(loaded, dict) else None
        target = inner if isinstance(inner, dict) else (loaded if isinstance(loaded, dict) else {})
        if name not in target:
            return False
        target.pop(name, None)
        with open(nodes_path, "w", encoding="utf-8") as fh:
            json.dump(loaded, fh, indent=2)
        return True
    except Exception:  # noqa: BLE001
        return False
