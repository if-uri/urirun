# Author: Tom Sapletta · Part of the ifURI solution.
"""Per-ticket augmentation for the /work queue table.

For every queue ticket the operator wants to SEE, at a glance and on demand:
  * which **LLM(s)** participate (short tags, possibly several, per task),
  * which **URI processes** actually ran for it (first 3 inline, full list in a popup —
    read from koru's real run log, not invented),
  * on which **machine / node** it will run,
  * an **allow / deny** list of URI processes (policy intent),
and to EDIT the LLM, the ticket text, the node and the allow/deny policy on tickets that
are not done yet.

planfile owns the ticket's name/description/status. This side-store
(~/.urirun/host-dashboard/ticket-meta.json) owns the augmentation the operator edits —
LLM tags, node, allow/deny — so it survives without fighting planfile's schema.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

_META_ENV = "URIRUN_TICKET_META_FILE"
_TICKET_RE = re.compile(r"[A-Z]{2,}-\d+")
_DONE = {"done", "closed", "cancelled"}

_DIGITAL_PERSONS_ENV = "URIRUN_DIGITAL_PERSONS_FILE"


# ------------------------------------------------------------------ meta side-store

def meta_file() -> Path:
    p = Path(os.environ.get(_META_ENV) or "~/.urirun/host-dashboard/ticket-meta.json").expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_meta() -> dict:
    f = meta_file()
    if not f.is_file():
        return {}
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def save_meta(data: dict) -> None:
    meta_file().write_text(json.dumps(data, indent=1), encoding="utf-8")


# ------------------------------------------------------------------ digital persons / twin

def digital_persons_file() -> Path:
    p = Path(os.environ.get(_DIGITAL_PERSONS_ENV) or "~/.urirun/host-dashboard/digital-persons.json").expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


_DEFAULT_DIGITAL_PERSONS = [
    {
        "id": "tom",
        "type": "human",
        "name": "Tom Sapletta",
        "competencies": ["architecture", "review", "unblock", "signal", "node-setup", "policy", "full"],
        "grants": ["human:*", "policy:*", "node:*", "secret:*", "unblock:*"]
    },
    {
        "id": "claude-coder",
        "type": "digital",
        "name": "Claude Coder",
        "model": "claude-3.5-sonnet",
        "competencies": ["code", "refactor", "test", "kvm", "deploy", "ui-control"],
        "grants": ["code:*", "test:*", "kvm:*", "repo.edit", "agent:code"]
    },
    {
        "id": "gemini-planner",
        "type": "digital",
        "name": "Gemini Planner",
        "model": "gemini-2.5-flash",
        "competencies": ["plan", "triage", "strategy", "nxdo", "goal"],
        "grants": ["ticket.create", "plan:*", "intent.resolve", "vision.inspect"]
    },
    {
        "id": "koru-worker",
        "type": "digital",
        "name": "Koru Worker",
        "model": "autonomous",
        "competencies": ["drive", "claim-next", "verify", "reconcile"],
        "grants": ["ticket.claim", "work:*", "loop:*"]
    },
    {
        "id": "nvidia-agent",
        "type": "digital",
        "name": "NVIDIA Agent",
        "model": "local",
        "competencies": ["host-control", "capture", "input", "nvidia"],
        "grants": ["node:nvidia", "kvm:host", "capture:*"]
    },
    {
        "id": "lenovo-node",
        "type": "digital",
        "name": "Lenovo Node Twin",
        "model": "node",
        "mode": "real",  # "real" = physical KVM hardware; "sim" = digital twin sim for testing (Signal app etc.)
        "competencies": ["node:lenovo", "kvm", "signal", "email", "deploy"],
        "grants": ["node:lenovo", "kvm:*", "signal:*"]
    }
]


def _enrich_person(p: dict) -> None:
    """Add backing (real-node / virtual-twin / human) + components for UI podgląd."""
    try:
        if "mode" not in p:
            p["mode"] = "sim" if str(p.get("id","")).endswith("-sim") else "real"
        comps_l = [str(c).lower() for c in (p.get("competencies") or [])]
        keys = ("kvm", "lenovo", "node:", "signal", "desktop", "input")
        is_node_like = any(any(k in c for k in keys) for c in comps_l)
        if p.get("type") == "human":
            p["backing"] = "human"
        elif p.get("mode") == "real" and is_node_like:
            p["backing"] = "real-node"
        else:
            p["backing"] = "virtual-twin"
        p["components"] = [c for c in (p.get("competencies") or []) if any(k in c.lower() for k in ("kvm","lenovo","signal","node","input","capture","deploy"))][:5] or (p.get("competencies") or [])[:4]
    except Exception:
        p.setdefault("backing", "virtual-twin")
        p.setdefault("components", [])

def load_digital_persons() -> list[dict]:
    f = digital_persons_file()
    if not f.is_file():
        save_digital_persons(_DEFAULT_DIGITAL_PERSONS)
        persons = list(_DEFAULT_DIGITAL_PERSONS)
        for p in persons: _enrich_person(p)
        return persons
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        persons = d if isinstance(d, list) else list(_DEFAULT_DIGITAL_PERSONS)
        now = time.time()
        for p in persons:
            if "enabled" not in p:
                p["enabled"] = True
            _enrich_person(p)   # always compute backing + components (wirtualny DT vs rzeczywisty node + inne komponenty)
            en = bool(p.get("enabled", True))
            du = p.get("disabled_until")
            if du:
                try:
                    if isinstance(du, (int, float)) and du > now:
                        en = False
                    elif isinstance(du, str):
                        from datetime import datetime
                        if datetime.fromisoformat(du.replace("Z", "+00:00")).timestamp() > now:
                            en = False
                except:
                    pass
            p["_is_enabled"] = en
        return persons
    except Exception:  # noqa: BLE001
        persons = list(_DEFAULT_DIGITAL_PERSONS)
        for p in persons: _enrich_person(p)
        return persons


def save_digital_persons(persons: list[dict]) -> None:
    digital_persons_file().write_text(json.dumps(persons, indent=1, ensure_ascii=False), encoding="utf-8")


def set_digital_person_enabled(pid: str, enabled: bool, disabled_until: float | str | None = None) -> bool:
    """Toggle a digital twin on/off. disabled_until can be unix timestamp or ISO for temp disable."""
    persons = load_digital_persons()
    changed = False
    for p in persons:
        if p.get("id") == pid:
            p["enabled"] = bool(enabled)
            if disabled_until is not None:
                p["disabled_until"] = disabled_until
            elif "disabled_until" in p and enabled:
                del p["disabled_until"]
            changed = True
            break
    if changed:
        save_digital_persons(persons)
    return changed


def set_digital_person_mode(pid: str, mode: str) -> bool:
    """Set mode for a digital twin: 'real' (use physical hardware/KVM) or 'sim' (digital twin simulation, for testing)."""
    if mode not in ("real", "sim"):
        return False
    persons = load_digital_persons()
    changed = False
    for p in persons:
        if p.get("id") == pid:
            p["mode"] = mode
            changed = True
            break
    if changed:
        save_digital_persons(persons)
    return changed


def get_digital_person_mode(pid: str) -> str:
    """Return 'real' or 'sim' for the twin. Defaults to 'real'."""
    p = get_digital_person(pid)
    if p:
        return p.get("mode", "real")
    return "real"


def get_digital_person(pid: str) -> dict | None:
    for p in load_digital_persons():
        if p.get("id") == pid:
            return p
    return None


# ------------------------------------------------------------------ LLM attribution

def koru_ide(project: str) -> str:
    """The IDE/agent model koru drives the loop with (`--ide <x>`), if it is running."""
    try:
        out = subprocess.run(["pgrep", "-af", "autonomous up"], capture_output=True,
                             text=True, timeout=5).stdout
    except Exception:  # noqa: BLE001
        return ""
    for ln in out.splitlines():
        if project in ln:
            m = re.search(r"--ide\s+(\S+)", ln)
            if m:
                return m.group(1)
    return ""


def session_llms(project: str) -> list[str]:
    """Default LLM tags for this run: koru's IDE model + the configured planner model."""
    tags = []
    ide = koru_ide(project)
    if ide:
        tags.append(ide)
    planner = (os.environ.get("LLM_MODEL") or "").strip()
    if planner:
        tags.append(planner.split("/")[-1])
    return tags or ["(brak LLM)"]


def ticket_llms(ticket: dict, m: dict, session: list[str]) -> list[str]:
    """LLM tags for one ticket: explicit edit → `llm:<x>` labels → session default if llm-ready."""
    if m.get("llm"):
        return list(m["llm"])
    labels = [str(x) for x in (ticket.get("labels") or [])]
    explicit = [l.split("llm:", 1)[1] for l in labels if l.startswith("llm:")]
    if explicit:
        return explicit
    if any("llm" in l.lower() for l in labels):
        return session
    return []


def ticket_node(ticket: dict, m: dict, koru_host: str) -> str:
    return m.get("node") or koru_host


# ------------------------------------------------------------------ real processes (koru log)

def koru_log_path(project: str) -> Path | None:
    for name in ("queue.log", "soak.log"):
        p = Path(project) / ".planfile" / ".koru" / name
        if p.is_file():
            return p
    return None


def _tail(path: Path, n: int) -> list[str]:
    try:
        return path.read_text(errors="replace").splitlines()[-n:]
    except OSError:
        return []


def parse_proc(line: str) -> dict | None:
    """Turn one koru log line into a short process descriptor (time · what · detail)."""
    t = (re.match(r"\[(\d\d:\d\d:\d\d)\]", line) or [None, ""])[1] if line[:1] == "[" else ""
    if "OBS:" in line:
        surf = re.search(r"surface=(\S+)", line)
        op = re.search(r"operation=(\S+)", line)
        argv = re.search(r'argv_text="([^"]*)"', line)
        label = " · ".join(x.group(1) for x in (surf, op) if x)
        return {"time": t, "kind": "OBS", "label": label or "process",
                "detail": (argv.group(1) if argv else "")[:160]}
    if "QUEUE:" in line:
        return {"time": t, "kind": "QUEUE", "label": "queue", "detail": line.split("QUEUE:", 1)[1].strip()[:160]}
    return None


def _dedup(rows: list[dict]) -> list[dict]:
    seen, out = set(), []
    for r in rows:
        key = (r.get("label"), r.get("detail"))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def scan_log_processes(project: str, per_ticket: int = 40) -> dict[str, list[dict]]:
    """Scan koru's log ONCE → {ticket_id: [process, …]} newest-first, deduped."""
    log = koru_log_path(project)
    if not log:
        return {}
    by: dict[str, list[dict]] = {}
    for line in _tail(log, 6000):
        ids = set(_TICKET_RE.findall(line))
        if not ids:
            continue
        p = parse_proc(line)
        if not p:
            continue
        for tid in ids:
            by.setdefault(tid, []).append(p)
    for tid, lst in by.items():
        lst.reverse()
        by[tid] = _dedup(lst)[:per_ticket]
    return by


# ------------------------------------------------------------------ enrichment + detail + edit

def enrich(tickets: list[dict], project: str) -> list[dict]:
    """Attach llm / node / process-preview / allow-deny to each ticket row (in place-ish)."""
    meta = load_meta()
    session = session_llms(project)
    host = os.uname().nodename
    procs = scan_log_processes(project)
    out = []
    persons = {p["id"]: p for p in load_digital_persons()}
    for t in tickets:
        m = meta.get(t.get("id")) or {}
        p = procs.get(t.get("id")) or []
        owner_id = m.get("owner") or m.get("assigned_person") or ""
        owner = persons.get(owner_id) or ({"id": owner_id, "name": owner_id, "type": "unknown"} if owner_id else None)
        out.append({**t,
                    "llm": ticket_llms(t, m, session),
                    "llm_model": m.get("llm_model") or (m.get("llm") or [None])[0] if m.get("llm") else None,
                    "node": ticket_node(t, m, host),
                    "owner": owner,
                    "assigned_person": m.get("assigned_person") or m.get("owner") or "",
                    "procs": p[:3], "procs_total": len(p),
                    "allow": m.get("allow") or [], "deny": m.get("deny") or [],
                    "schedule": m.get("schedule") or "",
                    "editable": (t.get("status") not in _DONE)})
    return out


def ticket_detail(project: str, ticket_id: str) -> dict[str, Any]:
    """Full popup payload: every process for the ticket + its editable meta."""
    tid = str(ticket_id or "").strip()
    if not tid:
        return {"ok": False, "error": "ticket id required"}
    m = load_meta().get(tid) or {}
    procs = scan_log_processes(project).get(tid) or []
    persons = {p["id"]: p for p in load_digital_persons()}
    owner_id = m.get("owner") or m.get("assigned_person") or ""
    owner = persons.get(owner_id)
    return {"ok": True, "id": tid, "processes": procs, "process_total": len(procs),
            "llm": m.get("llm") or [], "llm_model": m.get("llm_model"),
            "node": m.get("node") or "",
            "owner": owner,
            "assigned_person": owner_id,
            "allow": m.get("allow") or [], "deny": m.get("deny") or [],
            "schedule": m.get("schedule") or ""}


def _split_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return [x.strip() for x in re.split(r"[,\n]+", str(value or "")) if x.strip()]


def edit_meta(ticket_id: str, *, llm: Any = None, node: Any = None, allow: Any = None,
              deny: Any = None, schedule: Any = None, owner: Any = None, llm_model: Any = None,
              assigned_person: Any = None) -> dict:
    """Persist the operator's LLM / node / allow / deny / schedule / owner / llm_model edits."""
    tid = str(ticket_id or "").strip()
    data = load_meta()
    entry = data.get(tid) or {}
    if llm is not None:
        entry["llm"] = _split_list(llm)
    if node is not None:
        entry["node"] = str(node).strip()
    if allow is not None:
        entry["allow"] = _split_list(allow)
    if deny is not None:
        entry["deny"] = _split_list(deny)
    if schedule is not None:
        entry["schedule"] = str(schedule).strip()
    if owner is not None:
        entry["owner"] = str(owner).strip()
    if llm_model is not None:
        entry["llm_model"] = str(llm_model).strip()
    if assigned_person is not None:
        entry["assigned_person"] = str(assigned_person).strip()
    data[tid] = entry
    save_meta(data)
    return entry
