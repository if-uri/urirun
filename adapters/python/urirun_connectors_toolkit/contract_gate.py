"""Compatibility facade for the contract gate.

The implementation lives in the ``urirun_contract`` package. This module remains so existing imports
from ``urirun_connectors_toolkit.contract_gate`` keep working without creating a second kernel copy.

Re-export from the PACKAGE (not ``.gate``): the kernel spans gate/jsonschema/lint/reversible, so
``from urirun_contract.gate import *`` would silently drop ``to_json_schema``, ``lint_handler_signatures``
and ``callspecs_from_contracts``. The package ``__all__`` is the one true public surface.
"""
from urirun_contract import *  # noqa: F401,F403
