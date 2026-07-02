from __future__ import annotations

import base64
import time
from pathlib import Path

import urirun


SCREEN_CAPTURE_URI = "kvm://host/screen/query/capture"


def _default_output_path() -> Path:
    root = Path.home() / ".urirun" / "artifacts" / "screenshots"
    root.mkdir(parents=True, exist_ok=True)
    return root / f"host-screen-{int(time.time() * 1000)}.png"


def _capture_with_pillow(path: Path) -> None:
    from PIL import ImageGrab  # type: ignore

    image = ImageGrab.grab()
    image.save(path, format="PNG")


@urirun.handler(
    SCREEN_CAPTURE_URI,
    meta={
        "label": "Built-in host screenshot",
        "connector": "urirun-host",
        "contract": {
            "artifact": {"kind": "screenshot", "mediaType": "image/png"},
        },
    },
)
def capture_screen(output: str = "", base64: bool = False) -> dict:
    path = Path(output).expanduser() if output else _default_output_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        _capture_with_pillow(path)
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": str(exc),
            "backend": "pillow-imagegrab",
            "message": "Built-in host screenshot backend is unavailable.",
        }
    result = {
        "ok": True,
        "path": str(path),
        "kind": "screenshot",
        "mediaType": "image/png",
        "backend": "pillow-imagegrab",
    }
    if base64:
        result["bytes_b64"] = base64_encode(path)
    return result


def base64_encode(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def route() -> dict:
    return {
        "uri": SCREEN_CAPTURE_URI,
        "kind": "query",
        "title": "Built-in host screenshot",
        "source": "urirun host built-in",
        "adapter": "local-function",
        "inputSchema": {
            "type": "object",
            "properties": {
                "output": {"type": "string"},
                "base64": {"type": "boolean", "default": False},
            },
            "additionalProperties": False,
        },
        "meta": {"contract": {"artifact": {"kind": "screenshot", "mediaType": "image/png"}}},
        "safe": True,
        "layer": "connector",
        "node": "host",
        "target": "host",
    }


def bindings() -> dict:
    return {"version": "urirun.bindings.v2", "bindings": {SCREEN_CAPTURE_URI: route()}}
