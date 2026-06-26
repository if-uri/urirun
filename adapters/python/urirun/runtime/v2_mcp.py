# Shim: v2_mcp moved to the urirun-runtime package (Phase 5 kernel extraction).
# urirun.runtime.v2_mcp and `from urirun.runtime import v2_mcp` resolve to the real module (every symbol,
# public + private); `python -m urirun.runtime.v2_mcp` delegates to the real module's CLI.
import sys as _sys
if __name__ == "__main__":
    import runpy as _rp
    _rp.run_module("urirun_runtime.v2_mcp", run_name="__main__")
else:
    import urirun_runtime.v2_mcp as _m
    _sys.modules[__name__] = _m
