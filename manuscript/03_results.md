# Results

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
