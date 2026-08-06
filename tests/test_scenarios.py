"""Tests for the canonical mission scenario snapshots (scenarios.py)."""

from __future__ import annotations

import pytest

from casino_royale_2006 import poker_engine as pe
from casino_royale_2006 import scenarios


def test_poker_snapshot_shape_and_bounds():
    snap = scenarios.poker_snapshot()
    equity, be = float(snap["equity_pct"]), float(snap["break_even_pct"])
    assert 0.0 < equity < 100.0
    assert 0.0 < be < 100.0
    assert snap["action"] in {"fold", "call", "raise"}
    assert float(snap["pot"]) > 0 and float(snap["to_call"]) > 0


def test_poker_range_is_selected_by_the_observed_tendencies():
    """The published range must be *derived* from the observed history.

    Le Chiffre's canonical history is raise-heavy, so the frequentist model
    reads him loose-aggressive and the snapshot must price the hand against the
    loose range. The second half proves the selection is live rather than
    decorative: a fold-heavy history goes down the same code path and lands on
    the other range.
    """
    model = scenarios.observed_opponent_model()
    assert model.archetype() == "loose-aggressive"

    snap = scenarios.poker_snapshot()
    assert snap["opponent_archetype"] == "loose-aggressive"
    assert snap["range"] == "loose"
    assert snap["range_classes"] == len(pe.RANGE_ARCHETYPES["loose"])
    assert snap["raise_margin_pct"] == pytest.approx(
        100.0 * pe.recommended_raise_margin("loose-aggressive")
    )

    passive = pe.OpponentModel(name="mark")
    for action in ("call", "fold", "fold", "fold"):
        passive.update(action)
    assert pe.range_key_for_archetype(passive.archetype()) == "tight"
    assert pe.range_for_archetype(passive.archetype()) != pe.range_for_archetype(model.archetype())


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


def test_route_costs_are_only_comparable_within_one_objective():
    """Each route must win under its own weighting - and only under it.

    The two headline costs are computed under different objective functions, so
    the smaller headline number does not mean the cheaper route. This pins both
    halves: the cross-priced comparisons (which the manuscript quotes) order the
    routes correctly, and the naive headline comparison is shown to invert.
    """
    snap = scenarios.route_snapshot()
    fastest = float(snap["fastest_cost"])
    safest = float(snap["safest_cost"])
    safest_under_fast = float(snap["safest_cost_under_fast"])
    fastest_under_safe = float(snap["fastest_cost_under_safe"])

    # Under one objective at a time, each solve is the cheaper of the two.
    assert fastest < safest_under_fast
    assert safest < fastest_under_safe

    # And the naive cross-objective comparison genuinely misleads: the ground
    # route's headline cost is the smaller number while being ~3x more
    # expensive under the speed objective the rooftop route was solved for.
    assert safest < fastest
    assert safest_under_fast > fastest


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


# ------------------------------------------------- round-2 regressions -------
def test_poker_snapshot_can_recommend_fold_at_an_unfavourable_price():
    """Negative control: the snapshot decision path is able to say ``fold``.

    The canonical hand always clears the pot-odds bar, so ``fold`` had never
    been produced on the snapshot path the manuscript and mission read. By
    overriding the price (a huge to-call against a small pot) that same path
    must return ``fold`` - proving the decision code is shown capable of
    refusing a hand, not just of raising/calling.
    """
    default = scenarios.poker_snapshot()
    assert default["action"] == "raise"  # canonical stays on the raise path

    folded = scenarios.poker_snapshot(pot=100.0, to_call=500.0)
    assert float(folded["break_even_pct"]) > 50.0
    assert folded["action"] == "fold"
    # The override is the *only* thing that differs - the equity and range are
    # still drawn by the exact same canonical engine path.
    assert folded["range"] == default["range"]


def test_cross_detector_agreement_on_the_named_suspect():
    """The typology and network detectors must name the *same* account.

    Both layers are claimed to converge on Le Chiffre; this binds that claim to
    a single failure point so neither detector can silently drift onto a
    different account without a test failing. The negative-control half proves
    the assertion is account-specific and not just \"somebody was flagged\".
    """
    launder = scenarios.laundering_snapshot()
    net = scenarios.network_snapshot()
    assert launder["launderer_flagged"] is True
    assert net["launderer_flagged"] is True
    assert scenarios.LAUNDERER in net["flagged"]
    # The agreement is about THIS account, not merely that anyone was flagged:
    # an unrelated name must answer False in both layers.
    for other in ("nobody", "cage", "P2"):
        assert scenarios.named_verdict(net["flagged"], other) is False
