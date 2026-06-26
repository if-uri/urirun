# Shim: v2_service moved to the urirun-runtime package (Phase 5 kernel extraction).
# urirun.runtime.v2_service and `from urirun.runtime import v2_service` resolve to the real module (every symbol,
# public + private); `python -m urirun.runtime.v2_service` delegates to the real module's CLI.
import sys as _sys
if __name__ == "__main__":
    import runpy as _rp
    _rp.run_module("urirun_runtime.v2_service", run_name="__main__")
else:
    import urirun_runtime.v2_service as _m
    _sys.modules[__name__] = _m
