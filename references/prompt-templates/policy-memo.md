# Prompt Template — Policy Memo

Use this template when the requested format is `policy-memo` (the general default).

## System context
You are producing a structured policy memo that combines the relevant frameworks. Name each framework you apply. Keep the structure consistent and auditable.

## User prompt skeleton
```
Policy question: {user_query}
Jurisdiction: {jurisdiction}

Produce a structured memo with these sections:
1. Summary — one-paragraph framing and headline finding.
2. Frameworks applied — name each (CBA, market-failure, incidence, comparative schools, causal evaluation) and why.
3. Market-failure diagnosis — if applicable.
4. Cost-benefit summary — qualitative-ordinal, with confidence flags.
5. Distributional effects — reported separately from efficiency.
6. Viewpoints — if the question is contested, present the major schools.
7. Empirical evidence — recommended identification strategy if evaluation is requested.
8. Recommendations — actionable, hedged, with explicit assumptions.
9. Uncertainties — what could change the conclusion.
10. Disclaimer — the standing disclaimer.
```

## Required disclaimer
Append the standing disclaimer to every substantive response.
