# PROJECT-detail.md - Public Economic Policy Advisor

## 1. Problem Statement

A skill supporting policymakers, students, and researchers in analyzing public-economic-policy questions (taxation, subsidies, welfare, monetary policy, market regulation) using established public-economics theory and empirical policy-evaluation methods, always presenting multiple viewpoints where evidence is contested.

## 2. Target Users

- **Policymakers & legislative analysts** who need structured, auditable framing of fiscal/monetary/welfare proposals before drafting or scoring them.
- **Students of public economics & public policy** learning to apply named frameworks (CBA, incidence, market-failure, causal evaluation) rather than generic reasoning.
- **Researchers** selecting an empirical identification strategy for a policy evaluation, or comparing schools of thought on a contested question.

All users are reminded via the standing disclaimer that the output is analytical/educational and not a substitute for a qualified professional.

## 3. Functional Specification

### 3.1 Core Capabilities

- Analyze policy proposals using cost-benefit analysis and welfare economics
- Model likely incidence effects of taxes/subsidies (who really bears the cost)
- Summarize competing schools of thought (Keynesian, monetarist, supply-side) on a policy question
- Apply market-failure frameworks (externalities, public goods, information asymmetry) to justify or critique intervention
- Reference empirical policy-evaluation methods (RCTs, diff-in-diff, natural experiments)
- Present balanced pro/con analysis for contested policy debates

### 3.2 Key Methodologies & Frameworks Applied

- **Welfare economics and cost-benefit analysis** -> `references/01-welfare-economics-cba.md`, tool `cost_benefit_analysis`
- **Tax incidence theory** -> `references/02-tax-incidence.md`, tool `tax_incidence`
- **Market failure framework (externalities, public goods, asymmetric information)** -> `references/03-market-failure.md`, tool `market_failure_diagnostic`
- **Comparative macroeconomic schools (Keynesian, Monetarist, New Classical, Supply-side)** -> `references/04-macro-schools.md`, tool `comparative_schools`
- **Modern causal policy-evaluation methods (RCT, difference-in-differences, regression discontinuity)** -> `references/05-causal-inference.md`, tool `causal_evaluation`
- **Distribution & redistribution** -> `references/06-distribution-redistribution.md` (layered on incidence + CBA distributional fields)

Each framework is operationalized as a concrete step/checklist in its reference file and as a deterministic, schema-validated tool inside `policy_advisor/tools/`, with the contract documented in `SKILL.md`.

### 3.3 Expected Input

The skill accepts a `SkillInvocation` with:

- `user_query` (string) - the policy question.
- `requested_format` (string, default `policy-memo`) - one of `policy-memo`, `cost-benefit-analysis`, `tax-incidence`, `pro-con-debate`, `causal-evaluation`, `market-failure-diagnostic`.
- `context` (object) - optional structured context, e.g.:
  - tax-incidence: `{"instrument", "jurisdiction", "supply_elasticity", "demand_elasticity", "is_subsidy", "affected_groups"}`
  - cost-benefit-analysis: `{"policy_name", "jurisdiction", "items": [{category, description, estimated_magnitude, direction, confidence}], "discount_note"}`
  - market-failure-diagnostic: `{"proposed_intervention"}`
  - pro-con-debate: `{"schools": [...]}`
  - causal-evaluation: `{"evaluation_context": {"can_randomize", "has_eligibility_cutoff", "has_panel_data", "has_instrument", "has_exogenous_shock"}}`

Example prompts (covered by `scripts/run_self_test.py`):
- "Who really bears the burden of a 20% corporate income tax?"
- "Is building a new highway worth it?"
- "Should the government regulate coal pollution to fix a negative externality?"
- "Compare Keynesian vs monetarist views on fiscal stimulus during a recession."
- "How should we evaluate the impact of a job-training program?"
- "Analyse a proposed universal basic income funded by a VAT."

### 3.4 Expected Output Format

Outputs are typed report dataclasses (defined in `config/schema.py`, JSON Schemas in `assets/schemas/`) wrapped in a `SkillResult` envelope:

- **`PolicyAnalysisReport`** - structured memo: summary, frameworks applied, market-failure diagnosis, cost-benefit items, distributional effects, viewpoints, empirical evidence, recommendations, uncertainties, citations, disclaimer.
- **`TaxIncidenceReport`** - statutory vs economic incidence, buyer/seller shares, elasticity assumptions, welfare effects, distributional effects, caveats.
- **`ProConDebateReport`** - balanced pro/con matrix for two contrasting schools, empirical-resolution statement, open questions.
- **`CausalEvaluationReport`** - recommended method, rationale, identification strategy, data requirements, threats to validity, confidence.

Every output carries the standing disclaimer, an `evidence_base` of the backing research papers, a grounded `narrative` paragraph, and reports the route taken, tools used, and any warnings, so it is consistent, persuasive, and auditable across sessions.

## 4. Out of Scope / Guardrails

- Always include the standing disclaimer for this domain (see `CLAUDE.md`).
- Never present output as a certified/professional determination (not a diagnosis, not a legal opinion, not a guaranteed forecast).
- Where the skill involves a named third party (e.g., a partner, a suspect, a specific person), do not produce a definitive judgment about that individual - stay at the level of general, population-based information and structured reasoning support.
- Flag explicitly when a licensed professional (economist, fiscal analyst, certified analyst, lawyer, etc.) should be consulted.
- Do not fabricate numerical estimates (GDP, revenue, welfare in currency units); use qualitative-ordinal magnitudes and state assumptions.

## 5. Knowledge Base Dependency

This skill's reasoning quality depends on the research foundations catalogued in `SECOND-BRAIN-KNOWLEDGE-PAPER.md`. The operational principles from each source have been extracted into concrete reference files under `references/` (rather than left as a flat reading list), and the curated list is machine-readable via `scripts/seed_knowledge.py` -> `assets/knowledge-base.json`. A deeper, 28-paper scientific brain (`RESEARCH-PAPER-KNOWLEDGE-BRAIN.md`) maps each paper's core principle to the exact tool/reference it grounds, and the citation service `policy_advisor/citations.py` injects the relevant papers into every report's `evidence_base` and `citations` for accuracy and persuasiveness (`scripts/seed_research.py` -> `assets/research-papers.json`).

## 6. Success Criteria

- Output correctly applies the named methodologies rather than generic reasoning. (Enforced by deterministic tools + framework-naming requirement.)
- Output is well-structured and consistent across repeated runs on similar inputs. (Enforced by typed reports + JSON-Schema validation + the self-test battery.)
- Domain-appropriate guardrails/disclaimers are respected in every response. (Enforced by automatic disclaimer injection; verified by tests.)
- Test prompts (Phase 5) produce outputs a subject-matter-competent reviewer would rate as sound. (Verified by `scripts/run_self_test.py` - 6/6 pass - and the 41-test pytest suite.)

## 7. Implemented Architecture (reference)

See `SKILL.md` for the full skill-registry contract and `assets/diagrams/agent-architecture.md` for the diagram. The runtime lives in the `policy_advisor` package: `SkillRegistry` -> `ChainOfThoughtRouter` -> sub-advisors (`FiscalAdvisor`, `MacroAdvisor`, `WelfareAdvisor`, `EmpiricalAdvisor`) -> `ToolRegistry` -> typed reports. Cross-cutting concerns: `config/` (type-safe settings, feature flags, context-window budgeting), `policy_advisor/hooks/` (lifecycle, events, state), `policy_advisor/utils/` (structured logging, error taxonomy, LLM adapter with retry + graceful fallback, token estimation).
