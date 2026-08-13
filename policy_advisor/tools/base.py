"""Base classes for the tool system.

A :class:`Tool` declares its name, description, input schema, and output
schema, and implements :meth:`execute`. The :class:`ToolRegistry` resolves
tools by name and validates inputs against the declared schema before
delegating execution, so sub-advisors can invoke tools dynamically and
safely.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from ..utils.errors import ToolExecutionError, ValidationError
from ..utils.logging import get_logger

_log = get_logger("tools")


# --------------------------------------------------------------------------- #
# Lightweight JSON-Schema validator (stdlib only)
# --------------------------------------------------------------------------- #
def _validate(value: Any, schema: Dict[str, Any], path: str = "$") -> List[str]:
    """Return a list of human-readable validation errors (empty if valid)."""
    errors: List[str] = []
    if not isinstance(schema, dict):
        return errors

    stype = schema.get("type")
    if stype is not None:
        type_ok = True
        if stype == "object":
            type_ok = isinstance(value, dict)
        elif stype == "array":
            type_ok = isinstance(value, list)
        elif stype == "string":
            type_ok = isinstance(value, str)
        elif stype == "number":
            type_ok = isinstance(value, (int, float)) and not isinstance(value, bool)
        elif stype == "integer":
            type_ok = isinstance(value, int) and not isinstance(value, bool)
        elif stype == "boolean":
            type_ok = isinstance(value, bool)
        if not type_ok:
            errors.append(f"{path}: expected type {stype}, got {type(value).__name__}")
            return errors

    if stype == "object" and isinstance(value, dict):
        required = schema.get("required", [])
        for req in required:
            if req not in value:
                errors.append(f"{path}: missing required property '{req}'")
        props = schema.get("properties", {})
        for key, subschema in props.items():
            if key in value:
                errors.extend(_validate(value[key], subschema, f"{path}.{key}"))

    if stype == "array" and isinstance(value, list):
        items = schema.get("items")
        if isinstance(items, dict):
            for i, item in enumerate(value):
                errors.extend(_validate(item, items, f"{path}[{i}]"))
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            errors.append(f"{path}: expected at least {min_items} items")

    if stype == "string" and isinstance(value, str):
        pattern = schema.get("pattern")
        if pattern and not re.search(pattern, value):
            errors.append(f"{path}: does not match pattern {pattern}")
        enum = schema.get("enum")
        if enum is not None and value not in enum:
            errors.append(f"{path}: '{value}' not in allowed values {enum}")

    return errors


@dataclass
class ToolResult:
    """Envelope returned by every tool execution."""

    tool: str
    ok: bool
    output: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class Tool:
    """Abstract base class for a domain tool."""

    name: str = ""
    description: str = ""
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}

    def execute(self, **inputs: Any) -> ToolResult:  # pragma: no cover - abstract
        raise NotImplementedError

    # Convenience for sub-advisors that want a plain dict back.
    def __call__(self, inputs: Dict[str, Any]) -> ToolResult:
        return self.run(inputs)

    def run(self, inputs: Dict[str, Any]) -> ToolResult:
        """Validate inputs, execute, validate outputs, and return a result."""
        errors = _validate(inputs, self.input_schema)
        if errors:
            raise ValidationError("; ".join(errors))
        try:
            result = self.execute(**inputs)
        except ToolExecutionError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ToolExecutionError(f"{self.name} failed: {exc}", tool=self.name) from exc
        out_errors = _validate(result.output, self.output_schema)
        if out_errors:
            _log.warning("tool_output_violated_schema", tool=self.name, errors=out_errors)
            result.warnings.extend(out_errors)
        return result


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #
class ToolRegistry:
    """Resolves tools by name and tracks what was invoked."""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}
        self._invocations: List[Dict[str, Any]] = []

    def register(self, tool: Tool) -> None:
        if not tool.name:
            raise ValueError("Tool must declare a non-empty name")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise ToolExecutionError(f"Unknown tool '{name}'", tool=name)
        return self._tools[name]

    def available(self) -> List[str]:
        return sorted(self._tools)

    def invoke(self, name: str, inputs: Dict[str, Any]) -> ToolResult:
        tool = self.get(name)
        result = tool.run(inputs)
        self._invocations.append({"tool": name, "ok": result.ok})
        _log.info("tool_invoked", tool=name, ok=result.ok)
        return result

    def invocation_log(self) -> List[Dict[str, Any]]:
        return list(self._invocations)


_REGISTRY: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = ToolRegistry()
    return _REGISTRY
