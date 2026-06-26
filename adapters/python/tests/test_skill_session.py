# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Trace-first authoring surfaces on top of the episode/recall store:
#   skill://  — promote a known-good episode to a NAMED, replayable concrete flow; recall by name.
#   session:// — record steps, export to a flow document, or promote the recording to a skill.
# Tested at two levels: the TwinMemory store primitives, and the URI handlers.
import os
import tempfile
import unittest

from urirun.node.reversible import TwinMemory, environment_fingerprint
from urirun.node.episode import make_episode, intent_signature
from urirun.node import skill as S


class SkillStoreTests(unittest.TestCase):
    """The TwinMemory store primitives (no connector layer)."""

    def test_remember_recall_and_list_skill(self):
        m = TwinMemory()
        m.remember_skill("shot", {"name": "shot", "flow": {"steps": [1]}, "ts": "t1"})
        self.assertEqual(m.recall_skill("shot")["flow"]["steps"], [1])
        self.assertIsNone(m.recall_skill("missing"))
        self.assertEqual([s["name"] for s in m.skills()], ["shot"])

    def test_session_append_accumulates_in_order(self):
        m = TwinMemory()
        m.session_append("s1", {"id": "a"})
        steps = m.session_append("s1", {"id": "b"})
        self.assertEqual([s["id"] for s in steps], ["a", "b"])
        self.assertEqual([s["id"] for s in m.session_steps("s1")], ["a", "b"])
        self.assertEqual(m.session_steps("other"), [])


class SkillSessionURITests(unittest.TestCase):
    """The skill:// / session:// handlers against an isolated durable_memory."""

    def setUp(self):
        self._path = tempfile.mktemp(suffix=".json")
        self._prev = os.environ.get("URIRUN_TWIN_MEMORY")
        os.environ["URIRUN_TWIN_MEMORY"] = self._path

        def _restore():
            if self._prev is None:
                os.environ.pop("URIRUN_TWIN_MEMORY", None)
            else:
                os.environ["URIRUN_TWIN_MEMORY"] = self._prev
            if os.path.exists(self._path):
                os.unlink(self._path)
        self.addCleanup(_restore)

    def _seed_episode(self, prompt="zrob screenshot"):
        from urirun.node.twin_store import durable_memory
        mem = durable_memory()
        prof = {"platform": "linux", "wayland": True, "monitors": [{"w": 2560, "h": 1600}],
                "best": "cdp", "osLevelReliable": True}
        mem.remember("host", prof)
        ep = make_episode(experience_id="e", goal=prompt, ts="t0",
                          env_fingerprint=environment_fingerprint(prof), env_snapshot=prof,
                          flow={"steps": [{"id": "cap", "uri": "kvm://host/screen/query/capture", "payload": {}}]},
                          outcome_status="ok")
        ed = ep.to_dict()
        ed["intent_sig"] = intent_signature(prompt)
        mem.remember_episode(ed)

    def test_promote_episode_to_skill_then_recall(self):
        self._seed_episode()
        r = S._uri_skill_promote(name="shot", intent="zrob screenshot", node="host")
        self.assertTrue(r["ok"])
        self.assertEqual(r["skill"]["flow"]["steps"][0]["uri"], "kvm://host/screen/query/capture")
        rc = S._uri_skill_recall(name="shot")
        self.assertTrue(rc["found"])
        self.assertEqual(rc["flow"]["steps"][0]["uri"], "kvm://host/screen/query/capture")

    def test_promote_requires_name_and_a_matching_episode(self):
        self.assertFalse(S._uri_skill_promote(intent="x", node="host")["ok"])      # no name
        self._seed_episode()
        self.assertFalse(S._uri_skill_promote(name="x", intent="nope", node="host")["ok"])  # no match

    def test_recall_missing_skill_is_found_false(self):
        self.assertFalse(S._uri_skill_recall(name="nope")["found"])

    def test_session_record_export_and_promote(self):
        S._uri_session_append(session="s1", step={"id": "a", "uri": "kvm://host/screen/query/capture"})
        S._uri_session_append(session="s1", step={"id": "b", "uri": "twin://host/memory/command/remember"})
        ex = S._uri_session_export(session="s1")
        self.assertEqual([s["uri"] for s in ex["flow"]["steps"]],
                         ["kvm://host/screen/query/capture", "twin://host/memory/command/remember"])
        pr = S._uri_session_promote(session="s1", name="cap-flow")
        self.assertTrue(pr["ok"])
        self.assertTrue(S._uri_skill_recall(name="cap-flow")["found"])

    def test_session_append_rejects_empty_step(self):
        self.assertFalse(S._uri_session_append(session="s", step={})["ok"])

    def test_connectors_register_and_expose_bindings(self):
        self.assertTrue(S.register())
        self.assertIsInstance(S.skill_bindings(), dict)
        self.assertIsInstance(S.session_bindings(), dict)


if __name__ == "__main__":
    unittest.main()
