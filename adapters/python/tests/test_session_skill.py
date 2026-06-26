# Author: Tom Sapletta · https://tom.sapletta.com
# Tests for session:// trace-first recorder and skill:// promote-to-name (Faza 3).
# End-to-end: start → append → commit → replay → promote → flow:// address.
from __future__ import annotations

import os
import tempfile
import unittest
from unittest import mock

from urirun.host.dispatch import inprocess_fallback as ip, _flow_scheme_dispatch


def _ensure_handlers():
    """Force reload to register new handlers in decorated_bindings."""
    import importlib
    import urirun.node.skill as sk
    importlib.reload(sk)


class TestSessionRecorder(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="session-skill-")
        self._old = os.environ.get("URIRUN_TWIN_MEMORY")
        os.environ["URIRUN_TWIN_MEMORY"] = os.path.join(self.tmp, "mem.json")
        _ensure_handlers()

    def tearDown(self):
        if self._old is None:
            os.environ.pop("URIRUN_TWIN_MEMORY", None)
        else:
            os.environ["URIRUN_TWIN_MEMORY"] = self._old
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ── command/start ─────────────────────────────────────────────────────────

    def test_start_creates_session(self):
        r = ip("session://host/session/command/start",
               {"session": "s1", "goal": "capture screen"})
        self.assertTrue(r.get("ok"), r)
        res = r.get("result") or {}
        self.assertEqual(res.get("status"), "recording")
        self.assertEqual(res.get("steps"), 0)
        self.assertEqual(res.get("goal"), "capture screen")

    def test_start_is_idempotent(self):
        ip("session://host/session/command/start", {"session": "s-id", "goal": "g1"})
        ip("session://host/session/command/append",
           {"session": "s-id", "step": {"id": "x", "uri": "kvm://host/screen/query/capture"}})
        r = ip("session://host/session/command/start", {"session": "s-id", "goal": "g2"})
        res = r.get("result") or {}
        self.assertEqual(res.get("steps"), 1, "second start must not wipe steps")
        self.assertEqual(res.get("goal"), "g1", "second start must not override goal")

    # ── command/append + query/events ─────────────────────────────────────────

    def test_append_then_events(self):
        ip("session://host/session/command/start", {"session": "s2"})
        ip("session://host/session/command/append",
           {"session": "s2", "step": {"id": "a", "uri": "kvm://host/screen/query/capture"}})
        ip("session://host/session/command/append",
           {"session": "s2", "step": {"id": "b", "uri": "twin://host/env/query/drift"}})
        r = ip("session://host/session/query/events", {"session": "s2"})
        res = r.get("result") or {}
        self.assertTrue(res.get("found"))
        self.assertEqual(res.get("total"), 2)
        uris = [s["uri"] for s in (res.get("steps") or [])]
        self.assertIn("kvm://host/screen/query/capture", uris)
        self.assertIn("twin://host/env/query/drift", uris)

    def test_events_unknown_session_returns_not_found(self):
        r = ip("session://host/session/query/events", {"session": "ghost-session"})
        res = r.get("result") or {}
        self.assertFalse(res.get("found"))
        self.assertEqual(res.get("steps"), [])

    # ── command/commit ────────────────────────────────────────────────────────

    def test_commit_seals_session(self):
        ip("session://host/session/command/start", {"session": "s3"})
        ip("session://host/session/command/append",
           {"session": "s3", "step": {"id": "x", "uri": "kvm://host/screen/query/capture"}})
        r = ip("session://host/session/command/commit", {"session": "s3"})
        res = r.get("result") or {}
        self.assertEqual(res.get("status"), "committed")
        self.assertIsNotNone(res.get("committed_at"))
        self.assertEqual(res.get("steps"), 1)

    # ── query/export-flow ─────────────────────────────────────────────────────

    def test_export_flow_materialises_steps(self):
        ip("session://host/session/command/start", {"session": "s4", "goal": "daily capture"})
        ip("session://host/session/command/append",
           {"session": "s4", "step": {"id": "s", "uri": "kvm://host/screen/query/capture"}})
        r = ip("session://host/session/query/export-flow",
               {"session": "s4", "title": "Daily Screenshot"})
        res = r.get("result") or {}
        flow = res.get("flow") or {}
        self.assertEqual(len(flow.get("steps") or []), 1)
        self.assertEqual((flow.get("task") or {}).get("title"), "Daily Screenshot")

    # ── command/replay (dry-run) ──────────────────────────────────────────────

    def test_replay_dryruns_recorded_steps(self):
        ip("session://host/session/command/start", {"session": "s5"})
        ip("session://host/session/command/append",
           {"session": "s5", "step": {"id": "s", "uri": "twin://host/env/query/drift",
                                      "payload": {}, "depends_on": []}})
        dispatched: list[str] = []
        def fake_call(uri, payload=None, *a, **kw):
            dispatched.append(uri)
            return {"ok": True, "result": {"value": {"ok": True, "drift": False, "known": True}}}
        with mock.patch("urirun.v2_service.call", side_effect=fake_call):
            r = ip("session://host/session/command/replay",
                   {"session": "s5", "execute": True})
        res = r.get("result") or {}
        self.assertTrue(res.get("ok"), res)
        self.assertIn("twin://host/env/query/drift", dispatched)

    def test_replay_empty_session_fails(self):
        r = ip("session://host/session/command/replay", {"session": "empty-ses"})
        res = r.get("result") or {}
        self.assertFalse(res.get("ok"))

    # ── command/promote-to-skill → skill://recall → flow:// ──────────────────

    def test_promote_then_recall_skill(self):
        ip("session://host/session/command/start", {"session": "s6", "goal": "take screenshot"})
        ip("session://host/session/command/append",
           {"session": "s6", "step": {"id": "sc", "uri": "kvm://host/screen/query/capture"}})
        ip("session://host/session/command/promote-to-skill",
           {"session": "s6", "name": "take-screenshot"})
        r = ip("skill://host/skill/query/recall", {"name": "take-screenshot"})
        res = r.get("result") or {}
        self.assertTrue(res.get("found"))
        steps = (res.get("flow") or {}).get("steps") or []
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0]["uri"], "kvm://host/screen/query/capture")

    def test_promote_then_flow_scheme_get(self):
        ip("session://host/session/command/start", {"session": "s7"})
        ip("session://host/session/command/append",
           {"session": "s7",
            "step": {"id": "sc", "uri": "kvm://host/screen/query/capture", "payload": {}}})
        ip("session://host/session/command/promote-to-skill",
           {"session": "s7", "name": "quick-cap"})
        r = _flow_scheme_dispatch("flow://host/quick-cap/query/get")
        self.assertIsNotNone(r)
        self.assertTrue(r.get("ok"))
        out = r.get("result") or {}
        self.assertEqual(out.get("skill"), "quick-cap")
        self.assertEqual(len(out.get("steps") or []), 1)

    def test_skill_list_shows_promoted_skill(self):
        ip("session://host/session/command/start", {"session": "s8"})
        ip("session://host/session/command/append",
           {"session": "s8", "step": {"id": "x", "uri": "kvm://host/screen/query/capture"}})
        ip("session://host/session/command/promote-to-skill",
           {"session": "s8", "name": "listed-skill"})
        r = ip("skill://host/skill/query/list", {})
        res = r.get("result") or {}
        names = [s.get("name") for s in (res.get("skills") or [])]
        self.assertIn("listed-skill", names)


class TestSkillFromEpisode(unittest.TestCase):
    """skill://host/skill/command/promote from a known-good episode (not a session)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="skill-ep-")
        self._old = os.environ.get("URIRUN_TWIN_MEMORY")
        os.environ["URIRUN_TWIN_MEMORY"] = os.path.join(self.tmp, "mem.json")
        _ensure_handlers()

    def tearDown(self):
        if self._old is None:
            os.environ.pop("URIRUN_TWIN_MEMORY", None)
        else:
            os.environ["URIRUN_TWIN_MEMORY"] = self._old
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _mem(self):
        from urirun.node.twin_store import durable_memory
        return durable_memory()

    def test_promote_from_episode_id(self):
        ep = {
            "episode_id": "ep-promote",
            "goal": "capture and remember",
            "plan": {"steps": [{"id": "s", "uri": "kvm://host/screen/query/capture"}]},
            "reality": {"fingerprint": "fp-abc"},
            "outcome": {"status": "ok"},
            "ts": "2026-01-01T00:00:00Z",
        }
        self._mem().remember_episode(ep)
        r = ip("skill://host/skill/command/promote",
               {"name": "ep-skill", "episode_id": "ep-promote"})
        res = r.get("result") or {}
        self.assertTrue(res.get("ok"), res)
        self.assertEqual(res.get("name"), "ep-skill")
        skill = res.get("skill") or {}
        self.assertEqual(skill.get("episode_id"), "ep-promote")
        # Recall by name
        r2 = ip("skill://host/skill/query/recall", {"name": "ep-skill"})
        self.assertTrue((r2.get("result") or {}).get("found"))

    def test_promote_fails_without_episode(self):
        r = ip("skill://host/skill/command/promote",
               {"name": "ghost-skill", "episode_id": "ep-nonexistent"})
        res = r.get("result") or {}
        self.assertFalse(res.get("ok"))


if __name__ == "__main__":
    unittest.main()
