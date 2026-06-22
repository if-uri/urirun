# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Process-streaming hook, shared low in the stack so both the node (mesh) and the runtime
# executors (v1._run_process) can use it without an import cycle. The node binds a sink
# around a /run; handlers — or the subprocess reader — call `emit({...})` to push
# incremental progress to that run's live stream. A no-op when nothing is bound.
from __future__ import annotations

import contextvars
from typing import Any, Callable

_SINK: contextvars.ContextVar = contextvars.ContextVar("urirun_progress_sink", default=None)


def bind(sink: Callable[[dict], None]):
    """Bind a progress sink for the current run; returns a token for reset()."""
    return _SINK.set(sink)


def reset(token) -> None:
    try:
        _SINK.reset(token)
    except Exception:  # noqa: BLE001 - reset across contexts is best-effort
        pass


def active() -> bool:
    return _SINK.get() is not None


def emit(event: dict) -> bool:
    """Push a progress event to the bound sink. Returns True if a sink was bound."""
    sink = _SINK.get()
    if sink is None:
        return False
    try:
        sink(event)
    except Exception:  # noqa: BLE001 - a streaming sink must never break the run
        pass
    return True
