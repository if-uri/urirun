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
import time
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
            lines = [
                line for line in log.read_text(errors="replace").splitlines()
                if "cycle=" in line or "queue:" in line or "QUEUE:" in line or "ticket" in line.lower()
            ]
            last = lines[-1][-200:] if lines else ""
        except Exception:  # noqa: BLE001
            pass
    return {"running": running, "loops": len(loops), "project": project, "last_activity": last.strip()}


def tickets(limit: int = 40, include_done: bool = False, sprint: str = "current") -> list[dict[str, Any]]:
    """The planfile queue — tickets for the view.

    By default we exclude done tickets (they should be archived to 'archive' sprint
    using the new archiving functions). This keeps the main /work view clean.
    Use include_done=True or sprint="archive" to see historical/archived work.
    """
    pf = _planfile()
    if not pf:
        return []
    try:
        cmd = [pf, "ticket", "list", "--format", "json", "--sprint", sprint]
        if not include_done:
            # planfile CLI --status supports one value or 'all'; we fetch and filter client-side
            # to avoid showing done clutter. For exact, user can use include_done.
            cmd += ["--status", "all"]
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=15, cwd=_project())
        raw = cp.stdout
        data = json.loads(raw[raw.index("["):raw.rindex("]") + 1]) if "[" in raw else \
            json.loads(raw).get("tickets", [])
    except Exception:  # noqa: BLE001
        return []

    if not include_done and sprint == "current":
        data = [t for t in data if (t.get("status") or "").lower() != "done"]

    # Load grants once (best-effort, long-term autonomy memory).
    # We attach grant + autonomy_state to every ticket row so UI and drivers
    # can distinguish "planfile blocked" from "human-granted for autonomous drive".
    grants = {"keys": set(), "tickets": set()}
    try:
        from urirun_connector_grants import unblock_ledger as ul
        for g in (ul.list_type_grants() or []):
            k = (g.get("key") or "").strip().lower()
            if k:
                grants["keys"].add(k)
        for g in (ul.list_ticket_grants() or []):
            tid = (g.get("ticket") or g.get("key") or "").strip()
            if tid:
                grants["tickets"].add(tid)
    except Exception:  # noqa: BLE001
        pass

    def _has_grant(t: dict) -> dict | None:
        """Lightweight grant detection (mirrors key ideas from ledger.decision_keys)."""
        tid = str(t.get("id") or "").strip()
        if tid and tid in grants["tickets"]:
            return {"type": "ticket", "key": tid}
        labels = [str(x).lower() for x in (t.get("labels") or [])]
        for lab in labels:
            label = lab.strip()
            if label in grants["keys"]:
                return {"type": "type", "key": label}
            if label.startswith("waiting:"):
                suffix = label.split(":", 1)[1]
                g = "wait-gate:waiting_" + suffix.replace("-", "_")
                if g in grants["keys"]:
                    return {"type": "type", "key": g}
                g2 = "waiting:" + suffix
                if g2 in grants["keys"]:
                    return {"type": "type", "key": g2}
            if label.startswith(("wait-gate:", "action:", "goal:", "source:")):
                if label in grants["keys"]:
                    return {"type": "type", "key": label}
        # action from name heuristic (cheap)
        import re
        m = re.search(r"\b([a-z_]+\.[a-z_]+)\b", t.get("name", "") or "")
        if m:
            ak = "action:" + m.group(1).lower()
            if ak in grants["keys"]:
                return {"type": "type", "key": ak}
        return None

    rows = []
    for t in data:  # WSZYSTKIE — sortuj przed limitem...
        src = t.get("source") or {}
        status = t.get("status")
        row = {
            "id": t.get("id"),
            "name": t.get("name"),
            "status": status,
            "priority": t.get("priority"),
            "source": src.get("tool") if isinstance(src, dict) else src,
            "labels": t.get("labels") or t.get("label"),
            "updated": t.get("updated_at") or t.get("updatedAt"),
            "sprint": t.get("sprint") or "current",
        }
        gh = _has_grant(t)
        if gh:
            row["grant"] = gh
            # Canonical long-term autonomy states for UI / claim-next / drivers.
            # "granted_blocked" = planfile still shows blocked/waiting (real condition or label),
            #                    but human has permanently granted this class → koru/claim-next should treat as runnable.
            if status in ("blocked", "waiting_input"):
                row["autonomy"] = "granted_blocked"
                row["autonomy_note"] = "granted — will auto-drive when koru/executor is ready"
            elif status in ("open", "ready"):
                row["autonomy"] = "granted_open"
            else:
                row["autonomy"] = "granted"
        else:
            if status in ("blocked", "waiting_input"):
                row["autonomy"] = "needs_human_or_condition"
        rows.append(row)

    order = {"in_progress": 0, "claimed": 1, "waiting_input": 2, "blocked": 2, "open": 3, "done": 4}

    def _rid(r):  # numeryczny sufiks ID malejąco = najnowsze pierwsze w obrębie statusu
        import re
        m = re.search(r"(\d+)$", str(r.get("id") or ""))
        return -int(m.group(1)) if m else 0
    rows.sort(key=lambda r: (order.get(r.get("status"), 5), _rid(r)))  # aktywne+najnowsze najpierw, PRZED limitem
    return rows[:limit]


def _bucket_skip(reason: str) -> str:
    """Map a planfile runnability skip-reason to a /work bucket."""
    if reason == "autonomy-frontier" or reason == "goal-frozen":
        return "frozen"
    if reason == "actor:human" or reason.startswith("waiting:") or reason.startswith("needs-human"):
        return "waiting"
    if reason.startswith("blocked_by:"):
        return "dependency_blocked"
    return "other"  # exec_state:*, queue:*


def runnable_summary() -> dict[str, Any]:
    """WHY koru serves work or idles — the operator's answer to "czemu koru nic nie bierze?".
    Uses planfile's runnability contract (`ticket next --debug`) to split the queue into servable
    vs the reason each open ticket is held (frozen / waiting-on-human-or-resource / dependency).
    An idle koru with a full ``waiting`` bucket is a CLEAN frontier, not a stall."""
    buckets: dict[str, Any] = {"selected": None, "servable": [], "frozen": [],
                               "waiting": [], "dependency_blocked": [], "other": []}
    pf = _planfile()
    if not pf:
        return {**buckets, "error": "planfile not found"}
    try:
        cp = subprocess.run([pf, "ticket", "next", "--debug", "--format", "json"],
                            capture_output=True, text=True, timeout=15, cwd=_project())
        raw = cp.stdout
        rep = json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
    except Exception:  # noqa: BLE001
        return {**buckets, "error": "planfile next --debug failed"}
    buckets["selected"] = rep.get("selected")
    buckets["servable"] = rep.get("servable", [])
    for row in rep.get("skipped", []):
        buckets[_bucket_skip(row.get("reason", ""))].append({"id": row.get("id"), "reason": row.get("reason")})
    if rep.get("warning"):
        buckets["warning"] = rep["warning"]
    return buckets


def _ticket_cmds(pf: str, tid: str, act: str, note: str) -> tuple[list[list[str]] | None, str]:
    """Map a panel action to planfile CLI invocations.

    Long-term autonomy rule for "unblock":
    - ALWAYS force --status open (this is the "force open gdy grant" behavior).
    - The ledger grant provides the persistent memory so similar future tickets
      of the same type are treated as runnable without re-asking.
    - We record a clear note for audit trail.
    """
    cmds: list[list[str]] = []
    user_note = (note or "").strip()

    if act == "unblock":
        # Force planfile state to open — this is what makes the ticket leave "blocked"
        # in the list. Grant (if present) is already in ledger from previous or current action.
        cmds.append([pf, "ticket", "update", tid, "--status", "open"])
        force_note = "Odblokowano (force open). Grant w ledgerze dla tego typu/ticketu — autonomia nie będzie pytać ponownie."
        if user_note:
            force_note = f"{user_note} | {force_note}"
        cmds.append([pf, "ticket", "update", tid, "--note", force_note])
    else:
        if user_note:
            cmds.append([pf, "ticket", "update", tid, "--note", user_note])
        if act in ("ready", "done", "start", "block", "claim"):
            cmds.append([pf, "ticket", act, tid])
        elif act in ("close", "cancel"):
            cmds.append([pf, "ticket", "update", tid, "--status", "cancelled"])
        elif act == "delete":
            cmds.append([pf, "ticket", "delete", tid, "--force"])
        elif act == "archive":
            # handled specially in ticket_action using python adapter for sprint move
            pass
        elif act == "unarchive":
            # handled specially
            pass
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
    if action in ("unblock", "ready"):  # ODBLOKOWANIE RAZ = ZAPAMIĘTANE (per Tom): persystuj trwale
        _remember_unblock(tid, note)     # → bramki/watchdog nigdy więcej nie re-blokują/re-pytają
    if action == "archive":
        # Archiwizacja: przenieś do sprintu "archive" aby zmniejszyć zaśmiecenie widoku /work
        try:
            from . import planfile_adapter as pa
            pa.archive_ticket(_project(), tid, note=note or "zarchiwizowane z /work dashboard")
            ran.append({"cmd": f"planfile archive {tid} -> sprint=archive", "rc": 0})
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"archive failed: {exc}", "ran": ran}
    elif action == "unarchive":
        try:
            from . import planfile_adapter as pa
            pa.unarchive_ticket(_project(), tid)
            ran.append({"cmd": f"planfile unarchive {tid} -> sprint=current", "rc": 0})
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"unarchive failed: {exc}", "ran": ran}
    _emit_ticket_event(tid, action)  # edge-trigger: zmiana statusu → event na szynę → reconciler
    # Standard URI process logging
    try:
        from .twin_bridge import TWIN_EVENT_HUB
        TWIN_EVENT_HUB.publish({
            "uri": f"ticket://{tid}/{action or 'note'}",
            "type": "URI_PROCESS",
            "step": "ticket-action",
            "ticket": tid,
            "action": action,
            "note": note or "",
            "timestamp": __import__("time").time()
        })
    except Exception:
        pass
    return {"ok": True, "ticket": tid, "action": (action or "note"), "ran": ran,
            "remembered": action in ("unblock", "ready"),
            "archived": action == "archive",
            "unarchived": action == "unarchive"}


def _fetch_ticket(tid: str) -> dict | None:
    """Pobierz ticket z planfile (do wyliczenia kluczy typu przy odblokowaniu)."""
    pf = _planfile()
    if not pf:
        return None
    try:
        cp = subprocess.run([pf, "ticket", "show", tid, "--format", "json"],
                            capture_output=True, text=True, timeout=15, cwd=_project())
        raw = cp.stdout
        if cp.returncode != 0 or "{" not in raw:
            return None
        return json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
    except Exception:  # noqa: BLE001
        return None


def _remember_unblock(tid: str, note: str) -> None:
    """Zapisz TRWAŁE odblokowanie do ledgera — ticket + stabilne klucze typu (per Tom: nie re-pytaj)."""
    try:
        from urirun_connector_grants import unblock_ledger
        from urirun_connector_work import gates
        ticket = _fetch_ticket(tid) or {"id": tid}
        action = gates.action_of_ticket(ticket) if ticket else ""
        unblock_ledger.record_unblock(tid, action=action, by="human",
                                      note=note or "odblokowane w /work", ticket=ticket)
    except Exception:  # noqa: BLE001
        pass


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


def queue_state(include_done: bool = False, sprint: str = "current") -> dict[str, Any]:
    ts = tickets(include_done=include_done, sprint=sprint)
    counts: dict[str, int] = {}
    autonomy_counts: dict[str, int] = {}
    for t in ts:
        st = t.get("status") or "?"
        counts[st] = counts.get(st, 0) + 1
        au = t.get("autonomy") or "unknown"
        autonomy_counts[au] = autonomy_counts.get(au, 0) + 1
    try:
        from . import ticket_meta  # LLM tags, real processes, node, allow/deny per ticket + Digital Twin
        ts = ticket_meta.enrich(ts, _project())
        persons = ticket_meta.load_digital_persons()
        digital_twin = {
            "persons": persons,
            "file": str(ticket_meta.digital_persons_file()),
            "active_count": sum(1 for p in persons if p.get("_is_enabled", True)),
        }
    except Exception:  # noqa: BLE001 - enrichment is best-effort; the raw table still renders
        digital_twin = {"persons": [], "error": "unavailable"}
        pass
    return {"koru": koru_status(), "tickets": ts, "counts": counts, "total": len(ts),
            "autonomy_counts": autonomy_counts,
            "digital_twin": digital_twin,  # list of digital persons with competencies + grants
            "include_done": include_done, "sprint": sprint}


def ticket_edit_full(ticket_id: str, *, name: str = "", description: str = "", llm: Any = None,
                     node: Any = None, allow: Any = None, deny: Any = None,
                     schedule: Any = None, owner: Any = None, llm_model: Any = None,
                     assigned_person: Any = None) -> dict[str, Any]:
    """Edit a not-done ticket: name/description go to planfile; LLM/node/allow/deny/owner/llm_model to the
    side-store (Digital Twin owner, model, person). Any subset may be given."""
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
        entry = ticket_meta.edit_meta(tid, llm=llm, node=node, allow=allow, deny=deny, schedule=schedule,
                                      owner=owner, llm_model=llm_model, assigned_person=assigned_person)
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
    from .env_loader import koru_ide, load_project_env
    load_project_env(project)
    ide = koru_ide()
    # Long-term: start koru with claim-next hard gate enforced.
    # KORU_WORK_GATE=hard makes work://claim-next the only source of tickets (grants, leases, runnable checks).
    env = {**os.environ, "KORU_WORK_GATE": "hard"}
    cmd = ["bash", "-lc",
           f"nohup {binp!r} autonomous up --project {project!r} --ide {ide!r} "
           f"--ticket-sources {lane} --allow-duplicate >> {str(log)!r} 2>&1 &"]
    try:
        subprocess.Popen(cmd, start_new_session=True, env=env)  # noqa: S603
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


def unblock_board() -> dict[str, Any]:
    """Trwałe odblokowania z ledgera — typy + tickety (dla panelu /work)."""
    try:
        from urirun_connector_grants import unblock_ledger as ul
        types = ul.list_type_grants()
        tickets = ul.list_ticket_grants()
        return {"ok": True, "ledger": ul.ledger_path(), "types": types, "tickets": tickets,
                "total_types": len(types), "total_tickets": len(tickets)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "types": [], "tickets": []}


def active_tickets() -> dict[str, Any]:
    """Currently simultaneously running / active tickets (with leases/workers).

    Returns list of active items with a visual badge: ▶ play (executing), ⏸ pause (waiting/claimed),
    ⏹ stop (releasing/stopping). Used to show concurrent work in /work.
    """
    items: list[dict] = []
    try:
        from urirun_connector_work import core as wc
        leases = (wc.locks_query_list() or {}).get("active", []) or []
        for lease in leases:
            tid = str(lease.get("ticket") or "").strip()
            if not tid:
                continue
            t = _fetch_ticket(tid) or {"id": tid, "name": f"Ticket {tid}", "status": lease.get("status", "in_progress")}
            worker = lease.get("worker") or "?"
            lstatus = str(lease.get("status") or "running").lower()
            # Badge mapping
            if any(k in lstatus for k in ("pause", "wait", "input")) or t.get("status") in ("waiting_input",):
                badge = "⏸"
                badge_label = "pause"
            elif any(k in lstatus for k in ("stop", "release", "done")):
                badge = "⏹"
                badge_label = "stop"
            else:
                badge = "▶"
                badge_label = "play"
            items.append({
                "id": tid,
                "name": t.get("name") or tid,
                "status": t.get("status"),
                "worker": worker,
                "lease_id": lease.get("id"),
                "badge": badge,
                "badge_label": badge_label,
                "expires_in": max(0, int((lease.get("expires", 0) or 0) - time.time())),
            })
    except Exception:  # noqa: BLE001 - degrade gracefully if work connector not fully available
        # Fallback: just use planfile in_progress / claimed
        for t in tickets(include_done=True):
            if t.get("status") in ("in_progress", "claimed"):
                items.append({
                    "id": t["id"],
                    "name": t.get("name") or t["id"],
                    "status": t.get("status"),
                    "worker": "koru",
                    "badge": "▶",
                    "badge_label": "play",
                    "expires_in": None,
                })

    # sort by worker or id
    items.sort(key=lambda x: (x.get("worker") or "", x.get("id") or ""))
    return {"ok": True, "active": items, "count": len(items)}


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
