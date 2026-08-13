"""Citation-grounding service.

Maps each methodology to the scientific papers that back it (sourced from
``RESEARCH-PAPER-KNOWLEDGE-BRAIN.md``). Sub-advisors use this to populate the
``citations`` and ``evidence_base`` fields of reports so every output cites the
research that actually supports the framework it applied - improving accuracy
and persuasiveness instead of hard-coding a couple of citations.

The registry is self-contained (no parsing required at runtime) and mirrors
the human-readable brain file; ``scripts/seed_research.py`` materializes a
JSON manifest from the brain for tooling and auditing.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from config.schema import Citation

# --------------------------------------------------------------------------- #
# Paper registry: id -> (label, methodologies)
# --------------------------------------------------------------------------- #
PAPERS: Dict[str, Tuple[str, List[str]]] = {
    "musgrave-1959": ("Musgrave (1959), The Theory of Public Finance, McGraw-Hill", ["welfare-economics-cba", "distribution-redistribution"]),
    "atkinson-stiglitz-1980": ("Atkinson & Stiglitz (1980), Lectures on Public Economics, McGraw-Hill", ["welfare-economics-cba", "distribution-redistribution"]),
    "harberger-1962": ("Harberger (1962), The Incidence of the Corporation Income Tax, JPE", ["tax-incidence"]),
    "coase-1960": ("Coase (1960), The Problem of Social Cost, J. Law & Econ.", ["market-failure"]),
    "samuelson-1954": ("Samuelson (1954), The Pure Theory of Public Expenditure, REStat", ["market-failure"]),
    "akerlof-1970": ("Akerlof (1970), The Market for 'Lemons', QJE", ["market-failure"]),
    "keynes-1936": ("Keynes (1936), The General Theory of Employment, Interest and Money", ["macro-schools"]),
    "friedman-1968": ("Friedman (1968), The Role of Monetary Policy, AER", ["macro-schools"]),
    "lucas-1976": ("Lucas (1976), Econometric Policy Evaluation: A Critique", ["macro-schools", "causal-inference"]),
    "laffer-wanniski-1978": ("Laffer, in Wanniski (1978), The Way the World Works", ["tax-incidence", "macro-schools"]),
    "deaton-2010": ("Deaton (2010), Instruments, Randomization, and Learning about Development, JEL", ["causal-inference"]),
    "angrist-pischke-2009": ("Angrist & Pischke (2009), Mostly Harmless Econometrics, Princeton", ["causal-inference"]),
    "banerjee-duflo-2011": ("Banerjee & Duflo (2011), Poor Economics, PublicAffairs", ["causal-inference", "distribution-redistribution"]),
    "atkinson-2015": ("Atkinson (2015), Inequality: What Can Be Done?, Harvard", ["distribution-redistribution", "welfare-economics-cba"]),
    "piketty-2014": ("Piketty (2014), Capital in the Twenty-First Century, Harvard", ["tax-incidence", "distribution-redistribution"]),
    "oecd-2019": ("OECD (2019), Tax Policy Reforms: OECD and Selected Partner Economies", ["tax-incidence", "distribution-redistribution"]),
    "worldbank-2021": ("World Bank (2021), World Development Report: Data for Better Lives", ["causal-inference"]),
    "mankiw-2020": ("Mankiw (2020), Principles of Economics (9th ed.), Cengage", ["welfare-economics-cba"]),
    "stiglitz-2000": ("Stiglitz (2000), Economics of the Public Sector (3rd ed.), Norton", ["welfare-economics-cba", "market-failure", "distribution-redistribution"]),
    "rodrik-2007": ("Rodrik (2007), One Economics, Many Recipes, Princeton", ["macro-schools", "distribution-redistribution"]),
    "mirrlees-1971": ("Mirrlees (1971), An Exploration in the Theory of Optimum Income Taxation, REStud", ["tax-incidence", "distribution-redistribution"]),
    "diamond-mirrlees-1971": ("Diamond & Mirrlees (1971), Optimal Taxation and Public Production, AER", ["tax-incidence", "welfare-economics-cba"]),
    "oates-1972": ("Oates (1972), Fiscal Federalism", ["market-failure", "distribution-redistribution"]),
    "tiebout-1956": ("Tiebout (1956), A Pure Theory of Local Expenditures, JPE", ["market-failure"]),
    "chetty-2009": ("Chetty (2009), Sufficient Statistics for Welfare Analysis, Ann. Rev. Econ.", ["tax-incidence", "welfare-economics-cba"]),
    "saez-2001": ("Saez (2001), Using Elasticities to Derive Optimal Income Tax Rates, REStud", ["tax-incidence", "distribution-redistribution"]),
    "card-krueger-1994": ("Card & Krueger (1994), Minimum Wages and Employment", ["causal-inference"]),
    "heckman-1979": ("Heckman (1979), Sample Selection Bias as a Specification Error, Econometrica", ["causal-inference"]),
}

# Ordered priority citations per methodology (the most directly-grounding first).
METHODOLOGY_INDEX: Dict[str, List[str]] = {
    "welfare-economics-cba": ["atkinson-stiglitz-1980", "stiglitz-2000", "mankiw-2020", "musgrave-1959", "diamond-mirrlees-1971", "chetty-2009"],
    "tax-incidence": ["harberger-1962", "chetty-2009", "saez-2001", "mirrlees-1971", "diamond-mirrlees-1971", "oecd-2019", "piketty-2014", "laffer-wanniski-1978"],
    "market-failure": ["coase-1960", "samuelson-1954", "akerlof-1970", "stiglitz-2000", "oates-1972", "tiebout-1956"],
    "macro-schools": ["keynes-1936", "friedman-1968", "lucas-1976", "laffer-wanniski-1978", "rodrik-2007"],
    "causal-inference": ["angrist-pischke-2009", "deaton-2010", "banerjee-duflo-2011", "card-krueger-1994", "heckman-1979", "worldbank-2021", "lucas-1976"],
    "distribution-redistribution": ["atkinson-2015", "piketty-2014", "saez-2001", "mirrlees-1971", "oecd-2019", "rodrik-2007", "musgrave-1959", "atkinson-stiglitz-1980", "banerjee-duflo-2011", "oates-1972"],
}


def citations_for(methodology: str, limit: int = 5, exclude: Optional[List[str]] = None) -> List[Citation]:
    """Return the most directly-grounding ``Citation`` objects for a methodology.

    Falls back to scanning ``PAPERS`` for any paper tagged with the methodology
    if no explicit index entry exists.
    """
    exclude = set(exclude or [])
    ids = list(METHODOLOGY_INDEX.get(methodology, []))
    if not ids:
        ids = [pid for pid, (_, tags) in PAPERS.items() if methodology in tags]
    out: List[Citation] = []
    for pid in ids:
        if pid in exclude:
            continue
        label = PAPERS[pid][0]
        out.append(Citation(source_id=pid, label=label, relevance="supporting"))
        if len(out) >= limit:
            break
    return out


def evidence_base_for(methodologies: List[str], limit_per_method: int = 2) -> List[Citation]:
    """Compose a de-duplicated evidence base across several methodologies."""
    seen: set[str] = set()
    out: List[Citation] = []
    for m in methodologies:
        for c in citations_for(m, limit=limit_per_method, exclude=list(seen)):
            if c.source_id in seen:
                continue
            seen.add(c.source_id)
            out.append(c)
    return out


def all_papers() -> Dict[str, Tuple[str, List[str]]]:
    return dict(PAPERS)
