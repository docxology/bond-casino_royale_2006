# References

Every entry below has a matching BibTeX key in `references.bib`. This list is
descriptive so a reader can see *which module* rests on *which source*; the
machine-readable metadata lives in the `.bib`.

## Software

- **BOND-API — the frozen `MissionProvider` protocol** (`bond_api_protocol`).
  The contract this film package implements: protocol dataclasses, slug
  discovery, and the gadget registry. This package's only non-stdlib suite
  dependency.
- **This package** (`casino_royale_2006`). The {{NUM_CONCEPT_MODULES}} domain
  modules and the mission adapter described in [@sec:methodology].
- Runtime libraries: the Python `random` module (seeded RNG), `matplotlib`
  (Agg backend, figures), and `PyYAML` (manuscript configuration).

## Game theory and poker

- Zinkevich, Johanson, Bowling & Piccione (2007), *Regret Minimization in
  Games with Incomplete Information* — counterfactual regret minimization,
  implemented in `poker_cfr.py`.
- Billings, Davidson, Schaeffer & Szafron (2002), *The Challenge of Poker* —
  hand evaluation, simulation-based equity, and opponent modelling; the
  literature `poker_engine.py` sits in.
- Chen & Ankenman (2006), *The Mathematics of Poker* — pot odds, equity, and
  the Independent Chip Model behind `icm.py`.
- Ganzfried & Sandholm (2011), *Game Theory-Based Opponent Modeling in Large
  Imperfect-Information Games* — the motivation for `opponent_bayes.py`.
- Minka (2000), *Estimating a Dirichlet Distribution* — the
  Dirichlet-multinomial machinery `opponent_bayes.py` evaluates in log space.

## Financial crime and networks

- Financial Action Task Force (2009), *Vulnerabilities of Casinos and Gaming
  Sector* — the casino chip-laundering typologies `laundering_detect.py`
  scores: chip purchase and redemption, structuring, minimal-play cash-out.
- Weber et al. (2019), *Anti-Money Laundering in Bitcoin* — graph-based AML
  over transaction networks; the framing `laundering_network.py` follows.
- Page, Brin, Motwani & Winograd (1999), *The PageRank Citation Ranking* —
  the collection-account ranking in `laundering_network.py`.
- Raghavan, Albert & Kumara (2007), *Near Linear Time Algorithm to Detect
  Community Structures in Large-Scale Networks* — label propagation, made
  deterministic in `laundering_network.py`.
- Brandes (2001), *A Faster Algorithm for Betweenness Centrality* — the
  collection-hub centrality in `laundering_detect.py`.
- Hirschman (1964), *The Paternity of an Index* — the Herfindahl-Hirschman
  concentration index applied to counterparty flow shares.

## Routing and toxicology

- Dijkstra (1959), *A Note on Two Problems in Connexion with Graphs* — the
  shortest-path search `urban_routes.py` runs over feasible parkour edges.
- Antman, Wenger, Butler, Haber & Smith (1990), *Treatment of 150 Cases of
  Life-Threatening Digitalis Intoxication with Digoxin-Specific Fab Antibody
  Fragments* — the evidence for the severe-grade intervention in
  `poison_detect.antidote_plan`.
