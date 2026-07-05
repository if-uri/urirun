#!/usr/bin/env bash
# Author: Tom Sapletta · Part of the ifURI solution.
#
# Deploy a LIBRARY-BACKED urirun connector (vdisplay/vql/urivision/…) to a mesh node.
# Proven on lenovo 2026-07-05. Two things a heavy-lib connector needs that a self-contained
# one (kvm) does not:
#
#   1. The wrapped library must be INSTALLED on the node — done over the mesh (no SSH) via the
#      signed node://<name>/package/command/install route (the node must run with --manage +
#      key auth). We install here before deploying the connector code.
#   2. Flat --code deploy pushes files by BASENAME into one dir, so every connector's core.py
#      would collide as "core.py" (kvm's core.py then shadows the others → "local function ref
#      is not callable"). We push the connector under a UNIQUE module name (<id>_core.py) and
#      rewrite the bindings' python.module to match.
#
# Usage: deploy_lib_connector.sh <connector_dir> <lib_pip_spec> [NODE_URL] [NODE_NAME]
#   e.g. deploy_lib_connector.sh ~/github/if-uri/urirun-connector-vql vql \
#          http://192.168.188.201:8765 laptop
set -euo pipefail

CONNECTOR_DIR="$1"                       # e.g. ~/github/if-uri/urirun-connector-vql
LIB_SPEC="$2"                            # pip spec of the wrapped library, e.g. "vql" or "vql,pillow"
NODE_URL="${3:-http://192.168.188.201:8765}"
NODE_NAME="${4:-laptop}"
PY="${URIRUN_PY:-$HOME/github/if-uri/urirun/venv/bin/python}"
URIRUN="$(dirname "$PY")/urirun"
ID="${URIRUN_IDENTITY:-$HOME/.ssh/id_ed25519}"

# connector id from dir name: urirun-connector-<id>
CID="$(basename "$CONNECTOR_DIR" | sed 's/^urirun-connector-//')"
PKG="urirun_connector_${CID//-/_}"
MOD="${CID//-/_}_core"                   # unique flat module name, e.g. vql_core
PKG_DIR="$CONNECTOR_DIR/$PKG"

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

# 1. install the wrapped library on the node (signed, over the mesh)
IFS=',' read -ra SPECS <<< "$LIB_SPEC"
SPEC_JSON="$($PY -c "import json,sys; print(json.dumps({'spec': sys.argv[1:]}))" "${SPECS[@]}")"
echo "[deploy] installing library on node: ${SPECS[*]}"
"$URIRUN" host run "$NODE_URL" "node://$NODE_NAME/package/command/install" \
  --payload "$SPEC_JSON" --identity "$ID" --timeout 300 >/dev/null

# 2. push core.py under the unique module name + rewrite bindings' python.module
cp "$PKG_DIR/core.py" "$TMP/$MOD.py"
cd "$PKG_DIR"   # neutral cwd so `import $PKG` isn't shadowed by a repo folder
"$PY" -c "import json; from ${PKG}.core import urirun_bindings; \
print(json.dumps(urirun_bindings()).replace('${PKG}.core', '${MOD}').replace('${PKG}.', '${MOD}'))" \
  > "$TMP/bindings.json"

echo "[deploy] deploying connector '$CID' as module '$MOD'"
exec "$URIRUN" host deploy "$NODE_URL" --bindings "$TMP/bindings.json" \
  --allow "${CID}://**" --code "$TMP/$MOD.py" --merge --persist --identity "$ID"
