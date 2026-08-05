# Casino Royale (2006): LE CHIFFRE — Special-Agent Mission Software

PROJECT BOND film package for *Casino Royale* (2006), mission codename
**LE CHIFFRE**. Implements the frozen BOND-API `MissionProvider` protocol over
four deterministic, infrastructure-free domain cores.

## What it does

A special-agent mission system maps the film's set pieces to real algorithms.
The package grew to eight pure, deterministic domain modules:

1. **Poker game-theory engine** (`poker_engine.py`) — exact 5/7-card hand
   evaluation, Monte-Carlo + exact equity, pot-odds break-even, expected
   value, and opponent modelling (VPIP, aggression, starting-hand ranges) that
   prices a hand against an adversary's range before recommending
   fold/call/raise.
2. **Counterfactual regret minimization** (`poker_cfr.py`) — solves the river
   toy game by CFR to a near-Nash polar equilibrium (value-bet the top, bluff
   the bottom, call the middle), fully enumerated and deterministic.
3. **Tournament Independent Chip Model** (`icm.py`) — exact + Monte-Carlo
   prize equity, the all-in bubble factor, and prize-equity tournament
   call decisions on the freezeout bubble.
4. **Bayesian opponent archetype inference** (`opponent_bayes.py`) —
   Dirichlet-multinomial posterior over tight/loose × passive/aggressive
   archetypes from observed actions, with predictive and expected-aggression
   rates.
5. **Chip-movement laundering detection** (`laundering_detect.py`) —
   transaction-graph typology scoring: structuring (smurf bands), round-trip
   rings, velocity bursts, chip parking, and betweenness collection-hub
   detection, each verified on deterministic synthetic scenes.
6. **Network-level financial crime** (`laundering_network.py`) — HHI
   concentration, PageRank collection-account ranking, label-propagation
   communities, and conservation-imbalance scoring; an independent structural
   detector that flags the launderer at value-neutral churn.
7. **Parkour mobility routing** (`urban_routes.py`) — a directed
   feasibility-constrained mobility graph (ground/roof/wall/rail) planned with
   weighted Dijkstra, cross-checked against exhaustive search.
8. **Digitalis poison triage** (`poison_detect.py`) — reference-range
   toxicity scoring, Bayesian posterior from documented likelihood ratios,
   spiked-sample identification, and a deterministic antidote plan.

`mission.py` folds all four into a single deterministic
`MissionOutcome` with full provenance; `scenarios.py` is the one canonical
scenario the mission, manuscript, and CLI share.

## Quick start

```bash
cd projects/working/bond/casino_royale_2006
uv sync --extra dev            # installs deps incl. the frozen bond-api sibling
uv run python scripts/00_preflight.py
uv run python scripts/run_debrief.py            # full five-stage mission
uv run python scripts/z_generate_manuscript_variables.py   # tokens + figures
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```

Phase CLIs: `run_brief.py`, `run_recon.py`, `run_plan.py`, `run_execute.py`,
`run_debrief.py`. Outputs land under `output/` (git-ignored, regenerable).

## Layout

```
src/casino_royale_2006/   domain core + mission adapter + manuscript + figures
scripts/                  thin phase CLIs
tests/                    zero-mock, deterministic test suite
manuscript/               config.yaml + {{TOKEN}} prose sections + bib
docs/                     behavioral rulebook + protocol
```

## Documentation

- [`docs/agent_instructions.md`](docs/agent_instructions.md) — read first.
- [`docs/architecture.md`](docs/architecture.md) — layers & forbidden patterns.
- [`docs/protocol.md`](docs/protocol.md) — bond-api integration.
- [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) — live test/coverage.

> Local-only working tree. No remote exists; this package is never pushed.
