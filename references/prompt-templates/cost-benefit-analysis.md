# Prompt Template — Cost-Benefit Analysis

Use this template when the requested format is `cost-benefit-analysis` or for the CBA section of a policy memo.

## System context
You are applying welfare-economics cost-benefit analysis. Name the framework explicitly. Use qualitative-ordinal magnitudes, not fabricated currency.

## User prompt skeleton
```
Policy proposal: {policy_name}
Jurisdiction: {jurisdiction}

Enumerate, for each affected party (consumers, producers, taxpayers, government, third parties):
- a benefit or cost item,
- its qualitative magnitude (negligible | small | moderate | large | very large),
- its direction (benefit | cost),
- your confidence (low | medium | high).

Then aggregate using the transparent weighting rule (sign * magnitude * confidence) and state the verdict band. Flag low-confidence items for sensitivity analysis and report distributional effects separately from the efficiency verdict.
```

## Required disclaimer
Append the standing disclaimer to every substantive response.
