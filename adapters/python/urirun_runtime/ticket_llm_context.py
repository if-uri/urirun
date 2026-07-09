# Author: Tom Sapletta · Part of the ifURI solution.
"""Pierwszy prompt LLM dla ticketu: środowisko URI + katalog procesów ze schematami payload.

Używany przez goal.py, twin-human, planner — jeden format, pełna historia w journal.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable

NodeRunFn = Callable[[str, str, dict | None, float], dict]


FIRST_PROMPT_ROLE = (
    "Jesteś executorem automatyzacji IF-URI. Działasz W ŚRODOWISKU URI RUNTIME — nie piszesz "
    "imperatywnego Pythona zamiast procesów URI.\n\n"
    "**Jak działa runtime:**\n"
    "- Węzeł wykonawczy (np. lenovo) to uruchomiony `urirun node serve` z connectorami.\n"
    "- Każda akcja = URI proces: `scheme://target/path` + JSON payload zgodny ze schematem.\n"
    "- Dispatch: POST {node_base_url}/run → {\"uri\": \"kvm://host/...\", \"payload\": {...}}.\n"
    "- Segment `host` w kvm://host/... to alias węzła (URIRUN_KVM_URI_HOST), nie hostname.\n"
    "- Plan realizuj jako blok ```urirun:processes``` (JSON array) lub def run(ctx): ctx.run_uri(...).\n"
    "- Python hosta = tylko cienki glue; NIE zastępuj URI własnym skryptem.\n\n"
    "**Twoje zadanie:** z poniższej listy procesów wybierz minimalny plan w formacie "
    "`urirun:processes`. Zawsze: router://host/plan/query/diagnose przed keyboard, verify po mutacji."
)


def format_ticket_for_llm(ticket: dict[str, Any] | None) -> str:
    if not ticket:
        return ""
    tid = ticket.get("id") or ticket.get("ticket") or "?"
    labels = ticket.get("labels") or []
    name = ticket.get("name") or ""
    desc = (ticket.get("description") or "").split("BLOCKED:")[0].strip()
    inputs = ticket.get("inputs") or {}
    lines = [
        "**TICKET DO REALIZACJI:**",
        f"- id: {tid}",
        f"- name: {name}",
        f"- labels: {', '.join(str(x) for x in labels) if labels else '(brak)'}",
    ]
    if desc:
        lines.append(f"- description: {desc[:800]}")
    if inputs:
        lines.append(f"- inputs: {json.dumps(inputs, ensure_ascii=False)[:500]}")
    try:
        from urirun_connector_work.signal_kvm import resolve_node, is_signal_ticket
        if is_signal_ticket(ticket):
            node = resolve_node(ticket)
            lines.append(f"- suggested_execution_node: {node} (signal/KVM)")
    except Exception:  # noqa: BLE001
        pass
    return "\n".join(lines)


def _flatten_registry_lines() -> list[str]:
    live: list[str] = []
    try:
        import urirun
        from urirun.runtime._registry import flatten_registry_document
        reg: dict = {}
        try:
            reg = urirun.entry_point_registry() or {}
        except Exception:  # noqa: BLE001
            try:
                reg = urirun.compile_registry({}) or {}
            except Exception:  # noqa: BLE001
                reg = {}
        flat = flatten_registry_document(reg) if reg else []
        for r in flat[:100]:
            if not isinstance(r, dict):
                continue
            u = r.get("uri") or r.get("path")
            route_entry = r.get("routeEntry") or {}
            meta = route_entry.get("meta") or {}
            desc = (
                r.get("description") or r.get("doc") or r.get("help")
                or meta.get("label") or meta.get("description") or ""
            )
            cls = r.get("class") or meta.get("connector", "")
            schema = ((route_entry.get("config") or {}).get("inputSchema")) or {}
            props = schema.get("properties") or {}
            required = set(schema.get("required") or [])
            if props:
                fields = []
                for name, spec in list(props.items())[:8]:
                    t = spec.get("type", "any") if isinstance(spec, dict) else "any"
                    mark = "*" if name in required else ""
                    default = spec.get("default") if isinstance(spec, dict) else None
                    hint = f"{name}{mark}:{t}"
                    if default not in (None, False, ""):
                        hint += f"={default!r}"
                    fields.append(hint)
                payload_hint = "{" + ", ".join(fields) + "}"
            else:
                payload_hint = "{}"
            if u:
                live.append(f"- {u} payload={payload_hint} [{cls}] {str(desc)[:80]}")
        try:
            space = urirun.action_space(reg) if hasattr(urirun, "action_space") and reg else []
            for s in space[:50]:
                if isinstance(s, dict) and s.get("uri"):
                    live.append(f"- {s['uri']} (action)")
                elif isinstance(s, str):
                    live.append(f"- {s}")
        except Exception:  # noqa: BLE001
            pass
    except Exception:  # noqa: BLE001
        pass
    return live


def _fallback_catalog(node: str) -> list[str]:
    try:
        from urirun_connector_work.signal_kvm import registry_kvm_examples
        base = registry_kvm_examples().splitlines()
    except Exception:  # noqa: BLE001
        base = [
            "- kvm://host/window/command/focus payload={title*:string}",
            "- kvm://host/ui/query/verify payload={text*:string}",
            "- kvm://host/input/command/type payload={text*:string}",
        ]
    return [
        *base,
        "- app://host/desktop/query/list : running apps on node",
        "- router://host/plan/query/diagnose : validate plan BEFORE exec",
        "- vdisplay://host/windows/query/list : window enumeration",
        "- inquiry://host/case/command/create : debugger case on failure",
        f"- (execution node for this task: {node})",
    ]


def collect_uri_process_catalog(
    node: str = "lenovo",
    *,
    node_run: NodeRunFn | None = None,
) -> list[str]:
    lines = _flatten_registry_lines()
    if node_run:
        try:
            r = node_run(node, "router://host/plan/query/diagnose",
                         {"intent": {"id": "registry-snapshot"}, "flow": {"steps": []}}, 5.0)
            if isinstance(r, dict):
                for k in ("available", "routes", "uris", "capabilities", "options"):
                    v = r.get(k)
                    if isinstance(v, list):
                        for x in v[:30]:
                            lines.append(f"- {x}")
        except Exception:  # noqa: BLE001
            pass
    deduped = list(dict.fromkeys(lines))
    return deduped if deduped else _fallback_catalog(node)


def build_first_system_prompt(
    *,
    ticket: dict[str, Any] | None = None,
    node: str = "lenovo",
    node_run: NodeRunFn | None = None,
    include_decision_rules: bool = True,
) -> str:
    """Pełny pierwszy prompt: środowisko + ticket + katalog URI ze schematami."""
    parts: list[str] = [FIRST_PROMPT_ROLE]

    try:
        from urirun_runtime.environment_topology import format_topology_for_llm
        topo = format_topology_for_llm()
        if topo:
            parts.append(topo)
    except Exception:  # noqa: BLE001
        parts.append(f"(topology unavailable; execution node={node})")

    ticket_block = format_ticket_for_llm(ticket)
    if ticket_block:
        parts.append(ticket_block)

    catalog = collect_uri_process_catalog(node, node_run=node_run)
    parts.append(
        "**DOSTĘPNE PROCESY URI (wybierz z listy; payload ze schematu — * = required):**\n"
        "Użyj WYŁĄCZNIE tych URI (+ ich dokładnych nazw pól) do realizacji ticketu.\n"
        + "\n".join(catalog[:60])
    )

    if include_decision_rules:
        parts.append(
            "**Proces decyzyjny:**\n"
            "1. Zrozum ticket → wybierz minimalny podzbiór URI z katalogu.\n"
            "2. router://host/plan/query/diagnose na złożony plan (tylko na węźle z connector-router — dashboard; na lenovo pomijaj lub użyj kvm://host/doctor).\n"
            "3. Małe kroki: observe → jeden URI → verify efektu.\n"
            "4. Przy błędzie: inquiry:// + poprawiony plan (feedback w historii).\n"
            "5. Output: WYŁĄCZNIE blok ```urirun:processes``` z JSON array (standard urirun-llm-runtime).\n"
            "6. W trakcie wykonania: pętla LLM-runtime — każda tura dostajesz OBSERVATION (gap, wyniki /run) i wybierasz 1–3 następne URI.\n"
            f"\n[Catalog: {len(catalog)} processes | node={node}]"
        )

    try:
        from urirun_runtime.process_standard import LLM_OUTPUT_CONTRACT, load_process_examples
        parts.append(LLM_OUTPUT_CONTRACT)
        examples = load_process_examples(max_chars=3500)
        if examples:
            parts.append("**PRZYKŁADY (prompt → urirun:processes):**\n" + examples)
    except Exception:  # noqa: BLE001
        pass

    return "\n\n".join(p for p in parts if p)


def save_llm_turn(
    ticket: str | None,
    *,
    role: str,
    phase: str,
    content: str,
    model: str = "",
    extra: dict | None = None,
) -> None:
    """Historia konwersacji LLM↔runtime (plan, wynik, debugger) — {ticket}-turns.jsonl."""
    if not ticket:
        return
    entry = {
        "ts": time.time(),
        "role": role,
        "phase": phase,
        "model": model,
        "content": content[:12000] if len(content) > 12000 else content,
        "extra": extra or {},
    }
    try:
        jdir = Path(os.environ.get("URIRUN_JOURNAL_DIR") or "~/.urirun/host-dashboard/journal").expanduser()
        jdir.mkdir(parents=True, exist_ok=True)
        with open(jdir / f"{ticket}-turns.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:  # noqa: BLE001
        pass


def record_first_prompt(ticket: dict[str, Any] | None, node: str, prompt: str, *, model: str = "system") -> None:
    tid = (ticket or {}).get("id") or (ticket or {}).get("ticket")
    save_llm_turn(
        str(tid) if tid else None,
        role="system",
        phase="first-prompt-environment",
        content=prompt,
        model=model,
        extra={"node": node, "ticket_id": tid},
    )


def load_llm_turns(ticket: str, *, limit: int = 20) -> list[dict]:
    path = Path(os.environ.get("URIRUN_JOURNAL_DIR") or "~/.urirun/host-dashboard/journal").expanduser()
    f = path / f"{ticket}-turns.jsonl"
    if not f.is_file():
        return []
    lines = f.read_text(encoding="utf-8").strip().splitlines()
    out = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def format_turns_for_llm(ticket: str, *, limit: int = 10) -> str:
    """Dołącz do retry promptu: poprzedni plan + runtime + debugger."""
    turns = load_llm_turns(ticket, limit=limit)
    if not turns:
        return ""
    parts = ["**HISTORIA KONWERSACJI (plan → runtime → debugger):**"]
    for t in turns:
        parts.append(f"[{t.get('role')}/{t.get('phase')}] {str(t.get('content', ''))[:2000]}")
    return "\n\n".join(parts)


def parse_ticket_process_plan(content: str) -> tuple[list[dict[str, Any]], str]:
    """Parsuj odpowiedź LLM — standard urirun:processes (fallback: decision_loop)."""
    from urirun_runtime.process_standard import extract_plan_from_llm
    return extract_plan_from_llm(content)


def execute_ticket_process_plan(
    plan: list[dict[str, Any]],
    *,
    node: str,
    node_run: NodeRunFn,
    ticket: str | None = None,
) -> list[dict[str, Any]]:
    """Wykonaj plan na węźle; zapisz wynik w historii ticketu."""
    from urirun_runtime.process_standard import execute_plan
    results = execute_plan(plan, node=node, node_run=node_run)
    if ticket:
        save_llm_turn(
            ticket,
            role="tool",
            phase="runtime-process-plan",
            content=json.dumps({"steps": len(plan), "results": results}, ensure_ascii=False, default=str)[:8000],
            extra={"node": node, "step_count": len(plan)},
        )
    return results
