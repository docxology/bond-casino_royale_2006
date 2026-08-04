# Architecture

The LE CHIFFRE package follows a strict layered structure, mirroring the BOND
suite's guardrails: **pure core**, **protocol adapter**, **manuscript**, and
**thin scripts**.

## Layers and dependency arrows

```
tests/  ->  src/            (exercise everything, no mocks)
scripts/  ->  src/  (+ bond_api)   (thin orchestrators only)
src/casino_royale_2006/mission.py  ->  bond_api + domain core   (the adapter)
src/casino_royale_2006/*.py (core) ->  stdlib only             (pure)
```

The dependency arrow is one-directional and never invertible: nothing in
`src/` or `tests/` imports `scripts/`; the core never imports upward.

## Domain core (pure, framework-free)

| Module | Concept | Key entry points |
|---|---|---|
| `poker_engine.py` | Hold'em game theory | `evaluate_5`, `best_hand`, `exact_equity_turn_river`, `monte_carlo_equity`, `equity_vs_range`, `break_even_equity`, `recommend_action`, `OpponentModel` |
| `laundering_detect.py` | Chip-flow laundering | `MovementGraph`, `structuring_count`, `round_trips`, `max_velocity`, `play_ratio`, `detect`, `synthetic_flow` |
| `urban_routes.py` | Parkour mobility graph | `MobilityGraph`, `ParkourProfile`, `build_city_quarter`, `brute_force_path` |
| `poison_detect.py` | Digitalis triage | `ToxPanel`, `toxicity_score`, `toxicity_grade`, `posterior_toxicity`, `identify_poisoned_sample`, `antidote_plan` |
| `scenarios.py` | Canonical mission scenario | `poker_snapshot`, `laundering_snapshot`, `route_snapshot`, `poison_snapshot`, `full_snapshot` |

Purity contract: none of these import `infrastructure.*` **or** `bond_api`;
they must import standalone (stdlib, plus matplotlib in `figures/`).

## Protocol adapter (`mission.py`)

The only module with a `bond_api` import. Exposes `MissionProvider`
(`brief` -> `recon` -> `plan` -> `execute` -> `debrief`), declares
`film = "casino_royale_2006"`, computes results through `scenarios.full_snapshot`,
and registers six callable gadgets with `GadgetRegistry` at import time
(`GADGET_REGISTRY`).

## Manuscript (`manuscript_variables.py`, `figures/`)

`generate_variables()` reads `manuscript/config.yaml`, computes live engine
snapshots, and emits the `{{TOKEN}}` mapping. `figures/plotting.py` renders the
two manuscript figures headlessly (Agg backend).

## Scripts (`scripts/`)

Thin phase CLIs — `00_preflight.py`, `run_brief.py`, `run_recon.py`,
`run_plan.py`, `run_execute.py`, `run_debrief.py`,
`z_generate_manuscript_variables.py`. Each bootstraps `src/` onto `sys.path`
and forwards to `src/`; none contains business logic.

## Forbidden patterns

- Any `infrastructure.*` or `bond_api` import inside the four core modules.
- Any mock in `tests/` (see `testing_philosophy.md`).
- Math, dealing logic, or scenario constants inside `scripts/`.
- Hand-authored numeric metrics in manuscript prose (must be `{{TOKEN}}`s).
