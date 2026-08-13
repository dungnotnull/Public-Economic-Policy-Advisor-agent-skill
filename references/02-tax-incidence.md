# 02 — Tax & Subsidy Incidence (Operational Reference)

> Distilled from Harberger (1962), Musgrave (1959), and OECD (2019) Tax Policy Reforms.

## When to apply
Any question about who "really pays" a tax, who benefits from a subsidy, or the welfare effects of a fiscal instrument.

## Core principle
**Economic incidence depends on relative elasticities, not on who legally remits the tax.** The more inelastic side bears the larger share of a tax burden (and captures the larger share of a subsidy benefit).

## Operational steps
1. Identify the instrument (e.g., corporate income tax, VAT, carbon tax, subsidy).
2. Obtain or assume supply elasticity (Es) and demand elasticity (Ed). State the assumed values explicitly.
3. Compute buyer share = Es / (Es + Ed); seller share = Ed / (Es + Ed). (Implemented in the `tax_incidence` tool.)
4. Map statutory incidence (who remits) vs economic incidence (who bears the burden) — they almost always differ.
5. Flag distributional consequences for affected groups (capital owners, workers, consumers).
6. Note deadweight loss: any wedge between marginal benefit and marginal cost creates efficiency loss growing with the wedge and the elasticities.

## Standing cautions
- Elasticities are empirical estimates, not constants; report the assumed values.
- This is a partial-equilibrium result. General-equilibrium effects (capital mobility, cross-market shifting) are not modelled here and should be flagged.
- For subsidies, watch for benefits accruing to unintended beneficiaries (e.g., landlords capturing housing subsidies).

## Output mapping
Maps to `TaxIncidenceReport` via the `tax_incidence` tool.
