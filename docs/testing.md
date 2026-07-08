# Testing ownership

This repository keeps the tests that are needed to develop, refactor, secure and
release `urirun` itself. External black-box multiplatform E2E testing lives in a
separate repository:

<https://github.com/if-uri/urirun-multiplatform-test>

The main-repo workflow, selector, install, artifact, production-promotion and
gRPC policy contracts are documented in
[`docs/MULTIPLATFORM_HARNESS.md`](MULTIPLATFORM_HARNESS.md).

## Tests in this repository

The main `urirun` repository owns developer-facing validation:

- unit tests for runtime, host, node, connector and helper modules;
- integration tests that validate internal contracts between `urirun` modules;
- adapter/runtime tests for Python, JavaScript, C and URI runtime behavior;
- connector smoke helpers used by the product and connector SDK;
- security regression tests, including the mesh security probe;
- examples validation and conformance checks that protect examples and SDK
  contracts;
- build, lint, complexity, documentation and release gates.

These tests may use local fixtures, internal APIs, temporary files, local
servers, package build artifacts or source-tree imports. They are allowed to be
white-box tests because they protect the implementation and release process of
`urirun`.

## Tests in the multiplatform repository

The `urirun-multiplatform-test` repository owns external black-box coverage:

- fresh checkout/bootstrap of the test harness;
- fresh installation of a selected `urirun` ref;
- Linux testing through Docker;
- Windows testing through GitHub Actions or self-hosted Windows runners;
- macOS testing through GitHub Actions or self-hosted macOS runners;
- black-box CLI smoke and E2E scenarios;
- HTTP, gRPC and MCP transport smoke tests where supported;
- allow-list, invalid command, invalid URI and error-reporting scenarios;
- diagnostic reports, JUnit output and CI artifacts.

Those tests should not depend on manually copied files from this repository.
They fetch `urirun` through `URIRUN_REPO_URL` and `URIRUN_REF`, install it in a
fresh environment and exercise the public CLI/transport surface as a user would.

## Rule of thumb

Keep tests here when they validate implementation details, refactoring safety,
release packaging or examples that are part of this source tree.

Put tests in `urirun-multiplatform-test` when they validate a full installed
`urirun` from the outside across Linux, Windows or macOS.
