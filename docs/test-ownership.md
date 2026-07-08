# Test Ownership

`if-uri/urirun` owns tests that prove internal correctness of the source tree.
`if-uri/urirun-multiplatform-test` owns black-box behavior of installed builds
across operating systems, shells, transports, installers, and GUI/browser flows.

## Main Repository

Keep tests in this repository when they are narrow, source-level, or release
packaging checks:

- parser construction and command handler routing;
- schema validation, registry compilation, and dispatch internals;
- host/node routing, recovery, dashboard API, and helper-function regressions;
- import boundaries and bundled-module/package metadata checks;
- release gates that prove a wheel can be built and that expected modules,
  shims, and console-script metadata are present.

These tests should run from the working tree or from a freshly built package
without trying to prove a full installed user journey.

## External Multiplatform Harness

Move broad smoke and E2E coverage to `if-uri/urirun-multiplatform-test`,
including:

- installed `urirun --version`, `urirun --help`, and `urirun doctor --json`
  smoke tests;
- full CLI command sequences against a fresh virtual environment;
- Linux, Windows, macOS, shell, path-with-spaces, and native path behavior;
- HTTP `/health` and `/run`, MCP, and gRPC transport smoke tests;
- get.urirun.com installer flow checks;
- product artifact deployment bundle E2E checks;
- dashboard GUI/browser Playwright journeys.

That harness runs the `linux-docker`, `windows-runner`, `macos-runner`,
`linux-installer-gui`, `windows-installer-gui`, and `macos-installer-gui`
profiles.

## Removed Duplication

The main repository no longer runs the `scripts/test_pypi_install.sh` installed
node-server smoke that started `urirun node serve`, waited for `/health`, and
posted to `/run`. The same black-box behavior is covered externally by
`urirun-multiplatform-test/tests/test_transports.py`, while this repository keeps
the package import, shim, host-dashboard import, and console-script metadata
checks needed for release safety.

Release workflow checks that look similar to CLI smokes should stay metadata- or
import-level. Full installed CLI help, version, doctor, transport, installer, and
GUI evidence must come from the external harness and from GitHub Actions run
results.
