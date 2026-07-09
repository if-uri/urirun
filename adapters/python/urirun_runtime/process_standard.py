# Author: Tom Sapletta · Part of the ifURI solution.
"""Standard komunikacji LLM ↔ ticket: blok ```urirun:processes``` (urirun-llm-runtime).

https://github.com/if-uri/urirun-llm-runtime
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

NodeRunFn = Callable[[str, str, dict | None, float], dict]

_PROCESS_BLOCK = re.compile(
    r"```urirun:processes\s*\n(.*?)\n```",
    re.DOTALL | re.IGNORECASE,
)
_ALLOWED_ACTORS = frozenset({"llm", "script", "human", "system"})
_URI_RE = re.compile(r"^[a-z][a-z0-9+.-]*://[^/\s]+/.+")

LLM_RUNTIME_REPO = os.environ.get(
    "URIRUN_LLM_RUNTIME_REPO",
    "https://github.com/if-uri/urirun-llm-runtime",
)

LLM_OUTPUT_CONTRACT = f"""\
**STANDARD WYJŚCIA (obowiązkowy — urirun-llm-runtime):**
Odpowiedź LLM dla ticketu MUSI zawierać dokładnie jeden blok:

```urirun:processes
[
  {{
    "id": "step-1",
    "name": "Krótki opis",
    "actor": "script",
    "uri": "kvm://host/doctor/query/report",
    "payload": {{}},
    "depends_on": [],
    "human_approval": false
  }}
]
```

Pola: id, name, actor (llm|script|human|system), uri, payload, depends_on, human_approval.
Wykonanie: POST {{node}}/run z każdym krokiem w kolejności depends_on.
Bez subprocess/os.system — tylko URI z katalogu.
Spec: {LLM_RUNTIME_REPO}/blob/main/docs/llm/process_contract.md
"""


@dataclass
class UriProcess:
    id: str
    name: str
    actor: str
    uri: str
    payload: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    human_approval: bool = False
    timeout_seconds: int | None = None
    retries: int = 0

    def as_step(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "uri": self.uri,
            "payload": self.payload,
            "depends_on": self.depends_on,
            "human_approval": self.human_approval,
        }


def from_dict(item: dict[str, Any]) -> UriProcess:
    return UriProcess(
        id=str(item["id"]),
        name=str(item.get("name") or item["id"]),
        actor=str(item.get("actor") or "script"),
        uri=str(item["uri"]),
        payload=dict(item.get("payload") or {}),
        depends_on=[str(x) for x in (item.get("depends_on") or [])],
        human_approval=bool(item.get("human_approval")),
        timeout_seconds=item.get("timeout_seconds"),
        retries=int(item.get("retries") or 0),
    )


def parse_processes_block(text: str) -> list[UriProcess]:
    match = _PROCESS_BLOCK.search(text)
    raw = match.group(1) if match else text.strip()
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("urirun:processes must be a JSON array")
    return [from_dict(item) for item in data]


def validate_processes(processes: list[UriProcess]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for proc in processes:
        if not proc.id:
            errors.append("process missing id")
            continue
        if proc.id in seen:
            errors.append(f"duplicate id: {proc.id}")
        seen.add(proc.id)
        if proc.actor not in _ALLOWED_ACTORS:
            errors.append(f"{proc.id}: invalid actor {proc.actor!r}")
        if not _URI_RE.match(proc.uri):
            errors.append(f"{proc.id}: invalid uri {proc.uri!r}")
    ids = {p.id for p in processes}
    for proc in processes:
        for dep in proc.depends_on:
            if dep not in ids:
                errors.append(f"{proc.id}: unknown depends_on {dep!r}")
    return errors


def topological_order(processes: list[UriProcess]) -> list[UriProcess]:
    by_id = {p.id: p for p in processes}
    order: list[UriProcess] = []
    done: set[str] = set()

    def visit(pid: str) -> None:
        if pid in done:
            return
        for dep in by_id[pid].depends_on:
            visit(dep)
        done.add(pid)
        order.append(by_id[pid])

    for proc in processes:
        visit(proc.id)
    return order


def _legacy_steps_from_json(content: str) -> list[dict[str, Any]]:
    if "{" not in content:
        return []
    try:
        j = json.loads(content[content.find("{") : content.rfind("}") + 1])
    except Exception:
        return []
    if isinstance(j.get("decision_loop"), dict):
        flow = j["decision_loop"].get("flow") or {}
        steps = flow.get("steps")
        if isinstance(steps, list):
            return [s for s in steps if isinstance(s, dict) and s.get("uri")]
    if isinstance(j.get("flow"), dict):
        steps = j["flow"].get("steps")
        if isinstance(steps, list):
            return [s for s in steps if isinstance(s, dict) and s.get("uri")]
    if isinstance(j.get("procedure_steps"), list):
        return [s for s in j["procedure_steps"] if isinstance(s, dict) and s.get("uri")]
    return []


def extract_plan_from_llm(content: str) -> tuple[list[dict[str, Any]], str]:
    """Zwraca (kroki, format) — preferuje urirun:processes."""
    if not content:
        return [], "empty"
    if _PROCESS_BLOCK.search(content):
        try:
            procs = parse_processes_block(content)
            errs = validate_processes(procs)
            if errs:
                return [], f"urirun:processes-invalid:{';'.join(errs[:3])}"
            return [p.as_step() for p in topological_order(procs)], "urirun:processes"
        except Exception as exc:
            return [], f"urirun:processes-parse:{exc}"
    legacy = _legacy_steps_from_json(content)
    if legacy:
        return legacy, "decision_loop"
    return [], "none"


def load_process_examples(*, max_chars: int = 4000) -> str:
    """Przykłady prompt→urirun:processes (bundled lub URIRUN_LLM_EXAMPLES_FILE)."""
    custom = os.environ.get("URIRUN_LLM_EXAMPLES_FILE", "")
    if custom:
        path = Path(custom).expanduser()
        if path.is_file():
            return path.read_text(encoding="utf-8")[:max_chars]
    bundled = Path(__file__).resolve().parent / "llm_standard" / "process_examples.md"
    if bundled.is_file():
        return bundled.read_text(encoding="utf-8")[:max_chars]
    return (
        "(examples: set URIRUN_LLM_EXAMPLES_FILE or see "
        f"{LLM_RUNTIME_REPO}/blob/main/docs/markpact_marksync_process_examples.md)"
    )


def execute_plan(
    plan: list[dict[str, Any]],
    *,
    node: str,
    node_run: NodeRunFn,
    default_timeout: float = 60.0,
    stop_on_error: bool = True,
) -> list[dict[str, Any]]:
    """Wykonaj plan kroków na węźle przez node_run (POST /run)."""
    results: list[dict[str, Any]] = []
    for step in plan:
        if not isinstance(step, dict):
            continue
        if step.get("human_approval"):
            results.append({"id": step.get("id"), "skipped": True, "reason": "human_approval"})
            continue
        uri = str(step.get("uri") or "")
        if not uri:
            continue
        payload = step.get("payload") if isinstance(step.get("payload"), dict) else {}
        timeout = float(step.get("timeout_seconds") or default_timeout)
        retries = int(step.get("retries") or 0)
        last: dict[str, Any] = {}
        for attempt in range(retries + 1):
            try:
                last = node_run(node, uri, payload, timeout) or {}
            except Exception as exc:  # noqa: BLE001
                last = {"ok": False, "error": str(exc)}
            if last.get("ok", True) is not False and not last.get("error"):
                break
        entry = {"id": step.get("id"), "uri": uri, "result": last, "attempts": attempt + 1}
        results.append(entry)
        if stop_on_error and (last.get("ok") is False or last.get("error")):
            break
    return results
