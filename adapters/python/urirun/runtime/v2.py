# Shim: v2 moved to the urirun-runtime package (Phase 5 kernel extraction).
# urirun.runtime.v2 and `from urirun.runtime import v2` resolve to the real module (every symbol,
# public + private); `python -m urirun.runtime.v2` delegates to the real module's CLI.
import sys as _sys
if __name__ == "__main__":
    import runpy as _rp
    _rp.run_module("urirun_runtime.v2", run_name="__main__")
else:
    import urirun_runtime.v2 as _m
    _sys.modules[__name__] = _m
