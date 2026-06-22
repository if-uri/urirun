# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""One shared out-of-process runner for ``local-function`` handlers.

``python -m urirun.exec <module>:<export>`` imports the connector's handler,
reads a JSON payload from **stdin**, calls ``handler(**payload)`` (filtered to its
signature), and writes the result as JSON to **stdout**. It is the single,
in-core replacement for every connector's hand-written ``_exec.py``: a route that
wants process isolation (untrusted code, crash containment, a heavy import kept
out of the host) uses the ``local-function-subprocess`` adapter, which spawns this
runner — the connector still declares the route once as a ``@handler`` and ships
no argv shim of its own.
"""

from __future__ import annotations

import importlib
import inspect
import json
import sys


def _resolve(ref: str):
    module_name, _, export = ref.partition(":")
    if not module_name or not export:
        raise ValueError(f"expected '<module>:<export>', got {ref!r}")
    return getattr(importlib.import_module(module_name), export)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("usage: python -m urirun.exec <module>:<export>  (payload JSON on stdin)", file=sys.stderr)
        return 2
    fn = _resolve(argv[0])
    raw = sys.stdin.read()
    payload = json.loads(raw) if raw.strip() else {}
    if not isinstance(payload, dict):
        payload = {}
    try:                                  # drop keys the handler doesn't accept
        params = inspect.signature(fn).parameters
        if not any(p.kind == p.VAR_KEYWORD for p in params.values()):
            payload = {k: v for k, v in payload.items() if k in params}
    except (TypeError, ValueError):
        pass
    result = fn(**payload)
    sys.stdout.write(json.dumps(result))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
