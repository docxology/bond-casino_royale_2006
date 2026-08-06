"""Tests for chip-movement money-laundering detection (laundering_detect.py).

Real transactions built by hand and by the seeded :func:`synthetic_flow`;
assertions on typology primitives and on a composite detector that must catch
the planted smurfer while letting a clean scene pass.
"""

from __future__ import annotations

import pytest

from casino_royale_2006 import laundering_detect as ld


# ----------------------------------------------------- ChipTransaction -----
def test_chip_transaction_validation():
    with pytest.raises(ValueError):
        ld.ChipTransaction("a", "a", 100.0, 0)  # self-sourced
    with pytest.raises(ValueError):
        ld.ChipTransaction("a", "b", -1.0, 0)  # negative amount
    with pytest.raises(ValueError):
        ld.ChipTransaction("a", "b", 1.0, -1)  # negative tick
    with pytest.raises(ValueError):
        ld.ChipTransaction("a", "b", 1.0, 0, kind="wire")  # bad kind


# ------------------------------------------------------ MovementGraph ------
def _triangle() -> tuple[ld.ChipTransaction, ...]:
    return (
        ld.ChipTransaction("cage", "A", 10000.0, 0, "cash_in"),
        ld.ChipTransaction("A", "B", 2000.0, 1, "transfer"),
        ld.ChipTransaction("B", "C", 1500.0, 2, "transfer"),
        ld.ChipTransaction("C", "A", 900.0, 3, "transfer"),
        ld.ChipTransaction("C", "cage", 4000.0, 4, "cash_out"),
    )


def test_movement_graph_flow_and_nodes():
    graph = ld.MovementGraph(_triangle())
    assert set(graph.nodes()) == {"cage", "A", "B", "C"}
    assert set(graph.players()) == {"A", "B", "C"}
    assert graph.total_in("A") == pytest.approx(10000.0 + 900.0)
    assert graph.total_out("A") == pytest.approx(2000.0)
    assert graph.net_flow("A") == pytest.approx(8900.0)
    assert graph.counterparties("A") == 3  # cage + B + C


def test_betweenness_collection_hub():
    # A is on the path B->A? Build a hub: all outer nodes route through "hub".
    txns = (
        ld.ChipTransaction("cage", "x1", 1000.0, 0, "cash_in"),
        ld.ChipTransaction("cage", "x2", 1000.0, 1, "cash_in"),
        ld.ChipTransaction("x1", "hub", 990.0, 2, "transfer"),
        ld.ChipTransaction("x2", "hub", 990.0, 3, "transfer"),
        ld.ChipTransaction("hub", "cage", 1980.0, 4, "cash_out"),
    )
    graph = ld.MovementGraph(txns)
    bc = graph.betweenness()
    # hub mediates many cross paths and scores far above the leaf nodes it
    # collects from - the collection-hub signature.
    assert bc["hub"] > bc["x1"]
    assert bc["hub"] > 0.0


# -------------------------------------------------- typology primitives -----
def test_structuring_count_band():
    txns = (
        ld.ChipTransaction("A", "B", 6000.0, 0, "transfer"),  # in [5000, 10000)
        ld.ChipTransaction("A", "C", 3000.0, 1, "transfer"),  # below band
        ld.ChipTransaction("A", "D", 12000.0, 2, "transfer"),  # above band
        ld.ChipTransaction("A", "cage", 6000.0, 3, "cash_out"),  # not a transfer
    )
    assert ld.structuring_count(txns, "A") == 1
    assert ld.structuring_count(txns, "missing") == 0


def test_round_trips_detection():
    txns = (
        ld.ChipTransaction("A", "B", 8000.0, 0, "transfer"),
        ld.ChipTransaction("B", "A", 8000.0, 3, "transfer"),  # within window 10
        ld.ChipTransaction("C", "D", 8000.0, 0, "transfer"),
        ld.ChipTransaction("D", "C", 8000.0, 40, "transfer"),  # too far apart
        ld.ChipTransaction("E", "F", 100.0, 0, "transfer"),  # too small
    )
    rings = ld.round_trips(txns, window_ticks=10, min_amount=5000.0)
    assert rings == (("A", "B"),)


def test_max_velocity_both_directions():
    txns = (
        ld.ChipTransaction("A", "X", 1.0, 0, "transfer"),
        ld.ChipTransaction("A", "X", 1.0, 1, "transfer"),
        ld.ChipTransaction("Y", "A", 1.0, 2, "transfer"),  # incoming counts
        ld.ChipTransaction("A", "Z", 1.0, 50, "transfer"),  # far window
    )
    assert ld.max_velocity(txns, "A", window_ticks=10) == 3


def test_play_ratio():
    txns = (
        ld.ChipTransaction("cage", "A", 10000.0, 0, "cash_in"),
        ld.ChipTransaction("A", "cage", 9600.0, 5, "cash_out"),
    )
    assert ld.play_ratio(txns, "A") == pytest.approx(0.96)
    assert ld.play_ratio(txns, "absent") is None


# ----------------------------------------------------------- composite -----
def test_detect_flags_planted_launderer():
    flow = ld.synthetic_flow(3)
    alerts = ld.detect(flow)
    launderer = next((a for a in alerts if a.player == "LeChiffre"), None)
    assert launderer is not None
    assert launderer.score >= 1.5
    reasons = " ".join(launderer.reasons)
    assert "structuring" in reasons and "velocity" in reasons
    assert launderer.evidence  # supporting transactions attached


def test_detect_clean_scene_no_alerts():
    clean = (
        ld.ChipTransaction("cage", "A", 10000.0, 0, "cash_in"),
        ld.ChipTransaction("A", "cage", 5200.0, 5, "cash_out"),  # play ratio ~0.52
        ld.ChipTransaction("cage", "B", 8000.0, 1, "cash_in"),
        ld.ChipTransaction("B", "cage", 4100.0, 5, "cash_out"),
    )
    assert ld.detect(clean, velocity_limit=3) == ()


def test_detect_velocity_alert():
    txns = (
        *tuple(ld.ChipTransaction("A", "cage", 500.0, i, "cash_out") for i in range(6)),
        ld.ChipTransaction("cage", "A", 3000.0, 7, "cash_in"),
    )
    alerts = ld.detect(txns, velocity_limit=3)
    assert any(a.player == "A" for a in alerts)


# --------------------------------------------------------- synthetic -------
def test_synthetic_flow_deterministic():
    f1 = ld.synthetic_flow(3, num_players=5, ticks=20)
    f2 = ld.synthetic_flow(3, num_players=5, ticks=20)
    assert f1 == f2
    assert f1


# ------------------------------------------------- round-2 regression --------
def test_detect_round_trip_contributes_a_ring_reason():
    """Regression: ring scoring must actually run inside ``detect``.

    ``round_trips()`` was unit-tested in isolation, but no flow ever drove
    ``detect`` through the branch that folds a ring into the composite score
    and emits the ``roundtrip:N`` reason - a regression dropping ring scoring
    from alerts would have kept every test green. This flow's *only* signals
    are small structured legs plus a returned ring, and the resulting Alert
    must carry the ``roundtrip:`` reason and a score that includes it.
    """
    txns = (
        ld.ChipTransaction("cage", "A", 50000.0, 0, "cash_in"),
        *tuple(ld.ChipTransaction("A", "B", 9800.0, i, "transfer") for i in range(1, 7)),
        ld.ChipTransaction("B", "A", 6000.0, 7, "transfer"),  # the returned ring
    )
    alerts = ld.detect(txns)
    ring = next((a for a in alerts if a.player == "A"), None)
    assert ring is not None
    reasons = " ".join(ring.reasons)
    assert "roundtrip:1" in reasons
    assert "structuring" in reasons  # ring coexists with the structured legs
    assert ring.score >= 1.5
