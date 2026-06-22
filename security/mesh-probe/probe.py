#!/usr/bin/env python3
# Mesh security probe — runs from a SEPARATE container with only network access to
# the node (no shared filesystem, no credentials). Authorized defensive testing of
# urirun's own mesh surface.
#
# Each check has a category that decides the exit code (so this doubles as a CI
# regression gate):
#   fixed     a code-level gap that was closed — MUST stay closed (regress -> exit 1)
#   defended  an attack the node already blocks — MUST keep blocking (break -> exit 1)
#   config    risky only because of the deliberately-permissive test config
#   bydesign  an accepted trade-off (trusted-LAN assumption)
# Only `fixed`/`defended` regressions fail the run; config/bydesign are informational.
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://node:8765").rstrip("/")
rows: list[tuple[str, str, bool, str]] = []  # (category, id, bad, note)


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
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat
    k = Ed25519PrivateKey.generate()
    p = "/tmp/attacker_ed25519"
    open(p, "wb").write(k.private_bytes(Encoding.PEM, PrivateFormat.OpenSSH, NoEncryption()))
    return p


def record(cat: str, fid: str, bad: bool, note: str):
    # bad == True means "the node behaved insecurely on this check"
    tag = {"fixed": "FIX!", "defended": "BRK!", "config": "VULN", "bydesign": "VULN"}[cat] if bad else "ok  "
    rows.append((cat, fid, bad, note))
    print(f"  [{tag}] {fid:26} {note}")


print(f"== mesh security probe vs {BASE} ==\n")

# --- transport / disclosure (bydesign/config: informational) ---
record("bydesign", "plaintext-transport", BASE.startswith("http://"),
       "plaintext HTTP — tokens/signed headers sniffable, MITM (front with TLS/overlay)")
st, b = http("GET", "/routes")
record("config", "info-routes", st == 200, f"GET /routes unauth -> {st} (capability map)")
st, _ = http("GET", "/errors")
record("config", "info-errors", st == 200, f"GET /errors unauth -> {st} (gate with --admin-token)")

# --- unauth command exec via /run (config: broad --allow includes the command route) ---
p = json.dumps({"uri": "demo://host/shell/command/run", "payload": {"marker": "PWNED"}}).encode()
st, b = http("POST", "/run", body=p, headers={"Content-Type": "application/json"})
out = (json.loads(b or b"{}").get("result") or {}).get("stdout", "") if st == 200 else ""
record("config", "unauth-run-command", st == 200 and "EXECUTED:PWNED" in out,
       f"unauth /run of a COMMAND route -> exec={'EXECUTED:PWNED' in out} (scope --allow to /query/)")

# --- FIXED: oversized body must be refused (no OOM) ---
big = b'{"uri":"demo://host/echo/query/ping","payload":{"x":"' + b"A" * (8 * 1024 * 1024) + b'"}}'
st, _ = http("POST", "/run", body=big, headers={"Content-Type": "application/json"})
record("fixed", "unbounded-body", st == 200, f"8MB body -> {st} (must be refused/413, not 200)")

# --- DEFENDED: malformed /run must 400, not crash/500 ---
st, _ = http("POST", "/run", body=b'{"not":"a uri"}', headers={"Content-Type": "application/json"})
record("defended", "malformed-run", st in (None, 500), f"/run with no uri -> {st} (must be a clean 4xx, not 500/crash)")

# --- DEFENDED: /deploy with no credential must 403 ---
st, _ = http("POST", "/deploy", body=b'{"bindings":{"version":"urirun.bindings.v2","bindings":{}}}',
             headers={"Content-Type": "application/json"})
record("defended", "deploy-no-auth", st not in (403,), f"/deploy with NO token/sig -> {st} (must be 403)")

# --- bydesign: trust-on-first-use claims a fresh node (race) ---
key = _attacker_key()
from urirun.node import keyauth  # noqa: E402
pub = keyauth.public_openssh(key)
st, b = http("POST", "/authorized-keys", body=json.dumps({"publicKey": pub}).encode(),
             headers={"Content-Type": "application/json"})
enrolled = st == 200 and json.loads(b or b"{}").get("ok") is True
record("bydesign", "tofu-enroll", enrolled, f"first key claims a fresh node, no sig -> {st} (enroll on provision)")

# --- FIXED: a captured signed request must not replay ---
if enrolled:
    raw = json.dumps({"publicKey": pub}).encode()
    hdrs = {**keyauth.sign(key, keyauth.PURPOSE_ENROLL, raw), "Content-Type": "application/json"}
    s1, _ = http("POST", "/authorized-keys", body=raw, headers=hdrs)
    s2, _ = http("POST", "/authorized-keys", body=raw, headers=hdrs)  # identical bytes+headers
    record("fixed", "signed-request-replay", s1 == 200 and s2 == 200,
           f"same signed request twice -> ({s1},{s2}) (replay must be rejected on the 2nd)")

    # --- DEFENDED: enrolling another key WITHOUT a signature, on a non-empty node, must 403 ---
    other = keyauth.public_openssh(_attacker_key())  # a different key, sent unsigned
    st, _ = http("POST", "/authorized-keys", body=json.dumps({"publicKey": other}).encode(),
                 headers={"Content-Type": "application/json"})
    record("defended", "enroll-after-first-unsigned", st not in (403,),
           f"unsigned 2nd-key enroll on a claimed node -> {st} (must be 403)")
else:
    record("fixed", "signed-request-replay", True, "skipped (enroll failed) — cannot verify")
    record("defended", "enroll-after-first-unsigned", True, "skipped (enroll failed)")

regress = [(c, f, n) for (c, f, bad, n) in rows if bad and c in ("fixed", "defended")]
print(f"\n== {sum(1 for r in rows if r[2])} insecure behaviours; {len(regress)} are regressions (fixed/defended) ==")
for c, f, n in regress:
    print(f"  REGRESSION [{c}] {f}")
sys.exit(1 if regress else 0)
