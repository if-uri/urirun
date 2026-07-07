# Author: Tom Sapletta · Part of the ifURI solution.
"""The queue panel data: is the autonomous loop (koru) running, and what is in the queue.

Answers "where can I see that it keeps going?" — koru's live status plus the planfile
ticket queue, so the /work dashboard shows continuous operation, not just a snapshot.
Everything is best-effort and read-only; missing tools degrade to empty, never an error.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

_PROJECT_ENV = "URIRUN_KORU_PROJECT"
_PLANFILE_ENV = "URIRUN_PLANFILE_BIN"


def _project() -> str:
    return os.environ.get(_PROJECT_ENV) or os.path.expanduser("~/github/if-uri")


def _planfile() -> str | None:
    b = os.environ.get(_PLANFILE_ENV) or shutil.which("planfile")
    if b:
        return b
    for c in ("~/github/if-uri/venv/bin/planfile", "~/github/semcod/koru/.venv/bin/planfile"):
        p = Path(c).expanduser()
        if p.is_file():
            return str(p)
    return None


def koru_status() -> dict[str, Any]:
    """Is the autonomous loop alive, and what was its last cycle line?"""
    project = _project()
    try:
        out = subprocess.run(["pgrep", "-af", "autonomous up"], capture_output=True, text=True, timeout=5).stdout
    except Exception:  # noqa: BLE001
        out = ""
    loops = [ln for ln in out.splitlines() if project in ln or "autonomous up" in ln]
    running = any(project in ln for ln in loops)
    last = ""
    log = Path(project) / ".planfile" / ".koru" / "queue.log"
    if not log.is_file():
        log = Path(project) / ".planfile" / ".koru" / "soak.log"
    if log.is_file():
        try:
            lines = [l for l in log.read_text(errors="replace").splitlines()
                     if "cycle=" in l or "queue:" in l or "QUEUE:" in l or "ticket" in l.lower()]
            last = lines[-1][-200:] if lines else ""
        except Exception:  # noqa: BLE001
            pass
    return {"running": running, "loops": len(loops), "project": project, "last_activity": last.strip()}


def tickets(limit: int = 40) -> list[dict[str, Any]]:
    """The planfile queue — every ticket with its status, newest work first."""
    pf = _planfile()
    if not pf:
        return []
    try:
        cp = subprocess.run([pf, "ticket", "list", "--format", "json"],
                            capture_output=True, text=True, timeout=15, cwd=_project())
        raw = cp.stdout
        data = json.loads(raw[raw.index("["):raw.rindex("]") + 1]) if "[" in raw else \
            json.loads(raw).get("tickets", [])
    except Exception:  # noqa: BLE001
        return []
    rows = []
    for t in data:  # WSZYSTKIE — sortuj przed limitem, żeby aktywne (blocked/open) nigdy nie wypadły
        src = t.get("source") or {}
        rows.append({"id": t.get("id"), "name": t.get("name"), "status": t.get("status"),
                     "priority": t.get("priority"),
                     "source": src.get("tool") if isinstance(src, dict) else src,
                     "labels": t.get("labels") or t.get("label"),
                     "updated": t.get("updated_at") or t.get("updatedAt")})
    order = {"in_progress": 0, "claimed": 1, "waiting_input": 2, "blocked": 2, "open": 3, "done": 4}

    def _rid(r):  # numeryczny sufiks ID malejąco = najnowsze pierwsze w obrębie statusu
        import re
        m = re.search(r"(\d+)$", str(r.get("id") or ""))
        return -int(m.group(1)) if m else 0
    rows.sort(key=lambda r: (order.get(r.get("status"), 5), _rid(r)))  # aktywne+najnowsze najpierw, PRZED limitem
    return rows[:limit]


def _ticket_cmds(pf: str, tid: str, act: str, note: str) -> tuple[list[list[str]] | None, str]:
    """Map a panel action to planfile CLI invocations (note first, then the status change)."""
    cmds: list[list[str]] = []
    if note:
        cmds.append([pf, "ticket", "update", tid, "--note", str(note)])
    if act == "unblock":
        cmds.append([pf, "ticket", "update", tid, "--status", "open"])
    elif act in ("ready", "done", "start", "block", "claim"):
        cmds.append([pf, "ticket", act, tid])
    elif act in ("close", "cancel"):
        cmds.append([pf, "ticket", "update", tid, "--status", "cancelled"])
    elif act == "delete":
        cmds.append([pf, "ticket", "delete", tid, "--force"])
    elif act and act != "note":
        return None, f"unknown action {act!r}"
    if not cmds:
        return None, "nothing to do (give an action or a note)"
    return cmds, ""


def ticket_action(ticket_id: str, action: str = "", note: str = "") -> dict[str, Any]:
    """React to a queue ticket from the /work panel: change its status and/or append a note.

    The human seam for BLOCKED tickets (e.g. one waiting on credentials): once the input is
    provided out-of-band, ``unblock`` reopens it so koru retries; ``ready`` marks it recovered;
    ``note`` records context. Maps to the planfile CLI; never raises, returns an envelope."""
    pf = _planfile()
    if not pf:
        return {"ok": False, "error": "planfile not found (install planfile or set URIRUN_PLANFILE_BIN)"}
    tid = str(ticket_id or "").strip()
    if not tid:
        return {"ok": False, "error": "ticket id required"}
    cmds, err = _ticket_cmds(pf, tid, str(action or "").strip(), note)
    if err:
        return {"ok": False, "error": err}
    ran = []
    for c in cmds or []:
        try:
            cp = subprocess.run(c, capture_output=True, text=True, timeout=20, cwd=_project())
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc), "ran": ran}
        ran.append({"cmd": " ".join(c[3:]), "rc": cp.returncode})
        if cp.returncode != 0:
            return {"ok": False, "error": (cp.stderr or cp.stdout or "planfile error").strip()[-200:], "ran": ran}
    _emit_ticket_event(tid, action)  # edge-trigger: zmiana statusu → event na szynę → reconciler
    return {"ok": True, "ticket": tid, "action": (action or "note"), "ran": ran}


def _emit_ticket_event(tid: str, action: str) -> None:
    """Publikuj zmianę stanu ticketu na szynę (TWIN_EVENT_HUB) — edge-trigger dla reconcilera/agentów."""
    if action in ("", "note"):
        return
    try:
        from .twin_bridge import TWIN_EVENT_HUB
        TWIN_EVENT_HUB.publish({"uri": "ticket://event", "step_uri": f"ticket://{tid}/{action}",
                                "ticket": tid, "action": action, "narration": f"{tid} → {action}",
                                "status": "ticket-change", "category": "ticket"})
    except Exception:  # noqa: BLE001
        pass


def _parse_criteria(text: Any) -> list[dict]:
    """Kryteria z formularza: linia 'label :: cmd' (cmd opcjonalny) → check verify://."""
    if isinstance(text, list):
        return [c for c in text if isinstance(c, dict)]
    checks = []
    for line in str(text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if "::" in line:
            lbl, cmd = line.split("::", 1)
            checks.append({"label": lbl.strip(), "cmd": cmd.strip()})
        else:
            checks.append({"label": line})  # Definition of Done bez cmd (jeszcze niesprawdzalny)
    return checks


def _create_planfile_ticket(cmd: list[str]) -> tuple[str, dict | None]:
    """Run `planfile ticket create`; return (ticket_id, error_result_or_None)."""
    import re
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=20, cwd=_project())
    except Exception as exc:  # noqa: BLE001
        return "", {"ok": False, "error": str(exc)}
    if cp.returncode != 0:
        return "", {"ok": False, "error": (cp.stderr or cp.stdout or "create failed").strip()[-200:]}
    m = re.search(r"[A-Z]+-\d+", cp.stdout or "")
    return (m.group(0) if m else ""), None


def _seed_ticket_verify(tid: str, node: str, checks: list) -> int:
    """Attach node meta + acceptance-criteria verify checks to a fresh ticket; return #seeded."""
    if tid and node:
        try:
            from . import ticket_meta
            ticket_meta.edit_meta(tid, node=str(node))
        except Exception:  # noqa: BLE001
            pass
    if tid and checks:
        try:
            from urirun_connector_verify import core as vf
            vf.ticket_command_seed(id=tid, checks=checks)
            return len(checks)
        except Exception:  # noqa: BLE001
            pass
    return 0


def create_ticket(name: str, description: str = "", priority: str = "normal", node: str = "",
                  labels: Any = None, criteria: Any = None) -> dict[str, Any]:
    """Człowiek dodaje zadanie z panelu: planfile create + node (meta) + acceptance_criteria (verify)."""
    name = str(name or "").strip()
    if not name:
        return {"ok": False, "error": "nazwa zadania wymagana"}
    pf = _planfile()
    if not pf:
        return {"ok": False, "error": "planfile niedostępny"}
    cmd = [pf, "ticket", "create", name, "-p", str(priority or "normal"), "--source", "human"]
    for lab in (labels or []):
        cmd += ["-l", str(lab)]
    if description:
        cmd += ["-d", str(description)]
    tid, err = _create_planfile_ticket(cmd)
    if err:
        return err
    seeded = _seed_ticket_verify(tid, node, _parse_criteria(criteria))
    return {"ok": True, "id": tid, "node": node, "criteria": seeded,
            "verifiable": seeded > 0}


def queue_state() -> dict[str, Any]:
    ts = tickets()
    counts: dict[str, int] = {}
    for t in ts:
        counts[t.get("status") or "?"] = counts.get(t.get("status") or "?", 0) + 1
    try:
        from . import ticket_meta  # LLM tags, real processes, node, allow/deny per ticket
        ts = ticket_meta.enrich(ts, _project())
    except Exception:  # noqa: BLE001 - enrichment is best-effort; the raw table still renders
        pass
    return {"koru": koru_status(), "tickets": ts, "counts": counts, "total": len(ts)}


def ticket_edit_full(ticket_id: str, *, name: str = "", description: str = "", llm: Any = None,
                     node: Any = None, allow: Any = None, deny: Any = None,
                     schedule: Any = None) -> dict[str, Any]:
    """Edit a not-done ticket: name/description go to planfile; LLM/node/allow/deny to the
    side-store. Any subset may be given. Returns an envelope; never raises."""
    tid = str(ticket_id or "").strip()
    if not tid:
        return {"ok": False, "error": "ticket id required"}
    pf = _planfile()
    upd: list[str] = []
    if name:
        upd += ["--name", str(name)]
    if description:
        upd += ["--description", str(description)]
    if upd and pf:
        try:
            cp = subprocess.run([pf, "ticket", "update", tid, *upd], capture_output=True,
                               text=True, timeout=20, cwd=_project())
            if cp.returncode != 0:
                return {"ok": False, "error": (cp.stderr or cp.stdout or "planfile error").strip()[-200:]}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}
    try:
        from . import ticket_meta
        entry = ticket_meta.edit_meta(tid, llm=llm, node=node, allow=allow, deny=deny, schedule=schedule)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "ticket": tid, "meta": entry}


def _koru_bin() -> str | None:
    b = shutil.which("koru")
    if b:
        return b
    for c in ("~/github/semcod/koru/.venv/bin/koru", "~/github/if-uri/venv/bin/koru"):
        p = Path(c).expanduser()
        if p.is_file():
            return str(p)
    return None


def ensure_running(*, lane: str = "queue") -> dict[str, Any]:
    """Start the koru autonomous loop against the project if it is not already running.
    Idempotent — the /work 'Continue koru' button calls this; a running loop is a no-op."""
    if koru_status().get("running"):
        return {"ok": True, "already_running": True, "project": _project()}
    binp = _koru_bin()
    if not binp:
        return {"ok": False, "error": "koru not found (install koru or set PATH)"}
    project = _project()
    log = Path(project) / ".planfile" / ".koru" / "queue.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["bash", "-lc",
           f"nohup {binp!r} autonomous up --project {project!r} --ide claude "
           f"--ticket-sources {lane} --allow-duplicate >> {str(log)!r} 2>&1 &"]
    try:
        subprocess.Popen(cmd, start_new_session=True)  # noqa: S603
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "started": True, "project": project, "cmd": " ".join(cmd[-1:])}


def _log_age_seconds() -> float | None:
    """Freshness of the loop's heartbeat — seconds since the queue/soak log last changed."""
    import time
    for name in ("queue.log", "soak.log"):
        p = Path(_project()) / ".planfile" / ".koru" / name
        if p.is_file():
            try:
                return max(0.0, time.time() - p.stat().st_mtime)
            except OSError:
                pass
    return None


_STALE_SECONDS = 1500   # ~25 min without a log tick while "running" → AT RISK


def _loop_controller_active() -> bool:
    """Czy loop:// jest zaplanowanym kontrolerem (cron woła /api/work/loop)?
    Wtedy koru NIE jest kontrolerem — jego brak to stan zamierzony, nie awaria."""
    import subprocess
    try:
        out = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5).stdout
        return any("work/loop" in ln and not ln.strip().startswith("#") for ln in out.splitlines())
    except Exception:  # noqa: BLE001
        return False


def _controller_label(running: bool, loop_ctrl: bool) -> str | None:
    """Who is actually driving the queue: koru, loop:// (cron), or nobody."""
    return "koru" if running else ("loop://" if loop_ctrl else None)


def _continuity_verdict(running: bool, loop_ctrl: bool, queue_empty: bool,
                        age: float | None) -> tuple[str, str | None]:
    """CONTINUITY verdict + suggested action from loop/controller/queue state."""
    if not running and loop_ctrl:
        # koru stopped intentionally — loop:// (cron) is controller; do NOT suggest restarting koru (recreates conflict)
        if queue_empty:
            return "AT_RISK", "kolejka pusta — inquiry/reflection utworzy następny ticket"
        return "OK", None
    if not running:
        return "STOPPED", "brak kontrolera — zaplanuj loop:// w cronie (*/10 /api/work/loop) lub uruchom cykl"
    if queue_empty:
        return "AT_RISK", "queue empty — run inquiry/reflection to create the next ticket"
    if age is not None and age > _STALE_SECONDS:
        return "AT_RISK", f"loop running but no heartbeat for {int(age // 60)} min — inspect logs"
    return "OK", None


def work_status() -> dict[str, Any]:
    """The control-room verdict: is the autonomous loop actually continuing?

    CONTINUITY = OK | AT_RISK | STOPPED, with the current ticket, the next step, and a
    concrete suggested action — so the operator never has to guess whether it is alive."""
    ku = koru_status()
    ts = tickets()
    counts: dict[str, int] = {}
    for t in ts:
        counts[t.get("status") or "?"] = counts.get(t.get("status") or "?", 0) + 1
    open_next = [t for t in ts if t.get("status") in ("open", "waiting_input")]
    in_progress = [t for t in ts if t.get("status") in ("in_progress", "claimed")]
    age = _log_age_seconds()
    running = ku.get("running")
    loop_ctrl = _loop_controller_active()
    controller = _controller_label(bool(running), loop_ctrl)
    queue_empty = not open_next and not in_progress
    cont, action = _continuity_verdict(bool(running), loop_ctrl, queue_empty, age)

    return {
        "continuity": cont,
        "controller": controller,
        "koru": {**ku, "last_seen_seconds": round(age) if age is not None else None},
        "tickets": {"open": counts.get("open", 0), "in_progress": counts.get("in_progress", 0)
                    + counts.get("claimed", 0), "blocked": counts.get("blocked", 0)
                    + counts.get("waiting_input", 0), "done": counts.get("done", 0), "total": len(ts)},
        "current": in_progress[0] if in_progress else None,
        "next": open_next[:5],
        "suggested_action": action,
    }
