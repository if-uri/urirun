# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""secret:// — address credentials by *reference*, never by value.

A URI carries a reference to a secret (``secret://keyring/ksef/{nip}``,
``getv://OPENROUTER_API_KEY``); the value is resolved **lazily, only in
``--execute``**, behind a deny-by-default policy, and injected at the executor
boundary (env / header / stdin). Resolved values are wrapped in ``SecretStr`` so
every serialized surface (registry, route table, error store, logs, MCP/A2A)
prints ``****`` instead of the secret.

Providers: ``env`` / ``getv`` (process env), ``dotenv`` (a .env file), ``keyring``
(OS credential store), ``vault`` (HashiCorp Vault KV v2) and ``oauth`` (a cached
access token with refresh). ``browser`` delegates acquisition to a registered
connector only after a standing AQL access contract grants discover/acquire/use.
"""

from __future__ import annotations

import fnmatch
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

SECRET_PLACEHOLDER = re.compile(r"\{(secret|getv):([^{}]*)\}")


class SecretStr:
    """An opaque secret value. ``str``/``repr``/JSON show ``****``; ``reveal()``
    returns the plaintext (call only at the injection boundary)."""

    __slots__ = ("_value", "_ref", "_metadata")

    def __init__(self, value: str | None, ref: str, metadata: dict | None = None):
        self._value = value
        self._ref = ref
        self._metadata = dict(metadata or {})

    def reveal(self) -> str:
        if self._value is None:
            raise ValueError(f"secret not resolved (dry-run): {self._ref}")
        return self._value

    @property
    def ref(self) -> str:
        return self._ref

    @property
    def credential_handle(self) -> str:
        return str(self._metadata.get("credential_handle") or "")

    @property
    def metadata(self) -> dict:
        return dict(self._metadata)

    def __str__(self) -> str:  # noqa: D105
        return "****"

    def __repr__(self) -> str:  # noqa: D105
        handle = self.credential_handle
        suffix = f", credential_handle={handle!r}" if handle else ""
        return f"SecretStr(ref={self._ref!r}{suffix})"

    def __bool__(self) -> bool:  # noqa: D105
        return self._value is not None


def redact(value: Any) -> Any:
    """Recursively replace SecretStr (and obvious secret refs) with ``****``."""
    if isinstance(value, SecretStr):
        return "****"
    if isinstance(value, dict):
        return {key: redact(val) for key, val in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


# --- providers -------------------------------------------------------------


@dataclass(frozen=True)
class BrowserAcquisitionRequest:
    acquirer: str
    target: str
    field: str
    actor: str
    environment: str
    environment_fingerprint: str


@dataclass(frozen=True)
class BrowserCredential:
    value: str
    credential_handle: str
    provider: str
    scopes: tuple[str, ...] = ()
    expires_at: str | None = None
    refreshable: bool = False
    delegatable: bool = False
    secret_value_visible: bool = False


class BrowserAcquisitionError(OSError):
    """A typed missing/invalid delegated browser acquisition route."""

    def __init__(self, code: str, detail: str = ""):
        self.code = code
        super().__init__(f"{code}{': ' + detail if detail else ''}")


BrowserAcquirer = Callable[[BrowserAcquisitionRequest], BrowserCredential]
_BROWSER_ACQUIRERS: dict[str, BrowserAcquirer] = {}


def register_browser_acquirer(name: str, acquirer: BrowserAcquirer) -> None:
    """Register a connector-owned acquisition bridge for development/runtime use."""
    if not re.fullmatch(r"[a-zA-Z0-9_.-]+", name):
        raise ValueError("invalid browser acquirer name")
    _BROWSER_ACQUIRERS[name] = acquirer


def unregister_browser_acquirer(name: str) -> None:
    _BROWSER_ACQUIRERS.pop(name, None)

def _provider_env(location: str, field: str | None) -> str:
    name = field or location
    if name not in os.environ:
        raise KeyError(f"env var not set: {name}")
    return os.environ[name]


def _provider_dotenv(location: str, field: str | None) -> str:
    if not field:
        raise ValueError("dotenv secret needs a #NAME fragment")
    for line in Path(location).expanduser().read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        if key.strip() == field:
            return val.strip().strip('"').strip("'")
    raise KeyError(f"{field} not found in {location}")


def _provider_keyring(location: str, field: str | None) -> str:
    try:
        import keyring
    except ImportError as exc:
        raise RuntimeError("keyring provider needs the 'keyring' package (pip install keyring)") from exc
    service, _, account = location.partition("/")
    value = keyring.get_password(service, account or field or "")
    if value is None:
        raise KeyError(f"no keyring entry for {service}/{account}")
    return value


def _provider_vault(location: str, field: str | None) -> str:
    """``secret://vault/<mount>/<path>#<field>`` — HashiCorp Vault KV v2.

    Reads ``$VAULT_ADDR/v1/<mount>/data/<path>`` with ``X-Vault-Token``. Sensitive
    by nature: gate it behind ``--secret-allow`` (and confirm) per policy."""
    import json
    import urllib.request

    addr, token = os.environ.get("VAULT_ADDR"), os.environ.get("VAULT_TOKEN")
    if not addr or not token:
        raise RuntimeError("vault provider needs VAULT_ADDR and VAULT_TOKEN")
    if not field:
        raise ValueError("vault secret needs a #field fragment")
    mount, _, path = location.partition("/")
    request = urllib.request.Request(f"{addr.rstrip('/')}/v1/{mount}/data/{path}",
                                     headers={"X-Vault-Token": token})
    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    data = ((payload.get("data") or {}).get("data")) or {}
    if field not in data:
        raise KeyError(f"{field} not in vault {mount}/{path}")
    return str(data[field])


def _provider_oauth(location: str, field: str | None) -> str:
    """``secret://oauth/<provider>/<account>`` — a cached OAuth access token, with
    refresh. The token bundle lives in the keyring under ``oauth:<provider>`` /
    ``<account>`` as JSON (``access_token``, ``refresh_token``, ``expires_at``,
    ``token_url``, optional ``client_id``/``client_secret``); refreshes in place
    when within 60s of expiry."""
    import json
    import time
    import urllib.parse
    import urllib.request

    try:
        import keyring
    except ImportError as exc:
        raise RuntimeError("oauth provider needs the 'keyring' package (pip install keyring)") from exc
    provider, _, account = location.partition("/")
    raw = keyring.get_password(f"oauth:{provider}", account)
    if not raw:
        raise KeyError(f"no oauth entry for {provider}/{account}")
    entry = json.loads(raw)
    if time.time() < float(entry.get("expires_at", 0)) - 60:
        return str(entry["access_token"])
    form = {"grant_type": "refresh_token", "refresh_token": entry["refresh_token"]}
    for key in ("client_id", "client_secret"):
        if entry.get(key):
            form[key] = entry[key]
    request = urllib.request.Request(entry["token_url"], data=urllib.parse.urlencode(form).encode(),
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(request, timeout=15) as response:
        refreshed = json.loads(response.read().decode("utf-8"))
    entry["access_token"] = refreshed["access_token"]
    if refreshed.get("refresh_token"):
        entry["refresh_token"] = refreshed["refresh_token"]
    entry["expires_at"] = time.time() + float(refreshed.get("expires_in", 3600))
    keyring.set_password(f"oauth:{provider}", account, json.dumps(entry))
    return str(entry["access_token"])


def _provider_browser(location: str, field: str | None, access_context: dict | None) -> BrowserCredential:
    """Delegate browser-assisted acquisition under a standing AQL contract."""
    from urirun_runtime import access as _access

    acquirer_name, separator, target = location.partition("/")
    if not separator or not target or not field:
        raise BrowserAcquisitionError(
            "BROWSER_ACQUISITION_REFERENCE_INVALID",
            "expected secret://browser/<acquirer>/<target>#<field>",
        )
    context = dict(access_context or {})
    requirement = {
        "schema_version": "access.requirement.v1",
        "actor": context.get("actor", ""),
        "environment": context.get("environment", ""),
        "environment_fingerprint": context.get("environment_fingerprint", ""),
        "capability": "credential.acquire.browser",
        "provider": "browser",
        "target": target,
        "requested_actions": ["ALLOW_DISCOVER", "ALLOW_ACQUIRE", "ALLOW_USE"],
        "effect": "credential_acquisition",
        "estimated_cost": 0,
        "max_credential_ttl_seconds": int(context.get("max_credential_ttl_seconds") or 1800),
    }
    _access.require_access(requirement, context.get("contract"))
    acquirer = _BROWSER_ACQUIRERS.get(acquirer_name)
    if acquirer is None:
        raise BrowserAcquisitionError(
            "AUTO_ACQUISITION_ROUTE_MISSING",
            f"browser acquirer {acquirer_name!r} is not registered",
        )
    acquired = acquirer(
        BrowserAcquisitionRequest(
            acquirer=acquirer_name,
            target=target,
            field=field,
            actor=requirement["actor"],
            environment=requirement["environment"],
            environment_fingerprint=requirement["environment_fingerprint"],
        )
    )
    if not isinstance(acquired, BrowserCredential):
        raise BrowserAcquisitionError("BROWSER_ACQUISITION_CONTRACT_INVALID")
    if not acquired.value or not acquired.credential_handle:
        raise BrowserAcquisitionError("BROWSER_ACQUISITION_EMPTY")
    if acquired.secret_value_visible:
        raise BrowserAcquisitionError("BROWSER_ACQUISITION_SECRET_VISIBILITY_INVALID")
    return acquired


_PROVIDERS = {
    "env": _provider_env, "getv": _provider_env, "dotenv": _provider_dotenv, "keyring": _provider_keyring,
    "vault": _provider_vault, "oauth": _provider_oauth,
}


def _parse_ref(ref: str) -> tuple[str, str, str | None]:
    if ref.startswith("getv://"):
        return ("env", ref[len("getv://"):], None)
    if not ref.startswith("secret://"):
        raise ValueError(f"not a secret reference: {ref}")
    rest = ref[len("secret://"):]
    location, _, field = rest.partition("#")
    provider, _, loc = location.partition("/")
    return (provider, loc, field or None)


def allowed(ref: str, allow: list[str] | None) -> bool:
    """Deny-by-default: a secret is resolvable only if it matches the allow-list."""
    if not allow:
        return False
    return any(fnmatch.fnmatch(ref, pattern) for pattern in allow)


def resolve(
    ref: str,
    *,
    execute: bool,
    allow: list[str] | None = None,
    access: dict | None = None,
) -> SecretStr:
    if execute and not allowed(ref, allow):
        raise PermissionError(f"secret denied by policy (add it to --secret-allow): {ref}")
    if not execute:
        return SecretStr(None, ref)  # dry-run: reference only, never the value
    provider, location, field = _parse_ref(ref)
    if provider == "browser":
        acquired = _provider_browser(location, field, access)
        return SecretStr(
            acquired.value,
            ref,
            {
                "credential_handle": acquired.credential_handle,
                "provider": acquired.provider,
                "scopes": list(acquired.scopes),
                "expires_at": acquired.expires_at,
                "refreshable": acquired.refreshable,
                "delegatable": acquired.delegatable,
                "secret_value_visible": acquired.secret_value_visible,
            },
        )
    func = _PROVIDERS.get(provider)
    if func is None:
        raise ValueError(f"unknown secret provider '{provider}' in {ref}")
    return SecretStr(func(location, field), ref)


def fill_secrets(
    text: str,
    *,
    execute: bool,
    allow: list[str] | None = None,
    disabled: bool = False,
    access: dict | None = None,
) -> str:
    """Replace ``{secret:...}`` / ``{getv:...}`` in a string with the value
    (execute) or ``****`` (dry-run). Run payload templating first so nested
    ``{param}`` slots are already filled.

    ``disabled`` is the node guard: when set, any secret reference is refused
    outright (a remote ``node serve`` must not resolve the host's local secrets
    unless its operator explicitly opted in)."""
    def repl(match: re.Match) -> str:
        ref = f"{match.group(1)}://{match.group(2)}"
        if not execute:
            return "****"
        if disabled:
            raise PermissionError(f"secret resolution disabled here (node guard): {ref}")
        return resolve(ref, execute=True, allow=allow, access=access).reveal()

    return SECRET_PLACEHOLDER.sub(repl, str(text))


def has_secret(text: str) -> bool:
    return bool(SECRET_PLACEHOLDER.search(str(text)))


def resolve_secret(value: str, secret_allow: str | list[str] | None = "") -> str:
    """Resolve a credential parameter that may be a secret *reference*.

    The one helper connectors use to honour the secrets layer for a credential they receive
    as a function/route argument (the runtime only auto-injects into ``fetch`` adapters, not
    local-function handlers). ``value`` may be:

    * a literal credential -> returned unchanged;
    * a ``{getv:NAME}`` / ``{secret:provider/loc#field}`` placeholder -> ``fill_secrets``;
    * a bare ``getv://NAME`` / ``secret://...`` reference -> ``resolve(...).reveal()``.

    References resolve under ``secret_allow`` (a glob list, or comma/space-separated string),
    deny-by-default (an unlisted reference raises ``PermissionError``). An empty ``value``
    returns ``''`` so callers can fall back to an ambient default.
    """
    value = (value or "").strip()
    if not value:
        return ""
    if isinstance(secret_allow, str):
        allow = [pattern for pattern in re.split(r"[,\s]+", secret_allow) if pattern]
    else:
        allow = list(secret_allow or [])
    if has_secret(value):
        return fill_secrets(value, execute=True, allow=allow)
    if value.startswith(("secret://", "getv://")):
        return resolve(value, execute=True, allow=allow).reveal()
    return value
