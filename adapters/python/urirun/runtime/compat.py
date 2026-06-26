# Shim: compat moved to the urirun-runtime package (Phase 5 kernel extraction).
# urirun.runtime.compat and `from urirun.runtime import compat` resolve to the real module (every symbol,
# public + private); `python -m urirun.runtime.compat` delegates to the real module's CLI.
import sys as _sys
if __name__ == "__main__":
    import runpy as _rp
    _rp.run_module("urirun_runtime.compat", run_name="__main__")
else:
    import urirun_runtime.compat as _m
    _sys.modules[__name__] = _m
