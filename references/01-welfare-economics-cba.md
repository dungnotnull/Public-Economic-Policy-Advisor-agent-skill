# 01 — Welfare Economics & Cost-Benefit Analysis (Operational Reference)

> Distilled operational principles from Atkinson & Stiglitz (1980), Stiglitz (2000), and Mankiw (2020). Apply these as concrete steps, not abstract citations.

## When to apply
Use this framework whenever the user asks whether a policy is "worth it", "good", or "efficient", or asks to compare benefits and costs of a proposal.

## Operational steps
1. **Enumerate all affected parties** — consumers, producers, taxpayers, government, and third parties. Missing a group is the most common CBA error.
2. **List benefit and cost items** as qualitative-ordinal magnitudes (`negligible | small | moderate | large | very large`) rather than fabricated currency. State that precise monetisation requires data the skill does not have.
3. **Weight each item by confidence** (`low | medium | high`). Low-confidence items must be flagged for sensitivity analysis.
4. **Distinguish efficiency from equity.** A policy can be Kaldor-Hicks efficient yet distributionally regressive; report both dimensions separately.
5. **Note the discounting caveat.** Without an explicit social discount rate, treat the weights as ordinal welfare weights, not a monetary NPV.
6. **Aggregate with a transparent rule** (the `cost_benefit_analysis` tool sums `sign * magnitude * confidence`) and report the verdict band, not a single spurious number.

## Standing cautions
- Do not invent numerical estimates of GDP, revenue, or welfare in currency units.
- Always state the framework name explicitly in the output (e.g., "Using weighted cost-benefit analysis...").
- Flag that distributional effects are a separate judgement from the efficiency verdict.

## Output mapping
Maps to `PolicyAnalysisReport.cost_benefit` and `PolicyAnalysisReport.distributional_effects` via the `cost_benefit_analysis` tool.
