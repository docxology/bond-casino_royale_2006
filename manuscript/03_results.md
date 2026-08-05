# Results {#sec:results}

All results are computed live from the engines on the canonical scenario in
`src/casino_royale_2006/scenarios.py` (fixed seed, deterministic RNG).
Every number below is a `TOKEN` placeholder, injected at manuscript time.

## The felt: equity, price, and decision

On the board `{{POKER_BOARD}}`, the hero holds `{{POKER_HERO}}` against
Le Chiffre's `{{POKER_RANGE}}` range. The engine prices a
Monte-Carlo equity of **{{POKER_EQUITY_PCT}}%** against a pot-odds break-even
of **{{POKER_BREAK_EVEN_PCT}}%** (pot {{POKER_POT}}, to call
{{POKER_TO_CALL}}). The resulting margin, **{{POKER_MARGIN_PCT}}%**, clears the
value threshold, so the model recommends **{{POKER_ACTION}}** — the
traditionally correct play when the price the pot lays exceeds the probability
of winning. Figure [@fig:poker] visualizes the equity-vs-price comparison.

![Poker decision: hero equity vs. pot-odds break-even with the resulting
action.](../output/figures/poker_decision.png){#fig:poker}

## The capital: chip-flow laundering

The scanner ingests **{{LAUNDER_TRANSACTIONS}}** chip movements across
**{{LAUNDER_PLAYERS}}** players, including the one planted smurfer. It raises
**{{LAUNDER_ALERTS}}** alert(s); the planted launderer is caught
(**{{LAUNDER_FLAGGED}}**) with a composite score of **{{LAUNDER_SCORE}}**,
accumulated from structuring + velocity dimensions rather than any single
transfer — the structural, not transactional, signature of the laundered
stake.

## The terrain: parkour extraction route

On the `{{ROUTE_GRID}}×{{ROUTE_GRID}}` city quarter (**{{ROUTE_NODES}}** nodes,
**{{ROUTE_EDGES}}** directed edges) the planner returns two routes. The
*fastest* route short-cuts across the rooftops at cost **{{ROUTE_FASTEST_COST}}**
(uses rooftops: **{{ROUTE_FASTEST_ROOF}}**); the *safest*, risk-priced route
stays on the ground at cost **{{ROUTE_SAFEST_COST}}**. This reproduces the
film's trade-off literally: the roof is faster, the street is safer.

## The martini: digitalis triage

From a tray of **{{POISON_SAMPLES}}** samples, the triage isolates the spiked
glass at **{{POISON_SPIKED_INDEX}}**, reading **{{POISON_DIGOXIN}}** ng/mL
digoxin, heart rate {{POISON_HEART_RATE}} bpm, potassium
{{POISON_POTASSIUM}} mmol/L — a **{{POISON_GRADE}}** toxicity with a Bayesian
posterior of **{{POISON_POSTERIOR}}**. Figure [@fig:digitalis] shows the
monogram-style toxicity curve used to place such a panel.

![Digitalis toxicity score vs. serum digoxin concentration with the severity
grade bands shaded.](../output/figures/digitalis_curve.png){#fig:digitalis}

## The solve: CFR river-toy equilibrium

CFR on the toy game converges to an average regret of **{{CFR_AVG_REGRET}}**
after **{{CFR_ITERATIONS}}** iterations, giving a game value of
**{{CFR_GAME_VALUE}}**. The equilibrium is *polar*, the classic shape behind
modern solver-based play: the out-of-position player bets the very top of
his range for value (**{{CFR_VALUE_BET_FREQ}}**) and bluffs near the very
bottom (**{{CFR_BLUFF_FREQ}}**), while the in-position caller calls the middle
of his range (**{{CFR_CALL_FREQ}}**). Figure [@fig:cfr] shows regret decaying
toward zero across the solve.

![CFR average counterfactual regret vs. iteration, decaying toward the Nash
equilibrium.](../output/figures/cfr_convergence.png){#fig:cfr}

## The freezeout: Independent Chip Model

On the {{ICM_PLAYERS}}-player, 3-paid bubble, exact ICM prices the short stack
at a tournament-equity bubble factor of **{{ICM_BUBBLE_FACTOR}}** — risking his
stack is negative prize-equity — while the chip leader faces a squeeze of
**{{ICM_LEADER_BUBBLE_FACTOR}}**. The model's tournament call on the bubble is
**{{ICM_DECISION}}** (prize-equity EV **{{ICM_CALL_EV}}**), the correct
survival discipline when the first chips are worth more than the last. Figure
[@fig:icm] shows the bubble factor rising with stack size.

![ICM bubble factor by start stack on the 4-player, 3-paid freezeout,
demonstrating the prize-equity squeeze.](../output/figures/icm_bubble.png){#fig:icm}

## The capital again: network-level laundering

The structural detector needs no single suspicious transfer: across the
canonical flow it computes **{{NET_COMMUNITIES}}** trading community and
flags the launderer specifically (**{{NET_FLAGGED}}**), giving him a
composite network risk of **{{NET_LAUNDERER_RISK}}** at HHI concentration
**{{NET_LAUNDERER_HHI}}** (everything moving through one counterparty), while
the collection account ranks highest on PageRank centrality
({{NET_TOP_CENTRALITY}}). It agrees with — but is independent of — the
typology detector.

## The read: Bayesian opponent archetype

From Le Chiffre's observed action history, the model infers an archetype of
**{{BAYES_ARCHETYPE}}** with a **{{BAYES_AGGRESSIVE_POSTERIOR}}** posterior
mass on aggressive archetypes, an expected aggression rate of
**{{BAYES_EXPECTED_AGGRESSION}}**, and a predictive raise probability of
**{{BAYES_PREDICTIVE_RAISE}}** — a quantified read of the adversary rather
than a bare action count.
