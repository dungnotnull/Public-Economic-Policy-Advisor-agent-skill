"""Seed the research-paper knowledge brain into a machine-readable manifest.

Parses ``RESEARCH-PAPER-KNOWLEDGE-BRAIN.md`` (each entry is a `## N. Title`
heading followed by labelled lines) and writes ``assets/research-papers.json``
with one record per paper: id, title, authors/year, core principle,
methodologies, and operational application. Cross-checked against the
in-code citation registry in ``policy_advisor/citations.py``.

Usage:
    python -m scripts.seed_research
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from policy_advisor.citations import PAPERS

_HEADING_RE = re.compile(r"^##\s+(\d+)\.\s+(.+)$", re.MULTILINE)


def parse_brain(text: str) -> list[dict]:
    entries: list[dict] = []
    blocks = re.split(r"(?=^##\s+\d+\.\s)", text, flags=re.MULTILINE)
    for block in blocks:
        m = _HEADING_RE.match(block)
        if not m:
            continue
        num = int(m.group(1))
        title = m.group(2).strip()
        authors = _field(block, "Authors/Year")
        principle = _field(block, "Core principle")
        methods = _field(block, "Methodologies")
        application = _field(block, "Operational application")
        entries.append({
            "number": num,
            "id": _slugify(title),
            "title": title,
            "authors_year": authors,
            "core_principle": principle,
            "methodologies": [m.strip() for m in methods.split(",") if m.strip()],
            "operational_application": application,
        })
    return entries


def _field(block: str, label: str) -> str:
    m = re.search(rf"^\*\*{re.escape(label)}:\*\*\s*(.+)$", block, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _slugify(title: str) -> str:
    # Map known titles to the citation-registry ids for cross-referencing.
    key = title.lower()
    id_map = {
        "the theory of public finance": "musgrave-1959",
        "lectures on public economics": "atkinson-stiglitz-1980",
        "the incidence of the corporation income tax": "harberger-1962",
        "the problem of social cost": "coase-1960",
        "the pure theory of public expenditure": "samuelson-1954",
        "the market for 'lemons'": "akerlof-1970",
        "the general theory of employment, interest and money": "keynes-1936",
        "the role of monetary policy": "friedman-1968",
        "econometric policy evaluation: a critique": "lucas-1976",
        "the way the world works (laffer curve)": "laffer-wanniski-1978",
        "instruments, randomization, and learning about development": "deaton-2010",
        "mostly harmless econometrics": "angrist-pischke-2009",
        "poor economics": "banerjee-duflo-2011",
        "inequality: what can be done?": "atkinson-2015",
        "capital in the twenty-first century": "piketty-2014",
        "tax policy reforms: oecd and selected partner economies": "oecd-2019",
        "world development report: data for better lives": "worldbank-2021",
        "principles of economics (9th ed.)": "mankiw-2020",
        "economics of the public sector (3rd ed.)": "stiglitz-2000",
        "one economics, many recipes": "rodrik-2007",
        "an exploration in the theory of optimum income taxation": "mirrlees-1971",
        "optimal taxation and public production i & ii": "diamond-mirrlees-1971",
        "fiscal federalism": "oates-1972",
        "a pure theory of local expenditures": "tiebout-1956",
        "sufficient statistics for welfare analysis": "chetty-2009",
        "using elasticities to derive optimal income tax rates": "saez-2001",
        "minimum wages and employment": "card-krueger-1994",
        "sample selection bias as a specification error": "heckman-1979",
    }
    return id_map.get(key, re.sub(r"[^a-z0-9]+", "-", key).strip("-"))


def main() -> int:
    brain = PROJECT_ROOT / "RESEARCH-PAPER-KNOWLEDGE-BRAIN.md"
    if not brain.exists():
        print("[seed_research] RESEARCH-PAPER-KNOWLEDGE-BRAIN.md missing", file=sys.stderr)
        return 1
    entries = parse_brain(brain.read_text(encoding="utf-8"))

    # Cross-check against the in-code registry.
    registry_ids = set(PAPERS)
    parsed_ids = {e["id"] for e in entries}
    missing_in_registry = parsed_ids - registry_ids
    missing_in_brain = registry_ids - parsed_ids

    manifest = {
        "source": "RESEARCH-PAPER-KNOWLEDGE-BRAIN.md",
        "count": len(entries),
        "entries": entries,
        "cross_check": {
            "registry_size": len(registry_ids),
            "parsed_size": len(parsed_ids),
            "missing_in_registry": sorted(missing_in_registry),
            "missing_in_brain": sorted(missing_in_brain),
        },
    }
    out = PROJECT_ROOT / "assets" / "research-papers.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[seed_research] wrote {len(entries)} papers to {out.relative_to(PROJECT_ROOT)}")
    for e in entries:
        print(f"  [{e['number']:>2}] {e['id']} -> {', '.join(e['methodologies'])}")
    if missing_in_registry or missing_in_brain:
        print(f"[seed_research] cross-check differences -> registry_missing: {sorted(missing_in_registry)}, brain_missing: {sorted(missing_in_brain)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
