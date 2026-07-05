#!/usr/bin/env bash
# Author: Tom Sapletta · Part of the ifURI solution.
#
# Re-deploy the full computer-use surface (kvm + vql + vdisplay) to a mesh node in ONE command.
# Run this after the node restarts: a node restart drops merge-deployed routes back to the
# built-ins (env/log/node/proc/shell) — the wrapped libraries stay pip-installed, only the served
# registry is lost — so the connectors must be re-served. See PERFORMANCE-REFACTOR / lenovo notes.
#
# Usage: redeploy_all.sh [NODE_URL] [NODE_NAME]
#   NODE_URL   default http://192.168.188.201:8765 (lenovo)
#   NODE_NAME  default laptop
set -euo pipefail

NODE_URL="${1:-http://192.168.188.201:8765}"
NODE_NAME="${2:-laptop}"
ROOT="${URIRUN_IFURI_ROOT:-$HOME/github/if-uri}"
LIBDEPLOY="$ROOT/urirun/scripts/deploy_lib_connector.sh"

echo "[redeploy-all] target $NODE_URL"

# 1. kvm — self-contained flat deploy (its own script; also sets URIRUN_NODE_SELF_URL)
echo "[redeploy-all] kvm …"
"$ROOT/urirun-connector-kvm/scripts/redeploy_node.sh" "$NODE_URL" >/dev/null

# 2 + 3. library-backed connectors — install the lib on the node (idempotent) + deploy under a
#        unique flat module name (deploy_lib_connector handles the core.py collision).
echo "[redeploy-all] vql …"
"$LIBDEPLOY" "$ROOT/urirun-connector-vql" vql,pillow "$NODE_URL" "$NODE_NAME" >/dev/null
echo "[redeploy-all] vdisplay …"
"$LIBDEPLOY" "$ROOT/urirun-connector-vdisplay" vdisplay "$NODE_URL" "$NODE_NAME" >/dev/null

# 4. re-hydrate kvm last (a lib merge-deploy leaves kvm's in-process routes served; this is
#    belt-and-braces so capture/readiness are freshly hydrated) and report.
"$ROOT/urirun-connector-kvm/scripts/redeploy_node.sh" "$NODE_URL" >/dev/null

COUNT=$(curl -s -m 10 "$NODE_URL/health" | "$HOME/github/if-uri/urirun/venv/bin/python" \
        -c "import json,sys; print(json.load(sys.stdin).get('routeCount','?'))" 2>/dev/null || echo "?")
echo "[redeploy-all] done — node serves $COUNT routes (kvm + vql + vdisplay + built-ins)"
