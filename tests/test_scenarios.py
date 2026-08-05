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


def test_full_snapshot_has_all_keys():
    snap = scenarios.full_snapshot()
    assert set(snap) == {
        "poker",
        "laundering",
        "routes",
        "poison",
        "cfr",
        "icm",
        "network",
        "opponent_bayes",
    }


def test_poker_snapshot_deterministic():
    assert scenarios.poker_snapshot() == scenarios.poker_snapshot()


def test_cfr_snapshot_reports_equilibrium():
    snap = scenarios.cfr_snapshot()
    assert snap["avg_regret"] < 0.01
    assert 0.0 < snap["game_value"] < 1.0
    assert snap["value_bet_frequency"] > 0.9


def test_icm_snapshot_reports_bubble():
    snap = scenarios.icm_snapshot()
    assert snap["players"] == 4
    assert len(snap["equities"]) == 4
    assert snap["bubble_factor"] > 1.0
    assert snap["decision"] in {"fold", "call"}


def test_network_snapshot_flags_launderer():
    snap = scenarios.network_snapshot()
    # The named verdict is decided here, not in the film-agnostic module: it is
    # True because LAUNDERER is in the flagged set, not because someone was.
    assert snap["launderer_flagged"] is True
    assert scenarios.LAUNDERER in snap["flagged"]
    assert snap["launderer_risk"] >= 0.5
    assert snap["top_risk_player"] == "LeChiffre"
    assert snap["any_flagged"] is True


def test_bayes_snapshot_infers_aggression():
    snap = scenarios.bayes_snapshot()
    assert snap["aggressive_posterior"] > 0.5
    assert snap["expected_aggression"] > 0.5
    assert snap["predictive_raise"] > 0.2
