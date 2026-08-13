"""Tests for the deterministic domain tools and the tool registry."""

import pytest

from policy_advisor.tools import (
    CausalEvaluationTool,
    ComparativeSchoolsTool,
    CostBenefitAnalysisTool,
    MarketFailureDiagnosticTool,
    TaxIncidenceTool,
    ToolRegistry,
    register_default_tools,
)
from policy_advisor.tools.base import _validate
from policy_advisor.utils.errors import ToolExecutionError, ValidationError


def _registry():
    reg = ToolRegistry()
    register_default_tools(reg)
    return reg


def test_default_tools_registered():
    reg = _registry()
    assert set(reg.available()) == {
        "cost_benefit_analysis",
        "tax_incidence",
        "market_failure_diagnostic",
        "comparative_schools",
        "causal_evaluation",
    }


def test_unknown_tool_raises():
    with pytest.raises(ToolExecutionError):
        _registry().get("does_not_exist")


def test_cba_weighting_and_verdict():
    tool = CostBenefitAnalysisTool()
    result = tool.run({
        "policy_name": "bridge",
        "items": [
            {"category": "benefit", "description": "time savings", "estimated_magnitude": "large", "direction": "benefit", "confidence": "high"},
            {"category": "cost", "description": "construction", "estimated_magnitude": "moderate", "direction": "cost", "confidence": "medium"},
        ],
    })
    assert result.ok
    assert result.output["net_score"] > 0
    assert "welfare-positive" in result.output["verdict"]


def test_cba_rejects_invalid_magnitude():
    tool = CostBenefitAnalysisTool()
    with pytest.raises(ValidationError):
        tool.run({"policy_name": "x", "items": [{"category": "a", "description": "b", "estimated_magnitude": "huge", "direction": "benefit"}]})


def test_tax_incidence_inelastic_side_bears_more():
    tool = TaxIncidenceTool()
    # Supply very elastic, demand inelastic -> buyers (demand side) bear more.
    result = tool.run({"instrument": "VAT", "supply_elasticity": 2.0, "demand_elasticity": 0.2})
    assert result.output["buyer_share"] > 0.5
    assert result.output["seller_share"] < 0.5
    assert pytest.approx(result.output["buyer_share"] + result.output["seller_share"], rel=1e-6) == 1.0


def test_tax_incidence_zero_elasticities_splits_evenly():
    result = TaxIncidenceTool().run({"instrument": "tax", "supply_elasticity": 0.0, "demand_elasticity": 0.0})
    assert result.output["buyer_share"] == 0.5


def test_market_failure_diagnoses_externality():
    result = MarketFailureDiagnosticTool().run({"situation": "factory pollution harms neighbours"})
    types = [f["failure_type"] for f in result.output["diagnosed_failures"]]
    assert "negative_externality" in types
    assert not result.output["no_failure_found"]


def test_market_failure_no_match():
    result = MarketFailureDiagnosticTool().run({"situation": "a perfectly competitive market with no issues"})
    assert result.output["no_failure_found"] is True


def test_comparative_schools_returns_multiple_viewpoints():
    result = ComparativeSchoolsTool().run({"policy_question": "stimulus?"})
    assert len(result.output["viewpoints"]) >= 2
    assert result.output["contested"] is True


def test_causal_evaluation_picks_rct_when_randomizable():
    result = CausalEvaluationTool().run({"policy_under_evaluation": "training", "evaluation_context": {"can_randomize": True}})
    assert result.output["recommended_method"] == "RCT"
    assert result.output["confidence"] == "high"


def test_causal_evaluation_defaults_to_did():
    result = CausalEvaluationTool().run({"policy_under_evaluation": "training", "evaluation_context": {}})
    assert result.output["recommended_method"] == "DiD"


def test_registry_invocation_log_records_calls():
    reg = _registry()
    reg.invoke("market_failure_diagnostic", {"situation": "pollution"})
    log = reg.invocation_log()
    assert log[-1]["tool"] == "market_failure_diagnostic"
    assert log[-1]["ok"] is True


def test_output_schema_validation_warns_not_raises():
    # A tool whose output violates its own schema should warn, not raise.
    class BadTool(CostBenefitAnalysisTool):
        output_schema = {"type": "object", "required": ["nonexistent_key"]}
    result = BadTool().run({"policy_name": "x", "items": [{"category": "a", "description": "b", "estimated_magnitude": "small", "direction": "benefit"}]})
    assert any("nonexistent_key" in w for w in result.warnings)
