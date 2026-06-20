#!/usr/bin/env bash
# Reference urirun connector in Bash: prints a urirun.bindings.v2 document.
set -euo pipefail
. "$(dirname "$0")/../urirun.sh"

schema='{"type":"object","additionalProperties":false,"required":["path"],"properties":{"path":{"type":"string"}}}'
argv='["sha256sum","{path}"]'
member="$(urirun_command hash host "sha256/command/file" "$schema" "$argv" hash)"
urirun_document "$member"
