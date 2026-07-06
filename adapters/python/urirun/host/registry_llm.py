# Author: Tom Sapletta · Part of the ifURI solution.
"""registry_llm — PEŁNY cross-node registry URI-procesów DLA LLM-orchestratora.

Sedno (dyrektywa użytkownika): orchestrator-LLM musi dostać w kontekście wszystkie dostępne
URI-procesy **z argami (inputSchema), efektem, bezpieczeństwem i tym KTÓRY węzeł je serwuje** —
żeby WYBIERAĆ i ORCHESTROWAĆ w oparciu o fakty, nie zgadywać tras/argów.

Każdy węzeł wystawia `/routes` z: uri, inputSchema.properties (argi), effect, safe, title.
Ta warstwa agreguje je po schemacie i buduje indeks zdolności (scheme → węzły serwujące).
"""
from __future__ import annotations

import json
import urllib.request
from typing import Any

_DEFAULT_NODES = {"laptop": "http://192.168.188.201:8765", "host": "http://127.0.0.1:8797"}


def _fetch_routes(url: str) -> list[dict]:
    for path in ("/routes", "/api/routes"):
        try:
            with urllib.request.urlopen(url + path, timeout=6) as r:  # noqa: S310
                d = json.loads(r.read().decode())
                routes = d.get("routes", d)
                if isinstance(routes, dict):
                    routes = list(routes.values())
                if isinstance(routes, list) and routes:
                    return [x for x in routes if isinstance(x, dict)]
        except Exception:  # noqa: BLE001
            continue
    return []


def _route_args(route: dict) -> list[str]:
    return sorted((route.get("inputSchema") or {}).get("properties", {}).keys())


def gather(nodes: dict[str, str] | None = None) -> dict[str, Any]:
    """Zbierz registry ze WSZYSTKICH węzłów. Zwróć po schemacie + indeks zdolności."""
    nodes = nodes or _DEFAULT_NODES
    by_scheme: dict[str, dict] = {}
    node_status: dict[str, Any] = {}
    for name, url in nodes.items():
        routes = _fetch_routes(url)
        node_status[name] = {"url": url, "routes": len(routes), "reachable": bool(routes)}
        for r in routes:
            uri = r.get("uri") or ""
            if "://" not in uri:
                continue
            scheme = uri.split("://", 1)[0]
            entry = by_scheme.setdefault(scheme, {}).setdefault(uri, {
                "args": _route_args(r), "effect": r.get("effect"), "safe": r.get("safe"),
                "title": r.get("title"), "nodes": []})
            if name not in entry["nodes"]:
                entry["nodes"].append(name)
    # indeks zdolności: scheme → które węzły je serwują (do doboru WHERE)
    capability_index = {s: sorted({n for u in routes.values() for n in u["nodes"]})
                        for s, routes in by_scheme.items()}
    return {"nodes": node_status, "schemes": sorted(by_scheme),
            "capability_index": capability_index, "registry": by_scheme}


def find(need: str, nodes: dict[str, str] | None = None) -> dict[str, Any]:
    """Wyszukaj URI-procesy pasujące do potrzeby (po schemacie/uri/tytule) + GDZIE są serwowane.
    To jest krok WHERE/HOW: dla 'signal reply' zwróci trasy signal:// i węzły (albo pustkę→brak zdolności)."""
    reg = gather(nodes)
    need_l = need.lower()
    hits = []
    for scheme, routes in reg["registry"].items():
        for uri, info in routes.items():
            if need_l in uri.lower() or need_l in (info.get("title") or "").lower() or need_l == scheme:
                hits.append({"uri": uri, "args": info["args"], "effect": info["effect"],
                             "safe": info["safe"], "nodes": info["nodes"], "title": info["title"]})
    return {"need": need, "matches": hits, "served": bool(hits),
            "nodes_for_need": sorted({n for h in hits for n in h["nodes"]})}
