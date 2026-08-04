# Methodology

This section defines the four algorithms. All are pure Python; none imports a
framework. Full signatures live in
`src/casino_royale_2006/`: `poker_engine.py`, `laundering_detect.py`,
`urban_routes.py`, `poison_detect.py`.

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
`(raises + bets) / calls`. Tendencies map to a `tight`/`loose`-`passive`/
`aggressive` archetype, which selects a starting-hand range (`RANGE_ARCHETYPES`
of 169 canonical hand classes). `equity_vs_range` then averages the hero's
Monte-Carlo equity over concrete opponent pairs sampled from that range — the
number the agent compares to the pot-odds price.

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
