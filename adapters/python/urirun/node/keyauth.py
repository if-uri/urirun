# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# SSH-style public-key authorization for urirun node admin (POST /deploy and key
# enrollment), as an alternative to a shared token. Reuses the operator's existing SSH
# ed25519 key. The node keeps an `authorized_keys` file just like sshd; admin requests
# carry an ed25519 signature over a canonical string (purpose + timestamp + body hash),
# verified against an authorized key. First enrollment on an empty file is trust-on-
# first-use (claim a fresh node); afterwards adding a key must be signed by an enrolled
# one. Requires the `cryptography` package; absent it, key-auth is unavailable and the
# node falls back to token auth.

from __future__ import annotations

import base64
import hashlib
import os
import time
from pathlib import Path

PURPOSE_DEPLOY = "deploy"
PURPOSE_ENROLL = "enroll"
PURPOSE_RUN = "run"  # signs POST /run when the node enforces --require-run-auth
MAX_SKEW = 300  # seconds a signed request stays valid (replay window on a trusted LAN)


def available() -> bool:
    try:
        import cryptography  # noqa: F401

        return True
    except Exception:
        return False


def state_dir() -> Path:
    d = Path(os.path.expanduser("~/.urirun-node"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def authorized_keys_path() -> Path:
    return state_dir() / "authorized_keys"


def _normalize(openssh: str) -> str:
    """`type base64` without the trailing comment, for set-membership comparison."""
    parts = openssh.split()
    return " ".join(parts[:2]) if len(parts) >= 2 else openssh.strip()


def fingerprint(openssh: str) -> str:
    """OpenSSH-style SHA256 fingerprint of a public key line."""
    parts = openssh.split()
    if len(parts) < 2:
        raise ValueError("not an OpenSSH public key")
    raw = base64.b64decode(parts[1])
    return "SHA256:" + base64.b64encode(hashlib.sha256(raw).digest()).decode().rstrip("=")


def load_authorized() -> list[str]:
    p = authorized_keys_path()
    if not p.exists():
        return []
    return [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.startswith("#")]


def is_authorized(openssh: str) -> bool:
    target = _normalize(openssh)
    return any(_normalize(k) == target for k in load_authorized())


def add_authorized(openssh: str) -> dict:
    openssh = openssh.strip()
    fp = fingerprint(openssh)  # also validates the line
    if not is_authorized(openssh):
        path = authorized_keys_path()
        with path.open("a", encoding="utf-8") as f:
            f.write(openssh + "\n")
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
    return {"fingerprint": fp, "count": len(load_authorized())}


def _canonical(purpose: str, ts: str, body: bytes) -> bytes:
    return f"urirun:{purpose}:{ts}:{hashlib.sha256(body or b'').hexdigest()}".encode("utf-8")


def public_openssh(identity_priv_path: str) -> str:
    """Derive the OpenSSH public key string from a private key file."""
    from cryptography.hazmat.primitives.serialization import (
        Encoding, PublicFormat, load_ssh_private_key)

    key = load_ssh_private_key(Path(identity_priv_path).read_bytes(), password=None)
    return key.public_key().public_bytes(Encoding.OpenSSH, PublicFormat.OpenSSH).decode("utf-8")


def sign(identity_priv_path: str, purpose: str, body: bytes, ts: str | None = None) -> dict:
    """Sign a request with an SSH private key. Returns the headers to attach."""
    from cryptography.hazmat.primitives.serialization import (
        Encoding, PublicFormat, load_ssh_private_key)

    key = load_ssh_private_key(Path(identity_priv_path).read_bytes(), password=None)
    ts = ts or str(int(time.time()))
    sig = key.sign(_canonical(purpose, ts, body))
    pub = key.public_key().public_bytes(Encoding.OpenSSH, PublicFormat.OpenSSH).decode("utf-8")
    return {"X-Urirun-Key": pub, "X-Urirun-Sig": base64.b64encode(sig).decode("utf-8"),
            "X-Urirun-Date": ts}


def verify(openssh: str, sig_b64: str, purpose: str, ts: str, body: bytes) -> bool:
    try:
        if abs(int(time.time()) - int(ts)) > MAX_SKEW:
            return False
        from cryptography.hazmat.primitives.serialization import load_ssh_public_key

        load_ssh_public_key(openssh.encode("utf-8")).verify(
            base64.b64decode(sig_b64), _canonical(purpose, ts, body))
        return True
    except Exception:
        return False


def verify_request(headers, body: bytes, purpose: str) -> bool:
    """Validate the X-Urirun-Key/Sig/Date headers against an authorized key."""
    key = headers.get("X-Urirun-Key")
    sig = headers.get("X-Urirun-Sig")
    ts = headers.get("X-Urirun-Date")
    if not (key and sig and ts and is_authorized(key)):
        return False
    return verify(key, sig, purpose, ts, body)
