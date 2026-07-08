# Multiplatform Harness

The main `if-uri/urirun` repository triggers the external
`if-uri/urirun-multiplatform-test` repository after the main `ci` workflow
completes successfully. This workflow only starts the external black-box
harness; it does not prove the harness passed until GitHub Actions run evidence
exists.

## Workflow

Workflow file:

```text
.github/workflows/trigger-multiplatform-smoke.yml
```

The workflow runs in two cases:

- automatically after the existing `ci` workflow completes with `success`;
- manually through GitHub Actions `workflow_dispatch`.

Manual dispatch sends the current workflow commit SHA as both `urirun_ref` and
`sha`.

## Required Secret

Configure this secret in the main `if-uri/urirun` repository:

```text
URIRUN_MULTIPLATFORM_TEST_TOKEN
```

The workflow uses it as `GH_TOKEN` for the `gh api` call that sends
`repository_dispatch` to `if-uri/urirun-multiplatform-test`.

## Payload

The dispatch event type is:

```text
urirun-main-ci
```

The payload includes:

- `urirun_repo_url`: `https://github.com/if-uri/urirun.git`
- `urirun_ref`: exact commit SHA/ref being tested
- `sha`: same exact SHA/ref
- `get_urirun_site_mode`: `production-site`
- `allow_remote_install`: `false`

`allow_remote_install=false` is the safe default. Keep it false for normal CI so
the external harness does not execute remote production installers by default.

## External Profiles

The external harness runs:

- `linux-docker`
- `windows-runner`
- `macos-runner`
- `linux-installer-gui`
- `windows-installer-gui`
- `macos-installer-gui`
