"""Tests for hooks: lifecycle, state synchronisation, and event emission."""

from policy_advisor.hooks import EventBus, LifecycleHookBus, LifecyclePhase, StateStore, StateSnapshot


def test_lifecycle_hooks_fire_in_order_and_isolate_failures():
    calls = []
    bus = LifecycleHookBus()
    bus.register(lambda phase, rid, ctx: calls.append(("a", phase.value)))
    bus.register(lambda phase, rid, ctx: (_ for _ in ()).throw(RuntimeError("boom")))  # failing observer
    bus.register(lambda phase, rid, ctx: calls.append(("c", phase.value)))
    bus.fire(LifecyclePhase.ROUTING, "req-1", {"k": "v"})
    assert ("a", "routing") in calls
    assert ("c", "routing") in calls  # failing observer did not block others


def test_state_store_snapshot_restore():
    store = StateStore()
    store.set("x", {"nested": [1, 2]})
    snap: StateSnapshot = store.snapshot()
    store.set("x", "changed")
    assert store.get("x") == "changed"
    store.restore(snap)
    assert store.get("x") == {"nested": [1, 2]}
    assert store.snapshot().version == snap.version


def test_state_store_deep_copies_values():
    store = StateStore()
    original = {"list": [1, 2]}
    store.set("data", original)
    original["list"].append(3)
    assert store.get("data") == {"list": [1, 2]}


def test_event_bus_emits_and_retains():
    seen = []
    bus = EventBus()
    bus.subscribe(lambda e: seen.append(e.type))
    ev = bus.emit("skill.test", foo="bar")
    assert ev.type == "skill.test"
    assert ev.payload == {"foo": "bar"}
    assert seen == ["skill.test"]
    assert bus.recent()[0].type == "skill.test"


def test_event_bus_isolates_failing_subscribers():
    bus = EventBus()
    bus.subscribe(lambda e: (_ for _ in ()).throw(ValueError("x")))
    bus.subscribe(lambda e: bus.emit  # noop
                  )
    ev = bus.emit("ok", n=1)
    assert ev.type == "ok"
