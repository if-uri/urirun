# Thin alias — the implementation lives in urirun-connector-scanner (loaded via _shim,
# which also handles the monorepo-checkout path when the package is not installed).
from __future__ import annotations

import sys

from urirun_scanner._shim import load_connector_module

sys.modules[__name__] = load_connector_module("artifacts_admin")
