#!/usr/bin/env python3
# Author: Tom Sapletta · Part of the ifURI solution.
"""Regenerate ERROR_CODES.md from the canonical taxonomy (urirun_runtime.errors)."""
from pathlib import Path

from urirun_runtime.errors import CATEGORIES, DEFAULT_CATEGORY

HEAD = """# Error Codes — the ONE canonical list

> Generated from `urirun/adapters/python/urirun_runtime/errors.py` (the single source of truth).
> Regenerate: `python urirun/docs/gen_error_codes.py`. Do not hand-edit this file.

Every failure envelope carries `error.category` (a **gRPC canonical status code**), `error.status`
(**HTTP status, RFC 9110**), `error.severity` (**syslog severity, RFC 5424**) and a stable
`error.code` (`E-<hash>` of the message). Connectors NEVER invent categories — they call
`urirun.fail(msg, ...)` and the runtime maps the exception/errno/message to a category below.

| category (gRPC) | HTTP (RFC 9110) | severity (RFC 5424) | meaning |
|---|---|---|---|
"""
TAIL = """
Default when unmapped: `{default}` (HTTP 500).

## Mapping sources (also in errors.py)
- **POSIX errno → category**: `ENOENT`→`NOT_FOUND`, `EACCES`→`PERMISSION_DENIED`, …
- **Python exception type → category**: `FileNotFoundError`→`NOT_FOUND`, `TimeoutError`→`DEADLINE_EXCEEDED`, …
- **Message substrings → category**: last-resort heuristic.

## Discover at runtime
`error://local/<code>/query/info` (the `error.uri` in every failure envelope) resolves the help URL.
"""


def main() -> None:
    rows = [f"| `{c}` | {s} | {sev} | {d} |" for c, (s, sev, d) in CATEGORIES.items()]
    out = HEAD + "\n".join(rows) + "\n" + TAIL.format(default=DEFAULT_CATEGORY)
    Path(__file__).with_name("ERROR_CODES.md").write_text(out, encoding="utf-8")
    print(f"ERROR_CODES.md regenerated: {len(CATEGORIES)} categories")


if __name__ == "__main__":
    main()
