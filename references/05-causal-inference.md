# 05 — Causal Policy-Evaluation Methods (Operational Reference)

> Distilled from Angrist & Pischke (2009), Deaton (2010), Banerjee & Duflo (2011), and World Bank (2021).

## When to apply
Any question about how to *evaluate* a policy empirically, or whether evidence for a policy is credible.

## Methods and selection rule
1. **RCT** — gold standard for internal validity when the intervention can be randomly assigned and is ethical. Threats: external validity, attrition, SUTVA/spillovers.
2. **Difference-in-Differences (DiD)** — uses a comparison group over time to net out common trends. Threats: parallel-trends violation, composition changes, confounding policy changes.
3. **Regression Discontinuity (RDD)** — exploits a sharp eligibility cutoff. Threats: manipulation of the running variable, local-only validity, small samples near the cutoff.
4. **Instrumental Variables (IV)** — uses an exogenous instrument. Threats: weak instruments, exclusion-restriction violation, LATE interpretation.
5. **Natural experiment** — exploits a plausibly exogenous shock. Threats: endogeneity of the shock, selection into exposure.

The `causal_evaluation` tool selects the method deterministically from the evaluation context:
`can_randomize -> RCT; has_eligibility_cutoff -> RDD; has_panel_data -> DiD; has_instrument -> IV; has_exogenous_shock -> natural experiment; else -> DiD`.

## Operational steps
1. State the policy under evaluation and the outcome of interest.
2. Report the recommended method and its identification strategy.
3. List the data requirements for that method.
4. List the threats to validity transparently.
5. Report a confidence level (RCT high; DiD/RDD medium; IV/natural experiment low).
6. Recommend pre-registration and transparent reporting of threats.

## Standing cautions
- Internal validity ≠ external validity. A clean RCT in one setting may not generalise.
- The Lucas critique is relevant: behavioural responses to a new policy may differ from historical estimates.
- Do not fabricate effect sizes; recommend estimating them once suitable data is available.

## Output mapping
Maps to `CausalEvaluationReport` via the `causal_evaluation` tool.
