# Introduction

*Casino Royale* (2006) follows the special agent against the banker-cipher
**Le Chiffre** — a name that literally means "the cipher". The story's set
pieces map onto a family of analytical problems that a real mission system
would have to solve, and each is implemented here as a serious, tested module
rather than a stunt. Four are the film's literal set pieces:

1. **The felt.** The climactic hand is a study in game theory: a hero hand on a
   dry board against an adversary whose range the hero can model, priced
   against the chips in the middle. Module: `poker_engine.py`.
2. **The capital.** Laundered money funds the stake; it travels as physical
   casino chips in structurally tell-tale patterns. Module:
   `laundering_detect.py`.
3. **The terrain.** The chase crosses a parkour-friendly city — ground
   streets, leapable rooftop gaps, climbable walls, droppable falls — which is
   exactly a weighted mobility graph. Module: `urban_routes.py`.
4. **The martini.** Bond's drink is spiked with digitalis, the cardiac
   glycoside with a notoriously narrow therapeutic index. Module:
   `poison_detect.py`.

Four more answer the question each set piece raises once it is taken seriously:

5. **What is the *equilibrium*, not just the price?** Pot odds decide one call;
   a solver decides a strategy. Counterfactual regret minimization on the river
   toy game recovers the polar equilibrium the finale depends on. Module:
   `poker_cfr.py`.
6. **What is a chip worth on the bubble?** In a freezeout, chips are not money:
   the Independent Chip Model converts stacks to prize equity and prices
   survival. Module: `icm.py`.
7. **What does the adversary's history actually license?** A raise count is not
   a read; a Dirichlet-multinomial posterior over archetypes is. Module:
   `opponent_bayes.py`.
8. **Is the laundering visible without a suspicious transfer?** The structural
   layer — concentration, centrality, communities, value conservation — finds
   the washer from the shape of the flow alone. Module:
   `laundering_network.py`.

Together these form the pure domain core ({{NUM_CONCEPT_MODULES}} concept
modules: {{CONCEPT_MODULES}}), each deliberately free of any framework,
`infrastructure.*` import, or bond-api dependency, so they stay importable in
isolation. A thin adapter, `mission.py`, implements the frozen BOND-API
`MissionProvider` (codename THE PROTOCOL) and folds their output into a single
deterministic mission outcome, alongside a catalogue of {{NUM_GADGETS}}
published gadgets (`gadgets.py`) that other suite packages may call directly.

## Principles

- **Deterministic by construction.** Every RNG draw flows through a
  caller-supplied seeded :class:`random.Random`; provenance carries the seed
  and never a wall-clock reading. Three of the eight engines (CFR, ICM, and the
  Bayesian opponent model) are exactly enumerated and carry no RNG at all.
- **Real computation, zero mocks.** The numbers in this manuscript are engine
  output (exact enumeration, Monte-Carlo simulation, graph search, tox
  triage), verified by a ≥90% line-and-branch test suite.
- **One scenario, everywhere.** A single canonical scenario (see
  `src/casino_royale_2006/scenarios.py`) feeds the mission, the manuscript
  tokens, and the CLI, so a claim computed once is the claim shown everywhere.

## Reader's guide

Section [@sec:methodology] defines all {{NUM_CONCEPT_MODULES}} algorithms;
[@sec:results] reports their outputs on the canonical scenario and shows the
figures; [@sec:setup] documents configuration and the runtime environment;
[@sec:reproducibility] covers determinism, artifact layout, and the
verification gates; and [@sec:scope] states, per module, what is deliberately
out of scope.
