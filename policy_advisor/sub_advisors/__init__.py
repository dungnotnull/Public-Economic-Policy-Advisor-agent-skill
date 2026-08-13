"""Specialised sub-advisors.

Each sub-advisor owns a slice of the public-economics domain, declares the
output formats it serves, and combines deterministic tools with the LLM
adapter to produce a structured report. The chain-of-thought router (see
``policy_advisor.router``) selects the appropriate sub-advisor per request.
"""

from .base import SubAdvisor, SubAdvisorContext
from .fiscal_advisor import FiscalAdvisor
from .macro_advisor import MacroAdvisor
from .welfare_advisor import WelfareAdvisor
from .empirical_advisor import EmpiricalAdvisor

__all__ = [
    "SubAdvisor",
    "SubAdvisorContext",
    "FiscalAdvisor",
    "MacroAdvisor",
    "WelfareAdvisor",
    "EmpiricalAdvisor",
    "default_sub_advisors",
]


def default_sub_advisors(ctx: SubAdvisorContext) -> list[SubAdvisor]:
    return [FiscalAdvisor(ctx), MacroAdvisor(ctx), WelfareAdvisor(ctx), EmpiricalAdvisor(ctx)]
