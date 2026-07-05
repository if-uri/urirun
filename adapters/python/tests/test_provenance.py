# Author: Tom Sapletta · Part of the ifURI solution.
"""Every local-function dispatch stamps _meta provenance: which module ran, its version,
file, when it was updated, git sha/source, and on which node — so a stale node is
self-evident. Opt out with URIRUN_NO_PROVENANCE=1."""
import os

from urirun_runtime import _runtime


def test_provenance_of_a_real_module():
    _runtime._PROV_CACHE.clear()
    p = _runtime._provenance("urirun_runtime._runtime")
    assert p["module"] == "urirun_runtime._runtime"
    assert "file" in p and "updatedAt" in p and p["ranOn"]
    # this repo is a git checkout → source + sha present
    assert p.get("source", "").startswith("git+") and "sha" in p


def test_run_local_function_stamps_meta():
    def handler(target, args, payload, descriptor):
        return {"ok": True, "x": 1}
    handler.__module__ = "urirun_runtime._runtime"
    ctx = {"routeEntry": {"ref": handler}, "target": "host", "args": {},
           "payload": {}, "descriptor": {}}
    out = _runtime.run_local_function(ctx, {})
    assert out["type"] == "function" and out["value"] == {"ok": True, "x": 1}
    assert out["_meta"]["module"] == "urirun_runtime._runtime" and out["_meta"]["ranOn"]


def test_provenance_opt_out(monkeypatch):
    monkeypatch.setenv("URIRUN_NO_PROVENANCE", "1")
    _runtime._PROV_CACHE.clear()
    assert _runtime._provenance("urirun_runtime._runtime") is None
