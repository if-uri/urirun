"""llm_runtime_loop — LLM steruje ticketem z pełnym URI runtime."""
from __future__ import annotations

import json

import pytest

from urirun_runtime.llm_runtime_loop import (
    LlmRuntimeLoop,
    llm_runtime_control_enabled,
    parse_llm_action,
)


def test_parse_single_json_step():
    raw = '{"uri": "kvm://host/doctor/query/report", "payload": {}, "reason": "diag"}'
    steps = parse_llm_action(raw)
    assert len(steps) == 1
    assert steps[0]["uri"] == "kvm://host/doctor/query/report"


def test_parse_urirun_processes_block():
    raw = '''```urirun:processes
[{"id":"a","name":"A","actor":"script","uri":"kvm://host/env/query/profile","payload":{},"depends_on":[]}]
```'''
    steps = parse_llm_action(raw)
    assert len(steps) == 1
    assert "env" in steps[0]["uri"]


def test_parse_done():
    steps = parse_llm_action('{"uri":"done","reason":"sent"}')
    assert steps[0]["uri"] == "done"


def test_llm_loop_executes_mock_steps():
    calls: list[str] = []

    def node_run(node, uri, payload, timeout):
        calls.append(uri)
        return {"ok": True, "uri": uri}

    responses = [
        '{"uri":"kvm://host/doctor/query/report","payload":{}}',
        '{"uri":"done","reason":"ok"}',
    ]
    idx = {"i": 0}

    def llm_fn(prompt, system):
        r = responses[min(idx["i"], len(responses) - 1)]
        idx["i"] += 1
        return r

    loop = LlmRuntimeLoop(
        node="lenovo",
        node_run=node_run,
        llm_fn=llm_fn,
        ticket="T-LOOP",
        ticket_dict={"id": "T-LOOP", "name": "test"},
    )
    result = loop.run("test goal", max_steps=5)
    assert result.get("status") == "done"
    assert "kvm://host/doctor/query/report" in calls


def test_llm_loop_initial_plan_then_llm():
    calls: list[str] = []

    def node_run(node, uri, payload, timeout):
        calls.append(uri)
        return {"ok": True}

    def llm_fn(prompt, system):
        return '{"uri":"done","reason":"finished"}'

    loop = LlmRuntimeLoop(node="host", node_run=node_run, llm_fn=llm_fn, ticket=None)
    plan = [{"id": "x", "uri": "kvm://host/window/query/list", "payload": {}}]
    result = loop.run("g", max_steps=3, initial_plan=plan)
    assert calls[0] == "kvm://host/window/query/list"
    assert result.get("status") == "done"


def test_llm_runtime_control_default_on():
    assert llm_runtime_control_enabled() is True
