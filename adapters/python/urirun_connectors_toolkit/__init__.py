"""urirun connector authoring toolkit."""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_MONOREPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", "..", ".."))
_LOCAL_CONTRACT = os.path.join(_MONOREPO_ROOT, "urirun-contract")
if os.path.isdir(os.path.join(_LOCAL_CONTRACT, "urirun_contract")):
    sys.path.insert(0, _LOCAL_CONTRACT)
