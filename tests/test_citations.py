"""Tests for the citation-grounding service and research-paper brain."""

import json
from pathlib import Path

import pytest

from policy_advisor.citations import (
    PAPERS,
    METHODOLOGY_INDEX,
    all_papers,
    citations_for,
    evidence_base_for,
)
from config.schema import Citation

ROOT = Path(__file__).resolve().parent.parent


def test_registry_has_at_least_28_papers():
    assert len(PAPERS) >= 28


def test_every_index_entry_exists_in_registry():
    for method, ids in METHODOLOGY_INDEX.items():
        for pid in ids:
            assert pid in PAPERS, f"{pid} in index for {method} but missing from PAPERS"


def test_citations_for_returns_citation_objects():
    out = citations_for("tax-incidence", limit=3)
    assert len(out) == 3
    assert all(isinstance(c, Citation) for c in out)
    assert all(c.source_id and c.label for c in out)
    # Harberger is the priority citation for tax incidence.
    assert out[0].source_id == "harberger-1962"


def test_citations_for_respects_limit_and_exclude():
    out = citations_for("tax-incidence", limit=2, exclude=["harberger-1962"])
    assert all(c.source_id != "harberger-1962" for c in out)
    assert len(out) == 2


def test_citations_for_unknown_methodology_falls_back_to_scan():
    out = citations_for("distribution-redistribution", limit=4)
    assert len(out) == 4


def test_evidence_base_dedupes_across_methodologies():
    base = evidence_base_for(["tax-incidence", "welfare-economics-cba", "market-failure"], limit_per_method=3)
    ids = [c.source_id for c in base]
    assert len(ids) == len(set(ids)), "evidence base must be de-duplicated"
    assert len(base) >= 3


def test_research_brain_file_exists_and_has_28_entries():
    brain = ROOT / "RESEARCH-PAPER-KNOWLEDGE-BRAIN.md"
    assert brain.exists()
    text = brain.read_text(encoding="utf-8")
    # Count "## N. " headings.
    import re
    headings = re.findall(r"^##\s+\d+\.\s", text, re.MULTILINE)
    assert len(headings) >= 28


def test_every_registry_id_appears_in_brain():
    brain = (ROOT / "RESEARCH-PAPER-KNOWLEDGE-BRAIN.md").read_text(encoding="utf-8")
    # Each registry label's first author/year token should appear somewhere.
    for pid, (label, _) in PAPERS.items():
        token = label.split(",")[0].split("(")[0].strip().split()[-1].lower()
        assert token in brain.lower(), f"registry id {pid} ({token}) not found in brain"


def test_all_papers_returns_copy():
    ap = all_papers()
    ap["__test__"] = ("x", [])
    assert "__test__" not in PAPERS
