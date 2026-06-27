# Guards a recurring extraction bug: the agent's bundled-fallback shape
#   try: from urirun_connector_X import *
#   except ImportError: from __future__ import annotations  # <- SyntaxError, must be first stmt
# traps `from __future__` (or the docstring) inside the except block. That one SyntaxError cascades
# into many confusing pytest COLLECTION errors. Compiling is import-free, so this catches EVERY broken
# source file — including ones no other test imports — as a single clear failure naming each file.
# Run standalone (`pytest tests/test_source_compiles.py`) to diagnose a collection-interrupted suite.
import pathlib
import py_compile
import unittest

_ROOT = pathlib.Path(__file__).resolve().parent.parent  # adapters/python
_PKGS = ["urirun", "urirun_runtime", "urirun_node", "urirun_flow",
         "urirun_contracts", "urirun_twin", "urirun_scanner"]


class SourceCompilesTests(unittest.TestCase):
    def test_all_package_sources_compile(self):
        bad = []
        for pkg in _PKGS:
            root = _ROOT / pkg
            if not root.exists():
                continue
            for f in root.rglob("*.py"):
                if "build/lib" in str(f):
                    continue
                try:
                    py_compile.compile(str(f), doraise=True)
                except py_compile.PyCompileError as exc:
                    bad.append(f"{f.relative_to(_ROOT)}: {str(exc).splitlines()[-1]}")
        self.assertEqual(bad, [], "package source has syntax errors:\n  " + "\n  ".join(bad))


if __name__ == "__main__":
    unittest.main()
