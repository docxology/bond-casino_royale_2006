# Scope & Related Work {#sec:scope}

## Scope

This package is a **deterministic engineering exemplar**, not a licensed
clinical or financial system. Its contributions are the algorithmic cores and
the reproducibility discipline around them; the specific numeric constants are
documented model choices, not regulatory thresholds. What each of the
{{NUM_CONCEPT_MODULES}} modules does *not* claim:

- **Poker (`poker_engine.py`).** The engine prices hands and recommends
  actions; it is not a full solver (no perfect-information exploitation, no
  multi-street counterfactual regret minimization). Monte-Carlo equity is
  sampled, not solved exhaustively — except the exact turn/river enumerator,
  which is complete over all runouts.
- **CFR (`poker_cfr.py`).** The solve is exact for the *river toy game* only:
  one street, one bet size, discrete uniform strengths. It is not a hold'em
  solver, has no card abstraction or bucketing, and its game value is the toy
  game's value, not the film hand's.
- **ICM (`icm.py`).** The Independent Chip Model assumes finish probability is
  proportional to stack share. That is the standard simplification and it is
  known to be wrong in detail: it ignores position, blind level, and skill
  edge. Bubble factors here are model output, not tournament advice.
- **Bayesian opponent (`opponent_bayes.py`).** The archetype Dirichlet priors
  are declared model choices, not fitted to a hand-history corpus. The
  posterior is exact *given* those priors; it is not a claim about any real
  player, and it assumes actions are exchangeable (no street or board context).
- **Laundering typologies (`laundering_detect.py`).** The detector flags
  *structural* typologies (structuring, round-tripping, velocity, chip
  parking). It uses documented heuristics rather than a supervised classifier
  and is un-tuned to any regulated jurisdiction; its thresholds carry no
  false-positive rate measured against real casino data.
- **Laundering network (`laundering_network.py`).** HHI, PageRank, label
  propagation, and conservation imbalance are computed exactly, but the
  composite risk score is a declared product of value-neutrality and turnover
  share, not a calibrated probability. The module is deliberately
  film-agnostic: it names no suspect, and whether a *particular* account was
  caught is decided by the caller (`scenarios.network_snapshot`).
- **Routes (`urban_routes.py`).** Dijkstra over feasible parkour edges is
  optimal for the fixed cost model; it does not model moving pursuers,
  stochastic edge risk, or fatigue.
- **Poison (`poison_detect.py`).** Triage reproduces standard cardiac-glycoside
  reference ranges and Bayesian reasoning; the likelihood ratios are
  conservative declared constants, and the module is explicitly not medical
  advice.

## Related work

The cores sit in well-established literatures. Hand ranking and Monte-Carlo
equity follow the combinatorial and simulation methods surveyed in computer
poker research [@billings2002poker], with chip-to-prize conversion from the
Independent Chip Model as presented by @chen_ankenman_2006. Equilibrium
computation in imperfect-information games via counterfactual regret
minimization is due to @zinkevich2007cfr; Bayesian opponent modelling in that
setting follows @ganzfried2011opponent, with the Dirichlet-multinomial
machinery as in @minka2000dirichlet.

The financial-crime layer draws on graph-based anti-money-laundering analysis
[@weber2019aml] and on the casino-sector typologies documented by the
Financial Action Task Force [@fatf2009casinos]. Its structural measures are
PageRank [@page1999pagerank], label-propagation community detection
[@raghavan2007labelprop], Brandes' betweenness centrality [@brandes2001], and
the Herfindahl-Hirschman concentration index [@hirschman1964]. Route planning
is Dijkstra's algorithm [@dijkstra1959] over a feasibility-constrained
directed graph. The toxicology follows the cardiac-glycoside literature,
including digoxin-specific Fab antibody fragments as definitive therapy for
life-threatening intoxication [@antman1990fab]. Full entries live in
`references.bib`; the descriptive list is in `99_references.md`.
