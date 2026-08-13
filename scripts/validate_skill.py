"""Validate the skill structure end-to-end.

Checks:
1. Required directories and key files exist.
2. Every ``assets/schemas/*.schema.json`` is valid JSON.
3. Every ``references/*.md`` is non-empty.
4. The registry initialises and every default tool's input/output schemas are
   internally consistent (validate a known-good sample against each tool).
5. The SKILL.md frontmatter is well-formed.

Exits non-zero on any failure. Intended for CI and pre-release checks.

Usage:
    python -m scripts.validate_skill
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REQUIRED_FILES = [
    "SKILL.md",
    "README.md",
    "CLAUDE.md",
    "PROJECT-detail.md",
    "PROJECT-DEVELOPMENT-PHASE-TRACKING.md",
    "SECOND-BRAIN-KNOWLEDGE-PAPER.md",
    "RESEARCH-PAPER-KNOWLEDGE-BRAIN.md",
    "config/default.json",
    "config/settings.py",
    "config/schema.py",
    "policy_advisor/__init__.py",
    "policy_advisor/skill_registry.py",
    "policy_advisor/router.py",
    "assets/diagrams/agent-architecture.md",
]

_FRONTMATTER_RE = re.compile(r"^---\r?\n.*?\r?\n---\r?\n", re.DOTALL)


def _check_files() -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (PROJECT_ROOT / rel).exists():
            errors.append(f"missing required file: {rel}")
    return errors


def _check_schemas() -> list[str]:
    errors: list[str] = []
    schema_dir = PROJECT_ROOT / "assets" / "schemas"
    if not schema_dir.exists():
        return ["assets/schemas directory missing"]
    for p in sorted(schema_dir.glob("*.json")):
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON schema {p.name}: {exc}")
    return errors


def _check_references() -> list[str]:
    errors: list[str] = []
    ref_dir = PROJECT_ROOT / "references"
    if not ref_dir.exists():
        return ["references directory missing"]
    for p in sorted(ref_dir.glob("*.md")):
        if len(p.read_text(encoding="utf-8").strip()) == 0:
            errors.append(f"empty reference file: {p.name}")
    return errors


def _check_skill_md() -> list[str]:
    skill = PROJECT_ROOT / "SKILL.md"
    if not skill.exists():
        return ["SKILL.md missing"]
    text = skill.read_text(encoding="utf-8")
    if not _FRONTMATTER_RE.match(text):
        return ["SKILL.md is missing YAML frontmatter"]
    frontmatter = _FRONTMATTER_RE.match(text).group(0)
    if "name:" not in frontmatter or "description:" not in frontmatter:
        return ["SKILL.md frontmatter must declare name and description"]
    return []


def _check_registry() -> list[str]:
    errors: list[str] = []
    try:
        from policy_advisor.tools import register_default_tools
        from policy_advisor.tools.base import ToolRegistry, _validate

        reg = ToolRegistry()
        register_default_tools(reg)
        samples = {
            "cost_benefit_analysis": {"policy_name": "test", "items": [{"category": "x", "description": "y", "estimated_magnitude": "moderate", "direction": "benefit"}]},
            "tax_incidence": {"instrument": "VAT", "supply_elasticity": 1.0, "demand_elasticity": 0.5},
            "market_failure_diagnostic": {"situation": "pollution externality"},
            "comparative_schools": {"policy_question": "stimulus?"},
            "causal_evaluation": {"policy_under_evaluation": "job training"},
        }
        for name, inputs in samples.items():
            tool = reg.get(name)
            errs = _validate(inputs, tool.input_schema)
            if errs:
                errors.append(f"{name} sample input failed schema: {errs}")
                continue
            result = tool.run(inputs)
            out_errs = _validate(result.output, tool.output_schema)
            if out_errs:
                errors.append(f"{name} output failed schema: {out_errs}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"registry check raised: {exc}")
    return errors



def _check_citation_registry() -> list[str]:
    """Cross-check the in-code citation registry against the research brain."""
    errors: list[str] = []
    try:
        from policy_advisor.citations import PAPERS, METHODOLOGY_INDEX
        import re
        brain = (PROJECT_ROOT / "RESEARCH-PAPER-KNOWLEDGE-BRAIN.md").read_text(encoding="utf-8")
        headings = re.findall(r"^##\s+\d+\.\s+(.+)$", brain, re.MULTILINE)
        if len(headings) < 28:
            errors.append(f"research brain has {len(headings)} entries, expected >= 28")
        # Every index entry must resolve to a registered paper.
        for method, ids in METHODOLOGY_INDEX.items():
            for pid in ids:
                if pid not in PAPERS:
                    errors.append(f"citation index references unknown paper '{pid}' for {method}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"citation registry check raised: {exc}")
    return errors


def main() -> int:
    errors: list[str] = []
    errors += _check_files()
    errors += _check_schemas()
    errors += _check_references()
    errors += _check_skill_md()
    errors += _check_citation_registry()
    errors += _check_registry()

    if errors:
        print("[validate_skill] FAILED with the following errors:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("[validate_skill] OK - all structural, schema, reference, and registry checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
