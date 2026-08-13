# Prompt Template — Tax Incidence Analysis

Use this template when the requested format is `tax-incidence`.

## System context
You are applying Harberger-style tax-incidence theory. Economic incidence depends on relative elasticities, not statutory assignment.

## User prompt skeleton
```
Instrument: {instrument}
Jurisdiction: {jurisdiction}
Assumed supply elasticity (Es): {supply_elasticity}
Assumed demand elasticity (Ed): {demand_elasticity}
Is this a subsidy? {is_subsidy}

Compute buyer share = Es / (Es + Ed) and seller share = Ed / (Es + Ed).
Report:
- statutory incidence vs economic incidence,
- the buyer-side and seller-side burden/benefit shares,
- distributional effects on affected groups ({affected_groups}),
- deadweight loss and welfare effects,
- caveats (elasticities are estimates; partial-equilibrium only; general-equilibrium effects not modelled).
State the assumed elasticities explicitly.
```

## Required disclaimer
Append the standing disclaimer to every substantive response.
