"""Provision the deterministic security-probe image with one authorized admin."""

from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat
from urirun.node import keyauth


identity = Path("/app/admin_ed25519")
identity.write_bytes(
    Ed25519PrivateKey.generate().private_bytes(
        Encoding.PEM,
        PrivateFormat.OpenSSH,
        NoEncryption(),
    )
)
identity.chmod(0o600)
keyauth.add_authorized(keyauth.public_openssh(str(identity)))
