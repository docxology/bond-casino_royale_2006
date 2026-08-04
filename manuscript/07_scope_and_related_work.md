# Scope & Related Work

## Scope

This package is a **deterministic engineering exemplar**, not a licensed
clinical or financial system. Its contributions are the algorithmic cores and
the reproducibility discipline around them; the specific numeric constants are
documented model choices, not regulatory thresholds.

- **Poker.**: The engine prices hands and recommends actions; it is not a
  full solver (no perfect-information exploitation, no multi-street
  counterfactual regret minimization). Monte-Carlo equity is sampled, not
  solved exhaustively (except the exact turn/river enumerator).
- **Laundering.**: The detector flags *structural* typologies (structuring,
  round-tripping, velocity, chip parking). It uses hand-class ranges and
  documented heuristics rather than a supervised classifier, and is un-tuned
  to any regulated jurisdiction.
- **Routes.**: Dijkstra over feasible parkour edges is optimal for the fixed
  cost model; it does not model moving pursuers or stochastic edge risk.
- **Poison.**: Triage reproduces standard cardiac-glycoside reference ranges
  and Bayesian reasoning; likelihood ratios are conservative placeholders, and
  the module is explicitly not medical advice.

## Related work

The four cores sit in well-established literatures: hand-ranking and
Monte-Carlo equity in poker (equivalent for small enumerations to published
preflop equity tables); graph-based anti-money-laundering typologies and
centrality in transaction networks; weighted shortest-path planning over
3-D mobility graphs; and toxicology of cardiac glycosides with digoxin Fab
therapy (Fab fragments as the definitive antidote). References are collected
in `99_references.md`.
