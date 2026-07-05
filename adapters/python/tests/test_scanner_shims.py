from __future__ import annotations

"""urirun_scanner shim contract — TWO requirements that must BOTH hold:

1. PREFERENCE: when urirun-connector-scanner IS installed, the shim serves the connector's
   objects (no stale duplicates) — asserted below via object identity.
2. FALLBACK: when it is NOT installed (every fresh `pip install urirun`), the bundled body
   inline in the same file serves — asserted in test_scanner_bundled_fallback.py and by the
   release smoke test.

An earlier version of this file demanded the THIN-ALIAS form (≤10 lines, no
`except ImportError`) — the exact opposite of requirement 2. Automated refactors kept
"fixing" the files back and forth between the two shapes, and every wheel built in the
thin-alias shape broke fresh installs and blocked publishing (nothing shipped after 0.4.190
until this was reconciled). Do NOT reintroduce a line-count/no-fallback assertion here.
"""

import importlib
from pathlib import Path

import pytest

_ADAPTER_ROOT = Path(__file__).resolve().parents[1] / "urirun_scanner"
_SHIM_MODULES = [
    "artifacts_admin",
    "document_metadata",
    "document_sync",
    "scanner_bridge",
    "scanner_net",
    "scanner_service",
]

# module -> a public callable both shapes must expose
_PROBES = {
    "artifacts_admin": "public_chat_attachment",
    "document_sync": "sync_documents_to_node",
}


def test_urirun_scanner_prefers_installed_connector_objects():
    """With the connector installed (dev/monorepo), the shim must serve ITS objects —
    same function objects, not stale bundled copies."""
    pytest.importorskip("urirun_connector_scanner")
    for name, probe in _PROBES.items():
        shim = importlib.import_module(f"urirun_scanner.{name}")
        moved = importlib.import_module(f"urirun_connector_scanner.{name}")
        assert getattr(shim, probe) is getattr(moved, probe), (
            f"urirun_scanner.{name}.{probe} is not the connector's object — "
            "the shim must prefer the installed connector package"
        )


def test_urirun_scanner_shims_import_cleanly():
    for name in _SHIM_MODULES:
        mod = importlib.import_module(f"urirun_scanner.{name}")
        assert mod is not None
