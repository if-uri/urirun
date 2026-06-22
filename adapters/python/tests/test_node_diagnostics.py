# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
"""Node diagnostics: /health reports the urirun version, and a concrete URI resolves
against a ``{param}`` template binding (the failure seen on an old remote node, where
`kvm://laptop/display/query/info` returned `Route not found: kvm.display.query`)."""
from __future__ import annotations

import json
import threading
import time
import urllib.request

from urirun import v2
from urirun.node import mesh
from urirun.runtime import _runtime as runtime


def _template_registry():
    return v2.compile_registry({
        "version": "urirun.bindings.v2",
        "bindings": {
            "kvm://{host}/display/query/info": {
                "kind": "query", "adapter": "argv-template",
                "argv": ["python3", "-c", "import json;print(json.dumps({'display': ':0'}))"],
                "inputSchema": {"type": "object", "additionalProperties": True, "properties": {}},
            },
        },
    })


def test_concrete_uri_resolves_against_host_template():
    # `kvm://laptop/...` must match the registered `kvm://{host}/...` and run — not fall
    # through to "Route not found" (it gets to the policy gate, proving resolution).
    reg = _template_registry()
    policy = runtime.build_policy(None, ["kvm://**"], None)
    env = v2.run("kvm://laptop/display/query/info", reg, {}, mode="execute", policy=policy)
    assert env["ok"] is True, env.get("error")
    assert json.loads(env["result"]["stdout"]) == {"display": ":0"}


def _free_port():
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def test_health_reports_version():
    port = _free_port()
    srv = mesh.serve_node("diag", _template_registry(), "127.0.0.1", port, execute=False)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        for _ in range(40):
            try:
                health = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1))
                break
            except Exception:
                time.sleep(0.05)
        else:
            raise AssertionError("node /health never came up")
        assert health["version"] == v2._package_version()
        assert "." in health["version"]            # looks like a real version string
    finally:
        srv.shutdown()
