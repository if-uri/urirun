#!/usr/bin/env bash
# Author: Tom Sapletta · Part of the ifURI solution.
#
# Start a urirun node with FULL CONSOLE TRANSPARENCY: every URI process it runs is printed to
# the shell (incoming command + result + timing + canonical error code), so you can see exactly
# what is happening on the node. Run this on the machine that hosts the node (e.g. lenovo).
#
#   [uri] → kvm://host/screen/query/capture  [execute]  {"max_width": 1600}
#   [uri] ← ok  47ms  kvm://host/screen/query/capture  {"via": "mutter-screencast-warm"}
#   [uri] ← ERROR NOT_FOUND 404  3ms  kvm://host/nope/query/x  "Route not found: …"
#
# Requires a urirun that has the verbose hook (urirun_node.server._verbose_run_*). If your node's
# urirun is older, update it first:  pip install -e <if-uri>/urirun/adapters/python
#
# Usage: node-verbose.sh [NAME] [PORT] [extra `urirun node serve` flags…]
#   defaults: name=laptop, port=8765, --host 0.0.0.0 --execute --key-auth --manage --pool
set -euo pipefail

NAME="${1:-laptop}"; shift || true
PORT="${1:-8765}"; shift || true
URIRUN="${URIRUN_BIN:-urirun}"

export URIRUN_NODE_VERBOSE=1      # verbose per-URI logging
export URIRUN_QR_SHELL=1          # scannable QR of the node URL in the shell (phone) + clickable local

echo "[node-verbose] starting node '$NAME' on :$PORT with URI-process logging → this shell"
echo "[node-verbose] every kvm://, vql://, vdisplay:// … call will print here. Ctrl-C to stop."
exec "$URIRUN" node serve --name "$NAME" --port "$PORT" --host 0.0.0.0 \
  --key-auth --manage --pool "$@"
