"""Network-level financial-crime analytics on the chip-movement graph.

The typology detector (`laundering_detect.py`) scores *behavioural* red flags
per transfer. This module adds the *structural* layer: it views the casino's
chip flows as a directed graph and applies four real network/measure algorithms
to find laundering signatures that no single transaction reveals:

* **HHI concentration** (Herfindahl-Hirschman index) - how concentrated a
  player's counterparty flow is; a launderer who pours everything through a
  single clean account scores 1.0.
* **Personalised PageRank** (Page et al., 1999) - which accounts receive chips
  from centrally-placed senders; the "collection account" the smurfs feed.
* **Label propagation** (Raghavan, Albert & Kumara, 2007) - deterministic
  community detection that pulls the smurf-ring accounts into one cluster.
* **Conservation imbalance** - how far a player's cash out plus transfers
  diverge from their cash in. A *value-neutral* player (chips in ~= chips out,
  no game losses) is the money-washer signature, not the loser.

The composite :func:`network_risk_report` multiplies value-neutrality by
turnover share, flagging accounts that churn large volume with near-zero
imbalance - a second, independent detector from the typology scanner. All
iteration orders are fixed and PageRank/label-propagation are deterministic, so
repeated runs are byte-identical.
"""

from __future__ import annotations

from dataclasses import dataclass

from casino_royale_2006.laundering_detect import ChipTransaction

__all__ = [
    "CAGE",
    "NetworkReport",
    "concentration_hhi",
    "conservation_imbalance",
    "label_propagation",
    "network_risk_report",
    "page_rank",
    "turnover",
]

#: The reserved casino cage node (cash in/out counterparty for every player).
CAGE = "cage"

#: Imbalance below this fraction counts as value-neutral (money-washing).
NEUTRALITY_TOL = 0.3
#: Composite risk above this threshold is flagged for investigation.
RISK_THRESHOLD = 0.5


@dataclass(frozen=True)
class NetworkReport:
    """Structural laundering-risk report for every player."""

    players: tuple[str, ...]
    hhi: dict[str, float]
    centrality: dict[str, float]
    communities: tuple[tuple[str, ...], ...]
    imbalance: dict[str, float]
    turnover: dict[str, float]
    risk: dict[str, float]
    flagged: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        """JSON-serialisable snapshot for provenance and manuscript tokens.

        ``any_flagged`` states only that *some* account cleared
        :data:`RISK_THRESHOLD`. This module is film-agnostic and deliberately
        does not decide whether a *named* suspect was caught - callers that
        care about a specific account must test membership in ``flagged``
        themselves (``scenarios.network_snapshot`` does exactly that).
        """
        return {
            "num_players": len(self.players),
            "num_communities": len(self.communities),
            "any_flagged": bool(self.flagged),
            "top_risk_player": self.flagged[0] if self.flagged else "",
            "top_risk_score": round(self.risk[self.flagged[0]], 4) if self.flagged else 0.0,
            "flagged": list(self.flagged),
        }


def _players(transactions: tuple[ChipTransaction, ...]) -> tuple[str, ...]:
    """Ordered unique player node names (excludes the cage), first-seen order."""
    seen: list[str] = []
    seen_set: set[str] = set()
    for t in transactions:
        for who in (t.source, t.target):
            if who != CAGE and who not in seen_set:
                seen_set.add(who)
                seen.append(who)
    return tuple(seen)


def _pair_flows(
    transactions: tuple[ChipTransaction, ...],
    players: tuple[str, ...],
) -> dict[tuple[str, str], float]:
    """Sum each directed player-to-player flow (amounts)."""
    flows: dict[tuple[str, str], float] = {}
    for t in transactions:
        if t.source in players and t.target in players:
            key = (t.source, t.target)
            flows[key] = flows.get(key, 0.0) + t.amount
    for a in players:
        for b in players:
            if (a, b) not in flows:
                flows[(a, b)] = 0.0
    return flows


def concentration_hhi(transactions: tuple[ChipTransaction, ...], player: str) -> float:
    """Herfindahl-Hirschman index over a player's player-to-player flow shares.

    Shares are the fraction of the player's *total* player-to-player flow value
    (in and out combined) that goes to / comes from each counterparty. HHI = 1
    means all counterparty flow touches a single account (the laundering
    concentration signature); HHI -> 0 means many evenly-split counterparties.
    """
    players = _players(transactions)
    if player not in players:
        return 0.0
    flows = _pair_flows(transactions, players)
    total = 0.0
    for (a, b), amount in flows.items():
        if a == player or b == player:
            total += amount
    if total <= 0.0:
        return 0.0
    counterparty: dict[str, float] = {}
    for (a, b), amount in flows.items():
        if amount <= 0.0:
            continue
        if a == player:
            counterparty[b] = counterparty.get(b, 0.0) + amount
        elif b == player:
            counterparty[a] = counterparty.get(a, 0.0) + amount
    return sum((v / total) ** 2 for v in counterparty.values())


def page_rank(
    transactions: tuple[ChipTransaction, ...],
    players: tuple[str, ...] | None = None,
    *,
    damping: float = 0.85,
    iterations: int = 60,
    tolerance: float = 1e-9,
) -> dict[str, float]:
    """Personalised PageRank over the player-to-player flow matrix.

    Builds a row-stochastic matrix from directed chip flows (un-connected rows
    teleport uniformly), then power-iterates with the damping factor. The score
    ranks accounts that receive flow from centrally-placed senders - high for a
    *collection account* that many smurfs feed. Deterministic given the flows.
    """
    players = _players(transactions) if players is None else players
    n = len(players)
    if n == 0:
        return {}
    index = {name: i for i, name in enumerate(players)}
    flows = _pair_flows(transactions, players)

    row_sum = [0.0] * n
    for (a, _b), amount in flows.items():
        row_sum[index[a]] += amount
    matrix = [[0.0] * n for _ in range(n)]
    for (a, b), amount in flows.items():
        i = index[a]
        if row_sum[i] > 0.0:
            matrix[i][index[b]] = amount / row_sum[i]
        else:
            matrix[i] = [1.0 / n] * n

    vector = [1.0 / n] * n
    for _ in range(iterations):
        nxt = [(1.0 - damping) / n] * n
        for i in range(n):
            if vector[i] == 0.0:
                continue
            row = matrix[i]
            for j in range(n):
                nxt[j] += damping * vector[i] * row[j]
        l1 = sum(nxt)
        nxt = [v / l1 for v in nxt] if l1 > 0.0 else nxt
        if sum(abs(nxt[i] - vector[i]) for i in range(n)) < tolerance:
            vector = nxt
            break
        vector = nxt
    return {name: vector[i] for i, name in enumerate(players)}


def label_propagation(
    transactions: tuple[ChipTransaction, ...],
    players: tuple[str, ...] | None = None,
    *,
    iterations: int = 15,
) -> tuple[tuple[tuple[str, ...], ...], dict[str, int]]:
    """Deterministic label-propagation community detection over chip flows.

    Nodes are linked (undirected) when either direction carries flow. Each node
    adopts the most frequent label among itself and its neighbours each pass
    (ties broken by the smallest label id for full determinism). Returns the
    detected communities (grouped by first-seen label) and the node->label map.
    """
    players = _players(transactions) if players is None else players
    if not players:
        return (), {}
    flows = _pair_flows(transactions, players)
    adjacency: dict[str, set[str]] = {name: {name} for name in players}
    for (a, b), amount in flows.items():
        if amount > 0.0:
            adjacency[a].add(b)
            adjacency[b].add(a)

    order = list(players)
    labels = {name: i for i, name in enumerate(players)}
    for _ in range(iterations):
        changed = False
        for node in order:
            counts: dict[int, int] = {}
            for nb in adjacency[node]:
                counts[labels[nb]] = counts.get(labels[nb], 0) + 1
            best = min(counts, key=lambda k: (-counts[k], k))
            if labels[node] != best:
                labels[node] = best
                changed = True
        if not changed:
            break

    groups: dict[int, list[str]] = {}
    for name in players:
        groups.setdefault(labels[name], []).append(name)
    communities = tuple(tuple(groups[key]) for key in sorted(groups))
    return communities, labels


def conservation_imbalance(transactions: tuple[ChipTransaction, ...], player: str) -> float:
    """How far cash out plus transfers diverge from cash in (0 = balanced)."""
    cash_in = sum(t.amount for t in transactions if t.source == CAGE and t.target == player)
    cash_out = sum(t.amount for t in transactions if t.target == CAGE and t.source == player)
    transfers_out = sum(t.amount for t in transactions if t.source == player and t.target != CAGE)
    if cash_in <= 0.0:
        return 1.0
    return abs(cash_in - (cash_out + transfers_out)) / cash_in


def turnover(transactions: tuple[ChipTransaction, ...], player: str) -> float:
    """Total chip value flowing through ``player`` (in + out, cage included)."""
    return sum(t.amount for t in transactions if player in (t.source, t.target))


def network_risk_report(
    transactions: tuple[ChipTransaction, ...],
    players: tuple[str, ...] | None = None,
) -> NetworkReport:
    """Composite structural laundering risk: value-neutrality x turnover share.

    For each player, ``value_neutrality = 1 - min(imbalance / tolerance, 1)``
    (1 for a perfect money-washer, ~0 for a losing player) and ``turnover_share``
    is the player's turnover fraction of the busiest account. Their product is
    the risk score; accounts at or above :data:`RISK_THRESHOLD` are flagged.
    """
    players = _players(transactions) if players is None else players
    hhi = {p: concentration_hhi(transactions, p) for p in players}
    centrality = page_rank(transactions, players)
    communities, _labels = label_propagation(transactions, players)
    imbalance = {p: conservation_imbalance(transactions, p) for p in players}
    turn = {p: turnover(transactions, p) for p in players}
    max_turn = max(turn.values()) if turn else 0.0

    risk: dict[str, float] = {}
    for p in players:
        neutrality = 1.0 - min(imbalance[p] / NEUTRALITY_TOL, 1.0)
        share = turn[p] / max_turn if max_turn > 0.0 else 0.0
        risk[p] = round(neutrality * share, 4)
    flagged = tuple(p for p in players if risk[p] >= RISK_THRESHOLD)
    return NetworkReport(
        players=players,
        hhi=hhi,
        centrality=centrality,
        communities=communities,
        imbalance=imbalance,
        turnover=turn,
        risk=risk,
        flagged=flagged,
    )
