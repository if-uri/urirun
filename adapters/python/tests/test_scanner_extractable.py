# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Boundary guard for the scanner / documents package extraction (see scripts/extraction_audit.py).
# The audit proved the package lifts cleanly (0 sideways imports into staying host siblings,
# 0 cycles). This test LOCKS that: it fails the moment a scanner module grows a hard import into
# a host sibling that stays behind (e.g. host_dashboard, chat_orchestrator) — which would re-couple
# the boundary and block the lift. Same intent as the cc_gate / test_kernel_adoption guards: keep a
# completed structural property durable against churn (these files are heavily co-edited).
#
# Auto-skips once the modules are actually extracted out of core, so it never breaks the move.
import importlib.util
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]          # …/urirun
_IMPORT_ROOT = Path(__file__).resolve().parents[1]   # …/urirun/adapters/python (contains `urirun`)
_AUDIT_PATH = _REPO / "scripts" / "extraction_audit.py"


def _load_audit():
    spec = importlib.util.spec_from_file_location("extraction_audit", _AUDIT_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod        # @dataclass needs the module registered during exec
    spec.loader.exec_module(mod)
    return mod


def test_audit_tool_self_test_passes():
    """The analyzer must be sound, or its boundary verdict means nothing."""
    assert _load_audit()._selftest() is True


def test_scanner_package_boundary_is_green():
    """The scanner package has zero OUTWARD (sideways into staying siblings) and zero CYCLE edges."""
    ea = _load_audit()
    spec = ea.PRESETS["A"]
    present = set(spec["package"]) & set(ea.discover_modules(_IMPORT_ROOT))
    if not present:
        pytest.skip("scanner package already extracted out of core — boundary guard moot")
    rep = ea.audit(_IMPORT_ROOT, spec)
    assert not rep.outward, (
        "scanner package re-coupled to staying host siblings: "
        + ", ".join(f"{e.src}→{e.target} ({e.symbol} L{e.line})" for e in rep.outward))
    assert not rep.cycles, f"import cycle(s) between package and staying modules: {sorted(rep.cycles)}"


def test_scanner_inward_surface_is_recorded():
    """Sanity: the shim re-export surface is non-empty (core still consumes the package in place)."""
    ea = _load_audit()
    spec = ea.PRESETS["A"]
    if not (set(spec["package"]) & set(ea.discover_modules(_IMPORT_ROOT))):
        pytest.skip("scanner package already extracted out of core")
    rep = ea.audit(_IMPORT_ROOT, spec)
    assert rep.inward, "expected INWARD edges (the shim re-export surface) while modules live in core"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
