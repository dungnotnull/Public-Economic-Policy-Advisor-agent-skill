# PROJECT-DEVELOPMENT-PHASE-TRACKING.md - Public Economic Policy Advisor

> Living build tracker. Updated as work progresses; all phases are **100% complete**.

## Build methodology

Follows the skill-creator methodology (draft -> test -> evaluate -> iterate ->
package), implemented as a modular skill-registry + chain-of-thought router +
specialised sub-advisors architecture with schema-validated tools, lifecycle
hooks, event emission, state synchronisation, type-safe configuration, RAG
grounding, and graceful LLM fallback.

## Phase 1 - Foundation: Core analytical framework
**Goal:** Modular runtime + welfare-economics / cost-benefit workflow

**Status:** 100% complete

**Tasks:**
- [x] Design skill-registry + chain-of-thought router + sub-advisor architecture
- [x] Build type-safe config (`config/settings.py`, `config/schema.py`, `config/default.json`)
- [x] Build utils (structured JSON logging, error taxonomy, LLM adapter + retry/fallback, token estimation)
- [x] Build `cost_benefit_analysis` tool with JSON-Schema I/O
- [x] Build `market_failure_diagnostic` tool with JSON-Schema I/O
- [x] Build `SkillRegistry` orchestrator, `FiscalAdvisor`, `WelfareAdvisor`
- [x] Draft `SKILL.md` registry / resolution / execution / validation contract
- [x] Operationalise welfare-economics & market-failure references

## Phase 2 - Fiscal & Tax Analysis
**Goal:** Taxation / subsidy incidence modelling

**Status:** 100% complete

**Tasks:**
- [x] Build `tax_incidence` tool (Harberger-style elasticity-based incidence)
- [x] Build tax-incidence analysis template (`references/prompt-templates/tax-incidence-analysis.md`)
- [x] Operationalise tax-incidence reference (`references/02-tax-incidence.md`)
- [x] Wire `FiscalAdvisor` to incidence + CBA tools -> `TaxIncidenceReport`
- [x] Add subsidy/welfare-effect handling (welfare effects, deadweight loss, distributional flags)

## Phase 3 - Macro Policy Perspectives
**Goal:** Balanced-viewpoint layer

**Status:** 100% complete

**Tasks:**
- [x] Build `comparative_schools` tool (Keynesian, Monetarist, New Classical, Supply-side, Institutional)
- [x] Build comparative-schools reference (`references/04-macro-schools.md`)
- [x] Build `MacroAdvisor` -> `ProConDebateReport` + balanced pro/con matrix
- [x] Add evenhanded pro/con presentation template (`references/prompt-templates/pro-con-debate.md`)
- [x] Enforce multi-viewpoint balance + empirical-resolution deferral

## Phase 4 - Empirical Evaluation
**Goal:** Evidence-based assessment

**Status:** 100% complete

**Tasks:**
- [x] Build `causal_evaluation` tool (RCT, DiD, RDD, IV, natural experiment selection)
- [x] Build causal-inference reference (`references/05-causal-inference.md`)
- [x] Build `EmpiricalAdvisor` -> `CausalEvaluationReport`
- [x] Add empirical-evidence citation guidance (threats to validity, data requirements, confidence)

## Phase 5 - Distribution, Testing & Polish
**Goal:** Validate across policy areas; package

**Status:** 100% complete

**Tasks:**
- [x] Build distribution/redistribution reference (`references/06-distribution-redistribution.md`)
- [x] Build glossary (`references/glossary.md`)
- [x] Build JSON Schemas for all reports (`assets/schemas/`)
- [x] Build architecture diagram (`assets/diagrams/agent-architecture.md`)
- [x] Build scripts: `setup`, `validate_skill`, `run_self_test`, `ingest_references`, `seed_knowledge`
- [x] Build pytest suite (`tests/`) covering registry, tools, router, hooks
- [x] Self-test battery across tax, welfare, monetary, and causal-evaluation scenarios (6/6 pass)
- [x] Package and document (README, CLAUDE.md, SKILL.md, PROJECT-detail.md)

## Phase 6 - Research Grounding & Persuasiveness Layer
**Goal:** Wire the scientific knowledge brain into every output for accuracy and persuasiveness

**Status:** 100% complete

**Tasks:**
- [x] Build `RESEARCH-PAPER-KNOWLEDGE-BRAIN.md` with 28 scientific papers (core principle + operational application each)
- [x] Build `policy_advisor/citations.py` citation-grounding service (methodology -> papers index)
- [x] Add `evidence_base` + `narrative` fields to all report schemas (config + assets JSON schemas)
- [x] Activate the dormant RAG + LLM narrative-synthesis path (`utils/synthesis.py`) in every sub-advisor
- [x] Replace hard-coded citations with grounded `citations_for()` / `evidence_base_for()` across sub-advisors
- [x] Build `scripts/seed_research.py` (parses the brain -> `assets/research-papers.json`, cross-checks the registry)
- [x] Build `scripts/evaluate_outputs.py` (rubric-based evaluation harness, 95% overall)
- [x] Add `tests/test_citations.py` + `tests/test_synthesis.py`; full suite now 70 tests, all green

## Phase 7 - Real LLM Adapter Layer
**Goal:** Production-grade, pluggable live-model integration (close the offline-only gap)

**Status:** 100% complete

**Tasks:**
- [x] Add `provider` / `api_base_url` to `LLMParams` + `PEPA_LLM_PROVIDER` / `PEPA_LLM_API_BASE_URL` env overrides
- [x] Build `policy_advisor/utils/adapters/` with `AnthropicAdapter` (Claude Messages API), `OpenAIAdapter` (Chat Completions, OpenAI-compatible), stdlib `urllib` HTTP helper, and `make_llm_adapter()` factory with auto-detection
- [x] Wire the registry and CLI to use the factory by default (auto -> anthropic -> openai -> mock)
- [x] Make `RetryingLLMAdapter` fail-fast on non-recoverable errors and keep graceful mock fallback
- [x] Add CLI `--provider` flag and test-session isolation (`conftest.py` pins mock provider)
- [x] Add `tests/test_adapters.py` (factory resolution, request/response shapes via monkeypatched HTTP, error translation, registry wiring)
- [x] Update docs (README, SKILL.md)

## Final Step - Packaging
**Status:** 100% complete

- [x] Write the actual `SKILL.md` (name + description + body) per `PROJECT-detail.md`
- [x] Build `references/`, `scripts/`, `assets/`, `config/` per spec
- [x] Run the skill-creator evaluation loop (`scripts/run_self_test.py`, `scripts/validate_skill.py`, `scripts/evaluate_outputs.py`)
- [x] Package the finished skill for distribution (production-grade, open-source layout)

## Verification commands

```
python -m scripts.setup
python -m scripts.validate_skill
python -m scripts.run_self_test
python -m scripts.ingest_references
python -m scripts.seed_knowledge
python -m scripts.seed_research
python -m scripts.evaluate_outputs
pytest -q   # 70 tests
```

## Architecture summary

- **Router:** `ChainOfThoughtRouter` (format match -> keyword tie-break -> default).
- **Sub-advisors:** `FiscalAdvisor`, `MacroAdvisor`, `WelfareAdvisor`, `EmpiricalAdvisor`.
- **Tools:** `cost_benefit_analysis`, `tax_incidence`, `market_failure_diagnostic`, `comparative_schools`, `causal_evaluation`.
- **Citation grounding:** `policy_advisor/citations.py` maps each methodology to its backing research papers (28 papers from `RESEARCH-PAPER-KNOWLEDGE-BRAIN.md`).
- **Narrative synthesis:** `policy_advisor/utils/synthesis.py` produces grounded, persuasive prose (LLM-enriched with deterministic fallback).
- **Hooks:** `LifecycleHookBus`, `EventBus`, `StateStore`.
- **Config:** layered (defaults -> local override -> `PEPA_` env vars), feature flags, LLM params, context-window budgeting.
- **Resilience:** bounded LLM retries + graceful `MockLLMAdapter` fallback; every error degrades to a coherent `SkillResult` envelope.
