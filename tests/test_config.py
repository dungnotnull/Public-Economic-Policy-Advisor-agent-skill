"""Tests for config layering, feature flags, and LLM fallback behaviour."""

import pytest

from config import reload_settings
from config.settings import Settings, load_settings
from policy_advisor.utils.context import MockLLMAdapter, RetryingLLMAdapter, token_estimate, build_system_prompt
from policy_advisor.utils.errors import LLMInvocationError


def test_defaults_load():
    s = load_settings(env={})
    assert s.skill_name == "public-economic-policy-advisor"
    assert s.llm.model
    assert s.features.enable_disclaimer_injection is True


def test_env_overrides_apply():
    s = load_settings(env={"PEPA_LLM_MODEL": "claude-opus-4", "PEPA_LLM_TEMPERATURE": "0.7", "PEPA_FEATURE_ENABLE_GRACEFUL_LLM_FALLBACK": "false"})
    assert s.llm.model == "claude-opus-4"
    assert s.llm.temperature == 0.7
    assert s.features.enable_graceful_llm_fallback is False


def test_context_budget_math():
    s = load_settings(env={})
    assert s.context_budget.available_input_tokens > 0
    assert s.context_budget.max_reference_tokens > 0
    assert s.context_budget.max_reference_tokens <= int(s.context_budget.available_input_tokens * 0.35) + 1


def test_token_estimate_positive():
    assert token_estimate("") == 0
    assert token_estimate("abcd") >= 1


def test_build_system_prompt_includes_disclaimer_and_references():
    prompt = build_system_prompt(reference_snippets=["A key externality principle."])
    assert "Public Economic Policy Advisor" in prompt
    assert "MANDATORY DISCLAIMER" in prompt
    assert "externality principle" in prompt


class _AlwaysFails:
    def complete(self, system_prompt, user_prompt, **kwargs):
        raise RuntimeError("network down")


def test_retrying_adapter_falls_back_gracefully(monkeypatch):
    monkeypatch.setenv("PEPA_LLM_MAX_RETRIES", "2")
    monkeypatch.setenv("PEPA_LLM_RETRY_BACKOFF", "0.0")
    reload_settings()
    adapter = RetryingLLMAdapter(_AlwaysFails(), MockLLMAdapter())
    resp = adapter.complete("sys", "user")
    assert resp.finish_reason == "fallback"
    assert "FALLBACK" in resp.text
    monkeypatch.delenv("PEPA_LLM_MAX_RETRIES", raising=False)
    monkeypatch.delenv("PEPA_LLM_RETRY_BACKOFF", raising=False)
    reload_settings()


def test_retrying_adapter_raises_when_fallback_disabled(monkeypatch):
    monkeypatch.setenv("PEPA_FEATURE_ENABLE_GRACEFUL_LLM_FALLBACK", "false")
    monkeypatch.setenv("PEPA_LLM_MAX_RETRIES", "2")
    monkeypatch.setenv("PEPA_LLM_RETRY_BACKOFF", "0.0")
    reload_settings()
    adapter = RetryingLLMAdapter(_AlwaysFails(), MockLLMAdapter())
    with pytest.raises(LLMInvocationError):
        adapter.complete("sys", "user")
    monkeypatch.delenv("PEPA_FEATURE_ENABLE_GRACEFUL_LLM_FALLBACK", raising=False)
    monkeypatch.delenv("PEPA_LLM_MAX_RETRIES", raising=False)
    monkeypatch.delenv("PEPA_LLM_RETRY_BACKOFF", raising=False)
    reload_settings()
