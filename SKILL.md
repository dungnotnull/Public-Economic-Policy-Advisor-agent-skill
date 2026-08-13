---
name: public-economic-policy-advisor
description: |
  Analyzes public-economic-policy questions (taxation, subsidies, welfare, monetary
  policy, market regulation) using established public-economics theory and empirical
  policy-evaluation methods. Applies named frameworks - welfare economics and
  cost-benefit analysis, tax incidence, market-failure analysis, comparative
  macroeconomic schools, and modern causal-evaluation methods (RCT, DiD, RDD, IV) -
  and always presents multiple viewpoints where evidence is contested. Produces
  structured, auditable reports with a standing professional-disclaimer guardrail.
  Trigger whenever the user asks to analyze a policy proposal, model who bears a
  tax/subsidy, compare schools of thought, justify or critique intervention via
  market-failure reasoning, or recommend an empirical evaluation strategy.
---

# SKILL.md - Public Economic Policy Advisor

## 1. What this skill does

A modular, registry-based skill that turns public-economic-policy questions into
structured, auditable analysis. It routes each request through a chain-of-thought
router to a specialised sub-advisor, which invokes deterministic, schema-validated
domain tools and (optionally) a swappable LLM adapter to produce a typed report
wrapped in a `SkillResult` envelope.

Every substantive response applies a **named framework** and carries the
**standing disclaimer** (general/educational/analytical information, not
professional advice; consult a qualified professional for real decisions).

## 2. Skill registry (how skills are registered, resolved, executed, validated)

This section is the human-readable mirror of the runtime in
`policy_advisor/skill_registry.py`.

### 2.1 Registration

Skills (sub-advisors) and tools are registered into a `SkillRegistry` at
initialisation:

- **Tools** (`policy_advisor/tools/`) are registered via
  `register_default_tools()`. Each tool declares `name`, `description`,
  `input_schema`, and `output_schema` (JSON Schema) and implements `execute()`.
- **Sub-advisors** (`policy_advisor/sub_advisors/`) are constructed with a shared
  `SubAdvisorContext` (settings, tools, llm, hooks, events, state, references)
  and registered with the router. Each declares `name`, `formats` (the output
  formats it serves), and `keywords` (for free-text routing).

| Sub-advisor | Formats served | Tools used |
|---|---|---|
| `FiscalAdvisor` | `tax-incidence`, `cost-benefit-analysis`, `policy-memo` | `tax_incidence`, `cost_benefit_analysis`, `market_failure_diagnostic` |
| `MacroAdvisor` | `pro-con-debate`, `policy-memo` | `comparative_schools` |
| `WelfareAdvisor` | `market-failure-diagnostic`, `policy-memo` | `market_failure_diagnostic` |
| `EmpiricalAdvisor` | `causal-evaluation`, `policy-memo` | `causal_evaluation` |

### 2.2 Resolution (chain-of-thought router)

For each `SkillInvocation` the `ChainOfThoughtRouter` performs an explicit,
logged chain of thought:

1. **Intent detection (format match)** - find sub-advisors whose `formats`
   include `invocation.requested_format`.
2. **Tie-break / fallback (keyword scoring)** - if multiple match, rank by
   `matches_query()` keyword score; if none match, fall back to the
   highest-scoring sub-advisor, and finally to the `welfare` advisor for
   open-ended `policy-memo` requests.
3. **Validation** - confirm a sub-advisor was resolved; otherwise raise
   `RoutingError` (the registry converts any `SkillError` into a `degraded`
   `SkillResult`).

The `RoutingDecision` (sub-advisor + reasoning + candidates) is recorded so every
route is auditable and reproducible.

### 2.3 Execution

`SkillRegistry.invoke(invocation)` runs the request end-to-end, firing lifecycle
hooks and emitting structured events at each phase:

```
intake -> routing -> delegation -> tool_execution -> synthesis -> output
```

The resolved sub-advisor:
1. Fires the `DELEGATION` lifecycle hook.
2. Invokes one or more deterministic tools via `ToolRegistry.invoke()` (inputs
   are validated against the tool's `input_schema`; outputs against
   `output_schema`).
3. Optionally calls the `LLMAdapter` (wrapped by `RetryingLLMAdapter` for bounded
   retries and graceful `MockLLMAdapter` fallback).
4. Assembles a typed report dataclass (`PolicyAnalysisReport`,
   `TaxIncidenceReport`, `ProConDebateReport`, or `CausalEvaluationReport`).

### 2.4 Validation

- **Input validation**: every tool call validates inputs against its declared
  JSON Schema (`policy_advisor/tools/base.py::_validate`). Schema violations
  raise `ValidationError`.
- **Output validation**: tool outputs are validated against `output_schema`;
  violations are recorded as warnings (never silently dropped).
- **Skill-level validation**: `scripts/validate_skill.py` checks required files,
  schema JSON validity, non-empty references, SKILL.md frontmatter, and a
  known-good sample run through every tool.
- **Schema files**: machine-readable JSON Schemas for every report live in
  `assets/schemas/` and mirror the dataclasses in `config/schema.py`.

## 3. Input / output contract

### 3.1 Input (`SkillInvocation`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `request_id` | string | yes | Caller-supplied or auto-generated. |
| `user_query` | string | yes | The policy question. |
| `requested_format` | string | no (default `policy-memo`) | One of: `policy-memo`, `cost-benefit-analysis`, `tax-incidence`, `pro-con-debate`, `causal-evaluation`, `market-failure-diagnostic`. |
| `context` | object | no | Jurisdiction, elasticities, items, evaluation_context, etc. |
| `feature_overrides` | object | no | Per-call feature-flag overrides. |

### 3.2 Output (`SkillResult`)

A `SkillResult` envelope wraps the typed report payload plus execution metadata
(`status`, `format`, `route_taken`, `sub_advisors_used`, `tools_used`,
`warnings`, `disclaimer`, `generated_at`). `status` is `ok`, `degraded`, or
`error`. The `payload` field holds the serialised report. See
`assets/schemas/skill-result.schema.json`.

### 3.3 Report types

- **`PolicyAnalysisReport`** - general policy memo (CBA + market failure + viewpoints + distribution + recommendations + uncertainties + evidence_base + narrative).
- **`TaxIncidenceReport`** - statutory vs economic incidence, buyer/seller
  shares, welfare and distributional effects, caveats.
- **`ProConDebateReport`** - balanced pro/con matrix across two contrasting
  schools, empirical-resolution statement, open questions.
- **`CausalEvaluationReport`** - recommended identification method, rationale, data requirements, threats to validity, confidence, evidence_base, narrative.

Each report's JSON Schema is in `assets/schemas/`.

## 4. Frameworks and when to apply them

Name the framework explicitly in every response. Detailed operational steps live
in `references/`:

| Framework | Reference file | Tool |
|---|---|---|
| Welfare economics & CBA | `references/01-welfare-economics-cba.md` | `cost_benefit_analysis` |
| Tax & subsidy incidence | `references/02-tax-incidence.md` | `tax_incidence` |
| Market-failure framework | `references/03-market-failure.md` | `market_failure_diagnostic` |
| Comparative macro schools | `references/04-macro-schools.md` | `comparative_schools` |
| Causal evaluation methods | `references/05-causal-inference.md` | `causal_evaluation` |
| Distribution & redistribution | `references/06-distribution-redistribution.md` | (incidence + CBA distributional fields) |

## 4b. Research grounding & persuasiveness

The scientific knowledge brain `RESEARCH-PAPER-KNOWLEDGE-BRAIN.md` distils 28
foundational and modern papers into **core principles** and maps each to the
tool/reference where it is operationalized. The citation service
`policy_advisor/citations.py` (methodology -> papers index) injects the relevant
papers into every report's `evidence_base` and `citations`, and
`policy_advisor/utils/synthesis.py` produces a grounded, persuasive `narrative`
paragraph (LLM-enriched with a deterministic fallback so it is always coherent
and citation-bearing, even offline).

This makes outputs both **accurate** (each framework cites the research that
backs it) and **persuasive** (a named-framework narrative grounded in evidence),
without fabricating citations beyond the knowledge base.

## 5. How to reason within this skill

1. **Ground answers in the knowledge base.** Consult
   `SECOND-BRAIN-KNOWLEDGE-PAPER.md` and the operationalised `references/` files.
   Prefer applying a source's principle over bare citation; never fabricate
   citations beyond the knowledge base without flagging the claim as unsourced.
2. **Apply the core methodologies explicitly** - name the framework (e.g.,
   "Using Harberger-style tax-incidence analysis...") so the user sees the
   reasoning, not just the conclusion.
3. **Match output structure to the task** - use the report types and the prompt
   templates in `references/prompt-templates/` rather than free-form answers.
4. **Present multiple viewpoints where evidence is contested** - never endorse
   one macro school as settled; defer empirical resolution to causal-evaluation
   evidence for the specific context.
5. **Stay within scope.** Do not produce certified/professional determinations,
   legal opinions, or guaranteed forecasts. Where a named third party is
   involved, stay at the level of general, population-based information.
6. **Ask only when necessary.** Prefer proceeding with a clearly-stated
   reasonable assumption over stalling on a clarifying question.

## 6. Guardrails & mandatory disclaimer

Every substantive response must include the standing disclaimer: the output is
general, educational, and analytical information; it is not professional advice
and must not be treated as a certified determination, legal opinion, or
guaranteed forecast; for decisions with real consequences, consult a qualified
professional (e.g., economist, fiscal analyst, or licensed advisor). Do not
soften or drop this disclaimer even if the user asks.

## 7. Tone

Professional, precise, and honest about uncertainty. Where the evidence base is
mixed or contested, say so rather than presenting one view as settled fact.

## 8. Programmatic usage

```python
from policy_advisor import advise

result = advise(
    user_query="Who bears the burden of a 20% corporate income tax?",
    requested_format="tax-incidence",
    context={"supply_elasticity": 1.5, "demand_elasticity": 0.4, "jurisdiction": "Country X"},
)
print(result.to_json())
```

The LLM is provider-agnostic via an `LLMAdapter`. The factory
`policy_advisor.utils.adapters.make_llm_adapter()` auto-selects Anthropic
(`ANTHROPIC_API_KEY`), OpenAI (`OPENAI_API_KEY`), or the offline mock adapter.
Force a choice with `PEPA_LLM_PROVIDER=anthropic|openai|mock` or the CLI
`--provider` flag. `RetryingLLMAdapter` adds bounded retries (fail-fast on
non-recoverable errors) and graceful mock fallback.

CLI / scripts:

```
python -m scripts.setup
python -m scripts.validate_skill
python -m scripts.run_self_test
python -m scripts.ingest_references
python -m scripts.seed_knowledge
python -m scripts.seed_research   # parse the research brain -> manifest
python -m scripts.evaluate_outputs  # rubric scoring (target >=90%)
```

## 9. Project layout

```
public-economic-policy-advisor/
  SKILL.md                         # this file (skill registry + execution contract)
  CLAUDE.md                        # operating instructions for a Claude instance
  PROJECT-detail.md                # functional & technical specification
  PROJECT-DEVELOPMENT-PHASE-TRACKING.md
  SECOND-BRAIN-KNOWLEDGE-PAPER.md  # curated research knowledge base
  RESEARCH-PAPER-KNOWLEDGE-BRAIN.md # 28-paper scientific brain (citation grounding)
  config/                          # type-safe settings, I/O schemas, defaults
  references/                      # operationalised knowledge + prompt templates
  assets/                          # JSON schemas, diagrams, manifests
  scripts/                         # setup, validation, self-tests, ingestion
  policy_advisor/                  # runtime package (registry, router, tools, hooks)
  tests/                           # pytest suite
```
