# Casino Royale (2006): LE CHIFFRE — Special-Agent Mission Software

PROJECT BOND film package for *Casino Royale* (2006), mission codename
**LE CHIFFRE**. Eight deterministic, infrastructure-free domain cores bound to
the frozen BOND-API `MissionProvider` protocol by one thin adapter.

## The concept mapping

The film is the spec. Four modules implement its literal set pieces; four more
implement the question each set piece raises once taken seriously.

| Module | What it computes | Film anchor |
|---|---|---|
| `poker_engine.py` | Exact 5/7-card hand evaluation, exact turn/river and Monte-Carlo equity, pot-odds break-even and EV, frequentist opponent modelling (VPIP, aggression) and starting-hand ranges — pricing a hand against an adversary's range before recommending fold/call/raise. | the high-stakes finale |
| `poker_cfr.py` | Counterfactual regret minimization on the river toy game, fully enumerated (no RNG), converging to the polar near-Nash profile: value-bet the top, bluff the bottom, call the middle. | the equilibrium behind the finale |
| `icm.py` | Tournament Independent Chip Model — exact recursion plus seeded Monte-Carlo prize equity, the all-in bubble factor, and prize-equity call decisions on the freezeout bubble. | surviving the freezeout |
| `opponent_bayes.py` | Dirichlet-multinomial posterior over tight/loose × passive/aggressive archetypes from an observed action history, evaluated in exact log space, with predictive action and expected-aggression rates. | reading Le Chiffre |
| `laundering_detect.py` | Chip-movement typology scoring: structuring (smurf bands), round-trip rings, velocity bursts, chip parking, and Brandes betweenness for collection hubs, emitting scored alerts with evidence. | the stake's funding |
| `laundering_network.py` | The structural layer over the same flows: HHI concentration, PageRank collection-account ranking, label-propagation communities, conservation imbalance — an independent detector that finds the washer at value-neutral churn. | the laundering structure |
| `urban_routes.py` | A directed, feasibility-constrained mobility graph (ground/roof/wall/rail) planned with weighted Dijkstra and cross-checked against exhaustive search. | the rooftop/street pursuit |
| `poison_detect.py` | Digitalis triage: reference-range toxicity scoring and grading, Bayesian posterior from documented likelihood ratios, spiked-sample identification, and a deterministic antidote plan. | the spiked martini |

Three supporting modules complete `src/`: `scenarios.py` owns the single
canonical scenario every consumer draws from (so a number computed once is the
number shown everywhere), `gadgets.py` is the pure catalogue of published
callables, and `manuscript_variables.py` plus `figures/plotting.py` produce the
manuscript tokens and the four figures. `mission.py` is the adapter.

## The MissionProvider surface

`src/casino_royale_2006/mission.py` implements the **frozen** BOND-API
protocol. This shape is consumed by bond-cli, the coordinator, and the
orchestrator across packages and must not be reshaped:

```python
from casino_royale_2006.mission import GADGET_REGISTRY, MissionProvider, register_gadgets

p = MissionProvider()
p.film                         # "casino_royale_2006" - equals the slug; how discovery works
brief   = p.brief()            # -> MissionBrief   (codename, objectives, assets, constraints)
report  = p.recon(request)     # -> ReconReport    (findings)
plan    = p.plan(brief)        # -> MissionPlan    (one Step per engine)
outcome = p.execute(plan)      # -> MissionOutcome (live results + deterministic Provenance)
debrief = p.debrief(outcome)   # -> Debrief        (outcome + standing lessons)
```

`execute` runs `scenarios.full_snapshot(SEED)` once and folds every engine's
real output into `MissionOutcome.results`, with `Provenance` carrying the
package version, the seed, and a SHA-256 `input_hash` over the scenario
constants — never a wall-clock reading. `register_gadgets(registry)` binds the
`gadgets.GADGETS` catalogue under the film slug; `GADGET_REGISTRY` is populated
at import so a coordinator can look gadgets up without instantiating the
provider. Read `gadgets.GADGET_NAMES` rather than hard-coding the list.

## Quick start

```bash
cd projects/working/bond/casino_royale_2006
uv sync --extra dev                                        # deps incl. the frozen bond-api sibling
uv run python scripts/00_preflight.py                      # protocol conformance + slug check
uv run python scripts/run_debrief.py                       # full five-stage mission
uv run python scripts/z_generate_manuscript_variables.py   # tokens + resolved prose + figures
uv run pytest tests/ --cov=src --cov-fail-under=90 -q      # the gate
uv run ruff check src/ scripts/ && uv run ruff format --check src/ scripts/
uv run mypy src/ scripts/
```

Phase CLIs: `run_brief.py`, `run_recon.py`, `run_plan.py`, `run_execute.py`,
`run_debrief.py`. Outputs land under `output/` (git-ignored, regenerable).

Coverage and test counts are deliberately not quoted here — such figures go
stale silently. The gate is `--cov-fail-under=90` (line + branch) on `src/`;
the last measured values live in
[`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md), regenerated from a
real run.

## Layout

```
src/casino_royale_2006/   eight domain cores + scenarios + gadgets + mission adapter
                          + manuscript_variables + figures/
scripts/                  thin phase CLIs (bootstrap + forward; no business logic)
tests/                    zero-mock, deterministic test suite
manuscript/               config.yaml + {{TOKEN}} prose sections + references.bib
docs/                     behavioural rulebook, architecture, protocol, testing doctrine
```

## Documentation

- [`docs/agent_instructions.md`](docs/agent_instructions.md) — read first.
- [`docs/architecture.md`](docs/architecture.md) — module-by-module architecture.
- [`docs/testing_philosophy.md`](docs/testing_philosophy.md) — the no-mock doctrine.
- [`docs/protocol.md`](docs/protocol.md) — bond-api binding + the frozen surface.
- [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md) — measured test/coverage.

> Local-only working tree. No remote exists; this package is never pushed.
