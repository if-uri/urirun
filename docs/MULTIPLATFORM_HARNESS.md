# Multiplatform Harness

The main `if-uri/urirun` repository triggers the external
`if-uri/urirun-multiplatform-test` harness after the main `ci` workflow succeeds.
The `ci` workflow remains the main gate; this integration only dispatches the
external black-box test suite after that gate is green.

## Workflow

Workflow file:

```text
.github/workflows/trigger-multiplatform-smoke.yml
```

Triggers:

- `workflow_run` after `ci` completes with `success`
- manual `workflow_dispatch`

The workflow calls GitHub `repository_dispatch` on:

```text
if-uri/urirun-multiplatform-test
```

with event type:

```text
urirun-main-ci
```

## Required Secret

Configure this secret in the main `if-uri/urirun` repository:

```text
URIRUN_MULTIPLATFORM_TEST_TOKEN
```

The token is used as `GH_TOKEN` for `gh api` and must be allowed to call
`repository_dispatch` on `if-uri/urirun-multiplatform-test`.

## Dispatch Payload

The workflow sends:

- `urirun_repo_url`: `https://github.com/if-uri/urirun.git`
- `urirun_ref`: exact SHA/ref from `${{ github.event.workflow_run.head_sha || github.sha }}`
- `sha`: same exact SHA/ref
- `get_urirun_site_mode`: `production-site`
- `allow_remote_install`: `false`

`allow_remote_install=false` is the safe default. It lets the harness validate
installer and GUI flows without executing remote production installers by
default.

## Manual Run

In GitHub Actions, open `trigger multiplatform smoke` and choose **Run workflow**.
For manual runs, the workflow dispatches the current commit SHA as `urirun_ref`
and `sha`.

## External Profiles

The external harness is responsible for running:

- `linux-docker`
- `windows-runner`
- `macos-runner`
- `linux-installer-gui`
- `windows-installer-gui`
- `macos-installer-gui`

This repository only triggers the harness. Do not claim the external harness has
passed until an actual GitHub Actions run in `if-uri/urirun-multiplatform-test`
confirms it.
