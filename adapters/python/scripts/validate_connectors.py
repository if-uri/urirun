#!/usr/bin/env python3
# Author: Tom Sapletta · Part of the ifURI solution.
"""CI validator: every served route MUST follow URI_COMMAND_STANDARD (resource/class/verb,
class in {query, command, session, event}) and every error the canonical ERROR_CODES catalog.

Iterates the installed ``urirun.bindings`` entry points (the authoritative route source),
runs ``manifest_routes`` (which raises on a bad class), and reports per-connector violations.
Exit code is non-zero when any connector violates the naming standard — wire into CI.
"""
from __future__ import annotations

import sys
from importlib.metadata import entry_points

from urirun_connectors_toolkit.connector_sdk import manifest_routes

# Routes that predate URI_COMMAND_STANDARD. Renaming a served URI is a BREAKING change (callers,
# dashboards, flows), so these are grandfathered: reported as MIGRATE debt, but do NOT fail CI.
# A NEW violation (not on this list) fails the build. Remove an entry once its owner migrates it.
#   human://{node}/grant/satisfy      -> grant/command/satisfy
#   invoice://host/ksef/folder/register -> ksef/folder/command/register (resource ksef/folder)
#   ksef://demo/auth/challenge        -> auth/command/challenge
#   twin://host/monitor/event         -> monitor/event/stream (missing verb; 'event' IS a class)
GRANDFATHERED = {"human", "invoice", "ksef", "twin"}


def main() -> int:
    eps = list(entry_points(group="urirun.bindings"))
    new_violations: list[str] = []
    migrate: list[str] = []
    ok = 0
    for ep in sorted(eps, key=lambda e: e.name):
        try:
            routes = manifest_routes(ep.load()())
        except ValueError as exc:            # a bad class — the standard violation we hunt
            (migrate if ep.name in GRANDFATHERED else new_violations).append(f"{ep.name}: {exc}")
            continue
        except Exception as exc:             # noqa: BLE001 - import/dep failure, not a violation
            print(f"  ~ {ep.name}: skipped ({type(exc).__name__})")
            continue
        ok += 1
        n_q = sum(1 for r in routes if r["class"] == "query")
        n_c = sum(1 for r in routes if r["class"] == "command")
        print(f"  ✓ {ep.name}: {len(routes)} routes ({n_q} query, {n_c} command)")
    print(f"\n{ok} connectors valid, {len(migrate)} grandfathered (MIGRATE), "
          f"{len(new_violations)} NEW violations")
    for m in migrate:
        print(f"  ⚠ MIGRATE {m}")
    for v in new_violations:
        print(f"  ✗ {v}")
    return 1 if new_violations else 0        # only NEW violations fail CI


if __name__ == "__main__":
    sys.exit(main())
