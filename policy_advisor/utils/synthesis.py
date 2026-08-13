"""Narrative synthesis: grounded, persuasive prose for report outputs.

The sub-advisors produce structured, deterministic report fields from tools.
This module adds the *persuasive* layer: a grounded narrative paragraph that
names the framework applied, cites the underlying research principles, and
references the evidence base. It uses the LLM adapter when a real model is
available (with the RAG reference snippets injected into the system prompt) and
falls back to a deterministic, framework-named paragraph otherwise - so the
skill always produces coherent, evidence-grounded prose even offline.
"""

from __future__ import annotations

from typing import List, Optional

from config import get_settings
from .context import LLMAdapter, build_system_prompt, token_estimate
from .logging import get_logger

_log = get_logger("synthesis")

_FALLBACK_TOKEN = "[FALLBACK/MOCK-LLM]"


def build_narrative(
    framework_name: str,
    principles: List[str],
    evidence_labels: List[str],
    summary: str,
) -> str:
    """Deterministic, grounded narrative used when no real LLM output is available."""
    parts = [f"Framework applied: {framework_name}."]
    if principles:
        parts.append("Grounding principles: " + "; ".join(principles[:4]) + ".")
    if evidence_labels:
        parts.append("Evidence base: " + "; ".join(evidence_labels[:5]) + ".")
    if summary:
        parts.append(summary)
    parts.append(
        "Where the evidence base is mixed or contested, this analysis presents "
        "multiple viewpoints rather than a single settled conclusion."
    )
    return " ".join(parts)


def synthesize_narrative(
    llm: Optional[LLMAdapter],
    framework_name: str,
    user_query: str,
    reference_snippets: List[str],
    principles: List[str],
    evidence_labels: List[str],
    summary: str,
) -> str:
    """Return grounded narrative prose, LLM-enriched with a deterministic fallback.

    The LLM is invoked only when sub-advisor delegation is enabled. If the LLM
    call fails, returns an empty string, or emits the mock-fallback marker, the
    deterministic ``build_narrative`` paragraph is used instead - guaranteeing
    a persuasive, citation-grounded narrative in every case.
    """
    settings = get_settings()
    fallback = build_narrative(framework_name, principles, evidence_labels, summary)

    if not llm or not settings.features.enable_sub_advisor_delegation:
        return fallback

    system_prompt = build_system_prompt(reference_snippets=reference_snippets)
    user_prompt = (
        f"Policy question: {user_query}\n\n"
        f"Framework applied: {framework_name}\n"
        f"Key principles: {'; '.join(principles[:5])}\n"
        f"Evidence base: {'; '.join(evidence_labels[:5])}\n"
        f"Structured summary: {summary}\n\n"
        "Write a concise, persuasive-but-honest analytical paragraph (3-6 sentences) "
        "that names the framework, references the principles and evidence base, states "
        "the main finding, and flags where evidence is contested. Do not invent numbers. "
        "Do not drop the standing disclaimer context."
    )
    try:
        resp = llm.complete(system_prompt, user_prompt)
        text = (resp.text or "").strip()
    except Exception as exc:  # noqa: BLE001
        _log.warning("narrative_llm_failed", framework=framework_name, error=str(exc))
        return fallback

    if not text or _FALLBACK_TOKEN in text:
        return fallback
    # Enrich: keep the LLM prose but ensure the evidence base is explicitly cited.
    if evidence_labels and not any(label.split(",")[0] in text for label in evidence_labels[:3]):
        text = text + " Evidence base: " + "; ".join(evidence_labels[:3]) + "."
    return text
