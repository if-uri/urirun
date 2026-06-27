#!/usr/bin/env python3
"""Auto-heal the recurring extraction bug where the agent's bundled-fallback shape

    try:
        from urirun_connector_X import *          # prefer the separately-installed package
    except ImportError:
        from __future__ import annotations        # <- SyntaxError: must be the module's first stmt

traps ``from __future__ import annotations`` (or a module docstring) inside the ``except`` block.
One such SyntaxError cascades into many opaque pytest COLLECTION errors and aborts the whole run.

Idempotent + safe by construction:
  * only rewrites a file that FAILS to compile (clean files are untouched),
  * only moves a *misplaced* ``from __future__ import annotations`` to the module top,
  * recompiles and REVERTS the edit if that did not make the file compile.

Used two ways:
  * automatically by ``conftest.py`` at pytest start, before collection imports anything;
  * standalone for Makefile / CI / manual:  ``python scripts/heal_future_imports.py [adapters/python]``.
"""
from __future__ import annotations

import pathlib
import py_compile

# The co-located extracted packages that the agent's scanner extraction keeps regenerating.
PKGS = ("urirun", "urirun_runtime", "urirun_node", "urirun_flow",
        "urirun_contracts", "urirun_twin", "urirun_scanner")


def _heal_file(f: pathlib.Path) -> bool:
    """Fix one file if it is broken by a misplaced ``from __future__``. Return True iff it was fixed."""
    try:
        py_compile.compile(str(f), doraise=True)
        return False  # already valid — never touch a compiling file
    except py_compile.PyCompileError:
        pass
    original = f.read_text(encoding="utf-8")
    lines = original.split("\n")
    idx = next((i for i, line in enumerate(lines)
                if line.strip() == "from __future__ import annotations"), None)
    if idx is None or idx == 0:
        return False  # not the from-__future__ misplacement — leave it for a human
    healed = "from __future__ import annotations\n\n" + "\n".join(lines[:idx] + lines[idx + 1:])
    f.write_text(healed, encoding="utf-8")
    try:
        py_compile.compile(str(f), doraise=True)
        return True
    except py_compile.PyCompileError:
        f.write_text(original, encoding="utf-8")  # the move didn't fix it — revert, don't guess
        return False


def heal(root: pathlib.Path, pkgs: tuple[str, ...] = PKGS) -> list[str]:
    """Heal every package source under *root*. Returns the list of repo-relative files fixed."""
    healed: list[str] = []
    for pkg in pkgs:
        pkg_dir = root / pkg
        if not pkg_dir.is_dir():
            continue
        for f in pkg_dir.rglob("*.py"):
            if "build/lib" in str(f):
                continue
            if _heal_file(f):
                healed.append(str(f.relative_to(root)))
    return healed


def main(argv: list[str] | None = None) -> int:
    import sys
    args = argv if argv is not None else sys.argv[1:]
    root = pathlib.Path(args[0]).resolve() if args else pathlib.Path(__file__).resolve().parent.parent
    healed = heal(root)
    if healed:
        print(f"[heal-future-imports] fixed {len(healed)} misplaced __future__ import(s):")
        for rel in healed:
            print(f"  + {rel}")
    else:
        print("[heal-future-imports] nothing to fix — all package sources compile")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
