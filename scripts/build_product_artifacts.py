"""Build urirun product artifacts and a manifest for external validation.

This is intentionally conservative: it always creates checksumed platform
installer bundles that bootstrap the Python package, and it builds wheel/sdist
when the local build backend is available. Native signed installers remain a
trusted release-promotion concern, not something the black-box harness should
invent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON_PACKAGE = ROOT / "adapters" / "python"


def _version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def _git_revision() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return ""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record(path: Path, *, platform: str, kind: str) -> dict:
    return {
        "product": "urirun",
        "version": _version(),
        "git_revision": _git_revision(),
        "platform": platform,
        "kind": kind,
        "file_name": path.name,
        "sha256": _sha256(path),
        "size": path.stat().st_size,
    }


def _write_text(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def _installer_text(platform: str, version: str) -> str:
    if platform == "windows":
        return f"""param(
  [string]$Python = "python",
  [string]$Source = "https://github.com/if-uri/urirun.git@v{version}"
)
$ErrorActionPreference = "Stop"
& $Python -m pip install --upgrade pip
& $Python -m pip install "urirun @ git+$Source#subdirectory=adapters/python"
& $Python -m urirun.v2 --version
"""
    return f"""#!/usr/bin/env sh
set -eu
PYTHON="${{PYTHON:-python3}}"
SOURCE="${{URIRUN_SOURCE:-https://github.com/if-uri/urirun.git@v{version}}}"
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install "urirun @ git+$SOURCE#subdirectory=adapters/python"
"$PYTHON" -m urirun.v2 --version
"""


def _platform_bundle(out_dir: Path, platform: str, version: str) -> Path:
    work = out_dir / f"urirun-{version}-{platform}"
    work.mkdir(parents=True, exist_ok=True)
    script_name = "install.ps1" if platform == "windows" else "install.sh"
    script = _write_text(work / script_name, _installer_text(platform, version))
    if platform != "windows":
        script.chmod(script.stat().st_mode | 0o755)
    _write_text(
        work / "README.txt",
        "This bundle is a reproducible bootstrap artifact for urirun validation. "
        "Signed native installers are produced only by the trusted promotion pipeline.\n",
    )
    if platform == "windows":
        archive = out_dir / f"urirun-{version}-windows.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for item in work.rglob("*"):
                zf.write(item, item.relative_to(out_dir))
        return archive
    archive = out_dir / f"urirun-{version}-{platform}.tar.gz"
    with tarfile.open(archive, "w:gz") as tf:
        tf.add(work, arcname=work.name)
    return archive


def _build_python_artifacts(out_dir: Path) -> list[Path]:
    if shutil.which(sys.executable) is None:
        return []
    build_cmd = [sys.executable, "-m", "build", "--sdist", "--wheel", "--outdir", str(out_dir)]
    try:
        subprocess.run(build_cmd, cwd=PYTHON_PACKAGE, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return sorted(
        path for path in out_dir.iterdir()
        if path.suffix == ".whl" or path.name.endswith(".tar.gz")
    )


def build(out_dir: Path, *, skip_python_build: bool = False) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    version = _version()
    artifacts: list[dict] = []
    if not skip_python_build:
        for path in _build_python_artifacts(out_dir):
            kind = "python-wheel" if path.suffix == ".whl" else "python-sdist"
            artifacts.append(_record(path, platform="python", kind=kind))
    for platform in ("windows", "linux", "macos"):
        path = _platform_bundle(out_dir, platform, version)
        artifacts.append(_record(path, platform=platform, kind="bootstrap-installer-bundle"))
    manifest = {
        "product": "urirun",
        "version": version,
        "repo_url": "https://github.com/if-uri/urirun.git",
        "revision": _git_revision(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": artifacts,
        "checksums": {item["file_name"]: item["sha256"] for item in artifacts},
        "promotion": {
            "production_deploys": False,
            "requires_manual_approval": True,
            "native_signed_installers": False,
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out_dir / "SHA256SUMS").write_text(
        "".join(f"{item['sha256']}  {item['file_name']}\n" for item in artifacts),
        encoding="utf-8",
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="dist/product-artifacts")
    parser.add_argument("--skip-python-build", action="store_true")
    args = parser.parse_args(argv)
    manifest = build(Path(args.out_dir), skip_python_build=args.skip_python_build)
    print(json.dumps({"ok": True, "outDir": args.out_dir, "artifacts": len(manifest["artifacts"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
