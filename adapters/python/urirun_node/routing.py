# Author: Tom Sapletta - https://tom.sapletta.com
# Part of the ifURI solution.
"""Back-compat shim: routing moved to urirun-connector-router.

New code should import from ``urirun_connector_router.routing``. This module
keeps the historical ``urirun_node.routing`` and ``urirun.node.routing`` import
paths working while the routing kernel has a single source.
"""

try:
    from urirun_connector_router import routing as _routing
except ModuleNotFoundError as exc:
    if exc.name != "urirun_connector_router":
        raise
    raise ModuleNotFoundError(
        "urirun's routing kernel moved to the 'urirun-connector-router' package "
        "(a declared dependency of urirun). Install it: pip install urirun-connector-router"
    ) from exc

for _name, _value in vars(_routing).items():
    if not _name.startswith("_"):
        globals()[_name] = _value

__all__ = [name for name in globals() if not name.startswith("_")]
