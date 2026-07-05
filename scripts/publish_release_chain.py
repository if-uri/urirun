#!/usr/bin/env python3
# Author: Tom Sapletta · Part of the ifURI solution.
"""Publish the urirun package ecosystem to PyPI in DEPENDENCY ORDER, with a per-package gate.

The chain is deep (a package can't install until its urirun-* deps are on PyPI), so a naive
publish fails. This computes the topological order over the UNPUBLISHED packages and, for each,
builds → ``twine check`` → ``twine upload --skip-existing``. It STOPS on the first failure, so a
broken build never cascades. Idempotent: a package already on PyPI is skipped.

DRY-RUN by default — prints the plan and does nothing. Pass ``--publish`` to actually upload
(needs ~/.pypirc or TWINE_* env). Reads every ``urirun*/pyproject.toml`` under the repo root.

    python scripts/publish_release_chain.py              # plan only
    python scripts/publish_release_chain.py --publish    # build + upload in order, gated
    python scripts/publish_release_chain.py --only urirun-contract,urirun-connector-router
"""
from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
import tomllib


def _load_packages(root: str) -> dict:
    pkgs: dict[str, dict] = {}
    patterns = [os.path.join(root, "urirun*/pyproject.toml"),
                os.path.join(root, "urirun/adapters/python/pyproject.toml")]
    for pp in sorted({p for pat in patterns for p in glob.glob(pat)}):
        try:
            d = tomllib.load(open(pp, "rb"))["project"]
        except Exception:  # noqa: BLE001
            continue
        deps = [x.split(">=")[0].split("==")[0].split("[")[0].strip()
                for x in (d.get("dependencies") or []) if x.strip().startswith("urirun")]
        pkgs[d["name"]] = {"dir": os.path.dirname(pp), "version": d["version"], "deps": deps}
    return pkgs


def _on_pypi(name: str) -> bool:
    r = subprocess.run([sys.executable, "-m", "pip", "index", "versions", name],
                       capture_output=True, text=True, timeout=30)
    return r.returncode == 0 and name in r.stdout


def _topo(missing: dict) -> list[str]:
    order, seen = [], set()

    def visit(n: str, stack: tuple = ()) -> None:
        if n in seen or n not in missing:
            return
        for dep in missing[n]["deps"]:
            if dep in missing and dep not in stack:
                visit(dep, stack + (n,))
        seen.add(n)
        order.append(n)
    for n in missing:
        visit(n)
    return order


def _publish_one(name: str, info: dict) -> bool:
    d = info["dir"]
    print(f"  → build {name} {info['version']} …")
    if subprocess.run([sys.executable, "-m", "build", "-o", os.path.join(d, "dist"), d]).returncode:
        print(f"  ✗ build failed: {name}")
        return False
    dist = glob.glob(os.path.join(d, "dist", f"*{info['version']}*"))
    if subprocess.run([sys.executable, "-m", "twine", "check", *dist]).returncode:
        print(f"  ✗ twine check failed: {name}")
        return False
    if subprocess.run([sys.executable, "-m", "twine", "upload", "--skip-existing", *dist]).returncode:
        print(f"  ✗ upload failed: {name}")
        return False
    print(f"  ✓ published {name} {info['version']}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.expanduser("~/github/if-uri"))
    ap.add_argument("--publish", action="store_true", help="actually build + upload (else plan only)")
    ap.add_argument("--only", help="comma-separated subset of package names")
    args = ap.parse_args()

    pkgs = _load_packages(args.root)
    only = set(args.only.split(",")) if args.only else None
    print(f"scanning {len(pkgs)} urirun packages under {args.root} …")
    missing = {n: v for n, v in pkgs.items()
               if (only is None or n in only) and not _on_pypi(n)}
    order = _topo(missing)
    print(f"\n{len(order)} to publish, in dependency order:")
    for i, n in enumerate(order, 1):
        blockers = [d for d in missing[n]["deps"] if d in missing]
        print(f"  {i:2d}. {n:34s} {missing[n]['version']:8s} after: {blockers or '—'}")

    if not args.publish:
        print("\n(plan only — pass --publish to build + upload, gated per package)")
        return 0
    print("\npublishing (stops on first failure):")
    for n in order:
        if not _publish_one(n, missing[n]):
            print(f"\nSTOPPED at {n}. Fix and re-run; already-published packages are skipped.")
            return 1
    print(f"\ndone — published {len(order)} packages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
