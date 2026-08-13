"""Chain-of-thought router.

The router is the skill's brainstem. For each invocation it performs an
explicit, logged chain of thought:

1. **Intent detection** -- match the requested format, falling back to
   keyword scoring over the sub-advisors.
2. **Resolution** -- pick the best sub-advisor (format match wins; ties broken
   by keyword relevance).
3. **Validation** -- confirm a sub-advisor was found; otherwise raise a
   :class:`RoutingError` (or fall back to the welfare advisor for general
   policy-memo requests).

Every step is recorded so the route is auditable and reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from config import get_settings
from config.schema import SkillInvocation
from .sub_advisors import SubAdvisor
from .utils.errors import RoutingError
from .utils.logging import get_logger

_log = get_logger("router")


@dataclass
class RoutingDecision:
    sub_advisor: str
    reasoning: List[str] = field(default_factory=list)
    candidates: List[str] = field(default_factory=list)


class ChainOfThoughtRouter:
    def __init__(self, sub_advisors: List[SubAdvisor]) -> None:
        self._advisors = sub_advisors

    def route(self, invocation: SkillInvocation) -> RoutingDecision:
        reasoning: List[str] = []
        settings = get_settings()

        # Step 1: explicit format match.
        explicit = [a for a in self._advisors if a.serves(invocation.requested_format)]
        reasoning.append(
            f"Step 1 (format match): requested_format='{invocation.requested_format}' "
            f"matched {[a.name for a in explicit]}."
        )
        candidates = explicit

        # Step 2: keyword scoring tie-break / fallback.
        if len(candidates) > 1:
            scored = sorted(candidates, key=lambda a: a.matches_query(invocation.user_query), reverse=True)
            reasoning.append(
                "Step 2 (keyword tie-break): "
                + ", ".join(f"{a.name}={a.matches_query(invocation.user_query)}" for a in scored)
            )
            top_score = scored[0].matches_query(invocation.user_query)
            if top_score > 0:
                candidates = [scored[0]]
            else:
                # No keyword signal among format matches: default to the
                # generalist welfare advisor when available, else the top-ranked.
                default = next((a for a in candidates if a.name == "welfare"), scored[0])
                candidates = [default]
                reasoning.append(f"Step 2b (default): no keyword signal; defaulting to '{default.name}'.")
        elif not candidates:
            scored = sorted(self._advisors, key=lambda a: a.matches_query(invocation.user_query), reverse=True)
            reasoning.append(
                "Step 2 (keyword fallback, no format match): "
                + ", ".join(f"{a.name}={a.matches_query(invocation.user_query)}" for a in scored)
            )
            if scored and scored[0].matches_query(invocation.user_query) > 0:
                candidates = [scored[0]]
            else:
                # Default to the welfare advisor for open-ended policy-memo requests.
                default = next((a for a in self._advisors if a.name == "welfare"), self._advisors[0])
                candidates = [default]
                reasoning.append(f"Step 2b (default): no keyword signal; defaulting to '{default.name}'.")

        if not candidates:
            raise RoutingError("No sub-advisor could be resolved for the invocation.")

        chosen = candidates[0]
        if not settings.features.enable_chain_of_thought_router:
            reasoning = ["Chain-of-thought router disabled by feature flag; using explicit match only."]

        decision = RoutingDecision(
            sub_advisor=chosen.name,
            reasoning=reasoning,
            candidates=[a.name for a in self._advisors],
        )
        _log.info("route_resolved", request_id=invocation.request_id, sub_advisor=chosen.name)
        return decision

    def resolve(self, invocation: SkillInvocation) -> SubAdvisor:
        decision = self.route(invocation)
        for a in self._advisors:
            if a.name == decision.sub_advisor:
                return a
        raise RoutingError(f"Resolved sub-advisor '{decision.sub_advisor}' not registered.")
