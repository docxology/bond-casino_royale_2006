"""Tests for the canonical mission scenario snapshots (scenarios.py)."""

from __future__ import annotations

from casino_royale_2006 import scenarios


def test_poker_snapshot_shape_and_bounds():
    snap = scenarios.poker_snapshot()
    equity, be = float(snap["equity_pct"]), float(snap["break_even_pct"])
    assert 0.0 < equity < 100.0
    assert 0.0 < be < 100.0
    assert snap["action"] in {"fold", "call", "raise"}
    assert float(snap["pot"]) > 0 and float(snap["to_call"]) > 0


def test_laundering_snapshot_flags_launderer():
    snap = scenarios.laundering_snapshot()
    assert snap["launderer"] == "LeChiffre"
    assert snap["launderer_flagged"] is True
    assert int(snap["num_transactions"]) > 0


def test_route_snapshot_reachable():
    snap = scenarios.route_snapshot()
    assert snap["fastest_cost"] is not None
    assert snap["safest_cost"] is not None
    assert snap["fastest_uses_roof"] is True
    assert snap["safest_uses_roof"] is False
    assert int(snap["nodes"]) > 0 and int(snap["edges"]) > 0


def test_poison_snapshot_finds_spiked():
    snap = scenarios.poison_snapshot()
    assert snap["spiked_index"] == scenarios.POISON_INDEX
    assert snap["toxicity_grade"] in {"none", "mild", "moderate", "severe"}


def test_full_snapshot_has_all_four_keys():
    snap = scenarios.full_snapshot()
    assert set(snap) == {"poker", "laundering", "routes", "poison"}


def test_poker_snapshot_deterministic():
    assert scenarios.poker_snapshot() == scenarios.poker_snapshot()
