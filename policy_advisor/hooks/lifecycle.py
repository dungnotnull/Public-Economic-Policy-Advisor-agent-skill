"""Lifecycle hook bus.

Allows callers to register callbacks that fire before and after each phase of
a skill invocation. Phases are: ``intake``, ``routing``, ``delegation``,
``tool_execution``, ``synthesis``, and ``output``. Hooks may mutate a shared
context dict but cannot short-circuit execution; failures in a hook are logged
and swallowed so a misbehaving observer never breaks the skill.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List

from ..utils.logging import get_logger

_log = get_logger("hooks.lifecycle")


class LifecyclePhase(str, Enum):
    INTAKE = "intake"
    ROUTING = "routing"
    DELEGATION = "delegation"
    TOOL_EXECUTION = "tool_execution"
    SYNTHESIS = "synthesis"
    OUTPUT = "output"


HookCallback = Callable[[LifecyclePhase, str, Dict[str, Any]], None]


@dataclass
class LifecycleHookBus:
    callbacks: List[HookCallback] = field(default_factory=list)

    def register(self, callback: HookCallback) -> None:
        self.callbacks.append(callback)

    def fire(self, phase: LifecyclePhase, request_id: str, context: Dict[str, Any]) -> None:
        for cb in self.callbacks:
            try:
                cb(phase, request_id, dict(context))
            except Exception as exc:  # noqa: BLE001 - observers must not break the flow
                _log.warning("lifecycle_hook_failed", phase=phase.value, error=str(exc))
