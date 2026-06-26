# Shim: adopt_pack moved to the urirun-runtime package (Phase 5 kernel extraction).
# urirun.runtime.adopt_pack and `from urirun.runtime import adopt_pack` resolve to the real module (every symbol,
# public + private); `python -m urirun.runtime.adopt_pack` delegates to the real module's CLI.
import sys as _sys
if __name__ == "__main__":
    import runpy as _rp
    _rp.run_module("urirun_runtime.adopt_pack", run_name="__main__")
else:
    import urirun_runtime.adopt_pack as _m
    _sys.modules[__name__] = _m
