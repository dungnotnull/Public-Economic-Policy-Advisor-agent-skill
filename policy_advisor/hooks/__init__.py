"""Lifecycle hooks, state synchronisation, and event emission for the skill.

Hooks let external code observe and react to skill execution without coupling
to the internal agent flow. The hook bus supports three concerns:

* **Lifecycle** -- before/after each phase of a skill invocation.
* **State sync** -- snapshot and restore conversational/skill state.
* **Event emission** -- structured event records for observability pipelines.
"""

from .lifecycle import LifecycleHookBus, LifecyclePhase
from .state_sync import StateStore, StateSnapshot
from .event_emitter import EventBus, Event

__all__ = [
    "LifecycleHookBus",
    "LifecyclePhase",
    "StateStore",
    "StateSnapshot",
    "EventBus",
    "Event",
]
