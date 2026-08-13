"""Tests for the pluggable LLM adapters and factory (no network required)."""

import os

import pytest

from policy_advisor.utils.adapters import AnthropicAdapter, OpenAIAdapter, make_llm_adapter, resolve_provider
from policy_advisor.utils.adapters import _http
from policy_advisor.utils.context import LLMResponse
from policy_advisor.utils.errors import LLMInvocationError


# --------------------------------------------------------------------------- #
# Factory / provider resolution
# --------------------------------------------------------------------------- #
def test_resolve_provider_defaults_to_mock_without_keys(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("PEPA_LLM_PROVIDER", "auto")
    from config import reload_settings
    reload_settings()
    assert resolve_provider() == "mock"


def test_resolve_provider_picks_anthropic_when_key_present(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("PEPA_LLM_PROVIDER", "auto")
    from config import reload_settings
    reload_settings()
    assert resolve_provider() == "anthropic"


def test_resolve_provider_picks_openai_when_only_openai_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("PEPA_LLM_PROVIDER", "auto")
    from config import reload_settings
    reload_settings()
    assert resolve_provider() == "openai"


def test_resolve_provider_explicit_override(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("PEPA_LLM_PROVIDER", "mock")
    from config import reload_settings
    reload_settings()
    assert resolve_provider() == "mock"


def test_make_llm_adapter_returns_mock_without_keys(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("PEPA_LLM_PROVIDER", "auto")
    from config import reload_settings
    reload_settings()
    adapter = make_llm_adapter()
    # Offline mock adapter emits the fallback marker.
    resp = adapter.complete("sys", "user")
    assert "FALLBACK" in resp.text


def test_make_llm_adapter_returns_anthropic_with_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("PEPA_LLM_PROVIDER", "anthropic")
    from config import reload_settings
    reload_settings()
    adapter = make_llm_adapter()
    assert isinstance(adapter, AnthropicAdapter)
    assert adapter.is_configured


# --------------------------------------------------------------------------- #
# AnthropicAdapter request/response (monkeypatched HTTP)
# --------------------------------------------------------------------------- #
def test_anthropic_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from config import reload_settings
    reload_settings()
    adapter = AnthropicAdapter()
    assert not adapter.is_configured
    with pytest.raises(LLMInvocationError):
        adapter.complete("sys", "user")


def test_anthropic_builds_correct_payload_and_parses_response(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    from config import reload_settings
    reload_settings()
    adapter = AnthropicAdapter()

    captured = {}

    def fake_post(url, payload, headers, timeout):
        captured["url"] = url
        captured["payload"] = payload
        captured["headers"] = headers
        captured["timeout"] = timeout
        return {
            "id": "msg_1",
            "model": payload["model"],
            "content": [{"type": "text", "text": "The burden falls on the inelastic side."}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 42, "output_tokens": 17},
        }

    import policy_advisor.utils.adapters.anthropic as _anth
    monkeypatch.setattr(_anth, "http_post_json", fake_post)
    resp = adapter.complete("You are an economist.", "Who bears the tax?")
    assert isinstance(resp, LLMResponse)
    assert resp.text == "The burden falls on the inelastic side."
    assert resp.model == captured["payload"]["model"]
    assert resp.prompt_tokens == 42
    assert resp.completion_tokens == 17
    assert resp.finish_reason == "end_turn"
    # Request shape
    assert captured["url"].endswith("/v1/messages")
    assert captured["payload"]["system"] == "You are an economist."
    assert captured["payload"]["messages"] == [{"role": "user", "content": "Who bears the tax?"}]
    assert captured["headers"]["x-api-key"] == "sk-ant-test"
    assert captured["headers"]["anthropic-version"] == "2023-06-01"


def test_anthropic_translates_http_error_to_llm_invocation_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    from config import reload_settings
    reload_settings()
    adapter = AnthropicAdapter()

    def boom(url, payload, headers, timeout):
        raise LLMInvocationError("HTTP 429 rate limited", recoverable=True)

    import policy_advisor.utils.adapters.anthropic as _anth
    monkeypatch.setattr(_anth, "http_post_json", boom)
    with pytest.raises(LLMInvocationError):
        adapter.complete("sys", "user")


# --------------------------------------------------------------------------- #
# OpenAIAdapter request/response (monkeypatched HTTP)
# --------------------------------------------------------------------------- #
def test_openai_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from config import reload_settings
    reload_settings()
    adapter = OpenAIAdapter()
    assert not adapter.is_configured
    with pytest.raises(LLMInvocationError):
        adapter.complete("sys", "user")


def test_openai_builds_correct_payload_and_parses_response(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    from config import reload_settings
    reload_settings()
    adapter = OpenAIAdapter()

    captured = {}

    def fake_post(url, payload, headers, timeout):
        captured["url"] = url
        captured["payload"] = payload
        captured["headers"] = headers
        return {
            "model": payload["model"],
            "choices": [{"message": {"role": "assistant", "content": "Use a DiD design."}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 30, "completion_tokens": 12},
        }

    import policy_advisor.utils.adapters.openai as _oai
    monkeypatch.setattr(_oai, "http_post_json", fake_post)
    resp = adapter.complete("You are an economist.", "How to evaluate?")
    assert resp.text == "Use a DiD design."
    assert resp.prompt_tokens == 30
    assert resp.completion_tokens == 12
    assert captured["url"].endswith("/v1/chat/completions")
    assert captured["payload"]["messages"][0] == {"role": "system", "content": "You are an economist."}
    assert captured["payload"]["messages"][1] == {"role": "user", "content": "How to evaluate?"}
    assert captured["headers"]["Authorization"] == "Bearer sk-test"


# --------------------------------------------------------------------------- #
# HTTP helper error translation
# --------------------------------------------------------------------------- #
def test_http_post_json_raises_on_http_error(monkeypatch):
    import urllib.error

    class _Resp:
        def __init__(self, code, body): self.code = code; self._body = body.encode()
        def read(self): return self._body
        def __enter__(self): return self
        def __exit__(self, *a): return False
        status = 200

    def fake_urlopen(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", {}, None)

    monkeypatch.setattr(_http.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(LLMInvocationError) as ei:
        _http.http_post_json("https://example/v1/messages", {"x": 1}, {})
    assert ei.value.recoverable is True  # 429 is retryable


def test_registry_uses_factory_by_default(monkeypatch):
    """The registry should construct its adapter via the factory, not a hard-coded mock."""
    from policy_advisor import reset_registry, get_registry
    from policy_advisor.skill_registry import SkillRegistry
    reset_registry()
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("PEPA_LLM_PROVIDER", "auto")
    from config import reload_settings
    reload_settings()
    reg = get_registry()
    from policy_advisor.utils.context import RetryingLLMAdapter, MockLLMAdapter
    # Factory returned the offline mock adapter when no credentials are present.
    assert isinstance(reg.llm, MockLLMAdapter)
    # Each sub-advisor's context wraps that adapter in the retrying/fallback wrapper.
    assert all(isinstance(a.ctx.llm, RetryingLLMAdapter) for a in reg.sub_advisors)
    reset_registry()
