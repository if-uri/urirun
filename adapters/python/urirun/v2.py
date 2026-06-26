"""Back-compat shim — moved to urirun.runtime.v2. Import from there in new code."""
import sys as _sys
# Bootstrap: importing mesh registers node/host CLI commands into the runtime CLI bridge.
# The runtime layer cannot import from the node layer; the node layer pushes down via register_cli_command().
from urirun.node import mesh as _mesh  # noqa: F401 — side-effectful bridge registration
from urirun.runtime import v2 as _moved

if __name__ == "__main__":
    _sys.exit(_moved.main() if hasattr(_moved, "main") else 0)
else:
    _sys.modules[__name__] = _moved
