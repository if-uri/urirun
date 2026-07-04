# Tests for the prompt-scoped twin widget data path:
# - api_twin_state ?prompt= returns a "focus" block (scoped events + durable Episode)
#   so a chat-embedded widget replays THAT run instead of the latest global event,
# - step events carry the real monitor layout (widget NOW/NEXT maps are not empty),
# - twin:inventory is classified as infra (widget shows actions, not bookkeeping),
# - _phase_timer (chat_ask timings) accumulates per-phase milliseconds.
import pytest

from urirun.host.twin_bridge import (
    TWIN_EVENT_HUB,
    _is_infra_step,
    _node_env_profile,
    _publish_step_event,
    _widget_monitors,
    api_twin_state,
)
from urirun.node.episode import intent_signature
from urirun.node.reversible import TwinMemory


# ──────────────────────────────────────────── _widget_monitors ──────────── #

def test_widget_monitors_prefers_logical_geometry():
    mons = _widget_monitors([{
        "connector": "HDMI-1", "x": 0, "y": 1609, "scale": 1.25, "primary": True,
        "width": 2560, "height": 1600, "logicalWidth": 2048, "logicalHeight": 1280,
    }])
    assert mons == [{"id": "HDMI-1", "x": 0, "y": 1609,
                     "width": 2048, "height": 1280, "scale": 1.25}]


def test_widget_monitors_falls_back_to_physical_and_index():
    mons = _widget_monitors([{"index": 2, "x": 100, "y": 0, "width": 3840, "height": 2160}])
    assert mons == [{"id": "mon2", "x": 100, "y": 0,
                     "width": 3840, "height": 2160, "scale": 1}]


def test_widget_monitors_tolerates_junk_entries():
    assert _widget_monitors([None, "junk", 42]) == []
    assert _widget_monitors(None) == []


# ──────────────────────────────────────────── _node_env_profile ─────────── #

def test_node_env_profile_reads_known_good(monkeypatch):
    mem = TwinMemory()
    mem.remember("host", {
        "monitors": [{"connector": "DP-1", "x": 0, "y": 0,
                      "logicalWidth": 2048, "logicalHeight": 1280, "scale": 1.25}],
    })
    import urirun.node.twin_store as ts
    monkeypatch.setattr(ts, "durable_memory", lambda: mem)
    fp, mons = _node_env_profile("host")
    assert fp == (mem.known_good("host") or {}).get("fingerprint")
    assert fp  # non-empty
    assert mons[0]["id"] == "DP-1"
    assert mons[0]["width"] == 2048


def test_node_env_profile_survives_store_failure(monkeypatch):
    import urirun.node.twin_store as ts
    monkeypatch.setattr(ts, "durable_memory", lambda: (_ for _ in ()).throw(RuntimeError("down")))
    assert _node_env_profile("host") == ("", [])


# ──────────────────────────────────────────── _is_infra_step ────────────── #

@pytest.mark.parametrize("step_id,infra", [
    ("twin:inventory:host", True),
    ("twin:drift:host", True),
    ("memory:remember", True),
    ("preflight-screen", True),
    ("capture_screen", False),
])
def test_is_infra_step_classification(step_id, infra):
    assert _is_infra_step({"id": step_id}) is infra


# ──────────────────────────────────────────── step event monitors ───────── #

def test_publish_step_event_carries_monitors():
    monitors = [{"id": "DP-1", "x": 0, "y": 0, "width": 2048, "height": 1280, "scale": 1.25}]
    before = TWIN_EVENT_HUB.replay_since(0)
    _publish_step_event({"id": "s1", "uri": "kvm://host/screen/query/capture", "ok": True},
                        "host", monitors=monitors)
    events = [e for e in TWIN_EVENT_HUB.replay_since(0) if e not in before]
    evt = [e for e in events if e.get("uri") == "twin://monitor/event"][-1]
    assert evt["transition"]["before"]["monitors"] == monitors
    assert evt["transition"]["after"]["monitors"] == monitors


# ──────────────────────────────────────────── api_twin_state focus ──────── #

def _episode_for(prompt: str) -> dict:
    return {
        "episode_id": "ep-1", "experience_id": "", "goal": prompt,
        "intent_sig": intent_signature(prompt),
        "reality": {"fingerprint": "env-abc"},
        "plan": {}, "proofs": [],
        "execution": {
            "timeline": [
                {"id": "twin:drift:host", "uri": "twin://host/env/query/drift", "ok": True},
                {"id": "capture_screen", "uri": "kvm://host/screen/query/capture",
                 "ok": True, "reversible": True, "target": "host"},
            ],
            "results": {},
        },
        "artifacts": [], "outcome": {"status": "ok", "next_intent": ""},
        "ts": "2026-07-04T07:08:58Z",
    }


def _fake_memory(monkeypatch, episodes):
    mem = TwinMemory()
    for ep in episodes:
        mem.remember_episode(ep)
    import urirun.node.twin_store as ts
    monkeypatch.setattr(ts, "durable_memory", lambda: mem)
    return mem


def test_api_twin_state_focus_matches_prompt_episode(monkeypatch):
    _fake_memory(monkeypatch, [_episode_for("zrob zrzut ekranu")])
    status, body = api_twin_state(".", None, None, {"prompt": ["zrob zrzut ekranu"]})
    assert status == 200
    focus = body["focus"]
    assert focus["prompt"] == "zrob zrzut ekranu"
    assert focus["intentSig"] == intent_signature("zrob zrzut ekranu")
    assert focus["episode"] is not None
    assert focus["episode"]["goal"] == "zrob zrzut ekranu"
    assert isinstance(focus["events"], list)


def test_api_twin_state_focus_none_without_prompt(monkeypatch):
    _fake_memory(monkeypatch, [_episode_for("zrob zrzut ekranu")])
    status, body = api_twin_state(".", None, None, {})
    assert status == 200
    assert body["focus"] is None


def test_api_twin_state_focus_no_match(monkeypatch):
    _fake_memory(monkeypatch, [_episode_for("zrob zrzut ekranu")])
    status, body = api_twin_state(".", None, None, {"prompt": ["otworz przegladarke"]})
    assert status == 200
    focus = body["focus"]
    assert focus["episode"] is None
    assert focus["intentSig"] == intent_signature("otworz przegladarke")


# ──────────────────────────────────────────── _phase_timer ──────────────── #

def test_phase_timer_accumulates_ms():
    from urirun.host.chat_orchestrator import _phase_timer
    timings: dict = {}
    lap = _phase_timer(timings)
    lap("a")
    lap("b")
    lap("a")  # repeated phase accumulates instead of overwriting
    assert set(timings) == {"a", "b"}
    assert all(isinstance(v, float) and v >= 0 for v in timings.values())
