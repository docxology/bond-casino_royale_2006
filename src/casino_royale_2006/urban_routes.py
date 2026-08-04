"""Urban parkour routing over mobility graphs (foot AND rooftop pursuit).

Models the physical chase geography - ground streets, rooftops, walls, rails,
gaps - as a weighted directed graph and plans the fastest / lowest-risk
extraction route for the agent. This is the escape-and-pursuit planner: Bond's
run across a parkour-friendly city (rooftop-to-rooftop in Madagascar, the
Nassau construction site) with pursuers adding ``risk`` to exposed edges.

Concepts implemented with real graph algorithms:

* A directed :class:`MobilityGraph` of :class:`UrbanNode`\\ s (x/y/height/kind)
  joined by :class:`UrbanEdge`\\ s carrying ``distance``, ``difficulty``,
  ``risk`` and a parkour ``move`` (``run``/``leap``/``climb``/``drop``).
* A :class:`ParkourProfile` encoding what the agent can physically execute
  (max leap length, climb height, drop height, and difficulty/risk caps).
* :func:`MobilityGraph.shortest_path` - deterministic Dijkstra over only the
  *feasible* directed edges, minimizing a weighted cost, with a stable
  tie-break so identical-cost routes are reproducible.
* :func:`brute_force_path` - exhaustive DFS over small graphs used to
  cross-check Dijkstra exactly in tests (real verification, not a mock).

No framework, no bond-api import: the module is pure stdlib.
"""

from __future__ import annotations

import heapq
import itertools
import math
import random
from dataclasses import dataclass, field

# cost-weight axis defaults (distance, difficulty, risk)
DEFAULT_WEIGHTS: tuple[float, float, float] = (1.0, 1.0, 2.0)


@dataclass(frozen=True)
class UrbanNode:
    """A point an agent can stand on: ground, roof, wall, rail, ledge."""

    node_id: str
    x: float
    y: float
    height: float = 0.0
    kind: str = "ground"

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("node_id must be non-empty")


@dataclass(frozen=True)
class UrbanEdge:
    """A directed parkour connection ``a -> b`` with movement cost and risk."""

    a: str
    b: str
    distance: float
    difficulty: float
    risk: float
    move: str = "run"

    def __post_init__(self) -> None:
        if self.a == self.b:
            raise ValueError("an urban edge cannot connect a node to itself")
        for label, value in (
            ("distance", self.distance),
            ("difficulty", self.difficulty),
            ("risk", self.risk),
        ):
            if value < 0:
                raise ValueError(f"{label} must be >= 0")
        if self.move not in {"run", "leap", "climb", "drop"}:
            raise ValueError(f"unknown move {self.move!r}")


@dataclass(frozen=True)
class ParkourProfile:
    """Physical limits of the agent's parkour ability."""

    max_leap: float = 3.0
    max_climb: float = 4.0
    max_drop: float = 8.0
    max_difficulty: float = 10.0
    max_risk: float = 10.0

    def __post_init__(self) -> None:
        for label, value in (
            ("max_leap", self.max_leap),
            ("max_climb", self.max_climb),
            ("max_drop", self.max_drop),
            ("max_difficulty", self.max_difficulty),
            ("max_risk", self.max_risk),
        ):
            if value < 0:
                raise ValueError(f"{label} must be >= 0")


@dataclass
class MobilityGraph:
    """Directed mobility graph; nodes carry geometry, edges carry parkour cost."""

    nodes: dict[str, UrbanNode] = field(default_factory=dict)
    edges: dict[tuple[str, str], UrbanEdge] = field(default_factory=dict)

    def add_node(self, node: UrbanNode) -> None:
        """Add or replace a node."""
        self.nodes[node.node_id] = node

    def add_edge(self, edge: UrbanEdge) -> None:
        """Add a directed edge, replacing any existing edge on ``(a, b)``."""
        if edge.a not in self.nodes or edge.b not in self.nodes:
            raise KeyError("both edge endpoints must be nodes of the graph")
        self.edges[(edge.a, edge.b)] = edge

    def node(self, node_id: str) -> UrbanNode:
        """Return the node, raising ``KeyError`` with an actionable message if absent."""
        try:
            return self.nodes[node_id]
        except KeyError:
            raise KeyError(f"no such node {node_id!r}") from None

    def outgoing(self, node_id: str) -> tuple[UrbanEdge, ...]:
        """All directed edges leaving ``node_id``."""
        return tuple(e for (a, _b), e in self.edges.items() if a == node_id)

    def euclidean(self, a: str, b: str) -> float:
        """3D Euclidean distance between two nodes (x, y, height)."""
        na, nb = self.node(a), self.node(b)
        return math.hypot(na.x - nb.x, na.y - nb.y, na.height - nb.height)

    def feasible(self, edge: UrbanEdge, profile: ParkourProfile) -> bool:
        """True when the agent's profile can execute ``edge``.

        Physical checks are per-move (leap length, climb rise, drop fall
        bounded by the profile), and every move must also sit under the
        global difficulty and risk caps. ``run`` edges are always feasible
        subject to those caps.
        """
        if edge.difficulty > profile.max_difficulty or edge.risk > profile.max_risk:
            return False
        na, nb = self.node(edge.a), self.node(edge.b)
        rise = nb.height - na.height
        if edge.move == "leap":
            return edge.distance <= profile.max_leap
        if edge.move == "climb":
            return 0 <= rise <= profile.max_climb
        if edge.move == "drop":
            return -profile.max_drop <= rise <= 0
        return True  # run

    def _cost(self, edge: UrbanEdge, weights: tuple[float, float, float]) -> float:
        wd, wf, wr = weights
        return wd * edge.distance + wf * edge.difficulty + wr * edge.risk

    def shortest_path(
        self,
        start: str,
        end: str,
        profile: ParkourProfile,
        weights: tuple[float, float, float] = DEFAULT_WEIGHTS,
    ) -> tuple[tuple[str, ...], float, tuple[UrbanEdge, ...]] | None:
        """Dijkstra over feasible edges: lowest weighted cost from ``start`` to ``end``.

        Returns ``(path_node_ids, total_cost, edge_path)`` or ``None`` if no
        feasible route exists. A monotonically increasing counter breaks cost
        ties deterministically.
        """
        if start not in self.nodes or end not in self.nodes:
            raise KeyError("start and end must be nodes of the graph")
        dist: dict[str, float] = {start: 0.0}
        prev_node: dict[str, str] = {}
        prev_edge: dict[str, UrbanEdge] = {}
        counter = itertools.count()
        heap: list[tuple[float, int, str]] = [(0.0, next(counter), start)]
        while heap:
            cost, _c, node_id = heapq.heappop(heap)
            if cost > dist.get(node_id, math.inf):
                continue
            if node_id == end:
                return self._reconstruct(start, end, prev_node, prev_edge, dist[end])
            for edge in self.outgoing(node_id):
                if not self.feasible(edge, profile):
                    continue
                ncost = cost + self._cost(edge, weights)
                if ncost < dist.get(edge.b, math.inf):
                    dist[edge.b] = ncost
                    prev_node[edge.b] = node_id
                    prev_edge[edge.b] = edge
                    heapq.heappush(heap, (ncost, next(counter), edge.b))
        return None

    def _reconstruct(
        self,
        start: str,
        end: str,
        prev_node: dict[str, str],
        prev_edge: dict[str, UrbanEdge],
        total: float,
    ) -> tuple[tuple[str, ...], float, tuple[UrbanEdge, ...]]:
        nodes: list[str] = [end]
        edges: list[UrbanEdge] = []
        cur = end
        while cur != start:
            edges.append(prev_edge[cur])
            cur = prev_node[cur]
            nodes.append(cur)
        nodes.reverse()
        edges.reverse()
        return tuple(nodes), total, tuple(edges)


def build_city_quarter(
    seed: int,
    *,
    grid: int = 4,
    cell: float = 10.0,
    roof_height: float = 12.0,
    gapy: float = 2.5,
) -> MobilityGraph:
    """Deterministically build a parkour-friendly city quarter for demos.

    Ground nodes form a ``grid x grid`` mesh; every node also has a rooftop
    node ``roof_height`` above it. Ground nodes connect by ``run`` edges;
    rooftop neighbours connect by ``leap`` edges of length ``gapy`` (a gap
    between parapets); each rooftop links to its own ground by a ``drop``
    edge and to the next rooftop's wall by ``climb`` edges. Fixed layout - the
    seed only shades each edge's risk/difficulty, keeping the graph itself
    deterministic.
    """
    rng = random.Random(seed)
    g = MobilityGraph()
    ids: list[tuple[str, str]] = []
    for i in range(grid):
        for j in range(grid):
            gid = f"g{i}_{j}"
            rid = f"r{i}_{j}"
            g.add_node(UrbanNode(gid, i * cell, j * cell, 0.0, "ground"))
            g.add_node(UrbanNode(rid, i * cell, j * cell, roof_height, "roof"))
            ids.append((gid, rid))
            # direct rooftop descent
            g.add_edge(UrbanEdge(rid, gid, 0.1, 0.5, 0.1 + rng.random() * 0.2, "drop"))
            g.add_edge(UrbanEdge(gid, rid, gapy, 3.0 + rng.random(), 0.3, "climb"))
    # ground mesh (run)
    for i in range(grid):
        for j in range(grid):
            gid = f"g{i}_{j}"
            if i + 1 < grid:
                other = f"g{i + 1}_{j}"
                g.add_edge(UrbanEdge(gid, other, cell, 1.0, 0.1 + rng.random() * 0.1, "run"))
                g.add_edge(UrbanEdge(other, gid, cell, 1.0, 0.1 + rng.random() * 0.1, "run"))
            if j + 1 < grid:
                other = f"g{i}_{j + 1}"
                g.add_edge(UrbanEdge(gid, other, cell, 1.0, 0.1 + rng.random() * 0.1, "run"))
                g.add_edge(UrbanEdge(other, gid, cell, 1.0, 0.1 + rng.random() * 0.1, "run"))
    # rooftop mesh (leap)
    for i in range(grid):
        for j in range(grid):
            rid = f"r{i}_{j}"
            if i + 1 < grid:
                other = f"r{i + 1}_{j}"
                g.add_edge(UrbanEdge(rid, other, gapy, 2.0, 0.4 + rng.random() * 0.3, "leap"))
                g.add_edge(UrbanEdge(other, rid, gapy, 2.0, 0.4 + rng.random() * 0.3, "leap"))
            if j + 1 < grid:
                other = f"r{i}_{j + 1}"
                g.add_edge(UrbanEdge(rid, other, gapy, 2.0, 0.4 + rng.random() * 0.3, "leap"))
                g.add_edge(UrbanEdge(other, rid, gapy, 2.0, 0.4 + rng.random() * 0.3, "leap"))
    return g


def brute_force_path(
    graph: MobilityGraph,
    start: str,
    end: str,
    profile: ParkourProfile,
    weights: tuple[float, float, float] = DEFAULT_WEIGHTS,
    max_depth: int = 8,
) -> tuple[tuple[str, ...], float, tuple[UrbanEdge, ...]] | None:
    """Exhaustively search every simple path for the cheapest feasible route.

    Intended for small graphs where exhaustive enumeration is the ground
    truth that :func:`MobilityGraph.shortest_path` is tested against. Returns
    the same ``(path, cost, edges)`` shape, or ``None`` if unreachable.
    """
    best: tuple[tuple[str, ...], float, tuple[UrbanEdge, ...]] | None = None

    def visit(
        node: str, path: tuple[str, ...], edges: tuple[UrbanEdge, ...], cost: float, depth: int
    ) -> None:
        nonlocal best
        if depth > max_depth:
            return
        if node == end:
            if best is None or cost < best[1]:
                best = (path, cost, edges)
            return
        for edge in graph.outgoing(node):
            if edge.b in path:
                continue
            if not graph.feasible(edge, profile):
                continue
            visit(
                edge.b,
                (*path, edge.b),
                (*edges, edge),
                cost + graph._cost(edge, weights),
                depth + 1,
            )

    visit(start, (start,), (), 0.0, 0)
    return best
