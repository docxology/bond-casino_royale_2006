# Architecture

The LE CHIFFRE package is four layers with a strictly one-directional
dependency arrow: a **pure domain core**, a **pure gadget catalogue**, a
**protocol adapter**, and **thin scripts**, with the **manuscript layer**
hanging off the core. Nothing in `src/` or `tests/` imports `scripts/`, and the
core never imports upward.

```
tests/     ->  src/                                    (exercise everything, no mocks)
scripts/   ->  src/  (+ bond_api)                      (thin orchestrators only)
src/casino_royale_2006/mission.py   -> bond_api + gadgets + scenarios  (the adapter)
src/casino_royale_2006/gadgets.py   -> the eight cores                 (pure catalogue)
src/casino_royale_2006/scenarios.py -> the eight cores                 (pure, one scenario)
src/casino_royale_2006/<core>.py    -> stdlib only                     (pure)
```

## Domain core (pure, framework-free)

Eight modules. None imports `infrastructure.*` or `bond_api`; all import
standalone on stdlib alone (matplotlib appears only under `figures/`).

### `poker_engine.py` — hold'em game theory

Cards are integers `0..51` (`rank = card // 4 + 2`, `suit = card % 4`).
`evaluate_5` returns `(category, tiebreak_ranks)` across the nine hand
categories; `best_hand` picks the best five of seven by enumerating subsets, so
comparison is exact and lexicographic. Equity comes two ways:
`exact_equity_turn_river` enumerates every two-card runout after a flop (no
RNG); `monte_carlo_equity` samples runouts for N players through a
caller-supplied seeded RNG. `break_even_equity`, `ev_of_call`, `equity_margin`,
and `recommend_action` turn that into the pot-odds decision. `OpponentModel`
tallies observed actions into VPIP and an aggression factor, which selects one
of the `RANGE_ARCHETYPES` starting-hand ranges; `equity_vs_range` averages hero
equity over concrete pairs drawn from that range.

### `poker_cfr.py` — counterfactual regret minimization

Solves the river toy game (heads-up, ante 1, P1 checks-or-bets, P2
folds-or-calls, discrete uniform hand strengths) by full enumeration — no RNG
at all. `cfr_solve` runs regret matching and returns a `CFRResult` with the
average strategy, average regret, game value, and regret trace;
`betting_profile` summarises the equilibrium's shape (value-bet / bluff / call
frequencies). That the equilibrium comes out *polar* is the point.

### `icm.py` — tournament Independent Chip Model

`exact_icm_equity` runs the recursion `E_i = Σ_j (s_j/S)·E_i(S∖j, P[1:])` for
small fields; `monte_carlo_icm` samples finish order under a seeded RNG for
larger ones. `bubble_factor` is prize equity risked over prize equity gained
(heads-up collapses to exactly 1 — a sanity check the tests pin);
`icm_call_ev` and `icm_decision` price a tournament call in prize-equity, not
chip, terms.

### `opponent_bayes.py` — Bayesian archetype inference

Each of four archetypes (tight/loose × passive/aggressive) owns a Dirichlet
prior over `(raise, bet, call, fold)`. `BayesianOpponentModel.posterior`
evaluates the Dirichlet-multinomial likelihood in exact log space with
`math.lgamma` — closed form, no sampling. `map_archetype`, `predictive`, and
`expected_aggression` are the read on the adversary; this is the Bayesian
upgrade of `poker_engine.OpponentModel`'s frequentist tally.

### `laundering_detect.py` — chip-flow typology detection

A directed graph over signed `ChipTransaction`s (`source`, `target`, `amount`,
`tick`, `kind ∈ {cash_in, cash_out, transfer}`) with the cage as a reserved
node. Four typologies score deterministically: `structuring_count` (transfers
in the smurf band), `round_trips` (A→B→A within a tick window), `max_velocity`
(transactions through a node per window), and `play_ratio` (chip parking —
value moved with no game action). `MovementGraph.betweenness` is Brandes'
algorithm, finding collection hubs. `detect` accumulates a capped composite
score per player and emits `Alert`s with supporting evidence; `synthetic_flow`
generates the seeded scene with one planted smurfer.

### `laundering_network.py` — the structural layer

The same flows, re-read as network structure: `concentration_hhi`
(Herfindahl-Hirschman over counterparty flow shares), `page_rank` (damped
power iteration over the flow matrix), `label_propagation` (deterministic
communities, ties broken by smallest label id), and `conservation_imbalance`
(cash out + transfers against cash in). `network_risk_report` multiplies
value-neutrality by turnover share and flags accounts at or above
`RISK_THRESHOLD`. It is deliberately **film-agnostic**: `NetworkReport.as_dict`
reports only `any_flagged`, never a named suspect. Deciding whether *Le
Chiffre* was caught is the caller's job, done explicitly in
`scenarios.network_snapshot`.

### `urban_routes.py` — parkour mobility routing

`UrbanNode` (x/y/height/kind) and directed `UrbanEdge` (`distance`,
`difficulty`, `risk`, `move ∈ {run, leap, climb, drop}`). A `ParkourProfile`
declares what the agent can execute; `MobilityGraph.feasible` filters edges by
it. `shortest_path` is Dijkstra over **feasible edges only**, minimising
`w_d·distance + w_f·difficulty + w_r·risk`, with a monotonic counter breaking
cost ties so equal-cost routes are reproducible. `brute_force_path`
exhaustively enumerates simple paths and is the ground truth the tests check
Dijkstra against. `build_city_quarter` builds the seeded ground+roof grid.

### `poison_detect.py` — digitalis triage

`ToxPanel` carries serum digoxin, heart rate, potassium, PR interval, and
reported symptoms; reference ranges are module constants.
`toxicity_score`/`toxicity_grade` band a panel into none/mild/moderate/severe;
`posterior_toxicity` applies documented likelihood ratios per present sign;
`identify_poisoned_sample` picks the spiked glass from a tray by highest
posterior with deterministic tie-breaking; `antidote_plan` returns the
intervention list (Fab fragments for severe toxicity, atropine for marked
bradycardia, potassium management for hyperkalemia).

### `scenarios.py` — the one canonical scenario

Owns every scenario constant and one `*_snapshot` per concept, plus
`full_snapshot`. Every snapshot takes `seed` for uniformity; `cfr_snapshot`,
`icm_snapshot`, and `bayes_snapshot` are exactly enumerated and say so in their
docstrings — they accept the seed and legitimately ignore it. This module is
why a number computed once is the number printed everywhere.

### `gadgets.py` — the pure gadget catalogue

`GADGETS` is the `name -> callable` mapping this film publishes; `GADGET_NAMES`
is its ordered keys; `gadget(name)` raises a `KeyError` that lists the valid
names. It lives outside `mission.py` on purpose: the catalogue can then be
counted, inspected, and tested **without** `bond_api` installed, and
`manuscript_variables` can emit `NUM_GADGETS` / `GADGET_NAMES` as tokens
instead of the manuscript hand-writing the count.

## Protocol adapter (`mission.py`)

The only module in the package that imports `bond_api`. It implements the
frozen `MissionProvider`:

| Stage | What this package does |
|---|---|
| `brief()` | Returns a `MissionBrief` with `film`, `codename = "LE CHIFFRE"`, one objective per concept, scenario `Asset`s, and `Constraint`s (determinism, core purity). |
| `recon(request)` | Returns a `ReconReport` of `Finding`s — objective, target, capital, terrain, threat, constraint — echoing the caller's `request.goal`. |
| `plan(brief)` | Returns a `MissionPlan` of one `Step` per engine (`poker`, `cfr`, `icm`, `laundering`, `network`, `routes`, `poison`, `opponent`). |
| `execute(plan)` | Calls `scenarios.full_snapshot(SEED)` **once**, folds each engine's real output into `MissionOutcome.results` under its concept key, and attaches `Provenance(package_version, seed, input_hash, wall_time_s=0.0)`. `_input_hash` is SHA-256 over the canonical scenario constants — no wall clock, so runs are byte-identical. |
| `debrief(outcome)` | Returns a `Debrief` wrapping the outcome plus the film's standing lessons, one per concept. |

`film = "casino_royale_2006"` must equal the directory slug: that is how the
orchestrator discovers the provider. `register_gadgets(registry)` binds
`gadgets.GADGETS` to a `GadgetRegistry` under the slug, and the module-level
`GADGET_REGISTRY` is populated at import so a coordinator can look up gadgets
without instantiating the provider. **Both names and the five stage signatures
are frozen** — bond-cli, the coordinator, and the orchestrator consume them
across packages. Deepen inside; never reshape the surface.

## Manuscript layer (`manuscript_variables.py`, `figures/`)

`generate_variables()` reads `manuscript/config.yaml`, computes live engine
snapshots, and emits the `{{TOKEN}}` mapping (identity, concept counts, gadget
counts, and one group of tokens per engine). `resolve_manuscript_tree()`
substitutes them into `manuscript/[0-9]*.md`, writing resolved copies to
`output/manuscript/`. `find_malformed_tokens()` catches the single-brace
`{TOKEN}` typo that would otherwise print braces into the PDF while passing the
unresolved-token check. `figures/plotting.py` renders the four manuscript
figures headlessly (Agg backend): `poker_decision`, `digitalis_curve`,
`cfr_convergence`, `icm_bubble`.

## Scripts (`scripts/`)

Thin phase CLIs — `00_preflight.py`, `run_brief.py`, `run_recon.py`,
`run_plan.py`, `run_execute.py`, `run_debrief.py`,
`z_generate_manuscript_variables.py`. Each bootstraps `src/` onto `sys.path`
and forwards to `src/`; none contains business logic.

## Forbidden patterns

- Any `infrastructure.*` or `bond_api` import inside the eight core modules,
  `scenarios.py`, `gadgets.py`, or `manuscript_variables.py`.
- Any mock in `tests/` (see `testing_philosophy.md`).
- Math, dealing logic, or scenario constants inside `scripts/`.
- Hand-authored numeric metrics in manuscript prose (must be `{{TOKEN}}`s).
- A film-specific suspect name inside a film-agnostic module — decide named
  verdicts in `scenarios.py`, not in `laundering_network.py`.
- Renaming or resignaturing anything on `mission.py`'s public surface.
