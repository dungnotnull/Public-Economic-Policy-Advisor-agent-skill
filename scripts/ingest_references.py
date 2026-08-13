"""Ingest references into a searchable manifest.

Scans ``references/*.md`` and ``references/prompt-templates/*.md``, builds a
manifest (title, path, token estimate, one-line summary) and writes it to
``assets/reference-manifest.json``. The manifest is consumed by tooling and
gives a quick overview of the grounding corpus without re-reading every file.

Usage:
    python -m scripts.ingest_references
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from policy_advisor.utils.context import token_estimate


def _summary(text: str) -> str:
    # First non-empty, non-heading line.
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith(">"):
            continue
        return s[:160]
    return ""


def _title(path: Path, text: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else path.stem


def main() -> int:
    ref_root = PROJECT_ROOT / "references"
    if not ref_root.exists():
        print("[ingest_references] references directory missing", file=sys.stderr)
        return 1

    entries: list[dict] = []
    for path in sorted(list(ref_root.glob("*.md")) + list((ref_root / "prompt-templates").glob("*.md"))):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        entries.append({
            "id": path.stem,
            "path": rel,
            "title": _title(path, text),
            "summary": _summary(text),
            "tokens_estimate": token_estimate(text),
            "chars": len(text),
        })

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(entries),
        "entries": entries,
    }
    out = PROJECT_ROOT / "assets" / "reference-manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ingest_references] wrote manifest with {len(entries)} entries to {out.relative_to(PROJECT_ROOT)}")
    for e in entries:
        print(f"  - {e['id']}: {e['tokens_estimate']} tokens | {e['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
