# Author: Tom Sapletta · Part of the ifURI solution.
"""Topologia środowiska URI dla promptów LLM — skąd LLM wie, gdzie działa kvm:// / signal://."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_DEFAULT_REL = "compose/uri-runtime/generated/environment.context.yaml"
_TEMPLATE_REL = "compose/uri-runtime/environment.uri-topology.yaml"


def _project_root() -> Path:
    return Path(os.environ.get("URIRUN_KORU_PROJECT") or os.getcwd()).expanduser()


def topology_path() -> Path:
    raw = os.environ.get("URIRUN_URI_TOPOLOGY_FILE", "")
    if raw:
        p = Path(raw).expanduser()
        return p if p.is_absolute() else _project_root() / p
    return _project_root() / _DEFAULT_REL


def _load_yaml_or_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    try:
        import yaml
        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else {}
    except Exception:
        pass
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def load_topology() -> dict[str, Any]:
    """Połącz szablon + wygenerowany kontekst (generated wygrywa nad template)."""
    root = _project_root()
    base = _load_yaml_or_json(root / _TEMPLATE_REL)
    live = _load_yaml_or_json(topology_path())
    if not base:
        return live
    if not live:
        return base
    merged = dict(base)
    env = dict((base.get("uri_runtime_environment") or {}))
    env.update(live.get("uri_runtime_environment") or {})
    merged["uri_runtime_environment"] = env
    return merged


def _fmt_nodes(env: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for node in env.get("live_nodes") or []:
        if not isinstance(node, dict):
            continue
        status = "OK" if node.get("reachable") else "UNREACHABLE"
        schemes = ", ".join((node.get("route_schemes") or [])[:12])
        extra = f" schemes=[{schemes}]" if schemes else ""
        rc = node.get("route_count")
        rc_s = f" routes={rc}" if rc is not None else ""
        lines.append(f"  - {node.get('id')}: {node.get('base_url')} [{status}]{rc_s}{extra}")
    return lines


def format_topology_for_llm(*, max_chars: int = 6000) -> str:
    """Blok tekstu do wstrzyknięcia w prompt executora/plannera."""
    data = load_topology()
    env = data.get("uri_runtime_environment") or {}
    if not env:
        return ""

    parts = [
        "**URI RUNTIME ENVIRONMENT (gdzie uruchamiane są procesy URI — NIE mylić z kodem Python hosta)**",
        "",
    ]
    how = env.get("how_uri_processes_run")
    if how:
        parts.append(str(how).strip())
        parts.append("")

    rules = env.get("addressing_rules") or []
    if rules:
        parts.append("**Adresowanie:**")
        parts.extend(f"- {r}" for r in rules)
        parts.append("")

    default = env.get("default_execution") or {}
    if default:
        parts.append("**Domyślne wykonanie:**")
        for k, v in default.items():
            parts.append(f"- {k}: {v}")
        parts.append("")

    nodes = _fmt_nodes(env)
    if nodes:
        parts.append("**Węzły (live probe):**")
        parts.extend(nodes)
        parts.append("")

    build = env.get("build_pipeline") or {}
    if build:
        parts.append("**Budowa środowiska:**")
        for k, v in build.items():
            parts.append(f"- {k}: {v}")
        parts.append("")

    layers = env.get("layers") or {}
    for layer_name, layer in layers.items():
        if not isinstance(layer, dict):
            continue
        parts.append(f"**Warstwa {layer_name}:** {layer.get('description', '')}")
        for svc in layer.get("services") or []:
            if isinstance(svc, dict):
                parts.append(f"  - {svc.get('id')}: {svc.get('role')} port={svc.get('default_port')} "
                             f"deploy={svc.get('deployment', 'n/a')}")
        parts.append("")

    if env.get("generated_at"):
        parts.append(f"(topology generated_at={env['generated_at']})")

    text = "\n".join(parts).strip()
    return text[:max_chars] if len(text) > max_chars else text
