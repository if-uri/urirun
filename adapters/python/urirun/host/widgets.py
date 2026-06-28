from __future__ import annotations

from urirun_widgets.render import (
    scanner_stream_summary,
    select_service_view,
    service_widget_summary,
)


def query_value(query: dict[str, list[str]], name: str, default: str | None = None) -> str | None:
    values = query.get(name)
    return values[0] if values else default
