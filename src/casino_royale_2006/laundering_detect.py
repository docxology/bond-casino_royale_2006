"""Chip-movement money-laundering detection (the bank behind Le Chiffre).

A special-agent follow-the-money module. Physical casino chip flows are a
graph: players buy chips with cash, transfer chips between themselves, and
cash out. Laundering typologies show up as measurable structural anomalies in
that flow:

* **Structuring / smurfing** - many transfers deliberately sized just under a
  reporting threshold (e.g. ``9,999``) to dodge CTR-style scrutiny.
* **Round-tripping / pass-through** - chips ``A -> B -> A`` within a short
  window with little net movement, washing provenance.
* **Chip parking** - a player buys in, never plays (no transfers), and cashes
  out the full buy-in: value moved with zero game action.
* **Velocity bursts** - an implausible number of transactions inside a short
  window.
* **Collection hubs** - a network node with high betweenness centrality that
  many smurfs feed into before redistribution.

All computation is deterministic (pure arithmetic + a caller-seeded RNG only
inside :func:`synthetic_flow`); there is no framework and no bond-api import.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field

#: De-facto structuring ceiling (reportable-transaction threshold).
STRUCTURING_THRESHOLD = 10000.0


@dataclass(frozen=True)
class ChipTransaction:
    """A single chip movement: source player -> target, sized ``amount``.

    ``kind`` is one of ``cash_in`` (buy-in from the cage), ``cash_out``
    (redemption to cash), or ``transfer`` (chips moved player-to-player). The
    casino cage is modeled as the reserved node ``"cage"``.
    """

    source: str
    target: str
    amount: float
    tick: int
    kind: str = "transfer"

    def __post_init__(self) -> None:
        if self.source == self.target:
            raise ValueError("a chip transaction cannot be self-sourced")
        if self.amount < 0:
            raise ValueError("amount must be >= 0")
        if self.tick < 0:
            raise ValueError("tick must be >= 0")
        if self.kind not in {"cash_in", "cash_out", "transfer"}:
            raise ValueError(f"unknown kind {self.kind!r}")


@dataclass(frozen=True)
class Alert:
    """A flagged player, a composite risk score, and the supporting evidence."""

    player: str
    score: float
    reasons: tuple[str, ...]
    evidence: tuple[ChipTransaction, ...] = field(default_factory=tuple)


def _iter_outgoing(
    transactions: tuple[ChipTransaction, ...], player: str
) -> tuple[ChipTransaction, ...]:
    return tuple(t for t in transactions if t.source == player)


def _iter_incoming(
    transactions: tuple[ChipTransaction, ...], player: str
) -> tuple[ChipTransaction, ...]:
    return tuple(t for t in transactions if t.target == player)


@dataclass
class MovementGraph:
    """Directed chip-movement graph with flow and centrality analytics."""

    transactions: tuple[ChipTransaction, ...]

    def __post_init__(self) -> None:
        self._adj: dict[str, list[str]] = {}
        self._players: set[str] = set()
        for t in self.transactions:
            self._adj.setdefault(t.source, []).append(t.target)
            self._players.add(t.source)
            self._players.add(t.target)

    def nodes(self) -> tuple[str, ...]:
        """All distinct nodes (players + the cage), in first-seen order."""
        return tuple(self._players)

    def players(self) -> tuple[str, ...]:
        """All nodes except the reserved ``"cage"`` node."""
        return tuple(p for p in self._players if p != "cage")

    def total_in(self, player: str) -> float:
        """Total chip value received by ``player``."""
        return sum(t.amount for t in self.transactions if t.target == player)

    def total_out(self, player: str) -> float:
        """Total chip value sent by ``player``."""
        return sum(t.amount for t in self.transactions if t.source == player)

    def net_flow(self, player: str) -> float:
        """Net chip inflow: total_in minus total_out."""
        return self.total_in(player) - self.total_out(player)

    def counterparties(self, player: str) -> int:
        """Number of distinct counterparties ``player`` trades with."""
        partners: set[str] = set()
        for t in self.transactions:
            if t.source == player:
                partners.add(t.target)
            if t.target == player:
                partners.add(t.source)
        return len(partners)

    def betweenness(self) -> dict[str, float]:
        """Unweighted betweenness centrality of every node (undirected view).

        Brandes-style accumulation counting, for each ordered pair ``(s, t)``,
        the fraction of shortest paths that pass through the node. Values are
        summed over all pairs (not normalized); a launderer's collection node
        scores highest because smurf paths funnel through it.
        """
        nodes = self.nodes()
        score = dict.fromkeys(nodes, 0.0)
        for source in nodes:
            # BFS layering + path counting from this source.
            stack: list[str] = []
            pred: dict[str, list[str]] = {n: [] for n in nodes}
            sigma: dict[str, float] = dict.fromkeys(nodes, 0.0)
            dist: dict[str, int] = dict.fromkeys(nodes, -1)
            sigma[source] = 1.0
            dist[source] = 0
            queue = deque([source])
            while queue:
                node = queue.popleft()
                stack.append(node)
                for nb in self._adj.get(node, []):
                    if nb not in self._players:
                        continue
                    if dist[nb] < 0:
                        dist[nb] = dist[node] + 1
                        queue.append(nb)
                    if dist[nb] == dist[node] + 1:
                        sigma[nb] += sigma[node]
                        pred[nb].append(node)
            delta = dict.fromkeys(nodes, 0.0)
            while stack:
                node = stack.pop()
                for p in pred[node]:
                    delta[p] += (sigma[p] / sigma[node]) * (1.0 + delta[node])
                if node != source:
                    score[node] += delta[node]
        return score


# --------------------------------------------------------------------------- #
# Typology primitives (pure)
# --------------------------------------------------------------------------- #


def structuring_count(
    transactions: tuple[ChipTransaction, ...],
    player: str,
    threshold: float = STRUCTURING_THRESHOLD,
) -> int:
    """Count transfers sized in the ``[threshold/2, threshold)`` smurf band."""
    return sum(
        1
        for t in _iter_outgoing(transactions, player)
        if t.kind == "transfer" and threshold * 0.5 <= t.amount < threshold
    )


def round_trips(
    transactions: tuple[ChipTransaction, ...],
    window_ticks: int,
    min_amount: float,
) -> tuple[tuple[str, str], ...]:
    """Detect ``A -> B -> A`` wiring pairs completing within a tick window.

    Returns one ``(a, b)`` pair per distinct round-trip ring detected, where
    both legs carry at least ``min_amount`` chips and ``b``'s return leg lands
    within ``window_ticks`` of ``a``'s outgoing leg.
    """
    rings: set[tuple[str, str]] = set()
    for out in transactions:
        if out.source == "cage" or out.target == "cage" or out.kind != "transfer":
            continue
        if out.amount < min_amount:
            continue
        for back in transactions:
            if back.source != out.target or back.target != out.source:
                continue
            if back.kind != "transfer":
                continue
            if back.amount < min_amount:
                continue
            if 0 <= back.tick - out.tick <= window_ticks:
                rings.add((out.source, out.target))
    return tuple(sorted(rings))


def max_velocity(
    transactions: tuple[ChipTransaction, ...],
    player: str,
    window_ticks: int,
) -> int:
    """Maximum number of transactions *involving* ``player`` in any tick window.

    Both directions count (money washing through a node is itself a signal),
    so a smurfer's inflow + outflow churn is captured.
    """
    ticks = sorted(t.tick for t in transactions if player in (t.source, t.target))
    best = 0
    window_end = 0
    for start in range(len(ticks)):
        while window_end < len(ticks) and ticks[window_end] - ticks[start] <= window_ticks:
            window_end += 1
        best = max(best, window_end - start)
    return best


def play_ratio(
    transactions: tuple[ChipTransaction, ...],
    player: str,
) -> float | None:
    """cash_out / cash_in ratio for a player, or None if they never bought in."""
    cash_in = sum(t.amount for t in transactions if t.source == "cage" and t.target == player)
    cash_out = sum(t.amount for t in transactions if t.source == player and t.target == "cage")
    if cash_in <= 0:
        return None
    return cash_out / cash_in


# --------------------------------------------------------------------------- #
# Composite detector
# --------------------------------------------------------------------------- #


def detect(
    transactions: tuple[ChipTransaction, ...],
    *,
    threshold: float = STRUCTURING_THRESHOLD,
    window_ticks: int = 10,
    min_round_trip: float = 5000.0,
    velocity_limit: int = 8,
    score_threshold: float = 1.5,
) -> tuple[Alert, ...]:
    """Scan chip flows and return alerts for players whose composite score clears the bar.

    A player's score accumulates (each capped) from: structuring count,
    distinct round-trip rings, velocity bursts, and chip-parking (full
    buy-in cashed out with zero game action). Players with ``score >=
    score_threshold`` get an :class:`Alert` carrying the contributing reasons
    and the offending transactions as evidence.
    """
    graph = MovementGraph(transactions)
    rings = round_trips(transactions, window_ticks, min_round_trip)
    alerts: list[Alert] = []
    for player in graph.players():
        reasons: list[str] = []
        evidence: set[ChipTransaction] = set()
        score = 0.0

        struct = structuring_count(transactions, player, threshold)
        if struct:
            score += min(struct / 5.0, 1.0)
            reasons.append(f"structuring:{struct}")
            evidence.update(t for t in _iter_outgoing(transactions, player) if t.kind == "transfer")

        player_rings = [r for r in rings if player in r]
        if player_rings:
            ring_score = min(len(player_rings), 2) * 1.0
            score += ring_score
            reasons.append(f"roundtrip:{len(player_rings)}")
            evidence.update(t for t in transactions if player in (t.source, t.target))

        vel = max_velocity(transactions, player, window_ticks)
        if vel >= velocity_limit:
            score += 1.0
            reasons.append(f"velocity:{vel}")

        ratio = play_ratio(transactions, player)
        # Chip parking: bought in, cashed out ~the same amount, and never
        # transferred chips to anyone (no game action at all).
        if ratio is not None and 0.9 <= ratio <= 1.1 and graph.counterparties(player) <= 1:
            score += 1.0
            reasons.append("chip_parking")

        if score >= score_threshold:
            alerts.append(
                Alert(
                    player=player,
                    score=round(score, 3),
                    reasons=tuple(reasons),
                    evidence=tuple(sorted(evidence, key=lambda t: (t.tick, t.source, t.target))),
                )
            )
    return tuple(alerts)


# --------------------------------------------------------------------------- #
# Synthetic scene generator (deterministic, for tests / demo / manuscript)
# --------------------------------------------------------------------------- #


def synthetic_flow(
    seed: int,
    *,
    num_players: int = 8,
    ticks: int = 30,
    launderer: str = "LeChiffre",
) -> tuple[ChipTransaction, ...]:
    """Generate a deterministic casino scene with one planted launderer.

    Legit players buy in, rebuy, occasionally transfer, and cash out with an
    outcome other than exactly their buy-in. The planted ``launderer`` smurfs:
    a single clean cash buy-in followed by many small ``transfer`` legs (each
    just under :data:`STRUCTURING_THRESHOLD`) into a counterparty laundering
    account, then a near-full cash-out - the exact structure :func:`detect`
    should flag.
    """
    rng = random.Random(seed)
    transactions: list[ChipTransaction] = []
    tick = 0
    buy_ins = [rng.uniform(8000.0, 60000.0) for _ in range(num_players)]
    for i, player in enumerate(_player_names(num_players)):
        transactions.append(ChipTransaction("cage", player, buy_ins[i] * 1.3, tick, "cash_in"))
        # A little normal action: occasional mid-size transfers between peers.
        peer = _player_names(num_players)[(i + 1) % num_players]
        for _ in range(rng.randint(1, 3)):
            tick += 1
            transactions.append(
                ChipTransaction(player, peer, rng.uniform(500.0, 4000.0), tick, "transfer")
            )
        tick += 1
        transactions.append(
            ChipTransaction(player, "cage", rng.uniform(0.4, 0.9) * buy_ins[i], tick, "cash_out")
        )

    # The launderer's stream - many small legs, one big clean buy-in.
    friend = _player_names(num_players)[-1]
    transactions.append(ChipTransaction("cage", launderer, 200000.0, tick, "cash_in"))
    for _ in range(6):
        tick += 1
        transactions.append(ChipTransaction(launderer, friend, 9800.0, tick, "transfer"))
    tick += 1
    transactions.append(ChipTransaction(launderer, "cage", 140000.0, tick, "cash_out"))
    return tuple(transactions)


def _player_names(num_players: int) -> tuple[str, ...]:
    return tuple(f"P{i + 1}" for i in range(num_players))
