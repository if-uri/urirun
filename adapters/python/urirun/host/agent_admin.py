# Author: Tom Sapletta · Part of the ifURI solution.
"""Most z dashboardu do connectora ``agent://`` — REALNY executor tickowej pracy.

koru napędza IDE/CLI przez `tillm` i to pada (`client command failed`), więc tickety stoją
jako pseudo-praca. `agent://` uruchamia headless narzędzie kodujące (`claude -p`, `codex exec`…)
wprost — sprawdzone, że działa. Ten most pozwala PANELOWI wykonać ticket realnym agentem, a bieg
idzie przez ``work_runs`` (rekord + log + exit), więc jest w pełni legibilny w panelu Runs.

Uruchomienie agenta zmienia repo — inicjuje je człowiek klikając „Wykonaj agentem" (nie pętla).
"""
from __future__ import annotations

import json
import shlex
import subprocess
from typing import Any


def _conn():
    from urirun_connector_agents import core
    return core


def tools() -> dict[str, Any]:
    try:
        return {"ok": True, **_conn().tools_list()}
    except ImportError:
        return {"ok": False, "error": "install urirun-connector-agents", "available": {}}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "available": {}}


def _planfile() -> str | None:
    from .work_queue import _planfile as p
    return p()


def _ticket(project, ticket_id: str) -> dict:
    pf = _planfile()
    if not pf:
        return {}
    try:
        cp = subprocess.run([pf, "ticket", "show", ticket_id, "--format", "json"],
                            capture_output=True, text=True, timeout=15, cwd=str(project))
        raw = cp.stdout
        return json.loads(raw[raw.index("{"):raw.rindex("}") + 1]) if "{" in raw else {}
    except Exception:  # noqa: BLE001
        return {}


def _prompt_for(t: dict) -> str:
    crit = t.get("acceptance_criteria") or []
    crit_txt = ("\nAcceptance criteria:\n- " + "\n- ".join(crit)) if crit else ""
    return (f"Execute ticket {t.get('id')}: {t.get('name')}.\n\n{t.get('description') or ''}{crit_txt}\n\n"
            "Work in the current repository. Make the concrete change, keep it minimal and tested. "
            "When done, summarise what you changed in 3 lines.")


def _agent_bin(agent: str) -> str | None:
    av = tools().get("available") or {}
    if agent != "auto":
        return (av.get(agent) or {}).get("path")
    for a in ("claude", "codex", "opencode", "aider"):
        if a in av:
            return av[a].get("path")
    return None


def _running_agents() -> list[dict]:
    from .work_runs import list_runs
    return [r for r in list_runs(tail_lines=1) if r.get("running") and "agent://" in (r.get("uri") or "")]


def run_ticket(project, ticket_id: str, agent: str = "claude", _autonomous: bool | None = None) -> dict[str, Any]:
    """Wykonaj ticket realnym agentem headless; bieg przez work_runs (widoczny w Runs).

    BLOKADA WSPÓŁBIEŻNOŚCI: wiele agentów na jednym repo koliduje (równoległe edycje/git).
    Domyślnie 1 agent naraz (URIRUN_AGENT_MAX_CONCURRENT); nigdy ten sam ticket dwa razy."""
    import os
    tid = str(ticket_id or "").strip()
    if not tid:
        return {"ok": False, "error": "id ticketu wymagane"}
    running = _running_agents()
    if any(f"/task/{tid}" in (r.get("uri") or "") for r in running):
        return {"ok": False, "error": f"agent już wykonuje {tid} (nie duplikuję)"}
    cap = int(os.environ.get("URIRUN_AGENT_MAX_CONCURRENT") or 1)
    if len(running) >= cap:
        return {"ok": False, "error": f"za dużo równoległych agentów ({len(running)}/{cap}) — "
                f"współbieżni agenci na jednym repo kolidują; poczekaj albo podnieś URIRUN_AGENT_MAX_CONCURRENT",
                "running": [r.get("uri") for r in running]}
    t = _ticket(project, tid)
    if not t:
        return {"ok": False, "error": f"nie znaleziono ticketu {tid}"}
    binp = _agent_bin(agent)
    if not binp:
        return {"ok": False, "error": f"agent {agent!r} niedostępny — zainstaluj/urun agent tools"}
    prompt = _prompt_for(t)
    # AUTO-WRITE (gap C): domyślnie claude -p PYTA o zgodę (planuje, nie stosuje). Z
    # URIRUN_AGENT_AUTONOMOUS=1 agent ZAPISUJE bez pytania — pełna autonomia, ale niebezpieczne
    # (agent może zrobić wszystko); produkcyjnie tylko w izolowanym worktree.
    autonomous = _autonomous if _autonomous is not None else \
        str(os.environ.get("URIRUN_AGENT_AUTONOMOUS", "")).strip().lower() in ("1", "true", "yes", "on")
    if agent in ("claude", "auto"):
        cmd = f"{shlex.quote(binp)} -p {shlex.quote(prompt)}"
        if autonomous:
            cmd += " --dangerously-skip-permissions"
    else:
        cmd = f"{shlex.quote(binp)} exec {shlex.quote(prompt)}"
    from .work_runs import start_run
    meta = start_run(project, f"agent://{agent}/task/{tid}", cmd, label=f"{tid}: {t.get('name','')[:60]}")
    return {"ok": True, "started": True, "ticket": tid, "agent": agent, "run": meta["id"], "log": meta["log"]}


def action(project, payload: dict) -> dict[str, Any]:
    act = str((payload or {}).get("action") or "").strip()
    if act == "run-ticket":
        auto = payload.get("autonomous")
        return run_ticket(project, str(payload.get("id") or ""), str(payload.get("agent") or "claude"),
                          _autonomous=bool(auto) if auto is not None else None)
    return {"ok": False, "error": f"unknown action {act!r}"}
