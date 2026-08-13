# RESEARCH-PAPER-KNOWLEDGE-BRAIN.md - Public Economic Policy Advisor

> The scientific knowledge brain powering this skill. 28 foundational and modern
> papers/books in public economics, each distilled to its **core principle** and
> mapped to the concrete place in this project where that principle is operationalized
> (tool, reference file, and report field). This file is the authoritative,
> machine-parseable grounding source for citation accuracy and persuasiveness.
>
> **How to use:** every substantive skill output should cite the papers that back
> the framework it applies. The runtime citation service (`policy_advisor/citations.py`)
> and `scripts/seed_research.py` consume this file's structured entries.

---

## 1. The Theory of Public Finance
**Authors/Year:** Richard Musgrave, 1959 (McGraw-Hill)
**Core principle:** Government has three economic branches - allocation, distribution, and stabilization - each justifying distinct public-sector interventions; public finance is the study of how these branches are financed and coordinated.
**Methodologies:** welfare-economics-cba, distribution-redistribution
**Operational application:** Frames the skill's separation of efficiency (allocation/market failure) from equity (distribution), enforced as distinct report fields (`distributional_effects` separated from the CBA verdict). Grounds `references/01-welfare-economics-cba.md` and `references/06-distribution-redistribution.md`.

## 2. Lectures on Public Economics
**Authors/Year:** Anthony Atkinson & Joseph Stiglitz, 1980 (McGraw-Hill)
**Core principle:** Welfare economics with explicit attention to second-best effects and distributional weights; optimal policy must trade off efficiency against equity, and information constraints make first-best rules inapplicable.
**Methodologies:** welfare-economics-cba, distribution-redistribution
**Operational application:** Justifies the `cost_benefit_analysis` tool's confidence-weighted, ordinal-magnitude aggregation (avoiding spurious first-best precision) and the explicit separation of efficiency from equity in `PolicyAnalysisReport`.

## 3. The Incidence of the Corporation Income Tax
**Authors/Year:** Arnold Harberger, 1962 (Journal of Political Economy)
**Core principle:** In a closed economy with perfectly inelastic capital, the corporate income tax is borne by all capital owners (not workers or consumers); incidence is determined by relative factor elasticities and mobility, not statutory assignment.
**Methodologies:** tax-incidence
**Operational application:** Core of the `tax_incidence` tool: buyer share = Es/(Es+Ed), seller share = Ed/(Es+Ed); the more inelastic side bears the burden. Drives `TaxIncidenceReport` and `references/02-tax-incidence.md`.

## 4. The Problem of Social Cost
**Authors/Year:** Ronald Coase, 1960 (Journal of Law and Economics)
**Core principle:** Externalities are reciprocal; with well-defined property rights and low transaction costs, private bargaining can internalize external costs without Pigouvian intervention. Transaction costs determine whether markets or regulation are efficient.
**Methodologies:** market-failure
**Operational application:** The `market_failure_diagnostic` tool's `negative_externality` signal and the caveat that "intervention should target the specific failure, not be broader than necessary" (Coasean precision). Grounds `references/03-market-failure.md`.

## 5. The Pure Theory of Public Expenditure
**Authors/Year:** Paul Samuelson, 1954 (Review of Economics and Statistics)
**Core principle:** Pure public goods are non-rival and non-excludable; their optimal provision requires summing individual marginal willingness-to-pay, and private markets under-supply them, justifying public financing.
**Methodologies:** market-failure
**Operational application:** The `public_good` failure type in `market_failure_diagnostic` and its intervention mapping to public provision/financing.

## 6. The Market for 'Lemons'
**Authors/Year:** George Akerlof, 1970 (Quarterly Journal of Economics)
**Core principle:** Asymmetric information (adverse selection) can cause markets to unravel - bad quality drives out good - justifying disclosure, standards, licensing, or pooling interventions.
**Methodologies:** market-failure
**Operational application:** The `information_asymmetry` failure type and its intervention rationale (disclosure, standards, pooling) in the diagnostic tool.

## 7. The General Theory of Employment, Interest and Money
**Authors/Year:** John Maynard Keynes, 1936 (Macmillan)
**Core principle:** Aggregate demand can be chronically deficient because of sticky prices/wages and liquidity preference, justifying active fiscal and monetary stabilization rather than relying on self-correcting markets.
**Methodologies:** macro-schools
**Operational application:** The `Keynesian` viewpoint in the `comparative_schools` tool and the `pro-con-debate` template; grounds the countercyclical-policy position in `ProConDebateReport`.

## 8. The Role of Monetary Policy
**Authors/Year:** Milton Friedman, 1968 (American Economic Review)
**Core principle:** Inflation is always and everywhere a monetary phenomenon; the long-run Phillips curve is vertical, so discretionary fine-tuning is inferior to stable money-growth rules.
**Methodologies:** macro-schools
**Operational application:** The `Monetarist` viewpoint in `comparative_schools` and the caveat on velocity instability; provides the counter-position to Keynesian stimulus in pro/con debates.

## 9. Econometric Policy Evaluation: A Critique
**Authors/Year:** Robert Lucas, 1976 (Carnegie-Rochester Conference Series)
**Core principle:** Structural econometric parameters are not invariant to changes in policy regime; agents form expectations and adapt, so models estimated under one regime cannot be mechanically used to forecast another.
**Methodologies:** macro-schools, causal-inference
**Operational application:** The `New Classical` viewpoint and the universal caveat in `references/05-causal-inference.md` ("behavioural responses to a new policy may differ from historical estimates"); guards against over-confident empirical extrapolation.

## 10. The Way the World Works (Laffer curve)
**Authors/Year:** Arthur Laffer, discussed in Jude Wanniski, 1978 (Basic Books)
**Core principle:** Beyond some tax rate, higher rates reduce revenue by shrinking the taxed base and encouraging avoidance; revenue feedback is largest where rates are already high and elasticities large.
**Methodologies:** tax-incidence, macro-schools
**Operational application:** The `Supply-side` viewpoint and the `tax_incidence` caveat that revenue feedback is "usually modest at typical OECD rates"; the tool flags distributional regressivity alongside supply-side claims.

## 11. Instruments, Randomization, and Learning about Development
**Authors/Year:** Angus Deaton, 2010 (Journal of Economic Literature)
**Core principle:** RCTs deliver high internal validity but limited external validity and often lack the structural theory needed for extrapolation; credible identification must be paired with economic theory and careful scale-up reasoning.
**Methodologies:** causal-inference
**Operational application:** The `causal_evaluation` tool's explicit external-validity threat for RCTs and the "do not fabricate effect sizes" guardrail; grounds `CausalEvaluationReport.threats_to_validity`.

## 12. Mostly Harmless Econometrics
**Authors/Year:** Joshua Angrist & Jorn-Steffen Pischke, 2009 (Princeton University Press)
**Core principle:** Causal effects are identified by clean research designs (RCT, DiD, RDD, IV); the credibility revolution prioritizes identification over structural modeling, with transparent attention to assumptions.
**Methodologies:** causal-inference
**Operational application:** The five-method selection logic and identification strategies in the `causal_evaluation` tool; the default confidence tiers (RCT high, DiD/RDD medium, IV/natural experiment low).

## 13. Poor Economics
**Authors/Year:** Abhijit Banerjee & Esther Duflo, 2011 (PublicAffairs)
**Core principle:** Randomized field experiments can identify what works for the poor at a granular level, enabling evidence-based welfare-policy design while remaining humble about generalization.
**Methodologies:** causal-inference, distribution-redistribution
**Operational application:** The RCT recommendation path in `causal_evaluation` when `can_randomize` is true and the welfare-policy evidence framing in `PolicyAnalysisReport.empirical_evidence`.

## 14. Inequality: What Can Be Done?
**Authors/Year:** Anthony B. Atkinson, 2015 (Harvard University Press)
**Core principle:** Inequality is a policy choice; a concrete package of progressive taxation, social insurance, and public services can reduce it, and distributional impact must be assessed separately from efficiency.
**Methodologies:** distribution-redistribution, welfare-economics-cba
**Operational application:** The distributional section of `references/06-distribution-redistribution.md` and the rule that distributional effects are reported as a separate dimension in every report.

## 15. Capital in the Twenty-First Century
**Authors/Year:** Thomas Piketty, 2014 (Harvard University Press)
**Core principle:** When the return on capital exceeds growth (r > g) for long periods, wealth concentration rises, informing debates on capital and inheritance taxation - but long-run forecasts are speculative.
**Methodologies:** tax-incidence, distribution-redistribution
**Operational application:** The `tax-incidence` caveat on capital-tax debates and the "long-run dynamics are speculative as forecasts" guardrail in the distribution reference.

## 16. Tax Policy Reforms: OECD and Selected Partner Economies
**Authors/Year:** OECD, 2019 (OECD Publishing)
**Core principle:** Comparative, regularly updated cross-country evidence on tax design reveals what reforms actually do in practice, anchoring incidence and distributional claims in observed policy rather than theory alone.
**Methodologies:** tax-incidence, distribution-redistribution
**Operational application:** Empirical anchor for `tax_incidence` caveats ("elasticities are empirical estimates, not constants") and the comparative-evidence framing in tax reports.

## 17. World Development Report: Data for Better Lives
**Authors/Year:** World Bank, 2021 (World Bank)
**Core principle:** Better data and public-data infrastructure enable more credible, granular policy evaluation and improved public-service delivery.
**Methodologies:** causal-inference
**Operational application:** The data-requirements fields in `CausalEvaluationReport` and the recommendation to "pre-register the analysis and report threats to validity transparently."

## 18. Principles of Economics (9th ed.)
**Authors/Year:** N. Gregory Mankiw, 2020 (Cengage)
**Core principle:** Ten principles of economics (trade-offs, marginal thinking, incentives, trade) provide the standard micro/macro bridge from theory to policy analysis.
**Methodologies:** welfare-economics-cba
**Operational application:** The common-language framing of the `cost_benefit_analysis` and `market_failure_diagnostic` tools and the glossary definitions in `references/glossary.md`.

## 19. Economics of the Public Sector (3rd ed.)
**Authors/Year:** Joseph Stiglitz, 2000 (Norton)
**Core principle:** Comprehensive public-sector economics: market failures, public goods, taxation, redistribution, and the limits of government must be analyzed together with attention to information and incentive constraints.
**Methodologies:** welfare-economics-cba, market-failure, distribution-redistribution
**Operational application:** The integrated framing behind `PolicyAnalysisReport` combining CBA + market failure + distribution; cited as the foundational public-sector reference.

## 20. One Economics, Many Recipes
**Authors/Year:** Dani Rodrik, 2007 (Princeton University Press)
**Core principle:** There is no single institutional recipe for growth; good policy is context-specific, diagnostic, and pragmatic, grounded in comparative institutional analysis rather than universal blueprints.
**Methodologies:** macro-schools, distribution-redistribution
**Operational application:** The "empirical resolution depends on context" statement in `ProConDebateReport` and the deferral to context-specific causal evidence rather than endorsing one school as settled.

## 21. An Exploration in the Theory of Optimum Income Taxation
**Authors/Year:** James Mirrlees, 1971 (Review of Economic Studies)
**Core principle:** Optimal nonlinear income taxation balances redistribution against the incentive cost of distorting labour supply; the marginal tax schedule depends on the distribution of abilities and the social welfare function, not on a flat "fair" rate.
**Methodologies:** tax-incidence, distribution-redistribution
**Operational application:** Deepens the `tax-incidence` welfare-effects analysis (deadweight loss from distorting labour supply) and grounds the optimal-tax framing in distributional analysis; warns against declaring a single "correct" top rate.

## 22. Optimal Taxation and Public Production I & II
**Authors/Year:** Peter Diamond & James Mirrlees, 1971 (American Economic Review)
**Core principle:** Production efficiency is generically optimal under broad conditions: indirect taxes should not distort intermediate production; tax distortions should be confined to final consumer goods to minimize productive efficiency loss.
**Methodologies:** tax-incidence, welfare-economics-cba
**Operational application:** Refines the `tax_incidence` welfare_effects and the `cost_benefit_analysis` deadweight-loss item; supports the "target the specific failure, not broader than necessary" precision principle.

## 23. Fiscal Federalism
**Authors/Year:** Wallace Oates, 1972 (Harcourt Brace Jovanovich)
**Core principle:** The assignment of fiscal responsibilities should follow the principle of fiscal equivalence - each public service should be provided by the jurisdiction whose boundaries match the benefit area; decentralization improves allocative efficiency for local goods.
**Methodologies:** market-failure, distribution-redistribution
**Operational application:** Extends the `public_good` analysis to jurisdictional assignment; informs the distributional and jurisdiction fields when the user specifies a level of government.

## 24. A Pure Theory of Local Expenditures
**Authors/Year:** Charles Tiebout, 1956 (Journal of Political Economy)
**Core principle:** When local public goods differ across jurisdictions and households are mobile, "voting with feet" can reveal preferences and produce an efficient provision of local goods, mitigating the Samuelson under-supply problem for local goods.
**Methodologies:** market-failure
**Operational application:** Nuances the `public_good` diagnosis: for local goods, interjurisdictional mobility can partially substitute for intervention; flagged as a caveat in `references/03-market-failure.md`.

## 25. Sufficient Statistics for Welfare Analysis
**Authors/Year:** Raj Chetty, 2009 (Annual Review of Economics)
**Core principle:** Many welfare and incidence conclusions can be derived from a small set of "sufficient statistics" (elasticities, pass-through, behavioural responses) without fully specifying a structural model - making incidence analysis tractable and empirically grounded.
**Methodologies:** tax-incidence, welfare-economics-cba
**Operational application:** Methodological justification for the `tax_incidence` tool's reliance on two elasticities as sufficient statistics for incidence shares, and for the `cost_benefit_analysis` tool's use of magnitudes and elasticities rather than full structural models.

## 26. Using Elasticities to Derive Optimal Income Tax Rates
**Authors/Year:** Emmanuel Saez, 2001 (Review of Economic Studies)
**Core principle:** Optimal top marginal tax rates can be derived from three sufficient statistics - the elasticity of taxable income, the Pareto parameter of the income distribution, and the social welfare weight - making optimal-tax claims empirically testable.
**Methodologies:** tax-incidence, distribution-redistribution
**Operational application:** Grounds the `tax_incidence` caveat that revenue feedback and optimal rates "depend on elasticities which are empirical estimates" and the refusal to declare a single optimal top rate; cited in distributional analysis.

## 27. Minimum Wages and Employment
**Authors/Year:** David Card & Alan Krueger, 1994 (NBER / American Economic Review)
**Core principle:** A well-identified natural experiment (comparing fast-food employment across a policy border) can overturn prior consensus; credible quasi-experimental design can estimate policy effects that theory alone could not settle.
**Methodologies:** causal-inference
**Operational application:** Canonical example behind the `natural_experiment` and `DiD` methods in `causal_evaluation`; demonstrates why contested policy questions should be deferred to credible empirical identification rather than theory.

## 28. Sample Selection Bias as a Specification Error
**Authors/Year:** James Heckman, 1979 (Econometrica)
**Core principle:** Non-random sample selection biases estimated relationships; credible policy evaluation must model selection into treatment and exposure, or estimates will be systematically misleading.
**Methodologies:** causal-inference
**Operational application:** The "selection into exposure" and "endogeneity of the shock" threats to validity in `CausalEvaluationReport`, and the universal guardrail against naively comparing treated and untreated groups without an identification strategy.

---

## Methodology -> Paper index (used by the citation service)

- **welfare-economics-cba:** 1, 2, 18, 19, 22, 25
- **tax-incidence:** 3, 10, 15, 16, 21, 22, 25, 26
- **market-failure:** 4, 5, 6, 19, 23, 24
- **macro-schools:** 7, 8, 9, 10, 20
- **causal-inference:** 9, 11, 12, 13, 17, 27, 28
- **distribution-redistribution:** 1, 2, 13, 14, 15, 16, 20, 21, 23, 26

> The runtime citation service (`policy_advisor/citations.py`) embeds this index
> so every report cites the research backing the framework it applied, and
> `scripts/seed_research.py` materializes it as `assets/research-papers.json`.
