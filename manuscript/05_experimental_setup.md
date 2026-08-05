# Experimental Setup

## Configuration

Mission identity and publication metadata live in `manuscript/config.yaml`
(title, subtitle, film slug, codename, version, keywords, authorship). The
engine scenario parameters live in `src/casino_royale_2006/scenarios.py` as
module constants (`POKER_SCENARIO`, `LAUNDERING_PLAYERS`, `ROUTE_GRID`,
`POISON_N_SAMPLES`, and the shared `SEED`). Manuscript tokens are computed from
these plus live engine output by
`src/casino_royale_2006/manuscript_variables.py` — prose never hardcodes a
number.

## Canonical scenario

| Concept | Fixed inputs (seed `SEED`) |
|---|---|
| Poker | hero `POKER_HERO` on board `POKER_BOARD`, `POKER_RANGE` range, every simulation seeded |
| CFR | river toy game, `CFR_STRENGTHS` strengths, `CFR_ITERATIONS` enumeration sweeps |
| ICM | `ICM_STACKS`/`ICM_PRIZES` freezeout bubble, short-stack player `ICM_PLAYER` |
| Bayesian opponent | `BAYES_HISTORY` of Le Chiffre's observed actions |
| Laundering | `LAUNDER_PLAYERS` players over a configurable tick horizon, one planted smurfer |
| Network crime | same canonical chip flow, structural (HHI/PageRank/community) analytics |
| Routes | `ROUTE_GRID`×`ROUTE_GRID` city quarter, ground + rooftop layers, climbable profile |
| Poison | `POISON_N_SAMPLES` tox panels, one spiked at `POISON_INDEX` |

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
