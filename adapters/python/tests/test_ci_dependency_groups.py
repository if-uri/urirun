from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_host_ci_dependencies_include_direct_example_imports(tmp_path: Path) -> None:
    repository = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [
            sys.executable,
            str(repository / "scripts" / "checkout_ci_dependencies.py"),
            "host",
            str(tmp_path),
            "--dry-run",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    dependencies = set(result.stdout.splitlines())
    assert f"if-uri/urirun-work\t{tmp_path / 'urirun-work'}" in dependencies
