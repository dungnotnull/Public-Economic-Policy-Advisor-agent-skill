"""Local setup routine.

Verifies the Python version, ensures the required directory layout exists,
confirms the ``policy_advisor`` and ``config`` packages import cleanly, and
prints a readiness summary. Idempotent and side-effect-light: it only creates
missing runtime directories (never deletes anything).

Usage:
    python -m scripts.setup
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REQUIRED_DIRS = ["config", "references", "references/prompt-templates", "assets", "assets/schemas", "assets/diagrams", "scripts", "policy_advisor", "tests"]


def ensure_dirs() -> list[str]:
    created: list[str] = []
    for rel in REQUIRED_DIRS:
        d = PROJECT_ROOT / rel
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(rel)
    return created


def check_imports() -> bool:
    try:
        import policy_advisor  # noqa: F401
        import config  # noqa: F401
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[setup] import check FAILED: {exc}", file=sys.stderr)
        return False


def main() -> int:
    if sys.version_info < (3, 9):
        print(f"[setup] Python 3.9+ required, found {sys.version_info.major}.{sys.version_info.minor}", file=sys.stderr)
        return 1

    created = ensure_dirs()
    print(f"[setup] ensured directories exist; created: {created or 'none'}")

    if not check_imports():
        return 2

    from policy_advisor import get_settings
    settings = get_settings()
    print(f"[setup] skill: {settings.skill_name} v{settings.skill_version}")
    print(f"[setup] environment: {settings.environment}, log_level: {settings.log_level}")
    print(f"[setup] LLM model: {settings.llm.model}")
    print(f"[setup] features enabled: {sum(1 for v in vars(settings.features) if getattr(settings.features, v))}")
    print("[setup] OK - skill runtime is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
