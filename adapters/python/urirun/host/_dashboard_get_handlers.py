# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""GET-path sub-handlers for the host dashboard.

Extracted from host_dashboard.py to keep the main module under 1800 lines.
This module is only ever imported lazily (from inside _handle_get()), so
``host_dashboard`` is fully initialised in sys.modules when the module-level
imports below execute — there is no circular import.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from urllib.parse import parse_qs, unquote

from urirun.node.mesh import _sse_initial_cursor, _sse_event_matches, _sse_frame
from .twin_bridge import TWIN_EVENT_HUB
from .dashboard_http import (
    _json_response, _html_response, _asset_response,
    _js_sdk_response, _file_response, _remote_file_response,
)
from .html_templates import SCANNER_HTML, NODE_TYPES_DOC_HTML
from .android_node import phone_web_nodes
from .dashboard_api import _first
# scanner_net / scanner_bridge are shims to urirun_scanner (needs the standalone
# urirun-connector-scanner, not on PyPI). Import them LAZILY inside the two handlers that use
# them so `import urirun.host.host_dashboard` stays clean on a fresh `pip install urirun`
# (guarded by the release smoke-test).
# Pulled from host_dashboard lazily — safe because this module is only imported
# after host_dashboard is fully loaded (from inside _handle_get() at request time).
from . import host_dashboard as _hd


def _docs_nodes_html() -> str:
    return _hd._docs_nodes_html()


def _standalone_service_html(project: str, query: dict) -> str:
    return _hd._standalone_service_html(project, query)


def _standalone_service_svg(project: str, query: dict) -> str:
    return _hd._standalone_service_svg(project, query)


def _scanner_bridge_deps():
    return _hd._scanner_bridge_deps()


def _sse_parse_filters(params: dict) -> tuple[set, set]:
    schemes = {s for s in params.get("scheme", "").split(",") if s}
    runs = {r for r in params.get("run", "").split(",") if r}
    return schemes, runs


def _sse_replay_history(wfile, hub, last_id: str, schemes: set, runs: set) -> None:
    for ev in hub.replay_since(last_id):
        if _sse_event_matches(ev, schemes, runs):
            wfile.write(_sse_frame(ev))


def _sse_drive_stream(wfile, q, schemes: set, runs: set) -> None:
    import queue
    while True:
        try:
            ev = q.get(timeout=15)
        except queue.Empty:
            wfile.write(b": keep-alive\n\n")
            wfile.flush()
            continue
        if _sse_event_matches(ev, schemes, runs):
            wfile.write(_sse_frame(ev))
            wfile.flush()


def _handle_events_sse(handler, parsed):
    params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    schemes, runs = _sse_parse_filters(params)
    last_id = _sse_initial_cursor(TWIN_EVENT_HUB, params, handler.headers)
    try:
        handler.send_response(200)
        handler.send_header("Content-Type", "text/event-stream")
        handler.send_header("Cache-Control", "no-cache")
        handler.send_header("Connection", "keep-alive")
        handler.send_header("Access-Control-Allow-Origin", "*")
        handler.end_headers()
        handler.wfile.write(b": connected\n\n")
        _sse_replay_history(handler.wfile, TWIN_EVENT_HUB, last_id, schemes, runs)
        handler.wfile.flush()
    except (BrokenPipeError, ConnectionResetError, OSError):
        return
    q = TWIN_EVENT_HUB.subscribe()
    try:
        _sse_drive_stream(handler.wfile, q, schemes, runs)
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass
    finally:
        TWIN_EVENT_HUB.unsubscribe(q)


def _handle_get_static(handler, parsed, project) -> bool:
    if parsed.path == "/health":
        _json_response(handler, 200, {"ok": True})
        return True
    if parsed.path == "/events":
        _handle_events_sse(handler, parsed)
        return True
    if parsed.path in {"/", "/index.html"}:
        _html_response(handler)
        return True
    _static = {"dashboard.js": "application/javascript", "scanner.js": "application/javascript",
               "dashboard.css": "text/css"}
    if parsed.path.lstrip("/") in _static:
        # Page JS/CSS extracted from the INDEX_HTML / SCANNER_HTML raw strings into real .js/.css
        # files next to this module, served fresh per request (edits load without a service restart).
        # Whitelist by exact basename — no user-controlled path, so no traversal.
        name = parsed.path.lstrip("/")
        f = Path(__file__).parent / name
        _asset_response(handler, f.read_bytes(), f"{_static[name]}; charset=utf-8")
        return True
    if parsed.path == "/favicon.ico":
        handler.send_response(204)
        handler.send_header("Cache-Control", "public, max-age=86400")
        handler.end_headers()
        return True
    if parsed.path == "/scanner":
        _html_response(handler, SCANNER_HTML)
        return True
    if parsed.path in {"/docs/nodes", "/docs/nodes/"}:
        _html_response(handler, NODE_TYPES_DOC_HTML)
        return True
    if parsed.path in {"/docs/node-types", "/docs/node-types/"}:
        _html_response(handler, _docs_nodes_html())
        return True
    if parsed.path in {"/twin", "/twin/"}:
        widget = Path(__file__).parent / "twin_monitor_widget.html"
        _asset_response(handler, widget.read_bytes(), "text/html; charset=utf-8")
        return True
    return False


def _handle_get_nodes_qr(handler, parsed) -> None:
    target = _first(parse_qs(parsed.query), "url") or ""
    if not target:
        _json_response(handler, 400, {"ok": False, "error": "url is required"})
        return
    try:
        digest = hashlib.sha256(target.encode("utf-8")).hexdigest()[:16]
        root = Path(os.environ.get("URIRUN_DASHBOARD_QR_DIR", "~/.urirun/host-dashboard/qr")).expanduser()
        qr_path = root / f"endpoint-{digest}.png"
        if not qr_path.exists():
            from .scanner_net import _write_qr_png  # lazy: keep scanner out of the import chain
            _write_qr_png(target, qr_path)
        _asset_response(handler, qr_path.read_bytes(), "image/png")
    except Exception as exc:  # noqa: BLE001
        _json_response(handler, 500, {"ok": False, "error": str(exc)})


def _work_view_html(project) -> str:
    """Render the ONE view of autonomous work (view connector) — legible surface for background
    goal/koru/nxdo activity. Graceful: a plain notice if the view connector isn't installed."""
    try:
        from urirun_connector_view.core import _state
        from urirun_connector_view.render import render_html
        return render_html(_state(str(project), 8))
    except Exception as exc:  # noqa: BLE001 - view connector optional; never break the dashboard
        return ("<!doctype html><meta charset=utf-8><title>Work view</title>"
                "<body style='font:14px system-ui;padding:40px;color:#556'>"
                "<h1>Work view unavailable</h1><p>Install <code>urirun-connector-view</code> to see "
                f"the autonomous-work view here.</p><pre>{exc}</pre>")


def _handle_get_services(handler, parsed, project) -> bool:
    if parsed.path == "/work":
        _html_response(handler, _work_view_html(project))
        return True
    if parsed.path == "/services/view":
        _html_response(handler, _standalone_service_html(project, parse_qs(parsed.query)))
        return True
    if parsed.path == "/services/view.svg":
        _asset_response(handler, _standalone_service_svg(project, parse_qs(parsed.query)).encode("utf-8"),
                        "image/svg+xml; charset=utf-8")
        return True
    if parsed.path == "/assets/urirun.js":
        _js_sdk_response(handler, project)
        return True
    return False


def _handle_get_api_nodes(handler, parsed, query) -> bool:
    if parsed.path == "/api/nodes/phone-web":
        _json_response(handler, 200, phone_web_nodes(query))
        return True
    if parsed.path == "/api/nodes/qr":
        _handle_get_nodes_qr(handler, parsed)
        return True
    return False


def _handle_get_file_api(handler, parsed, query, project) -> bool:
    if parsed.path == "/api/file":
        path = _first(query, "path")
        if not path:
            _json_response(handler, 400, {"ok": False, "error": "path is required"})
            return True
        _file_response(handler, unquote(path), project)
        return True
    if parsed.path == "/api/file/remote":
        node_url = unquote(_first(query, "nodeUrl") or "")
        path = unquote(_first(query, "path") or "")
        if not node_url or not path:
            _json_response(handler, 400, {"ok": False, "error": "nodeUrl and path are required"})
            return True
        _remote_file_response(handler, node_url, path)
        return True
    return False


def _handle_get_work_console(handler, parsed, project, query) -> bool:
    """Operator-console reads: confirm queue, live URI activity, ticket detail (popup)."""
    if parsed.path == "/api/work/ops":
        from .work_console import list_ops  # operations awaiting the operator's confirmation
        try:
            _json_response(handler, 200, {"ok": True, "ops": list_ops()})
        except Exception as exc:  # noqa: BLE001
            _json_response(handler, 200, {"ok": False, "error": str(exc)})
        return True
    if parsed.path == "/api/work/uri-log":
        from .work_console import uri_activity  # which URI processes urirun is running, live
        _json_response(handler, 200,
                       {"ok": True, "events": uri_activity(int(_first(query, "limit", "40") or 40))})
        return True
    if parsed.path == "/api/work/koru-log":
        from .work_console import koru_log_tail  # realne komendy koru na żywo (tail logu pętli)
        try:
            _json_response(handler, 200, {"ok": True, **koru_log_tail(int(_first(query, "tail", "150") or 150))})
        except Exception as exc:  # noqa: BLE001
            _json_response(handler, 200, {"ok": False, "error": str(exc)})
        return True
    if parsed.path == "/api/work/ticket/detail":
        from . import ticket_meta  # full process list + editable meta for the ticket popup
        try:
            _json_response(handler, 200, ticket_meta.ticket_detail(str(project), _first(query, "id", "") or ""))
        except Exception as exc:  # noqa: BLE001
            _json_response(handler, 200, {"ok": False, "error": str(exc)})
        return True
    return _handle_get_work_cron(handler, parsed, query)


def _handle_get_work_cron(handler, parsed, query) -> bool:
    """cron:// connector bridge: entries + upcoming-runs calendar, and iCalendar/CSV export."""
    if parsed.path == "/api/work/cron":
        from . import cron_admin
        _json_response(handler, 200, cron_admin.state())
        return True
    if parsed.path == "/api/work/cron/export":
        from . import cron_admin
        _json_response(handler, 200, cron_admin.export(_first(query, "fmt", "ics") or "ics",
                       id=_first(query, "id", "") or "", mode=_first(query, "mode", "rrule") or "rrule",
                       days=int(_first(query, "days", "30") or 30)))
        return True
    if parsed.path == "/api/work/watchdog":
        from . import watchdog_admin  # watch:// bridge: wykryte zapętlenia + rootcause
        _json_response(handler, 200, watchdog_admin.detect())
        return True
    if parsed.path == "/api/work/system":
        from .work_queue import _project as _wq_project  # zdrowie SYSTEMU (kontrolery/środowisko)
        try:
            from urirun_connector_watchdog import core as _wd
            _json_response(handler, 200, {"ok": True, **_wd.system_analyze(_wq_project())})
        except Exception as exc:  # noqa: BLE001
            _json_response(handler, 200, {"ok": False, "error": str(exc), "findings": []})
        return True
    return _handle_get_work_diag(handler, parsed, query)


def _handle_get_work_where(handler, parsed) -> bool:
    """where:// (gdzie jestem) + registry (cross-node registry URI-procesów dla grounded orchestration)."""
    if parsed.path == "/api/work/registry":
        from . import registry_llm
        need = (parse_qs(parsed.query).get("need") or [""])[0]
        _json_response(handler, 200, registry_llm.find(need) if need else registry_llm.gather())
        return True
    if parsed.path == "/api/work/meta":
        from . import meta_graph  # wyższa warstwa: graf relacji ticketów + wniosków dla wnioskowania
        q = parse_qs(parsed.query)
        fmt = (q.get("format") or ["json"])[0]
        if fmt in ("triples", "ttl"):  # widok dla LLM-planera (fakt-na-linię + legenda)
            topic = (q.get("topic") or [""])[0]
            txt = meta_graph.grounding_for(topic) if topic else meta_graph.to_llm(meta_graph.graph())
            handler.send_response(200)
            handler.send_header("Content-Type", "text/plain; charset=utf-8")
            data = txt.encode("utf-8")
            handler.send_header("Content-Length", str(len(data)))
            handler.end_headers()
            handler.wfile.write(data)
            return True
        _json_response(handler, 200, {"ok": True, **meta_graph.graph()})
        return True
    from . import where_admin
    if parsed.path == "/api/work/where":
        node = (parse_qs(parsed.query).get("node") or ["laptop"])[0]
        _json_response(handler, 200, where_admin.where_am_i(node))
        return True
    path = (parse_qs(parsed.query).get("path") or [""])[0]
    got = where_admin.shot_bytes(path)
    if not got:
        _json_response(handler, 404, {"ok": False, "error": "shot not found"})
        return True
    data, ctype = got
    handler.send_response(200)
    handler.send_header("Content-Type", ctype)
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)
    return True


def _loop_plan_grounded() -> dict:
    """Plan pętli korekcyjnej + RELACYJNY GROUNDING (triple) per decyzja — nie płaska lista."""
    from .work_queue import _project as _wq_project
    try:
        from urirun_connector_loop import core as _loop
        from . import meta_graph
        plan = _loop.plan(_wq_project())
        for a in plan.get("actions", []):
            a["grounding"] = meta_graph.grounding_for(a.get("ticket", ""))
        return {"ok": True, **plan}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "actions": []}


def _handle_get_work_diag(handler, parsed, query) -> bool:
    """Warstwa diagnostyczno-autonomiczna: luki (gap://), pętla korekcyjna (loop://), executor
    (agent://) i samodokumentujące API. Wydzielone, by trzymać dispatcher pod bramką CC."""
    if parsed.path == "/api/work/gaps":
        from .work_queue import _project as _wq_project  # gap:// — jawne luki per-ticket + systemowe
        try:
            from urirun_connector_continuity import core as _gap
            _json_response(handler, 200, {"ok": True, **_gap.scan(_wq_project())})
        except Exception as exc:  # noqa: BLE001
            _json_response(handler, 200, {"ok": False, "error": str(exc), "tickets": []})
        return True
    if parsed.path == "/api/work/loop":
        _json_response(handler, 200, _loop_plan_grounded())
        return True
    if parsed.path == "/api/work/agents":
        from . import agent_admin  # agent:// bridge: dostępne narzędzia AI (executor)
        _json_response(handler, 200, agent_admin.tools())
        return True
    if parsed.path == "/api/work/assign":
        from .work_queue import _project as _wq_project  # multi-agent: runnable→agent (node+capability)
        try:
            from urirun_connector_loop import core as _loop
            _json_response(handler, 200, {"ok": True, **_loop.assign(_wq_project())})
        except Exception as exc:  # noqa: BLE001
            _json_response(handler, 200, {"ok": False, "error": str(exc), "assignments": []})
        return True
    if parsed.path == "/api/work/verify":
        from .work_queue import _project as _wq_project  # verify:// — done-validation postcondition
        try:
            from urirun_connector_verify import core as _vf
            _json_response(handler, 200, _vf.ticket_query_check(id=_first(query, "id", "") or "",
                                                               cwd=str(_wq_project())))
        except Exception as exc:  # noqa: BLE001
            _json_response(handler, 200, {"ok": False, "error": str(exc)})
        return True
    if parsed.path in ("/api/work/where", "/api/work/where/shot", "/api/work/registry", "/api/work/meta"):
        return _handle_get_work_where(handler, parsed)
    if parsed.path == "/api/work/signal":
        try:
            from urirun_connector_signal import core as _sig  # signal:// outbox (mock gdy brak signal-cli)
            _json_response(handler, 200, _sig.messages_query_list())
        except Exception as exc:  # noqa: BLE001
            _json_response(handler, 200, {"ok": False, "error": str(exc), "messages": []})
        return True
    if parsed.path == "/api/work/actions":
        from .work_api import catalog  # samodokumentujące API całej strony /work
        _json_response(handler, 200, catalog())
        return True
    return False


def _handle_get_work(handler, parsed, project, query) -> bool:
    """All /api/work/* read surfaces for the /work view (runs, confirm queue, URI activity,
    koru queue/continuity, debug). Split out of _handle_get_api to keep each dispatcher small."""
    if _handle_get_work_console(handler, parsed, project, query):
        return True
    if parsed.path == "/api/work/runs":
        from .work_runs import list_runs  # lazy, like the other optional surfaces
        _json_response(handler, 200,
                       {"ok": True, "runs": list_runs(tail_lines=int(_first(query, "tail", "120") or 120))})
        return True
    if parsed.path == "/api/work/debug":
        try:
            from urirun_connector_view.debug import state_full  # optional, like the work view
            _json_response(handler, 200, state_full(repo=str(project)))
        except Exception as exc:  # noqa: BLE001
            _json_response(handler, 200, {"ok": False, "error": f"debug surface unavailable: {exc}"})
        return True
    if parsed.path == "/api/work/queue":
        from .work_queue import queue_state  # koru loop status + planfile ticket queue
        try:
            _json_response(handler, 200, {"ok": True, **queue_state()})
        except Exception as exc:  # noqa: BLE001
            _json_response(handler, 200, {"ok": False, "error": str(exc)})
        return True
    if parsed.path == "/api/work/status":
        from .work_queue import work_status  # continuity verdict: OK / AT_RISK / STOPPED
        try:
            _json_response(handler, 200, {"ok": True, **work_status()})
        except Exception as exc:  # noqa: BLE001
            _json_response(handler, 200, {"ok": False, "error": str(exc)})
        return True
    return False


def _handle_get_api(handler, parsed, project, db) -> bool:
    query = parse_qs(parsed.query)
    if _handle_get_api_nodes(handler, parsed, query):
        return True
    if _handle_get_work(handler, parsed, project, query):
        return True
    if parsed.path == "/api/uri/event":
        from .scanner_bridge import uri_event as _uri_event_impl  # lazy: scanner off import chain
        _json_response(handler, 200, _uri_event_impl(_scanner_bridge_deps(), db, query))
        return True
    if parsed.path == "/api/page/actions/poll":
        from .scanner_bridge import page_action_poll as _page_action_poll_impl  # lazy
        _json_response(handler, 200,
                       _page_action_poll_impl(_first(query, "target", "scanner") or "scanner",
                                              int(_first(query, "limit", "4") or 4)))
        return True
    if _handle_get_file_api(handler, parsed, query, project):
        return True
    return False


