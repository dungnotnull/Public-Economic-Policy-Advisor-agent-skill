"""Public Economic Policy Advisor - configuration package.

Type-safe, environment-aware configuration management for the skill runtime.
All configuration is loaded from a layered source chain:

    defaults (default.json)  ->  local override file  ->  environment variables

No third-party dependencies are required; the module relies on the Python
standard library so the skill can run in any standard CPython 3.9+ runtime.
"""

from .settings import Settings, get_settings, reload_settings
from .schema import (
    PolicyAnalysisReport,
    TaxIncidenceReport,
    ProConDebateReport,
    CausalEvaluationReport,
    SkillInvocation,
    SkillResult,
)

__all__ = [
    "Settings",
    "get_settings",
    "reload_settings",
    "PolicyAnalysisReport",
    "TaxIncidenceReport",
    "ProConDebateReport",
    "CausalEvaluationReport",
    "SkillInvocation",
    "SkillResult",
]
