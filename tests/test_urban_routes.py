"""Tests for parkour mobility-graph routing (urban_routes.py).

Real hand-built graphs plus the deterministic city generator; Dijkstra is
cross-checked against exhaustive brute-force search (no mocks).
"""

from __future__ import annotations

import pytest

from casino_royale_2006 import urban_routes as ur


# ------------------------------------------------------- validation -------
def test_urban_node_and_edge_validation():
    with pytest.raises(ValueError):
        ur.UrbanNode("", 0.0, 0.0)  # empty id
    with pytest.raises(ValueError):
        ur.UrbanEdge("a", "a", 1.0, 0.0, 0.0)  # self-loop
    with pytest.raises(ValueError):
        ur.UrbanEdge("a", "b", -1.0, 0.0, 0.0)  # negative distance
    with pytest.raises(ValueError):
        ur.UrbanEdge("a", "b", 1.0, 0.0, 0.0, move="swing")  # unknown move


def test_parkour_profile_validation():
    with pytest.raises(ValueError):
        ur.ParkourProfile(max_leap=-1.0)


# -------------------------------------------------------------- graph -----
def _small_graph() -> ur.MobilityGraph:
    g = ur.MobilityGraph()
    for nid in ("a", "b", "c", "d", "e"):
        g.add_node(ur.UrbanNode(nid, float(ord(nid)), 0.0, 0.0))
    return g


def test_add_edge_requires_existing_nodes():
    g = _small_graph()
    with pytest.raises(KeyError):
        g.add_edge(ur.UrbanEdge("a", "zz", 1.0, 0.0, 0.0))
    with pytest.raises(KeyError):
        g.node("zz")


def test_node_keyerror_message():
    g = _small_graph()
    with pytest.raises(KeyError):
        g.node("missing")


def test_outgoing_and_euclidean():
    g = _small_graph()
    g.add_edge(ur.UrbanEdge("a", "b", 1.0, 0.0, 0.0))
    g.add_edge(ur.UrbanEdge("a", "c", 2.0, 0.0, 0.0))
    assert len(g.outgoing("a")) == 2
    assert len(g.outgoing("b")) == 0
    assert g.euclidean("a", "b") == pytest.approx(1.0)


def test_feasibility_by_move():
    g = _small_graph()
    g.nodes["b"] = ur.UrbanNode("b", 0.0, 0.0, height=5.0)  # raise b
    g.nodes["c"] = ur.UrbanNode("c", 0.0, 0.0, height=3.0)  # modest rise
    prof = ur.ParkourProfile(max_leap=3.0, max_climb=4.0, max_drop=8.0)
    # leap too long vs within limit
    assert not g.feasible(ur.UrbanEdge("a", "c", 5.0, 0.0, 0.0, move="leap"), prof)
    assert g.feasible(ur.UrbanEdge("a", "c", 2.0, 0.0, 0.0, move="leap"), prof)
    # climb within limit (rise 3 <= 4) vs too tall (rise 5 > 4)
    assert g.feasible(ur.UrbanEdge("a", "c", 1.0, 0.0, 0.0, move="climb"), prof)
    assert not g.feasible(ur.UrbanEdge("a", "b", 1.0, 0.0, 0.0, move="climb"), prof)
    # drop within limit
    assert g.feasible(ur.UrbanEdge("b", "a", 1.0, 0.0, 0.0, move="drop"), prof)
    # difficulty/risk caps reject
    assert not g.feasible(ur.UrbanEdge("a", "c", 1.0, 99.0, 0.0, move="run"), prof)


def test_shortest_path_matches_brute_force():
    g = _small_graph()
    # a -> b -> d (cost 2) vs a -> c -> d (cost 2) plus a -> d direct (cost 5)
    for nid, height in (("a", 0.0), ("b", 0.0), ("c", 0.0), ("d", 0.0)):
        g.nodes[nid] = ur.UrbanNode(nid, float(ord(nid)), 0.0, height)
    for edge in (
        ur.UrbanEdge("a", "b", 1.0, 0.0, 0.0),
        ur.UrbanEdge("b", "d", 1.0, 0.0, 0.0),
        ur.UrbanEdge("a", "c", 5.0, 0.0, 0.0),
        ur.UrbanEdge("c", "d", 0.1, 0.0, 0.0),
        ur.UrbanEdge("a", "d", 5.0, 0.0, 0.0),
    ):
        g.add_edge(edge)
    prof = ur.ParkourProfile()
    dij = g.shortest_path("a", "d", prof)
    brute = ur.brute_force_path(g, "a", "d", prof)
    assert dij is not None and brute is not None
    assert dij[0] == brute[0]
    assert dij[1] == pytest.approx(brute[1])
    assert dij[1] == pytest.approx(2.0)  # a->b->d is cheapest


def test_shortest_path_unreachable():
    g = _small_graph()
    g.add_edge(ur.UrbanEdge("a", "b", 1.0, 0.0, 0.0))
    # 'e' is isolated
    assert g.shortest_path("a", "e", ur.ParkourProfile()) is None


def test_deterministic_tie_break():
    g = _small_graph()
    # two equal-cost routes a->b->d and a->c->d
    for edge in (
        ur.UrbanEdge("a", "b", 1.0, 0.0, 0.0),
        ur.UrbanEdge("b", "d", 2.0, 0.0, 0.0),
        ur.UrbanEdge("a", "c", 1.0, 0.0, 0.0),
        ur.UrbanEdge("c", "d", 2.0, 0.0, 0.0),
    ):
        g.add_edge(edge)
    p1 = g.shortest_path("a", "d", ur.ParkourProfile())
    p2 = g.shortest_path("a", "d", ur.ParkourProfile())
    assert p1 is not None and p2 is not None
    assert p1[0] == p2[0] and p1[1] == p2[1]


def test_shortest_path_start_end_validation():
    g = _small_graph()
    with pytest.raises(KeyError):
        g.shortest_path("a", "zz", ur.ParkourProfile())
    with pytest.raises(KeyError):
        g.shortest_path("zz", "a", ur.ParkourProfile())


# -------------------------------------------------------- city quarter -----
def test_city_quarter_reachable_and_deterministic():
    g = ur.build_city_quarter(7, grid=3)
    prof = ur.ParkourProfile(max_climb=13.0, max_drop=13.0)
    ground = g.shortest_path("g0_0", "g2_2", prof, weights=(1.0, 1.0, 2.0))
    assert ground is not None
    assert ground[0][0] == "g0_0" and ground[0][-1] == "g2_2"
    g2 = ur.build_city_quarter(7, grid=3)
    assert g2.edges == g.edges  # deterministic layout


def test_rooftop_shortcut_beats_ground():
    g = ur.build_city_quarter(5, grid=6)
    prof = ur.ParkourProfile(max_climb=13.0, max_drop=13.0)
    fastest = g.shortest_path("g0_0", "g5_5", prof, weights=(1.0, 0.3, 0.3))
    assert fastest is not None and any(n.startswith("r") for n in fastest[0])


def test_default_profile_cannot_climb_roof():
    g = ur.build_city_quarter(5, grid=3)
    # default max_climb=4 < roof_height=12 -> rooftop unreachable, stays ground
    path = g.shortest_path("g0_0", "g2_2", ur.ParkourProfile())
    assert path is not None
    assert not any(n.startswith("r") for n in path[0])


# ---------------------------------------------------------- path cost -----
def test_path_cost_reprices_a_route_under_another_objective():
    """A route's cost is only meaningful under the weighting that produced it.

    Priced under its own weighting, ``path_cost`` must reproduce the cost
    Dijkstra reported; priced under a different weighting it must change, which
    is precisely why two routes solved under two objectives cannot be compared
    by their headline numbers.
    """
    graph = ur.build_city_quarter(17, grid=4)
    profile = ur.ParkourProfile(max_climb=13.0, max_drop=13.0)
    fast_w = (1.0, 0.3, 0.3)
    safe_w = (0.1, 0.4, 1.0)

    fast = graph.shortest_path("g0_0", "g3_3", profile, weights=fast_w)
    safe = graph.shortest_path("g0_0", "g3_3", profile, weights=safe_w)
    assert fast is not None and safe is not None

    # Self-consistency: re-pricing a route under its own weighting is its cost.
    assert graph.path_cost(fast[2], fast_w) == pytest.approx(fast[1])
    assert graph.path_cost(safe[2], safe_w) == pytest.approx(safe[1])

    # Optimality under a single objective: each solve beats the other route
    # when both are priced under that solve's own weighting.
    assert fast[1] <= graph.path_cost(safe[2], fast_w)
    assert safe[1] <= graph.path_cost(fast[2], safe_w)

    # Re-pricing genuinely moves the number (the routes differ).
    assert fast[0] != safe[0]
    assert graph.path_cost(safe[2], fast_w) != pytest.approx(safe[1])


def test_path_cost_of_empty_path_is_zero():
    graph = ur.build_city_quarter(3, grid=3)
    assert graph.path_cost(()) == 0.0
