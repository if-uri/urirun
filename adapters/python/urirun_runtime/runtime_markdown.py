# Author: Tom Sapletta · Part of the ifURI solution.
"""Załaduj cały kontekst urirun-llm-runtime jako markdown dla LLM."""
from __future__ import annotations

import os
from pathlib import Path

_DEFAULT_ROOT = Path(__file__).resolve().parents[4] / "urirun-llm-runtime"

# Kolejność: spec → semantyka → przykłady → reszta
_BUNDLE_FILES = [
    "README.md",
    "docs/llm/README.md",
    "docs/llm/runtime_semantics.md",
    "docs/llm/process_contract.md",
    "docs/llm/if_uri_integration.md",
    "docs/llm/environment_topology.yaml",
    "docs/llm/route_catalog.yaml",
    "docs/llm/process_schema.json",
    "docs/openapi.yaml",
    "docs/markpact_marksync_process_examples.md",
    "docs/markpact_marksync_prompt.md",
    "runtime/README.md",
]


def runtime_root() -> Path:
    raw = os.environ.get("URIRUN_LLM_RUNTIME_ROOT", "")
    if raw:
        p = Path(raw).expanduser()
        if p.is_dir():
            return p
    sibling = _DEFAULT_ROOT
    if sibling.is_dir():
        return sibling
    return Path("/home/tom/github/if-uri/urirun-llm-runtime")


def load_runtime_markdown_bundle(*, max_chars: int = 48000) -> str:
    """Pełny pakiet markdown urirun-llm-runtime (dla system prompt LLM)."""
    root = runtime_root()
    parts: list[str] = [
        f"# URI RUNTIME BUNDLE\n",
        f"Source: `{root}`\n",
        "---\n",
    ]
    for rel in _BUNDLE_FILES:
        path = root / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8").strip()
        except Exception:
            continue
        parts.append(f"\n\n## FILE: `{rel}`\n\n{text}\n")
    out = "\n".join(parts)
    if len(out) > max_chars:
        return out[: max_chars - 120] + "\n\n…(bundle truncated; set URIRUN_LLM_RUNTIME_ROOT)\n"
    return out
