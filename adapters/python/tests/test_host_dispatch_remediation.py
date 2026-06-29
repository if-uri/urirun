from __future__ import annotations

from urirun.host.dispatch import make_local_dispatch_uri
from urirun.host.node_dispatch import classify_error
from urirun.runtime import v2_service


def _legacy_core_error() -> dict:
    return {
        "type": "subprocess-crash",
        "message": "ModuleNotFoundError: No module named 'core'",
        "stderr": "ModuleNotFoundError: No module named 'core'",
    }


def test_legacy_flat_core_subprocess_error_is_version_skew():
    rem = classify_error(_legacy_core_error(), node="lenovo", uri="kvm://host/screen/query/capture")

    assert rem.cls.value == "version-skew"
    assert rem.command == "pip install -U urirun urirun-connector-kvm"
    assert "runtime/connector deploy" in rem.human_action


def test_remote_dispatch_attaches_remediation_for_node_subprocess_crash(monkeypatch):
    def fake_make_dispatch(_registry, _mode, fallback=None):
        def _dispatch(_uri, _payload=None):
            return {
                "ok": False,
                "status": 400,
                "response": {
                    "service": "lenovo",
                    "error": _legacy_core_error(),
                },
            }
        return _dispatch

    monkeypatch.setattr(v2_service, "make_dispatch", fake_make_dispatch)
    dispatch = make_local_dispatch_uri({}, "execute")

    result = dispatch("kvm://host/screen/query/capture", {"monitor": -1})

    assert result["remediation"]["class"] == "version-skew"
    assert result["remediation"]["node"] == "lenovo"
    assert result["remediation"]["command"] == "pip install -U urirun urirun-connector-kvm"
