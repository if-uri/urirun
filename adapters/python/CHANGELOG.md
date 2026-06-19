# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.13] - 2026-06-20

### Added
- Add `urirun.connector(...)`, a convention helper for connector packages. It
  builds full URI routes from short paths, fills `meta.connector`, and exports
  connector-scoped bindings through `.bindings()`.

## [0.3.12] - 2026-06-20

### Added
- Add the preferred top-level decorator API:
  `@urirun.command(...)`, `@urirun.shell(...)` and
  `urirun.connector_bindings(...)`.

## [0.3.11] - 2026-06-20

### Fixed
- Restore release-version consistency after the skipped v0.3.8-v0.3.10 tags
  still built `urirun` Python artifacts with version 0.3.5.

## [0.3.5] - 2026-06-20

### Added
- Add `urirun.v2.connector_bindings()` for connector packages that generate
  serializable v2 bindings from `@uri_command` decorated functions.

## [0.3.4] - 2026-06-19

### Changed
- Keep the Python distribution GitHub-installable as `urirun`.
- Remove public console entry points for versions below v1.
- Keep only `urirun`, `urirun-v1`, `urirun-v2`, `urirun-v1`, and
  `urirun-v2` as installed scripts.
- Move legacy registry/scanner/policy helpers behind private module names used
  internally by v1/v2.

## [0.3.3] - 2026-06-19

### Docs
- Update CHANGELOG.md
- Update README.md
- Update adapters/python/CHANGELOG.md
- Update adapters/python/README.md
- Update v2/README.md
- Update v2/examples/docker_uri_flow/README.md
- Update v2/spec/urirun-v2.md

### Other
- Update adapters/python/VERSION
- Update adapters/python/pyproject.toml
- Update adapters/python/urirun/v2.py
- Update adapters/python/urirun/v2_service.py
- Update adapters/python/uv.lock
- Update v2/examples/docker_uri_flow/shell-worker/bindings.json
- Update v2/examples/docker_uri_flow/test_service_adapter.py

## [0.3.1] - 2026-06-19

### Docs
- Update CHANGELOG.md
- Update README.md
- Update adapters/python/README.md
- Update v2/README.md
- Update v2/examples/docker_uri_flow/README.md
- Update v2/spec/urirun-v2.md

### Other
- Update Makefile
- Update adapters/python/.gitignore
- Update adapters/python/pyproject.toml
- Update adapters/python/uv.lock
- Update v2/examples/docker_uri_flow/Makefile
- Update v2/examples/docker_uri_flow/node-worker/package.json
- Update v2/examples/docker_uri_flow/node-worker/server.js
- Update v2/examples/docker_uri_flow/orchestrator/flow_runner.py
- Update v2/examples/docker_uri_flow/python-worker/server.py
- Update v2/examples/docker_uri_flow/shell-worker/server.py
- ... and 2 more files
