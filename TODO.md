# TODO — Casino Royale (2006) / LE CHIFFRE

## Built (phase-4 deepening)

- [x] **Four new pure domain modules** (stdlib-only, deterministic, no bond-api):
  - [x] `src/casino_royale_2006/poker_cfr.py` — counterfactual regret
    minimization on a river toy game: fully-enumerated `cfr_solve`, polar
    equilibrium (value-bet top / bluff bottom / call middle), regret trace,
    `betting_profile`.
  - [x] `src/casino_royale_2006/icm.py` — Independent Chip Model: exact
    recursion + seeded Monte-Carlo prize equity, all-in `bubble_factor`
    (heads-up == 1 sanity check), `icm_call_ev`/`icm_decision`.
  - [x] `src/casino_royale_2006/laundering_network.py` — network-level
    financial crime: HHI concentration, PageRank, label-propagation
    communities, conservation imbalance, composite `network_risk_report`
    (independently flags Le Chiffre).
  - [x] `src/casino_royale_2006/opponent_bayes.py` — Dirichlet-multinomial
    Bayesian opponent-archetype inference (posterior/MAP/predictive/
    expected-aggression).
- [x] `scenarios.py` extended: `cfr_snapshot`, `icm_snapshot`,
  `network_snapshot`, `bayes_snapshot`; `full_snapshot` now 8 concepts.
- [x] `mission.py` deepened **inside** (public shape unchanged): 8 plan steps,
  new results keys (cfr/icm/network/opponent_bayes), +5 gadgets (11 total).
- [x] Manuscript updated: methodology/results/abstract/conclusion extended with
  live tokens; `references.bib` extended with real sources (Zinkevich 2007 CFR,
  Chen & Ankenman 2006 ICM, Raghavan 2007 label propagation, Page 1999, HHI,
  Ganzfried & Sandholm 2011); figures +2 (`cfr_convergence.png`,
  `icm_bubble.png`).
- [x] Tests: +4 module test files; scenarios/mission/figures extended. Gate:
  **155 passed**, **96.86%** line+branch on `src/`, ruff+mypy clean.

## Built (phase-2 conversion)

- [x] **Pure domain cores** (stdlib-only, importable without bond-api):
  - [x] `src/casino_royale_2006/poker_engine.py` — hold'em hand eval
    (`evaluate_5`/`best_hand`), `exact_equity_turn_river`, `monte_carlo_equity`,
    pot-odds/EV (`break_even_equity`, `ev_of_call`, `recommend_action`),
    `OpponentModel` (+ VPIP/aggression), starting-hand `RANGE_ARCHETYPES`,
    `equity_vs_range`.
  - [x] `src/casino_royale_2006/laundering_detect.py` — `ChipTransaction`,
    `MovementGraph` (+ Brandes `betweenness`), `structuring_count`,
    `round_trips`, `max_velocity`, `play_ratio`, composite `detect`,
    `synthetic_flow`.
  - [x] `src/casino_royale_2006/urban_routes.py` — `UrbanNode`/`UrbanEdge`/
    `ParkourProfile`, `MobilityGraph` (feasibility + Dijkstra),
    `build_city_quarter`, `brute_force_path`.
  - [x] `src/casino_royale_2006/poison_detect.py` — `ToxPanel`, toxicity
    score/grade, `posterior_toxicity`, `identify_poisoned_sample`,
    `antidote_plan`, `synthetic_panels`.
  - [x] `src/casino_royale_2006/scenarios.py` — canonical scenario + live
    snapshots (seed 17).
- [x] **Protocol adapter** `src/casino_royale_2006/mission.py` — frozen
  `bond_api.MissionProvider` (`brief/recon/plan/execute/debrief`), `film =
  "casino_royale_2006"`, deterministic provenance, six gadgets registered with
  `GadgetRegistry` at import.
- [x] **Thin CLIs** `scripts/` — `00_preflight.py`, `run_brief.py`,
  `run_recon.py`, `run_plan.py`, `run_execute.py`, `run_debrief.py`,
  `z_generate_manuscript_variables.py`.
- [x] **Manuscript** — `manuscript/config.yaml` + `[0-9]*.md` sections +
  `SYNTAX.md` + `references.bib`; tokens computed by
  `src/casino_royale_2006/manuscript_variables.py::generate_variables()`.
- [x] **Figures** (`src/casino_royale_2006/figures/plotting.py`) —
  `poker_decision.png`, `digitalis_curve.png` (Agg, deterministic).
- [x] **Docs/metadata** — `AGENTS.md`, `README.md`, `docs/`, `data/claim_ledger.yaml`,
  `domain_profile.yaml`, `experiment_plan.yaml`, `CITATION.cff`, `.zenodo.json`,
  `codemeta.json`, and project skill `.agents/skills/casino-royale-2006/SKILL.md`.
- [x] **Tests** — one per domain module + `test_mission.py` +
  `test_manuscript_variables.py` + `test_scripts_smoke.py`; zero mocks;
  deterministic.

## Declared integration points (acceptance criteria)

- [ ] **Delegate provenance persistence to `bond_utilities.mission_io.
  record_provenance_outcome`** once bond-utilities is converted. Current state:
  `mission.py` builds `Provenance` directly (frozen protocol requires it) and
  persists nothing. Acceptance: swap `execute` provenance storage to the shared
  helper with no change to the `MissionOutcome` surface or its determinism.
- [ ] **Bind film via entry-point registry** if the suite adopts one in
  `bond-orchestrator`/`bond-cli`. Current state: discovery is by slug import of
  `casino_royale_2006.mission` on `sys.path` (the frozen bond-api convention).
- [ ] **Incorporate `bond-utilities` ciphers/clock** for mission naming and
  timestamp handling if a future phase requires them (pure core stays
  framework-free; this would live only in `mission.py`/scripts).

## Verification gate (must pass)

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo Clean
rg "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo Clean
uv run ruff check src/ scripts/ && uv run ruff format --check src/ scripts/
uv run mypy src/ scripts/
git status --short   # clean after commit
```
