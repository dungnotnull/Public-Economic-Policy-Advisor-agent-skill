"""RAG grounding: load operationalised reference files into memory.

Reference markdown files under ``references/`` are loaded once and exposed as
keyed snippets so sub-advisors can inject grounded context into the system
prompt. Loading is lazy and defensive: a missing or malformed file is logged
and skipped rather than crashing the skill.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from config import get_settings
from .utils.errors import ReferenceLoadError
from .utils.logging import get_logger

_log = get_logger("grounding")

_CACHE: Optional[Dict[str, str]] = None


def references_dir() -> Path:
    settings = get_settings()
    return Path(settings.references_dir)


def load_references(force: bool = False) -> Dict[str, str]:
    """Load all ``references/*.md`` files (top-level) into a dict keyed by stem."""
    global _CACHE
    if _CACHE is not None and not force:
        return _CACHE

    out: Dict[str, str] = {}
    root = references_dir()
    if not root.exists():
        _log.warning("references_dir_missing", path=str(root))
        _CACHE = out
        return out

    for path in sorted(root.glob("*.md")):
        try:
            out[path.stem] = path.read_text(encoding="utf-8")
        except OSError as exc:
            _log.warning("reference_load_failed", path=str(path), error=str(exc))
    _log.info("references_loaded", count=len(out))
    _CACHE = out
    return out


def get_reference(key: str) -> str:
    refs = load_references()
    if key not in refs:
        raise ReferenceLoadError(f"Reference '{key}' not found in {references_dir()}")
    return refs[key]


def reset_cache() -> None:
    global _CACHE
    _CACHE = None
