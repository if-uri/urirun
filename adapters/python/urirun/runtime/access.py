# Shim: autonomous access contracts are owned by the extracted runtime package.
import sys as _sys

if __name__ == "__main__":
    import runpy as _rp

    _rp.run_module("urirun_runtime.access", run_name="__main__")
else:
    import urirun_runtime.access as _m

    _sys.modules[__name__] = _m
