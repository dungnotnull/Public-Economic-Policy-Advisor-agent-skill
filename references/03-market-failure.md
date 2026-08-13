# 03 — Market-Failure Framework (Operational Reference)

> Distilled from Coase (1960), Samuelson (1954), Akerlof (1970), and Stiglitz (2000).

## When to apply
Any question about whether government intervention is justified, or whether a market "fails".

## Diagnostic checklist (apply all)
1. **Negative externality** — pollution, congestion, third-party harm. Intervention: Pigouvian tax, regulation, or tradable permits.
2. **Positive externality** — vaccination, education, R&D spillovers. Intervention: subsidy, public provision, or IP protection.
3. **Public good** — non-excludable & non-rival (defence, basic research, clean air). Intervention: public provision/financing.
4. **Information asymmetry** — lemons, adverse selection, moral hazard, credence goods. Intervention: disclosure mandates, standards, licensing, pooling.
5. **Market power** — monopoly, oligopoly, barriers to entry, natural monopoly. Intervention: antitrust, price regulation, public ownership for natural monopolies.
6. **Coordination failure** — networks, standards, development traps. Intervention: standard-setting, infrastructure, strategic coordination.
7. **Distributional equity** — inequality, poverty. Intervention: progressive taxation and targeted transfers. **Equity is a value judgement, not a pure efficiency failure — flag it separately.**

## Operational steps
1. Scan the situation text for the signal keywords above (the `market_failure_diagnostic` tool automates this).
2. For each diagnosed failure, state the intervention it justifies.
3. Check the proposed intervention against the diagnosed failure: it should target the specific failure, not be broader than necessary.
4. If no failure is detected, state that an efficiency case is not supported; intervention may still be justified on equity grounds, separately.

## Standing cautions
- Do not conflate equity with efficiency.
- A diagnosed failure is necessary but not sufficient: the intervention's own costs must still pass a cost-benefit test.

## Output mapping
Maps to `PolicyAnalysisReport.market_failure_diagnosis` via the `market_failure_diagnostic` tool.
