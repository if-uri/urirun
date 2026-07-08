# Multiplatform Harness Contract

This repository is prepared to be tested by
`if-uri/urirun-multiplatform-test` after the main `ci` workflow succeeds.

## GitHub Actions Dispatch

Workflow: `.github/workflows/multiplatform-harness.yml`

Required secret:

- `URIRUN_MULTIPLATFORM_TEST_TOKEN` with permission to call
  `repository_dispatch` on `if-uri/urirun-multiplatform-test`.

The workflow sends event type `urirun-main-ci` and passes:

- `urirun_repo_url`
- `urirun_ref`
- `sha`
- `get_urirun_site_mode`
- `allow_remote_install`

`allow_remote_install` defaults to `false`. Keep it false for normal CI so the
external harness does not execute production installers.

## Fresh Install Contract

The Python package is installable from this repository without a `--no-deps`
fallback:

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install ./adapters/python
urirun --version
urirun doctor --json
urirun --help
```

Runtime split packages required by the base CLI are declared as normal
dependencies and must resolve from PyPI or the configured package index. The
current clean-install path resolves `urirun-contract`, `urirun-connector-router`
and `urirun-flow` without `--no-deps`.

## Dashboard GUI Contract

The dashboard exposes:

- command: `urirun host dashboard serve --project <path> --db <path> --host <host> --port <port>`
- health endpoint: `GET /api/health`
- stable selectors: `chat`, `nodes`, `tasks`, `services`, `artifacts`, `settings`
- matching section selectors: `<name>-section`
- ARIA labels for the primary and mobile navigation controls.

The selector names use lowercase kebab-case and are guarded by tests.

## Product Artifacts

Build local validation artifacts with:

```bash
python scripts/build_product_artifacts.py --out-dir dist/product-artifacts
```

The output contains:

- `manifest.json`
- `SHA256SUMS`
- Python wheel/sdist when `python -m build` is available
- platform bootstrap bundles for Windows, Linux, and macOS

The bootstrap bundles are real checksumed artifacts for validation and site
wiring. They are not signed native installers. Signed `.msi`, `.pkg`, `.dmg`,
`.deb`, `.rpm`, AppImage, or notarized `.app` outputs remain a release pipeline
task and must require trusted signing secrets plus approval.

## Production Promotion

The external harness must not deploy production. A trusted promotion job should
consume the manifest, checksums, and artifacts after tests pass, require manual
approval, sign/notarize where applicable, publish immutable artifacts, then
publish the manifest consumed by `get.urirun.com`.

## gRPC Policy

gRPC remains optional. Install it with:

```bash
python -m pip install "./adapters/python[grpc]"
```

Main CI verifies the optional extra. Black-box gRPC tests should treat missing
`grpcio` in a base install as optional coverage, not a base install failure.

## External Harness Local Run

From the harness repository:

```bash
URIRUN_SOURCE_DIR=/path/to/urirun python scripts/run_tests.py
```

PowerShell:

```powershell
$env:URIRUN_SOURCE_DIR="C:\path\to\urirun"
python scripts\run_tests.py
```
