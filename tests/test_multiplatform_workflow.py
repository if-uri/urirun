from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "trigger-multiplatform-smoke.yml"


def test_multiplatform_trigger_workflow_contract():
    assert WORKFLOW.exists()
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_run:" in text
    assert "- ci" in text
    assert "workflow_dispatch:" in text
    assert "workflow_run.conclusion == 'success'" in text
    assert "repository_dispatch" in text
    assert "if-uri/urirun-multiplatform-test" in text
    assert "URIRUN_MULTIPLATFORM_TEST_TOKEN" in text
    assert "event_type=urirun-main-ci" in text
    assert 'client_payload[urirun_ref]="$URIRUN_REF"' in text
    assert 'client_payload[sha]="$URIRUN_REF"' in text
    assert "client_payload[get_urirun_site_mode]=production-site" in text
    assert "client_payload[allow_remote_install]=false" in text
