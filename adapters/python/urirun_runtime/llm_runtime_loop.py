# Author: Tom Sapletta · Part of the ifURI solution.
"""Pętla wykonawcza sterowana przez LLM z pełnym URI runtime.

LLM na każdym kroku dostaje: topologię, katalog URI, gap ticketu, historię, wyniki runtime.
Decyduje o kolejnych krokach (dogrywanie brakujących, retry, inquiry) — wyłącznie przez URI.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Callable

from urirun_runtime.process_standard import (
    LLM_OUTPUT_CONTRACT,
    extract_plan_from_llm,
    parse_processes_block,
)
from urirun_runtime.ticket_llm_context import (
    build_first_system_prompt,
    format_turns_for_llm,
    save_llm_turn,
)
from urirun_runtime.runtime_markdown import load_runtime_markdown_bundle

NodeRunFn = Callable[[str, str, dict | None, float], dict]
LlmFn = Callable[[str, str | None], str]

_SINGLE_JSON = re.compile(r"\{[^{}]*\"uri\"\s*:\s*\"[^\"]+\"[^{}]*\}", re.DOTALL)

LLM_LOOP_ROLE = """\
Jesteś EXECUTOREM TICKETU z pełnym URI runtime do dyspozycji.

**Pętla (każda tura):**
1. OBSERVATION — gap (czego brakuje), ostatnie wyniki /run, historia.
2. Ty decydujesz o NASTĘPNYCH 1–3 krokach (dogrywanie, retry, brakujące URI).
3. Runtime wykonuje POST {node}/run — nie piszesz Pythona ani subprocess.

**Wyjście (jedno z):**
- Blok ```urirun:processes``` z 1–3 kolejnymi krokami, LUB
- Pojedynczy JSON: {"uri":"...", "payload":{...}, "reason":"..."}, LUB
- {"uri":"done", "reason":"cel osiągnięty"} gdy ticket zamknięty, LUB
- inquiry://host/case/command/create gdy zablokowany po 2 próbach.

**Gap / braki:** jeśli observation.gap.missing niepuste — pierwszy krok ma to adresować.
**Keyboard:** dopiero po verify/focus Signal; przy błędzie verify — capture + inny URI z katalogu.

**NAPRAWA (REPAIR):** gdy observation.last_error jest ustawione — poprzedni krok URI zawiódł.
Przeanalizuj error JSON i wybierz INNY URI z runtime bundle (nie powtarzaj tego samego payloadu).
Możesz: capture → focus → verify → retry z poprawionym payloadem → inquiry:// jeśli 2× fail.
"""

REPAIR_PROMPT = """\
**⚠ REPAIR REQUIRED** — ostatni krok URI zwrócił błąd (pełny JSON w observation.last_error).
Twoje następne kroki MUSZĄ naprawić sytuację używając WYŁĄCZNIE URI z runtime bundle w system prompt.
Nie kończ done dopóki cel ticketu nie jest spełniony lub nie użyjesz inquiry:// po 2 nieudanych naprawach.
"""


def _gap_for_ticket(ticket_id: str | None, project: str = "") -> dict[str, Any]:
    if not ticket_id:
        return {}
    try:
        from urirun_connector_continuity.core import analyze
        proj = project or os.environ.get("URIRUN_KORU_PROJECT") or os.path.expanduser("~/github/if-uri")
        return analyze(proj, ticket_id)
    except Exception:  # noqa: BLE001
        return {}


def _light_kvm_state(node_run: NodeRunFn, node: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for uri in ("kvm://host/doctor/query/report", "kvm://host/window/query/list"):
        try:
            r = node_run(node, uri, {}, 15.0)
            out[uri] = {
                "ok": r.get("ok", True) is not False,
                "snippet": json.dumps(r, default=str)[:600],
            }
        except Exception as exc:  # noqa: BLE001
            out[uri] = {"ok": False, "error": str(exc)}
    return out


def parse_llm_action(content: str) -> list[dict[str, Any]]:
    """Wyciągnij następne kroki z odpowiedzi LLM."""
    if not content:
        return []
    text = content.strip()
    if "done" in text.lower() and '"uri"' in text and "done" in text:
        try:
            j = json.loads(text[text.find("{") : text.rfind("}") + 1])
            if str(j.get("uri", "")).lower() == "done":
                return [{"id": "done", "uri": "done", "payload": {}, "reason": j.get("reason", "")}]
        except Exception:
            pass
    plan, fmt = extract_plan_from_llm(text)
    if plan:
        return plan[:3]
    # single JSON step
    if "{" in text:
        chunk = text[text.find("{") : text.rfind("}") + 1]
        try:
            j = json.loads(chunk)
            if j.get("uri"):
                return [{
                    "id": j.get("id") or "llm-step",
                    "name": j.get("reason") or j.get("name") or "llm-step",
                    "uri": j["uri"],
                    "payload": j.get("payload") if isinstance(j.get("payload"), dict) else {},
                    "human_approval": bool(j.get("human_approval")),
                }]
        except Exception:
            m = _SINGLE_JSON.search(text)
            if m:
                try:
                    j = json.loads(m.group(0))
                    if j.get("uri"):
                        return [{"id": "llm-step", "uri": j["uri"], "payload": j.get("payload") or {}}]
                except Exception:
                    pass
    return []


def _step_ok(result: dict[str, Any], *, step: dict[str, Any] | None = None) -> bool:
    if not isinstance(result, dict):
        return False
    if not result:
        return False
    if result.get("ok") is False or result.get("error"):
        return False
    inner = result.get("result") or result.get("value") or result
    if isinstance(inner, dict) and inner.get("ok") is False:
        return False
    uri = str((step or {}).get("uri") or "")
    payload = (step or {}).get("payload") if isinstance((step or {}).get("payload"), dict) else {}
    if "ui/query/verify" in uri:
        return bool(result.get("present"))
    if "screen/query/inspect" in uri and payload.get("contains"):
        return bool(result.get("matched"))
    if "ui/query/locate" in uri and payload.get("query"):
        q = str(payload.get("query", "")).lower()
        for m in result.get("matches") or []:
            if q in str(m.get("text", "")).lower():
                return True
        return False
    return True


class LlmRuntimeLoop:
    """LLM-controlled ticket execution against URI runtime."""

    def __init__(
        self,
        *,
        node: str,
        node_run: NodeRunFn,
        llm_fn: LlmFn,
        ticket: str | None = None,
        ticket_dict: dict[str, Any] | None = None,
        project: str = "",
    ) -> None:
        self.node = node
        self.node_run = node_run
        self.llm_fn = llm_fn
        self.ticket = ticket
        self.ticket_dict = ticket_dict or ({"id": ticket} if ticket else {})
        self.project = project
        ticket_prompt = build_first_system_prompt(
            ticket=self.ticket_dict, node=node, include_decision_rules=True,
            node_run=self.node_run,
        )
        runtime_bundle = load_runtime_markdown_bundle()
        self._system = (
            f"{ticket_prompt}\n\n"
            f"---\n\n# PEŁNY RUNTIME urirun-llm-runtime (markdown bundle)\n\n{runtime_bundle}"
        )

    def observe(self, timeline: list[dict[str, Any]]) -> dict[str, Any]:
        tid = self.ticket or self.ticket_dict.get("id")
        obs: dict[str, Any] = {
            "ticket": tid,
            "node": self.node,
            "step_count": len(timeline),
            "gap": _gap_for_ticket(str(tid) if tid else None, self.project),
            "last_steps": timeline[-5:],
        }
        if tid:
            hist = format_turns_for_llm(str(tid), limit=6)
            if hist:
                obs["llm_history_excerpt"] = hist[:3000]
        need_kvm = not timeline or not (timeline[-1].get("ok") if timeline else True)
        if need_kvm:
            try:
                obs["kvm"] = _light_kvm_state(self.node_run, self.node)
            except Exception:
                pass
        if timeline and not timeline[-1].get("ok"):
            last = timeline[-1]
            obs["last_error"] = {
                "uri": last.get("uri"),
                "payload": last.get("payload"),
                "result": last.get("result"),
                "repair_hint": "choose corrective URI from runtime bundle; do not repeat failed payload",
            }
        return obs

    def _prompt(self, goal: str, observation: dict[str, Any]) -> str:
        repair = REPAIR_PROMPT if observation.get("last_error") else ""
        return (
            f"{LLM_LOOP_ROLE}\n\n{LLM_OUTPUT_CONTRACT}\n\n{repair}"
            f"**CEL TICKETU:**\n{goal}\n\n"
            f"**OBSERVATION (JSON):**\n{json.dumps(observation, ensure_ascii=False, default=str)[:12000]}\n\n"
            "Wybierz następne 1–3 kroki URI (lub done). Tylko URI z runtime bundle w system prompt."
        )

    def run(
        self,
        goal: str,
        *,
        max_steps: int | None = None,
        initial_plan: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        max_steps = max_steps or int(os.environ.get("URIRUN_LLM_MAX_STEPS", "40"))
        timeline: list[dict[str, Any]] = []
        pending = list(initial_plan or [])
        failures_in_row = 0

        if self.ticket:
            save_llm_turn(
                self.ticket, role="system", phase="llm-runtime-loop-start",
                content=goal[:2000], extra={"node": self.node},
            )

        for turn in range(max_steps):
            steps: list[dict[str, Any]] = []
            if pending:
                steps = pending[:3]
                pending = pending[3:]
            else:
                obs = self.observe(timeline)
                prompt = self._prompt(goal, obs)
                raw = self.llm_fn(prompt, self._system)
                if self.ticket:
                    save_llm_turn(
                        self.ticket, role="assistant", phase="llm-runtime-decide",
                        content=raw[:12000], extra={"turn": turn},
                    )
                steps = parse_llm_action(raw)
                if steps and steps[0].get("uri") == "done":
                    return {
                        "ok": True,
                        "status": "done",
                        "timeline": timeline,
                        "plan_used": "llm-runtime-loop",
                        "turns": turn,
                        "reason": steps[0].get("reason", ""),
                    }
            if not steps:
                failures_in_row += 1
                if failures_in_row >= 2:
                    break
                continue

            for step in steps:
                uri = str(step.get("uri") or "")
                if uri == "done":
                    return {"ok": True, "status": "done", "timeline": timeline, "plan_used": "llm-runtime-loop"}
                if step.get("human_approval") and not skip_human_approval_enabled():
                    return {
                        "ok": False,
                        "status": "waiting_human",
                        "timeline": timeline,
                        "plan_used": "llm-runtime-loop",
                        "pending_step": step,
                    }
                payload = step.get("payload") if isinstance(step.get("payload"), dict) else {}
                timeout = float(step.get("timeout_seconds") or 60)
                try:
                    result = self.node_run(self.node, uri, payload, timeout) or {}
                except Exception as exc:  # noqa: BLE001
                    result = {"ok": False, "error": str(exc)}
                entry = {
                    "turn": turn,
                    "id": step.get("id"),
                    "uri": uri,
                    "payload": payload,
                    "result": result,
                    "ok": _step_ok(result, step=step),
                }
                timeline.append(entry)
                if self.ticket:
                    save_llm_turn(
                        self.ticket, role="tool", phase="runtime-step",
                        content=json.dumps(entry, default=str)[:4000],
                        extra={"uri": uri, "ok": entry["ok"]},
                    )
                if entry["ok"]:
                    failures_in_row = 0
                else:
                    failures_in_row += 1
                    if self.ticket:
                        save_llm_turn(
                            self.ticket, role="tool", phase="runtime-error-repair",
                            content=json.dumps(entry, default=str)[:6000],
                            extra={"uri": uri, "needs_repair": True},
                        )
                    # skip remaining steps this turn — next turn LLM gets last_error
                    break

        verified = any(
            "verify" in str(t.get("uri", "")) and t.get("ok")
            for t in timeline
        )
        return {
            "ok": verified and failures_in_row < 2,
            "verified": verified,
            "status": "incomplete" if failures_in_row else "stopped",
            "timeline": timeline,
            "plan_used": "llm-runtime-loop",
            "failures_in_row": failures_in_row,
        }


def llm_runtime_control_enabled() -> bool:
    return str(os.environ.get("URIRUN_LLM_RUNTIME_CONTROL", "1")).strip().lower() not in (
        "0", "false", "no", "off",
    )


def skip_human_approval_enabled() -> bool:
    """Autonomiczne testy E2E — wykonaj kroki human_approval bez waiting_human."""
    return str(os.environ.get("URIRUN_LLM_SKIP_HUMAN_APPROVAL", "0")).strip().lower() in (
        "1", "true", "yes", "on",
    )
