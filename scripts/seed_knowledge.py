"""Seed the knowledge base manifest from SECOND-BRAIN-KNOWLEDGE-PAPER.md.

Parses the numbered source list in ``SECOND-BRAIN-KNOWLEDGE-PAPER.md`` and
writes a structured ``assets/knowledge-base.json`` mapping each source to the
methodology it supports. This makes the curated reading list machine-readable
for grounding and citation tooling.

Usage:
    python -m scripts.seed_knowledge
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Heuristic mapping of source substrings to methodology buckets.
_METHODOLOGY_MAP = [
    ("welfare-economics-cba", ["public finance", "public economics", "public sector", "principles of economics", "atkinson", "stiglitz"]),
    ("tax-incidence", ["incidence", "laffer", "tax policy", " Piketty", "capital in the twenty"]),
    ("market-failure", ["social cost", "public expenditure", "lemons", "public good"]),
    ("macro-schools", ["keynes", "friedman", "monetary policy", "lucas", "econometric policy", "supply-side", "wanniski"]),
    ("causal-inference", ["instruments", "harmless econometrics", "poor economics", "data for better lives", "deaton"]),
    ("distribution-redistribution", ["inequality", " Piketty", "atkinson", "rodrik"]),
]


def _bucket(label: str) -> list[str]:
    low = label.lower()
    buckets: list[str] = []
    for bucket, signals in _METHODOLOGY_MAP:
        if any(sig in low for sig in signals):
            buckets.append(bucket)
    return buckets or ["general"]


_LINE_RE = re.compile(r"^\s*(\d+)\.\s+(.+)$")


def parse_sources(text: str) -> list[dict]:
    # Only parse the dedicated sources section; stop at the "How to Use" heading.
    section = text.split("## How to Use", 1)[0]
    sources: list[dict] = []
    for line in section.splitlines():
        m = _LINE_RE.match(line)
        if not m:
            continue
        num = int(m.group(1))
        body = m.group(2).strip()
        # Split label and note on the em-dash / hyphen separator.
        parts = re.split(r"\s[\u2014\-]\s", body, maxsplit=1)
        label = parts[0].strip()
        note = parts[1].strip() if len(parts) > 1 else ""
        sources.append({
            "number": num,
            "label": label,
            "note": note,
            "methodologies": _bucket(label + " " + note),
        })
    return sources


def main() -> int:
    kb_file = PROJECT_ROOT / "SECOND-BRAIN-KNOWLEDGE-PAPER.md"
    if not kb_file.exists():
        print("[seed_knowledge] SECOND-BRAIN-KNOWLEDGE-PAPER.md missing", file=sys.stderr)
        return 1
    text = kb_file.read_text(encoding="utf-8")
    sources = parse_sources(text)
    out = PROJECT_ROOT / "assets" / "knowledge-base.json"
    out.write_text(json.dumps({"count": len(sources), "sources": sources}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[seed_knowledge] wrote {len(sources)} sources to {out.relative_to(PROJECT_ROOT)}")
    for s in sources:
        print(f"  [{s['number']:>2}] {s['label']} -> {', '.join(s['methodologies'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
