# Shim: daemon moved to the urirun-runtime package (Phase 5 kernel extraction).
# urirun.runtime.daemon and `from urirun.runtime import daemon` resolve to the real module (every symbol,
# public + private); `python -m urirun.runtime.daemon` delegates to the real module's CLI.
import sys as _sys
if __name__ == "__main__":
    import runpy as _rp
    _rp.run_module("urirun_runtime.daemon", run_name="__main__")
else:
    import urirun_runtime.daemon as _m
    _sys.modules[__name__] = _m
