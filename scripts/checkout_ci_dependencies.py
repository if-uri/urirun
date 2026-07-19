#!/usr/bin/env python3
"""Shallow-clone external urirun test dependencies in parallel.

The destination is normally ``$GITHUB_WORKSPACE``. Existing Git checkouts are
kept intact, so the helper is safe to rerun in a developer workspace.
"""

from __future__ import annotations

import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


UNIT = (
    ("urirun-connectors/urirun-connector-twin", "urirun-connector-twin"),
    ("urirun-connectors/urirun-connector-domain-monitor", "urirun-connector-domain-monitor"),
)

DOCKER = (
    ("if-uri/urirun-contract", "urirun-contract"),
    ("if-uri/urirun-flow", "urirun-flow"),
    ("urirun-connectors/urirun-connector-router", "urirun-connector-router"),
    ("urirun-connectors/urirun-connector-domain-monitor", "urirun-connector-domain-monitor"),
)

HOST_CONNECTORS = (
    "adopt",
    "base64",
    "browser-control",
    "domain-monitor",
    "email",
    "flow-repair",
    "get-node",
    "hash",
    "http-check",
    "invoice",
    "ksef",
    "kvm",
    "llm",
    "mcp-filesystem",
    "mqtt",
    "namecheap-dns",
    "ocr",
    "planfile",
    "signal",
    "sqlite-context",
    "time-tools",
    "uuid",
    "work",
)
HOST = (
    ("if-uri/urirun-declarative", "urirun-declarative"),
    ("if-uri/urirun-openapi-import", "urirun-openapi-import"),
    *((f"urirun-connectors/urirun-connector-{name}", f"urirun-connector-{name}") for name in HOST_CONNECTORS),
)

GROUPS = {"unit": UNIT, "host": HOST, "docker": DOCKER}


def clone_one(repository: str, directory: str, destination: Path) -> tuple[str, bool, str]:
    target = destination / directory
    if (target / ".git").exists():
        return directory, True, "existing checkout"
    if target.exists():
        return directory, False, "target exists but is not a Git checkout"
    process = subprocess.run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--filter=blob:none",
            f"https://github.com/{repository}.git",
            str(target),
        ],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    detail = "cloned" if process.returncode == 0 else (process.stderr or process.stdout).strip()
    return directory, process.returncode == 0, detail


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("group", choices=sorted(GROUPS))
    parser.add_argument("destination", type=Path)
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    dependencies = GROUPS[args.group]
    if args.dry_run:
        for repository, directory in dependencies:
            print(f"{repository}\t{args.destination / directory}")
        return 0

    args.destination.mkdir(parents=True, exist_ok=True)
    results = []
    with ThreadPoolExecutor(max_workers=max(1, min(args.jobs, len(dependencies)))) as pool:
        futures = {
            pool.submit(clone_one, repository, directory, args.destination): directory
            for repository, directory in dependencies
        }
        for future in as_completed(futures):
            results.append(future.result())

    failed = False
    for directory, ok, detail in sorted(results):
        print(f"{'OK' if ok else 'FAIL'}\t{directory}\t{detail}")
        failed = failed or not ok
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
