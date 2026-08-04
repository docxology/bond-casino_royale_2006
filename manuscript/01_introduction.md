# Introduction

*Casino Royale* (2006) follows the special agent against the banker-cipher
**Le Chiffre** — a name that literally means "the cipher". The story's set
pieces map onto four analytical problems that a real mission system would have
to solve, and each is implemented here as a serious, tested module rather than
a stunt:

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

These four modules form the pure domain core ({NUM_CONCEPT_MODULES} concept
modules: {{CONCEPT_MODULES}}), each deliberately free of any framework,
`infrastructure.*` import, or bond-api dependency, so they stay importable in
isolation. A thin adapter, `mission.py`, implements the frozen BOND-API
`MissionProvider` (codename THE PROTOCOL) and folds their output into a single
deterministic mission outcome.

## Principles

- **Deterministic by construction.** Every RNG draw flows through a
  caller-supplied seeded :class:`random.Random`; provenance carries the seed
  and never a wall-clock reading.
- **Real computation, zero mocks.** The numbers in this manuscript are engine
  output (exact enumeration, Monte-Carlo simulation, graph search, tox
  triage), verified by a ≥90% line-and-branch test suite.
- **One scenario, everywhere.** A single canonical scenario (see
  `src/casino_royale_2006/scenarios.py`) feeds the mission, the manuscript
  tokens, and the CLI, so a claim computed once is the claim shown everywhere.

## Reader's guide

Section [@sec:methodology] defines the four algorithms; [@sec:results] reports
their outputs on the canonical scenario and shows the figures;
[@sec:setup] documents configuration and the runtime environment; and
[@sec:reproducibility] covers determinism, artifact layout, and the
verification gates.
