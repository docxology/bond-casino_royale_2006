# Experimental Setup {#sec:setup}

## Configuration

Mission identity and publication metadata live in `manuscript/config.yaml`
(title, subtitle, film slug, codename, version, keywords, authorship). The
engine scenario parameters live in `src/casino_royale_2006/scenarios.py` as
module constants (`POKER_SCENARIO`, `LAUNDERING_PLAYERS`, `ROUTE_GRID`,
`POISON_N_SAMPLES`, `CFR_STRENGTHS`, `ICM_STACKS`, `BAYES_HISTORY`, and the
shared `SEED`). Manuscript tokens are computed from these plus live engine
output by `src/casino_royale_2006/manuscript_variables.py` — prose never
hardcodes a number.

## Canonical scenario

| Concept | Fixed inputs (seed `SEED`) |
|---|---|
| Poker | hero {{POKER_HERO}} on board {{POKER_BOARD}}, a {{POKER_RANGE}} opponent range, pot {{POKER_POT}} / to-call {{POKER_TO_CALL}}, every simulation seeded |
| CFR | river toy game, {{CFR_STRENGTHS}} discrete strengths, {{CFR_ITERATIONS}} regret-matching sweeps, fully enumerated |
| ICM | {{ICM_PLAYERS}}-player, 3-paid freezeout bubble (`ICM_STACKS`/`ICM_PRIZES`), short-stack player `ICM_PLAYER` |
| Bayesian opponent | `BAYES_HISTORY`, Le Chiffre's observed action sequence |
| Laundering | {{LAUNDER_PLAYERS}} players over a fixed tick horizon, one planted smurfer, {{LAUNDER_TRANSACTIONS}} movements |
| Network crime | the same canonical chip flow, re-read structurally (HHI / PageRank / communities / conservation) |
| Routes | {{ROUTE_GRID}}×{{ROUTE_GRID}} city quarter ({{ROUTE_NODES}} nodes, {{ROUTE_EDGES}} directed edges), ground + rooftop layers, climbable profile |
| Poison | {{POISON_SAMPLES}} tox panels, one spiked (`POISON_INDEX`) |

## Software environment

- Python {{PYTHON_VERSION}} (requires-python `>=3.10`)
- Dependencies: `bond-api` (the frozen protocol, sibling path dependency),
  `matplotlib` (figures), `pyyaml` (config); dev: `pytest`, `pytest-cov`,
  `ruff`, `mypy`, `types-PyYAML`.
- Deterministic by design: fixed `SEED`, seeded `random.Random` instances,
  fully enumerated CFR, Agg matplotlib backend, no wall-clock in persisted
  artifacts.

## Runtime determinism

Each `*_snapshot` in `scenarios.py` constructs its own
`random.Random(seed)` and never touches the global RNG. The mission's
`Provenance` records `seed` and a deterministic `input_hash`; `wall_time_s` is
held at `0.0` so no two runs diverge on timing.
