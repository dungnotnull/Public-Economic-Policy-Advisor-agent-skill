"""Structured event emitter.

A tiny in-process event bus: producers emit typed events, subscribers receive
them. Subscribers are isolated (a failing subscriber does not block others).
The bus retains a bounded ring buffer of recent events for diagnostics.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Deque, Dict, List, Optional

from ..utils.logging import get_logger

_log = get_logger("hooks.events")


@dataclass
class Event:
    type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="milliseconds"))


Subscriber = Callable[[Event], None]


class EventBus:
    def __init__(self, buffer_size: int = 256) -> None:
        self._subscribers: List[Subscriber] = []
        self._buffer: Deque[Event] = deque(maxlen=buffer_size)

    def subscribe(self, subscriber: Subscriber) -> None:
        self._subscribers.append(subscriber)

    def emit(self, event_type: str, **payload: Any) -> Event:
        event = Event(type=event_type, payload=payload)
        self._buffer.append(event)
        for sub in list(self._subscribers):
            try:
                sub(event)
            except Exception as exc:  # noqa: BLE001
                _log.warning("event_subscriber_failed", event_type=event_type, error=str(exc))
        _log.info("event_emitted", event_type=event_type)
        return event

    def recent(self, limit: Optional[int] = None) -> List[Event]:
        items = list(self._buffer)
        return items[-limit:] if limit else items
