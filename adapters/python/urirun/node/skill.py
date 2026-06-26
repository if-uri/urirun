# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Two URI surfaces that close the trace-first authoring loop on top of the episode/recall store:
#
#   skill://   — a PROMOTED known-good run, replayable by NAME. A skill is a concrete flow (the
#                plan of a successful episode), NOT a parameterized generalization — so it needs no
#                inference: promote names it, recall returns it, and the env fingerprint it carries
#                lets a drifted environment be re-planned rather than silently replayed.
#   session:// — a trace-first RECORDER. Append the steps that actually ran, then export them to a
#                flow document or promote them to a skill. The dual of plan-first authoring.
#
# Registered in-process (mirrors urirun.node.flow's twin connector). Both ride the existing
# durable_memory namespaces (_skills / _sessions) — no new store.
from __future__ import annotations

import time


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _memory():
    from urirun.node.twin_store import durable_memory  # noqa: PLC0415
    return durable_memory()


def _episode_for(memory, payload: dict) -> dict | None:
    """Resolve the episode to promote: by explicit ``episode_id``, else the latest ok-status
    episode matching ``intent`` × the node's known-good env fingerprint (the recall key)."""
    eid = payload.get("episode_id") or payload.get("episodeId")
    if eid:
        ep = memory.episode_store.get(eid)
        return ep if isinstance(ep, dict) else None
    intent = payload.get("intent") or payload.get("prompt")
    node = payload.get("node")
    if intent and node:
        from urirun.node.episode import intent_signature  # noqa: PLC0415
        env_fp = (memory.known_good(node) or {}).get("fingerprint") or ""
        if env_fp:
            return memory.recall_episode(intent_signature(intent), env_fp)
    return None


def _uri_skill_promote(payload: dict) -> dict:
    """Handler for skill://<node>/skill/command/promote.

    Payload: {name, episode_id? | (intent + node)}. Names a known-good episode's plan as a
    reusable skill. Returns {ok, name, skill} or an error when no matching episode exists."""
    name = str(payload.get("name") or "").strip()
    if not name:
        return {"ok": False, "error": "skill name required"}
    memory = _memory()
    ep = _episode_for(memory, payload)
    if not ep:
        return {"ok": False, "error": "no matching known-good episode to promote"}
    steps = (ep.get("plan") or {}).get("steps") or []
    if not steps:
        return {"ok": False, "error": "episode has no plan steps"}
    record = {
        "name": name,
        "flow": {"steps": steps, "task": {"id": name, "source": "skill", "title": name}},
        "episode_id": ep.get("episode_id"),
        "intent_sig": ep.get("intent_sig"),
        "env_fingerprint": (ep.get("reality") or {}).get("fingerprint"),
        "ts": _now(),
    }
    memory.remember_skill(name, record)
    return {"ok": True, "name": name, "skill": record}


def _uri_skill_recall(payload: dict) -> dict:
    """Handler for skill://<node>/skill/query/recall.  Payload: {name} -> {ok, found, skill}."""
    name = str(payload.get("name") or "").strip()
    if not name:
        return {"ok": False, "error": "skill name required"}
    rec = _memory().recall_skill(name)
    if not rec:
        return {"ok": True, "found": False, "name": name}
    return {"ok": True, "found": True, "name": name, "skill": rec, "flow": rec.get("flow")}


def _uri_skill_list(payload: dict) -> dict:
    """Handler for skill://<node>/skill/query/list.  Returns {ok, skills: [{name, ts, episode_id}]}."""
    skills = _memory().skills()
    summary = [{"name": s.get("name"), "ts": s.get("ts"), "episode_id": s.get("episode_id")}
               for s in skills if isinstance(s, dict)]
    return {"ok": True, "skills": summary, "total": len(summary)}


def _uri_session_append(payload: dict) -> dict:
    """Handler for session://<node>/session/command/append.

    Payload: {session, step}. Records one step into a session trace. Returns {ok, session, steps}."""
    sid = str(payload.get("session") or payload.get("session_id") or "").strip()
    step = payload.get("step")
    if not sid or not isinstance(step, dict) or not step:
        return {"ok": False, "error": "session id and a non-empty step required"}
    steps = _memory().session_append(sid, step)
    return {"ok": True, "session": sid, "steps": len(steps)}


def _uri_session_export(payload: dict) -> dict:
    """Handler for session://<node>/session/query/export-flow.

    Payload: {session, title?}. Materializes the recorded session as a flow document."""
    sid = str(payload.get("session") or payload.get("session_id") or "").strip()
    if not sid:
        return {"ok": False, "error": "session id required"}
    steps = _memory().session_steps(sid)
    flow = {"steps": steps,
            "task": {"id": sid, "source": "session", "title": payload.get("title") or sid}}
    return {"ok": True, "session": sid, "flow": flow, "steps": len(steps)}


def _uri_session_promote(payload: dict) -> dict:
    """Handler for session://<node>/session/command/promote-to-skill.

    Payload: {session, name}. Names a recorded session's steps as a reusable skill."""
    sid = str(payload.get("session") or payload.get("session_id") or "").strip()
    name = str(payload.get("name") or "").strip()
    if not sid or not name:
        return {"ok": False, "error": "session id and skill name required"}
    memory = _memory()
    steps = memory.session_steps(sid)
    if not steps:
        return {"ok": False, "error": "session has no steps to promote"}
    record = {
        "name": name,
        "flow": {"steps": steps, "task": {"id": name, "source": "skill", "title": name}},
        "from_session": sid,
        "ts": _now(),
    }
    memory.remember_skill(name, record)
    return {"ok": True, "name": name, "skill": record}


def _build_connectors():
    """Create the skill:// and session:// connectors and register their handlers. Returns
    (skill_conn, session_conn) — or (None, None) if urirun isn't importable yet (best-effort)."""
    try:
        import urirun  # noqa: PLC0415
        skill = urirun.connector("skill", scheme="skill")
        skill.handler("skill/command/promote",
                      meta={"label": "Promote a known-good episode to a named, replayable skill"})(_uri_skill_promote)
        skill.handler("skill/query/recall",
                      meta={"label": "Recall a named skill's flow for direct reuse"})(_uri_skill_recall)
        skill.handler("skill/query/list",
                      meta={"label": "List promoted skills"})(_uri_skill_list)
        session = urirun.connector("session", scheme="session")
        session.handler("session/command/append",
                        meta={"label": "Append a step to a trace-first session recorder"})(_uri_session_append)
        session.handler("session/query/export-flow",
                        meta={"label": "Export a recorded session as a flow document"})(_uri_session_export)
        session.handler("session/command/promote-to-skill",
                        meta={"label": "Promote a recorded session to a named skill"})(_uri_session_promote)
        return skill, session
    except Exception:  # noqa: BLE001 - connector registration is optional
        return None, None


_SKILL_CONN, _SESSION_CONN = _build_connectors()


def skill_bindings() -> dict:
    """Entry-point binding document for the skill:// scheme (``urirun.bindings`` group)."""
    return _SKILL_CONN.bindings() if _SKILL_CONN is not None else {}


def session_bindings() -> dict:
    """Entry-point binding document for the session:// scheme (``urirun.bindings`` group)."""
    return _SESSION_CONN.bindings() if _SESSION_CONN is not None else {}


def register() -> bool:
    """True when both in-process connectors registered (importing this module already did so)."""
    return _SKILL_CONN is not None and _SESSION_CONN is not None
