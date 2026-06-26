# Shim: _scan moved to the urirun-runtime package (Phase 5 kernel extraction).
# urirun.runtime._scan and `from urirun.runtime import _scan` resolve to the real module (every symbol,
# public + private); `python -m urirun.runtime._scan` delegates to the real module's CLI.
import sys as _sys
if __name__ == "__main__":
    import runpy as _rp
    _rp.run_module("urirun_runtime._scan", run_name="__main__")
else:
    import urirun_runtime._scan as _m
    _sys.modules[__name__] = _m
