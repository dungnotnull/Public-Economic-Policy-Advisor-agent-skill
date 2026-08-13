# DEVELOPMENT-TRACKING.md - Agent Memory Log

> Internal development memory for the agent that built this skill. Mirrors and
> supplements `PROJECT-DEVELOPMENT-PHASE-TRACKING.md`.

## Session summary

Upgraded the scaffold into a production-grade, open-source Claude skill with a
modular agent/skill architecture. All phases are 100% complete.

## Decisions made

- **Architecture:** Redesigned the reference skill hierarchy into a
  **skill-registry + chain-of-thought router + specialised sub-advisors**
  pattern (instead of a flat main-agent / sub-advisor sketch). Four sub-advisors
  own fiscal, macro, welfare, and empirical domains.
- **Tools:** Implemented five deterministic, schema-validated tools
  (`cost_benefit_analysis`, `tax_incidence`, `market_failure_diagnostic`,
  `comparative_schools`, `causal_evaluation`) with real functional logic (not
  prompt-only stubs), so the skill produces consistent, auditable results even
  with no live LLM.
- **Hooks:** Added `LifecycleHookBus`, `EventBus`, `StateStore` for lifecycle
  management, event emission, and state synchronisation.
- **Config:** Layered, type-safe config (`config/`) with feature flags, LLM
  params, and context-window budgeting; stdlib-only (no third-party deps).
- **Resilience:** `RetryingLLMAdapter` with bounded retries + graceful
  `MockLLMAdapter` fallback; every error degrades to a coherent `SkillResult`.
- **Layout:** Added `config/`, `references/` (+ `prompt-templates/`), `assets/`
  (+ `schemas/`, `diagrams/`), `scripts/`, `policy_advisor/` package, `tests/`,
  `pyproject.toml`, `LICENSE`, `.gitignore`, CLI (`__main__.py`).

## Key fixes during the build

- Config package lives at project root (per spec) but is imported by
  `policy_advisor` via a sys.path bootstrap in `policy_advisor/__init__.py`.
- Switched all `..config` relative imports to absolute `config` imports.
- JSON logger was leaking stdlib LogRecord attributes; fixed the reserved-attr
  set so only caller `extra` fields are serialised.
- `default.json` had a UTF-8 BOM (PowerShell `Set-Content -Encoding UTF8`);
  rewrote with `UTF8Encoding($false)`.
- Router: when format matches but no keyword signal, default to the generalist
  `welfare` advisor (so open-ended memos route sensibly).
- `SkillResult.tools_used` now snapshots per-invocation instead of accumulating
  across the singleton registry.
- `comparative_schools` tool: only pass `schools` when supplied (avoid schema
  rejection of `None`).

## Verification (all green)

- `python -m scripts.setup` -> OK
- `python -m scripts.validate_skill` -> OK
- `python -m scripts.run_self_test` -> 6/6 pass
- `python -m scripts.ingest_references` -> 11 entries
- `python -m scripts.seed_knowledge` -> 20 sources
- `pytest -q` -> 41 passed

## Open items

None. All phases in `PROJECT-DEVELOPMENT-PHASE-TRACKING.md` are 100% complete.
No placeholders, stubs, or TODOs remain in the codebase.


## Session 2 - Research grounding & persuasiveness ("wow" upgrade)

Elevated the skill from solid-and-tested to genuinely research-grounded and
persuasive.

### Added
- `RESEARCH-PAPER-KNOWLEDGE-BRAIN.md`: 28 scientific papers (original 20 +
  Mirrlees 1971, Diamond-Mirrlees 1971, Oates 1972, Tiebout 1956, Chetty 2009,
  Saez 2001, Card-Krueger 1994, Heckman 1979), each with core principle +
  operational application mapping to a tool/reference.
- `policy_advisor/citations.py`: methodology -> papers citation-grounding
  service; `evidence_base_for()` de-duplicates across methodologies.
- `policy_advisor/utils/synthesis.py`: `build_narrative` (deterministic) +
  `synthesize_narrative` (LLM-enriched with deterministic fallback). Activates
  the previously-dormant RAG + LLM path; guarantees grounded, citation-bearing
  prose even offline.
- `evidence_base` + `narrative` fields on all four report types (config +
  assets JSON schemas).
- `scripts/seed_research.py` (brain -> `assets/research-papers.json`, cross-
  checks the in-code registry) and `scripts/evaluate_outputs.py` (rubric
  scorer, 95% overall).
- `tests/test_citations.py` + `tests/test_synthesis.py`.

### Key fixes
- `seed_research.py` heading regex needed `re.MULTILINE` (`$` matched only
  end-of-string without it) -> now parses all 28 entries.
- Stripped UTF-8 BOMs from all .py/.md/.json/.toml files for open-source
  cleanliness (PowerShell `Set-Content -Encoding UTF8` adds BOMs).

### Verification (all green)
- `validate_skill` OK (now includes citation-registry cross-check)
- `run_self_test` 6/6
- `seed_research` -> 28 papers, cross-check clean
- `evaluate_outputs` -> 570/600 (95.0%)
- `pytest -q` -> **57 passed**


## Session 3 - Real LLM adapter layer ("please implement")

Closed the offline-only caveat by adding production-grade, pluggable
live-model integration.

### Added
- `policy_advisor/utils/adapters/`: `AnthropicAdapter` (Claude Messages API),
  `OpenAIAdapter` (Chat Completions, OpenAI-compatible), stdlib `_http.py`
  helper, and `make_llm_adapter()` factory with auto-detection
  (anthropic -> openai -> mock).
- `LLMParams.provider` + `api_base_url` config fields; `PEPA_LLM_PROVIDER` /
  `PEPA_LLM_API_BASE_URL` env overrides; `default.json` updated.
- CLI `--provider` flag.
- `tests/test_adapters.py` (13 tests): factory resolution, request/response
  shapes via monkeypatched HTTP, error translation, registry wiring.

### Key fixes
- `RetryingLLMAdapter` now fails fast on non-recoverable errors (e.g. missing
  API key) instead of pointlessly retrying - better production behavior.
- `conftest.py` autouse fixture pins `PEPA_LLM_PROVIDER=mock`, reloads settings,
  and resets the registry per test, so the suite is deterministic and fast
  regardless of ambient keys (the host had a placeholder `OPENAI_API_KEY`
  that previously made advise() attempt real network calls + retries ~5s each).
- Stripped BOMs from the new adapter files.

### Verification (all green)
- `validate_skill` OK
- `run_self_test` 6/6
- `seed_research` 28 papers
- `evaluate_outputs` 95.0%
- `pytest -q` -> **70 passed in ~0.6s**
- CLI verified: `python -m policy_advisor --provider mock ...` returns ok.
