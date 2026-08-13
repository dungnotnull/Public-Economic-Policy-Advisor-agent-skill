"""Type-safe runtime settings for the Public Economic Policy Advisor skill.

The settings object is a frozen dataclass that is constructed once and then
cached. It is built from three layers, each one overriding the previous:

1. ``config/default.json`` -- shipped defaults.
2. An optional override file pointed to by the ``PEPA_CONFIG_FILE``
   environment variable (or discovered at ``config/local.json``).
3. Environment variables prefixed with ``PEPA_`` (e.g. ``PEPA_LLM_MODEL``).

The module deliberately avoids third-party libraries so the skill is portable
into minimal runtimes and sandboxed agents. All parsing is defensive: unknown
keys are ignored, malformed override files fall back to defaults with a logged
warning, and environment variables are coerced to the declared field type.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, fields, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:  # Python 3.11+
    from typing import Self
except ImportError:  # pragma: no cover - fallback for 3.9/3.10
    Self = "Self"  # type: ignore[assignment]


_CONFIG_DIR = Path(__file__).resolve().parent
_DEFAULT_FILE = _CONFIG_DIR / "default.json"


# --------------------------------------------------------------------------- #
# Feature flags
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class FeatureFlags:
    """Boolean toggles controlling optional skill behaviour."""

    enable_chain_of_thought_router: bool = True
    enable_sub_advisor_delegation: bool = True
    enable_structured_logging: bool = True
    enable_disclaimer_injection: bool = True
    enable_multi_viewpoint_balance: bool = True
    enable_citation_grounding: bool = True
    enable_context_window_budgeting: bool = True
    enable_graceful_llm_fallback: bool = True
    enable_rag_reference_loading: bool = True
    enable_event_emission: bool = True


# --------------------------------------------------------------------------- #
# LLM parameters
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class LLMParams:
    """Parameters passed to the backing language-model call.

    These are intentionally model-agnostic. An adapter (see
    ``policy_advisor.utils.context``) is responsible for translating them to
    the concrete provider's API.
    """

    model: str = "claude-sonnet-4-5"
    provider: str = "auto"
    """Provider selection: "auto", "anthropic", "openai", or "mock".

    "auto" picks the first provider with a usable API key in the environment,
    falling back to the offline mock adapter so the skill always runs.
    """
    api_base_url: str = ""
    """Optional override for the provider API base URL (empty = provider default)."""
    temperature: float = 0.2
    top_p: float = 0.95
    max_output_tokens: int = 4096
    request_timeout_seconds: float = 60.0
    max_retries: int = 3
    retry_backoff_base_seconds: float = 1.5


# --------------------------------------------------------------------------- #
# Context-window budgeting
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ContextBudget:
    """Token-budget plan used to keep prompts within the model's window."""

    model_context_window: int = 200_000
    reserved_output_tokens: int = 4096
    reserved_system_tokens: int = 2048
    reference_overhead_ratio: float = 0.35
    """Maximum share of the input budget that may be consumed by RAG references."""

    @property
    def available_input_tokens(self) -> int:
        usable = self.model_context_window - self.reserved_output_tokens - self.reserved_system_tokens
        return max(0, usable)

    @property
    def max_reference_tokens(self) -> int:
        return max(0, int(self.available_input_tokens * self.reference_overhead_ratio))


# --------------------------------------------------------------------------- #
# Top-level settings
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Settings:
    """Immutable, fully-resolved configuration for the skill runtime."""

    # General
    skill_name: str = "public-economic-policy-advisor"
    skill_version: str = "1.0.0"
    environment: str = "production"
    log_level: str = "INFO"
    log_format: str = "json"

    # Paths
    project_root: str = str(_CONFIG_DIR.parent)
    references_dir: str = str(_CONFIG_DIR.parent / "references")
    assets_dir: str = str(_CONFIG_DIR.parent / "assets")
    scripts_dir: str = str(_CONFIG_DIR.parent / "scripts")

    # Sub-components
    llm: LLMParams = field(default_factory=LLMParams)
    context_budget: ContextBudget = field(default_factory=ContextBudget)
    features: FeatureFlags = field(default_factory=FeatureFlags)

    # ------------------------------------------------------------------ #
    # Construction helpers
    # ------------------------------------------------------------------ #
    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "Settings":
        """Build a ``Settings`` instance from a flat dictionary.

        Unknown keys are dropped silently. Nested mappings are forwarded to
        the matching sub-dataclass when present.
        """
        known = {f.name for f in fields(cls)}
        base: Dict[str, Any] = {k: v for k, v in raw.items() if k in known}

        for sub_name, sub_cls in (
            ("llm", LLMParams),
            ("context_budget", ContextBudget),
            ("features", FeatureFlags),
        ):
            sub_raw = raw.get(sub_name)
            if isinstance(sub_raw, dict):
                base[sub_name] = _coerce_dataclass(sub_cls, sub_raw)

        return cls(**base)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    # ------------------------------------------------------------------ #
    # Environment override application
    # ------------------------------------------------------------------ #
    def with_env_overrides(self, env: Optional[Dict[str, str]] = None) -> "Settings":
        """Return a new ``Settings`` with ``PEPA_`` environment overrides applied."""
        env = env if env is not None else os.environ
        merged = self.to_dict()
        _apply_env_overrides(merged, env)
        return Settings.from_dict(merged)


# --------------------------------------------------------------------------- #
# Internal coercion helpers
# --------------------------------------------------------------------------- #
_PRIMITIVE_MAP = {bool, str, int, float}


def _coerce_dataclass(cls: type, raw: Dict[str, Any]) -> Any:
    known = {f.name for f in fields(cls)}
    clean: Dict[str, Any] = {}
    for f in fields(cls):
        if f.name in raw:
            clean[f.name] = _coerce_value(f.type, raw[f.name])
    # ignore unknown keys silently
    return cls(**{k: v for k, v in clean.items() if k in known})


def _coerce_value(declared_type: Any, value: Any) -> Any:
    if value is None:
        return None
    if declared_type is bool or declared_type == "bool":
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}
    if declared_type is int or declared_type == "int":
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
    if declared_type is float or declared_type == "float":
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
    if declared_type is str or declared_type == "str":
        return str(value)
    return value


_ENV_FLATTEN_MAP: Dict[str, Tuple[str, str]] = {
    "PEPA_SKILL_NAME": ("skill_name", "str"),
    "PEPA_SKILL_VERSION": ("skill_version", "str"),
    "PEPA_ENVIRONMENT": ("environment", "str"),
    "PEPA_LOG_LEVEL": ("log_level", "str"),
    "PEPA_LOG_FORMAT": ("log_format", "str"),
    "PEPA_PROJECT_ROOT": ("project_root", "str"),
    "PEPA_REFERENCES_DIR": ("references_dir", "str"),
    "PEPA_ASSETS_DIR": ("assets_dir", "str"),
    "PEPA_SCRIPTS_DIR": ("scripts_dir", "str"),
    "PEPA_LLM_MODEL": ("llm.model", "str"),
    "PEPA_LLM_PROVIDER": ("llm.provider", "str"),
    "PEPA_LLM_API_BASE_URL": ("llm.api_base_url", "str"),
    "PEPA_LLM_TEMPERATURE": ("llm.temperature", "float"),
    "PEPA_LLM_TOP_P": ("llm.top_p", "float"),
    "PEPA_LLM_MAX_OUTPUT_TOKENS": ("llm.max_output_tokens", "int"),
    "PEPA_LLM_REQUEST_TIMEOUT": ("llm.request_timeout_seconds", "float"),
    "PEPA_LLM_MAX_RETRIES": ("llm.max_retries", "int"),
    "PEPA_LLM_RETRY_BACKOFF": ("llm.retry_backoff_base_seconds", "float"),
    "PEPA_CTX_WINDOW": ("context_budget.model_context_window", "int"),
    "PEPA_CTX_RESERVED_OUTPUT": ("context_budget.reserved_output_tokens", "int"),
    "PEPA_CTX_RESERVED_SYSTEM": ("context_budget.reserved_system_tokens", "int"),
    "PEPA_CTX_REFERENCE_RATIO": ("context_budget.reference_overhead_ratio", "float"),
}


def _apply_env_overrides(merged: Dict[str, Any], env: Dict[str, str]) -> None:
    for env_key, (dotted, kind) in _ENV_FLATTEN_MAP.items():
        if env_key not in env:
            continue
        parts = dotted.split(".")
        target = merged
        for p in parts[:-1]:
            target = target.setdefault(p, {})
        target[parts[-1]] = _coerce_value(kind, env[env_key])

    # Feature flags: PEPA_FEATURE_<NAME>=true|false
    feats = merged.setdefault("features", {})
    for env_key, value in env.items():
        prefix = "PEPA_FEATURE_"
        if not env_key.startswith(prefix):
            continue
        flag_name = env_key[len(prefix):].lower()
        if hasattr(FeatureFlags, flag_name):
            feats[flag_name] = _coerce_value("bool", value)


# --------------------------------------------------------------------------- #
# Loading entry points
# --------------------------------------------------------------------------- #
def _load_json(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        # Log to stderr; never raise out of config loading.
        import sys
        print(f"[pepa.config] WARNING: malformed config file {path}: {exc}", file=sys.stderr)
        return {}


def load_settings(env: Optional[Dict[str, str]] = None) -> Settings:
    """Resolve settings from defaults, optional override file, and environment."""
    raw = _load_json(_DEFAULT_FILE)

    override_path = (env or os.environ).get("PEPA_CONFIG_FILE")
    if override_path:
        raw = _deep_merge(raw, _load_json(Path(override_path)))
    else:
        local = _CONFIG_DIR / "local.json"
        if local.exists():
            raw = _deep_merge(raw, _load_json(local))

    settings = Settings.from_dict(raw)
    return settings.with_env_overrides(env)


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


# --------------------------------------------------------------------------- #
# Cached accessor
# --------------------------------------------------------------------------- #
_cached: Optional[Settings] = None


def get_settings(refresh: bool = False) -> Settings:
    """Return the process-wide cached settings, loading them on first use."""
    global _cached
    if _cached is None or refresh:
        _cached = load_settings()
    return _cached


def reload_settings() -> Settings:
    """Force a reload of settings (e.g. after env changes in tests)."""
    return get_settings(refresh=True)
