"""State synchronisation store.

Provides a simple, in-memory key/value store with snapshot/restore so the
skill can persist conversational and invocation state across turns and resume
gracefully after errors. Backed by plain dicts (no external dependency); an
optional pluggable backend can be supplied for production persistence.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from ..utils.logging import get_logger

_log = get_logger("hooks.state")


@dataclass
class StateSnapshot:
    data: Dict[str, Any]
    version: int


class StateStore:
    """Thread-unsafe, single-process state store with snapshot/restore."""

    def __init__(self, backend: Optional[Callable[[], Dict[str, Any]]] = None) -> None:
        self._data: Dict[str, Any] = {}
        self._version = 0
        self._backend = backend

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = copy.deepcopy(value)
        self._version += 1
        _log.debug("state_set", key=key, version=self._version)

    def update(self, mapping: Dict[str, Any]) -> None:
        for k, v in mapping.items():
            self.set(k, v)

    def snapshot(self) -> StateSnapshot:
        return StateSnapshot(data=copy.deepcopy(self._data), version=self._version)

    def restore(self, snapshot: StateSnapshot) -> None:
        self._data = copy.deepcopy(snapshot.data)
        self._version = snapshot.version
        _log.info("state_restored", version=self._version)

    def to_json(self) -> str:
        return json.dumps(self._data, ensure_ascii=False, default=str, indent=2)

    def clear(self) -> None:
        self._data.clear()
        self._version = 0
