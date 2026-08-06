# Methodology {#sec:methodology}

This section defines all {{NUM_CONCEPT_MODULES}} algorithms. All are pure
Python; none imports a framework, `infrastructure.*`, or bond-api. Full
signatures live in `src/casino_royale_2006/`: `poker_engine.py`,
`poker_cfr.py`, `icm.py`, `opponent_bayes.py`, `laundering_detect.py`,
`laundering_network.py`, `urban_routes.py`, `poison_detect.py`. The canonical
inputs every one of them is run on live in `scenarios.py`; the published
callables are catalogued in `gadgets.py`.

## Poker game-theory engine (`poker_engine.py`)

**Hand strength.** A card is an integer in `0..51` (`rank = card // 4 + 2`,
`suit = card % 4`). `evaluate_5` returns `(category, tiebreak_ranks)` for the
nine categories (straight flush down to high card), and `best_hand` takes the
best five-card subset of a seven-card hold'em hand by enumerating all
five-card combinations. This is exact — the tiebreak tuple hashes the hand
category and ordered kickers so two hands compare lexicographically.

**Equity.** Two estimators are provided. `exact_equity_turn_river` enumerates
all 990 two-card runouts after a flop for a heads-up match — exact, no RNG.
`monte_carlo_equity` simulates `N` random runouts for an arbitrary number of
players using a seeded RNG, returning per-player `(win, tie)` fractions.

**Pot odds.** Given a pot and the amount to call, the break-even equity is
`to_call / (pot + to_call)`, and the expected value of calling is
`equity·(pot + to_call) − to_call`. `recommend_action` emits `fold`, `call`,
or `raise` by comparing the equity margin (`equity − break_even`) to
thresholds. This is precisely the "price the pot is laying me" decision of the
final hand.

**Opponent modelling.** An `OpponentModel` records observed `raise`/`bet`/
`call`/`fold` actions and derives VPIP and an aggression factor
`(raises + bets) / calls`. `archetype()` maps those two statistics to one of
four compound labels (`tight`/`loose` × `passive`/`aggressive`);
`range_key_for_archetype` then maps that label onto one of the two
`RANGE_ARCHETYPES` starting-hand ranges — `tight` and `loose`, hand-enumerated
as starting-hand *classes* (`AA`, `AKs`, `T9o`, …) rather than the full
169-class hold'em space. On the canonical scenario Le Chiffre's observed
history reads **{{POKER_OPPONENT_ARCHETYPE}}**, selecting the
**{{POKER_RANGE}}** range of {{POKER_RANGE_CLASSES}} classes, from which
{{POKER_RANGE_HANDS}} concrete pairs are drawn. `equity_vs_range` then averages
the hero's Monte-Carlo equity over those pairs — the number the agent compares
to the pot-odds price. Range fidelity is exact: a drawn hand is guaranteed
to match its class, so an offsuit class (e.g. ``AKo``) is always sampled with
two different suits and never silently treated as its suited sibling, which
would tilt the averaged equity toward suited runouts. The same label also sets the raise threshold, via
`recommended_raise_margin` ({{POKER_RAISE_MARGIN_PCT}}% here), which is passed
to `recommend_action` as `raise_margin`.

## Chip-movement laundering detection (`laundering_detect.py`)

Chip flows are a directed graph from a signed `ChipTransaction` list
(`source`, `target`, `amount`, `tick`, `kind ∈ {cash_in, cash_out,
transfer}`), with the casino cage as a reserved node. Four typologies are
computed deterministically:

- **Structuring:** count of `transfer`s sized in `[threshold/2, threshold)`
  (the smurf band).
- **Round-tripping:** `A → B → A` rings completing within a tick window.
- **Velocity:** the maximum number of transactions a node participates in
  within a tick window (both directions — money washing *through* a node is
  the signal).
- **Chip parking:** a player who buys in, never transfers, and cashes out
  ~their full buy-in (value moved with zero game action).

An unweighted Brandes-style `betweenness` centrality identifies *collection
hubs* — nodes many smurf paths funnel through. `detect` accumulates a capped
composite score per player and emits an `Alert` (with supporting `evidence`)
once it clears a threshold.

## Parkour routing (`urban_routes.py`)

A `MobilityGraph` of `UrbanNode`s (x/y/height/kind) joined by directed
`UrbanEdge`s (`distance`, `difficulty`, `risk`, `move ∈ {run, leap, climb,
drop}`). A `ParkourProfile` encodes what the agent can physically execute
(max leap length, climb rise, drop fall, and global difficulty/risk caps);
`MobilityGraph.feasible` decides whether an edge is executable. `shortest_path`
runs **Dijkstra over only the feasible edges**, minimizing a weighted cost
`w_d·distance + w_f·difficulty + w_r·risk`, with a monotonic counter breaking
cost ties so identical-cost routes are reproducible. `brute_force_path`
exhaustively enumerates every simple path on small graphs and serves as ground
truth the Dijkstra output is verified against.

A route's reported cost is only meaningful *under the weighting that produced
it*: a speed-weighted and a risk-weighted solve return numbers in different
units, so their totals are not comparable. `MobilityGraph.path_cost` re-prices
an existing route under any weighting, and the results section uses it to state
both routes under both objectives rather than juxtaposing two incommensurable
totals.

## Digitalis poison triage (`poison_detect.py`)

A `ToxPanel` records serum digoxin (ng/mL), heart rate, serum potassium, PR
interval, and reported symptoms. Reference ranges — therapeutic `0.5–2.0`
ng/mL, toxicity above `2.0`, severe above `3.5`; bradycardia `< 60` bpm;
hyperkalemia `> 5.5` mmol/L; prolonged PR `> 200` ms — are declared as module
constants (`poison_detect.py`). `toxicity_score` combines a concentration band
with cardiac feature boosts and a symptom penalty; `toxicity_grade` thresholds
it into `none`/`mild`/`moderate`/`severe`. `posterior_toxicity` multiplies a
prior into a Bayesian posterior using documented likelihood ratios per present
sign, and `identify_poisoned_sample` picks the spiked glass from a tray by
highest posterior (tie-broken deterministically). `antidote_plan` returns the
intervention list (digoxin-specific Fab fragments for severe toxicity,
atropine for marked bradycardia, potassium management for hyperkalemia).

## Counterfactual regret minimization (`poker_cfr.py`)

The deep game-theory layer. CFR (Zinkevich et al., 2007) finds an approximate
Nash equilibrium of an imperfect-information game by iteratively reducing
counterfactual regret at each information set. This package solves the classic
*river toy game* — heads-up, antes of 1, out-of-position player `P1` checks or
bets 1, in-position `P2` folds or calls, with `CFR_STRENGTHS` discrete hand
strengths drawn uniformly — by fully enumerating the game (no RNG). Regret
matching turns positive regrets into mixed strategies; the reported average
strategy and `game_value` are the equilibrium shape the finale depends on.

## Independent Chip Model (`icm.py`)

The tournament-economy layer. ICM (Chen & Ankenman, 2006) converts chip stacks
into prize equity under the random-tournament model: `exact_icm_equity` uses
the recursive ``E_i = Σ_j (s_j/S)·E_i(S∖j, P[1:])`` for small fields and
`monte_carlo_icm` simulates finish order with a seeded RNG for larger ones. The
*bubble factor* — prize equity lost if the stack is risked and lost, over prize
equity gained by doubling up — exceeds 1 on the bubble, and `icm_call_ev` /
`icm_decision` decide a tournament call in prize-equity (not chip) terms.

## Network-level financial crime (`laundering_network.py`)

The structural-crime layer. Viewing chip flows as a directed graph, four real
measures run deterministically: **HHI concentration** over a player's
counterparty flow shares, **PageRank** (Page et al., 1999) ranking the
collection account that centrally-placed senders feed, **label propagation**
(Raghavan, Albert & Kumara, 2007) detecting deterministic trading communities,
and a **conservation imbalance** score. The composite `network_risk_report`
multiplies value-neutrality by turnover share — a money-washer (chips in ≈
chips out, no game losses) churning large volume is the signature — producing
an independent laundering detector from the typology scanner.

## Bayesian opponent archetype inference (`opponent_bayes.py`)

The read-the-adversary layer. Each of the four archetypes owns a Dirichlet
prior over actions; the Dirichlet-multinomial likelihood updates a posterior
`P(archetype | history)` in exact log space. `map_archetype` is the MAP
estimate, `predictive` is the model-averaged next-action probability, and
`expected_aggression` is the Bayesian expectation of the raise/bet rate — a
proper upgrade over the frequentist `OpponentModel` in `poker_engine.py`.

## Mission adapter and gadget catalogue (`mission.py`, `gadgets.py`)

The engines above are joined by exactly one adapter. `mission.py` implements
the frozen BOND-API `MissionProvider` — `brief → recon → plan → execute →
debrief` — declaring `film = "casino_royale_2006"` so the orchestrator can
discover it by slug. `execute` calls `scenarios.full_snapshot(SEED)` once,
folds each engine's real output into `MissionOutcome.results` under a
per-concept key, and attaches a `Provenance` record carrying the package
version, the seed, and a SHA-256 `input_hash` over the canonical scenario
constants — never a wall-clock reading, so two runs are byte-identical.

The published callables are declared separately, in the pure `gadgets.py`
catalogue: {{NUM_GADGETS}} entries ({{GADGET_NAMES}}). Keeping the catalogue
out of the adapter means it can be counted and exercised without the protocol
dependency present, which is what lets this manuscript state its size as a
token rather than a hand-written number. `mission.register_gadgets` binds that
mapping to the protocol's `GadgetRegistry` under the film slug; the public
shape consumed by bond-cli, the coordinator, and the orchestrator is unchanged
by the split.
