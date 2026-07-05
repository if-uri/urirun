# Author: Tom Sapletta · Part of the ifURI solution.
"""GUARD: urirun_scanner shims must keep their BUNDLED FALLBACK bodies.

History: automated refactors repeatedly flattened these files to 9-line thin aliases
(`sys.modules[__name__] = load_connector_module(...)`), which import-errors on a fresh
`pip install urirun` (urirun-connector-scanner may not be installed) — that broke the release
smoke test and blocked every publish after 0.4.190. The contract is: PREFER the separately
installed connector package, FALL BACK to the bundled implementation inline in the same file.

If this test fails, do NOT delete it — restore the try/except-ImportError bundled bodies
(see git 551a8ed) instead of the thin-alias form.
"""
from __future__ import annotations

from pathlib import Path

import pytest

_PKG = Path(__file__).resolve().parents[1] / "urirun_scanner"

# module -> a sentinel symbol its bundled body must define
_SENTINELS = {
    "artifacts_admin": "public_chat_attachment",
    "document_sync": "sync_documents_to_node",
    "document_metadata": None,
    "scanner_bridge": None,
    "scanner_net": None,
    "scanner_service": None,
}


@pytest.mark.parametrize("name", sorted(_SENTINELS))
def test_shim_keeps_bundled_fallback_body(name: str) -> None:
    src = (_PKG / f"{name}.py").read_text(encoding="utf-8")
    assert "except ImportError" in src, (
        f"urirun_scanner/{name}.py lost its bundled fallback (flattened to a thin alias). "
        "A fresh `pip install urirun` would break. Restore the try/except bundled body "
        "(git 551a8ed) — do not silence this test."
    )
    # a thin alias is ~9 lines; a real bundled body is hundreds
    assert len(src.splitlines()) > 60, f"urirun_scanner/{name}.py suspiciously small — bundled body missing?"


def test_bundled_fallback_actually_imports_without_connector(monkeypatch) -> None:
    """Import document_sync with urirun_connector_scanner BLOCKED — the bundled body must serve."""
    import importlib
    import sys

    monkeypatch.setitem(sys.modules, "urirun_connector_scanner", None)  # forces ImportError path
    for mod in [m for m in list(sys.modules) if m.startswith("urirun_scanner")]:
        monkeypatch.delitem(sys.modules, mod, raising=False)
    ds = importlib.import_module("urirun_scanner.document_sync")
    assert hasattr(ds, "sync_documents_to_node")
