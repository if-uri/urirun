# Shim: agent moved to the urirun-runtime package (Phase 5 kernel extraction).
# urirun.runtime.agent and `from urirun.runtime import agent` resolve to the real module (every symbol,
# public + private); `python -m urirun.runtime.agent` delegates to the real module's CLI.
import sys as _sys
if __name__ == "__main__":
    import runpy as _rp
    _rp.run_module("urirun_runtime.agent", run_name="__main__")
else:
    import urirun_runtime.agent as _m
    _sys.modules[__name__] = _m
