"""process_standard — standard urirun:processes dla ticketów LLM."""
from __future__ import annotations

import json

import pytest

from urirun_runtime import ticket_llm_context as tlc
from urirun_runtime.process_standard import (
    LLM_OUTPUT_CONTRACT,
    extract_plan_from_llm,
    parse_processes_block,
    validate_processes,
    from_dict,
)


SAMPLE_BLOCK = '''
Plan:

```urirun:processes
[
  {
    "id": "diag",
    "name": "Doctor",
    "actor": "script",
    "uri": "kvm://host/doctor/query/report",
    "payload": {},
    "depends_on": []
  }
]
```
'''


def test_parse_processes_block():
    procs = parse_processes_block(SAMPLE_BLOCK)
    assert len(procs) == 1
    assert procs[0].uri == "kvm://host/doctor/query/report"


def test_extract_prefers_urirun_processes():
    plan, fmt = extract_plan_from_llm(SAMPLE_BLOCK)
    assert fmt == "urirun:processes"
    assert plan[0]["uri"] == "kvm://host/doctor/query/report"


def test_extract_legacy_decision_loop():
    legacy = json.dumps({
        "decision_loop": {
            "flow": {
                "steps": [{"id": "a", "uri": "kvm://host/env/query/profile", "payload": {}}],
            },
        },
    })
    plan, fmt = extract_plan_from_llm(legacy)
    assert fmt == "decision_loop"
    assert len(plan) == 1


def test_first_prompt_includes_standard_and_examples(monkeypatch, tmp_path):
    monkeypatch.setenv("URIRUN_KORU_PROJECT", str(tmp_path))
    tpl = tmp_path / "compose/uri-runtime/environment.uri-topology.yaml"
    tpl.parent.mkdir(parents=True)
    tpl.write_text("uri_runtime_environment:\n  addressing_rules:\n    - test\n", encoding="utf-8")
    prompt = tlc.build_first_system_prompt(ticket={"id": "T-1", "name": "test"})
    assert "urirun:processes" in prompt
    assert "STANDARD WYJŚCIA" in prompt or "urirun-llm-runtime" in prompt


def test_validate_processes_unknown_dep():
    procs = [from_dict({"id": "b", "name": "B", "actor": "script", "uri": "kvm://host/env/query/profile", "depends_on": ["a"]})]
    errs = validate_processes(procs)
    assert any("depends_on" in e for e in errs)


def test_llm_output_contract_mentions_repo():
    assert "urirun-llm-runtime" in LLM_OUTPUT_CONTRACT or "process_contract" in LLM_OUTPUT_CONTRACT
