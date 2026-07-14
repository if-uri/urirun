# Author: Tom Sapletta · Part of the ifURI solution.
"""where:// — „gdzie jestem / co robię": tożsamość maszyny + żywy zrzut ekranu (urivision).

Odpowiada na pytanie operatora „na której maszynie to się dzieje i co jest na ekranie" — łączy
strukturę (node/hostname/display/okna) z warstwą wizualną (capture) i HTML-overlay okien.
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any


def _node_url(node: str) -> str:
    return {"laptop": "http://192.168.188.201:8765"}.get(node, "")


def _invoke(uri: str, node: str, payload: dict | None = None, timeout: float = 20.0) -> dict:
    """Wywołaj URI BEZPOŚREDNIO na węźle przez /run (payload=). NIE przez dashboard /api/uri/invoke —
    ten fallbackuje na HOST (nvidia) i pokazywał zły ekran. /run trafia na realny węzeł."""
    url = _node_url(node)
    target = (url + "/run") if url else "http://127.0.0.1:8797/api/uri/invoke"
    body = json.dumps({"uri": uri, "payload": payload or {}}).encode()  # node /run: 'payload', nie 'args'
    req = urllib.request.Request(target, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
            d = json.loads(r.read().decode())
            res = d.get("result") or d
            if isinstance(res, dict) and isinstance(res.get("value"), dict):
                return res["value"]  # /run owija wynik handlera w result.value
            return res if isinstance(res, dict) else {"ok": False, "raw": res}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def _host_identity() -> dict:
    import os
    return {"hostname": os.uname().nodename, "platform": os.uname().sysname}


_HOST_NODES = {"nvidia", "host", "local", "localhost", "self"}


def _local_where(node: str, capture: bool) -> dict[str, Any]:
    """HOST (nvidia): urirun widzi WŁASNY komputer — capture in-process (mutter-screencast),
    nie zdalny węzeł. Bezpieczne (tylko odczyt). To domyka 'urirun widzi nvidia'."""
    out: dict[str, Any] = {"ok": True, "node": node, "host": _host_identity(), "at": None,
                           "node_identity": {"name": node, "kind": "host-local"}}
    try:
        from urirun_connector_kvm import core as kvm
        out["display"] = kvm.display_info() if hasattr(kvm, "display_info") else {}
        wl = kvm.window_list() if hasattr(kvm, "window_list") else {}
        out["windows"] = wl.get("windows") or []
        out["foreground"] = next((w.get("title") for w in out["windows"] if w.get("active") or w.get("focused")),
                                 (out["windows"][0].get("title") if out["windows"] else None))
        if capture:
            cap = kvm.capture(base64=True, max_width=1100)
            b64 = cap.get("pngBase64") or cap.get("base64") or ""
            out["capture"] = {"ok": cap.get("ok"), "path": cap.get("path", ""), "from_node": False,
                              "via": cap.get("via"), "url": ("data:image/png;base64," + b64) if b64 else None}
    except Exception as exc:  # noqa: BLE001
        out["capture"] = {"ok": False, "error": str(exc)}
    out["consistency_note"] = "źródło: KVM capture LOKALNIE na hoście (mutter-screencast, in-process)"
    return out


def where_am_i(node: str = "laptop", capture: bool = True) -> dict[str, Any]:
    """Zbierz: tożsamość węzła, display, okna, foreground i (opcjonalnie) świeży zrzut ekranu."""
    if node.lower() in _HOST_NODES:  # urirun widzi WŁASNY host (nvidia), nie tylko zdalne węzły
        return _local_where(node, capture)
    out: dict[str, Any] = {"ok": True, "node": node, "host": _host_identity(), "at": None}
    # tożsamość zdalnego węzła (bezpośrednio z jego /health — nie przez routing)
    url = _node_url(node)
    if url:
        try:
            with urllib.request.urlopen(url + "/health", timeout=6) as r:  # noqa: S310
                h = json.loads(r.read().decode())
                out["node_identity"] = {"name": h.get("name"), "kind": h.get("kind"),
                                        "version": h.get("version"), "routes": h.get("routeCount")}
        except Exception as exc:  # noqa: BLE001
            out["node_identity"] = {"error": str(exc)}
    out["display"] = _invoke(f"kvm://{node}/display/query/info", node)
    wl = _invoke(f"kvm://{node}/window/query/list", node, {"all": True})
    out["windows"] = wl.get("windows") or []
    out["foreground"] = next((w.get("title") for w in out["windows"] if w.get("active") or w.get("focused")),
                             (out["windows"][0].get("title") if out["windows"] else None))
    if capture:
        # base64 z WĘZŁA (plik jest na węźle, nie hoście) → data-URI, koniec host-fallbacku
        cap = _invoke(f"kvm://{node}/screen/query/capture", node, {"base64": True, "max_width": 1100}, timeout=30)
        b64 = cap.get("pngBase64") or cap.get("base64") or ""  # kvm zwraca 'pngBase64'
        out["capture"] = {"ok": cap.get("ok"), "path": cap.get("path", ""), "from_node": bool(_node_url(node)),
                          "url": ("data:image/png;base64," + b64) if b64 else None}
    out["consistency_note"] = "źródło: /run bezpośrednio na węźle (nie dashboard-fallback)"
    return out


def shot_bytes(path: str) -> tuple[bytes, str] | None:
    """Zwróć bajty zrzutu (tylko z katalogu artefaktów — bezpieczeństwo ścieżki)."""
    safe_root = str(Path("~/.urirun/artifacts").expanduser())
    rp = str(Path(path).expanduser())
    if not rp.startswith(safe_root) or not Path(rp).is_file():
        return None
    return Path(rp).read_bytes(), "image/png"
