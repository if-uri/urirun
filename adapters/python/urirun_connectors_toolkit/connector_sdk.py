"""Authoring helpers for connector packages.

Every external connector repeated the same scaffolding: load a bundled
``connector.manifest.json``, print JSON, and wire ``manifest`` / ``bindings``
subcommands around the package's own routes. These helpers move that boilerplate
into the runtime so a connector's ``cli.py`` only declares its domain commands.

Example ``cli.py``::

    import urirun
    from .core import connector_manifest, urirun_bindings, now

    def register(sub):
        p = sub.add_parser("now")
        p.add_argument("--timezone", default="UTC")

    def dispatch(args):
        if args.command == "now":
            result = now(timezone=args.timezone)
            urirun.connector_emit(result)
            return 0 if result.get("ok") else 2
        return 1

    def main(argv=None):
        return urirun.connector_cli(
            "urirun-time-tools",
            manifest=connector_manifest,
            bindings=urirun_bindings,
            register=register,
            dispatch=dispatch,
            argv=argv,
        )
"""

from __future__ import annotations

import argparse
import json
from importlib import resources
from typing import Any, Callable


def load_manifest(package: str, name: str = "connector.manifest.json") -> dict[str, Any]:
    """Load a JSON manifest bundled as package data (replaces per-connector loaders)."""
    text = resources.files(package).joinpath(name).read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"{name} must contain a JSON object")
    return data


# Command classes per URI_COMMAND_STANDARD.md §2, with the error categories each class can
# plausibly return (drawn from the ONE catalog in ERROR_CODES.md — never ad-hoc strings).
_CLASS_ERRORS: dict[str, list[str]] = {
    "query":   ["INVALID_ARGUMENT", "NOT_FOUND", "UNAVAILABLE"],
    "command": ["INVALID_ARGUMENT", "FAILED_PRECONDITION", "PERMISSION_DENIED", "UNAVAILABLE"],
    "session": ["INVALID_ARGUMENT", "FAILED_PRECONDITION", "UNAVAILABLE", "DEADLINE_EXCEEDED"],
    "event":   ["INVALID_ARGUMENT", "UNAVAILABLE"],
}
_KNOWN_CLASSES = tuple(_CLASS_ERRORS)


def manifest_routes(bindings: dict) -> list[dict[str, Any]]:
    """Generate the per-URI capability list for a connector manifest from its bindings —
    applies URI_COMMAND_STANDARD.md so every route is self-describing (class/verb parsed from
    the URI, summary from the handler ``meta.label``, ``mutates`` and plausible ``errors``
    derived from the class). Generated, so it can never drift from the served routes.

    Raises ValueError on a route whose class is not one of {query, command, session, event} —
    a lint that keeps the naming standard enforced.
    """
    routes: list[dict[str, Any]] = []
    for uri, binding in sorted((bindings.get("bindings") or {}).items()):
        parts = uri.split("://", 1)[-1].split("/")
        cls = parts[-2] if len(parts) >= 2 else ""
        verb = parts[-1] if parts else ""
        if cls not in _KNOWN_CLASSES:
            raise ValueError(
                f"route {uri!r} has class {cls!r}; must be one of {_KNOWN_CLASSES} "
                "(see URI_COMMAND_STANDARD.md §2)")
        summary = ((binding.get("meta") or {}).get("label")
                   or (binding.get("meta") or {}).get("summary") or "")
        routes.append({
            "uri": uri, "class": cls, "verb": verb, "summary": summary,
            "mutates": cls in ("command", "session"),
            "errors": _CLASS_ERRORS[cls],
        })
    return routes


def emit(payload: Any) -> None:
    """Print a payload as the stable, sorted JSON connectors emit on stdout."""
    print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))


def connector_cli(
    prog: str,
    *,
    manifest: Callable[[], dict],
    bindings: Callable[[], dict],
    register: Callable[[argparse._SubParsersAction], None] | None = None,
    dispatch: Callable[[argparse.Namespace], int] | None = None,
    argv: list[str] | None = None,
) -> int:
    """Build the standard connector CLI: domain commands + ``manifest``/``bindings``.

    ``register`` adds the connector's own subparsers; ``dispatch`` handles them.
    ``manifest`` and ``bindings`` are wired automatically.
    """
    parser = argparse.ArgumentParser(prog=prog)
    sub = parser.add_subparsers(dest="command", required=True)
    if register is not None:
        register(sub)
    sub.add_parser("manifest", help="Emit the connect.ifuri.com connector manifest")
    sub.add_parser("bindings", help="Emit urirun v2 bindings")

    args = parser.parse_args(argv)
    if args.command == "manifest":
        emit(manifest())
        return 0
    if args.command == "bindings":
        emit(bindings())
        return 0
    if dispatch is not None:
        return dispatch(args)
    return 1
