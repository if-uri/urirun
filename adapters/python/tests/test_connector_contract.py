# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
"""Contract test suite for connectors installed in the development environment.

Uses ConnectorContractSuite to verify universal invariants:
  - bindings validate and compile
  - every route survives a dry-run dispatch with a valid reply shape
  - failed dispatch returns ok=False + error (reply contract)

One suite per installed connector.  Connectors that aren't importable in this
environment are automatically skipped."""
from __future__ import annotations

import pytest

from urirun.connectors.connector_contract import ConnectorContractSuite


# ── twin connector ────────────────────────────────────────────────────────────

try:
    import urirun_connector_twin as _twin  # noqa: PLC0415

    _TWIN_BINDINGS = _twin.bindings()
    _TWIN_SKIP = False
except ImportError:
    _TWIN_BINDINGS = {}
    _TWIN_SKIP = True


@pytest.mark.skipif(_TWIN_SKIP, reason="urirun-connector-twin not installed")
class TestTwinConnectorContract(ConnectorContractSuite):
    bindings_doc = _TWIN_BINDINGS
    # All twin:// routes can be dry-run dispatched — they're local-function handlers
    # that validate arguments without executing real system effects.
    dry_run_routes = None  # None = all routes

    def test_twin_bindings_have_expected_routes(self):
        """Core twin routes must be present after compile."""
        import urirun
        uris = {r["uri"] for r in urirun.list_routes(self.compile())}
        assert "twin://host/flow/command/rollback-ledger" in uris
        assert "twin://host/flow/goal/query/verify" in uris

    def test_dry_run_routes_return_valid_reply_shape(self):
        """Override: dry-run dispatch on local-function routes that need no args."""
        import urirun
        from urirun.runtime.dispatch_protocol import validate_reply
        routes = [r["uri"] for r in urirun.list_routes(self.compile())]
        for uri in routes:
            env = self.dispatch_dry(uri)
            problems = validate_reply(env)
            assert not problems, f"dry-run {uri}: reply contract violation: {problems}"
