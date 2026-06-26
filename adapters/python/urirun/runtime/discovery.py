# Shim: discovery moved to the urirun-runtime package (Phase 5 kernel extraction).
# urirun.runtime.discovery and `from urirun.runtime import discovery` resolve to the real module (every symbol,
# public + private); `python -m urirun.runtime.discovery` delegates to the real module's CLI.
import sys as _sys
if __name__ == "__main__":
    import runpy as _rp
    _rp.run_module("urirun_runtime.discovery", run_name="__main__")
else:
    import urirun_runtime.discovery as _m
    _sys.modules[__name__] = _m
