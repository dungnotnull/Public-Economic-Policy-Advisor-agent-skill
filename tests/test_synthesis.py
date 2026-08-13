"""Tests for narrative synthesis (deterministic fallback + LLM enrichment)."""

import pytest

from policy_advisor.utils.context import LLMAdapter, LLMResponse, MockLLMAdapter
from policy_advisor.utils.synthesis import build_narrative, synthesize_narrative


def test_build_narrative_names_framework_and_cites_evidence():
    text = build_narrative(
        "Tax incidence",
        ["elasticities determine burden"],
        ["Harberger (1962)", "Chetty (2009)"],
        "Buyers bear 78%.",
    )
    assert "Framework applied: Tax incidence" in text
    assert "Harberger (1962)" in text
    assert "Buyers bear 78%" in text
    assert "multiple viewpoints" in text


def test_synthesize_narrative_falls_back_when_no_llm():
    out = synthesize_narrative(
        None, "Tax incidence", "q", [], ["p"], ["Harberger (1962)"], "sum",
    )
    assert "Framework applied: Tax incidence" in out
    assert "Harberger (1962)" in out


def test_synthesize_narrative_uses_real_llm_text():
    class RealLLM(LLMAdapter):
        def complete(self, system_prompt, user_prompt, **kwargs):
            return LLMResponse(text="A real model paragraph about the policy.", model="real")
    out = synthesize_narrative(RealLLM(), "Tax incidence", "q", ["ref snippet"], ["p"], ["Harberger (1962)"], "sum")
    assert "real model paragraph" in out


def test_synthesize_narrative_appends_evidence_when_llm_omits_it():
    class RealLLM(LLMAdapter):
        def complete(self, system_prompt, user_prompt, **kwargs):
            return LLMResponse(text="A real model paragraph with no citation.", model="real")
    out = synthesize_narrative(RealLLM(), "Tax incidence", "q", [], ["p"], ["Harberger (1962)"], "sum")
    assert "Harberger (1962)" in out


def test_synthesize_narrative_falls_back_on_mock_marker():
    out = synthesize_narrative(MockLLMAdapter(), "Tax incidence", "q", [], ["p"], ["Harberger (1962)"], "sum")
    # MockLLMAdapter default emits the FALLBACK marker -> deterministic narrative used.
    assert "Framework applied: Tax incidence" in out
    assert "FALLBACK" not in out


def test_synthesize_narrative_falls_back_on_llm_exception():
    class BoomLLM(LLMAdapter):
        def complete(self, system_prompt, user_prompt, **kwargs):
            raise RuntimeError("down")
    out = synthesize_narrative(BoomLLM(), "Tax incidence", "q", [], ["p"], ["Harberger (1962)"], "sum")
    assert "Framework applied: Tax incidence" in out


def test_reports_carry_evidence_base_and_narrative():
    from policy_advisor import advise, reset_registry
    reset_registry()
    result = advise("Who bears a corporate income tax?", requested_format="tax-incidence", context={"supply_elasticity": 1.5, "demand_elasticity": 0.4}, llm=MockLLMAdapter())
    assert result.payload["evidence_base"], "evidence_base should be populated"
    assert result.payload["narrative"], "narrative should be populated"
    assert any("harberger" in c["source_id"] for c in result.payload["citations"])
    reset_registry()
