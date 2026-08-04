"""Tests for the Texas hold'em game-theory engine (poker_engine.py).

Zero mocks: exact hand-evaluation vectors, exact turn/river equity, seeded
Monte-Carlo, pure pot-odds arithmetic, and opponent-model updates over real
action sequences.
"""

from __future__ import annotations

import random

import pytest

from casino_royale_2006 import poker_engine as pe


# ---------------------------------------------------------------- cards ----
def test_card_rank_and_suit():
    assert pe.card_rank(0) == 2  # 2c
    assert pe.card_suit(0) == 0
    assert pe.card_rank(52 - 1) == 14  # As
    assert pe.card_suit(51) == 3


def test_card_str_and_parse_roundtrip():
    for token in ("As", "Td", "7c", "2h", "Kh", "9s"):
        assert pe.card_str(pe.parse_card(token)) == token


def test_parse_cards():
    cards = pe.parse_cards(["As", "Kd", "7h"])
    assert len(cards) == 3


def test_parse_card_invalid():
    with pytest.raises(ValueError):
        pe.parse_card("A")  # too short
    with pytest.raises(ValueError):
        pe.parse_card("1x")  # bad rank/suit
    with pytest.raises(ValueError):
        pe.parse_card("KsX")  # too long


# ---------------------------------------------------------- hand eval ------
def test_evaluate_straight_flush():
    assert pe.evaluate_5(pe.parse_cards(["As", "Ks", "Qs", "Js", "Ts"])) == (8, (14,))


def test_evaluate_wheel_straight():
    # A-2-3-4-5 straight (mixed suits) is a wheel, high card 5.
    assert pe.evaluate_5(pe.parse_cards(["Ah", "2c", "3d", "4s", "5h"])) == (4, (5,))


def test_evaluate_full_house():
    assert pe.evaluate_5(pe.parse_cards(["As", "Ad", "Ah", "Kc", "Ks"])) == (6, (14, 13))


def test_evaluate_four_of_kind():
    assert pe.evaluate_5(pe.parse_cards(["9s", "9d", "9c", "9h", "2c"])) == (7, (9, 2))


def test_evaluate_flush():
    # five hearts, not a straight
    assert pe.evaluate_5(pe.parse_cards(["Ah", "6h", "8h", "3h", "Kh"])) == (5, (14, 13, 8, 6, 3))


def test_evaluate_two_pair_and_kicker():
    assert pe.evaluate_5(pe.parse_cards(["Qd", "Qs", "7c", "7h", "3s"])) == (2, (12, 7, 3))


def test_evaluate_one_pair_kickers():
    assert pe.evaluate_5(pe.parse_cards(["Td", "Ts", "Kc", "4h", "2s"])) == (1, (10, 13, 4, 2))


def test_evaluate_high_card():
    assert pe.evaluate_5(pe.parse_cards(["Ad", "Kd", "Qc", "8h", "2s"])) == (0, (14, 13, 12, 8, 2))


def test_evaluate_requires_five():
    with pytest.raises(ValueError):
        pe.evaluate_5(pe.parse_cards(["As", "Ks", "Qs", "Js"]))


def test_best_hand_from_seven():
    board = pe.parse_cards(["As", "Ks", "Qs", "Js", "3d"])
    hole = pe.parse_cards(["Ts", "2c"])  # royal flush available
    assert pe.best_hand(board + hole) == (8, (14,))


def test_best_hand_requires_five():
    with pytest.raises(ValueError):
        pe.best_hand(pe.parse_cards(["As", "Ks", "Qs"]))


def test_compare_hands():
    royal = pe.parse_cards(["As", "Ks", "Qs", "Js", "Ts"])
    wheel = pe.parse_cards(["Ah", "2c", "3d", "4s", "5h"])
    assert pe.compare_hands(royal, wheel) == 1
    assert pe.compare_hands(wheel, wheel) == 0
    assert pe.compare_hands(wheel, royal) == -1


def test_category_name_known():
    assert pe.category_name(8) == "straight flush"
    assert pe.category_name(0) == "high card"


# -------------------------------------------------------------- dealing ----
def test_shuffled_deck_deterministic():
    r1 = pe.shuffled_deck(random.Random(5))
    r2 = pe.shuffled_deck(random.Random(5))
    r3 = pe.shuffled_deck(random.Random(6))
    assert r1 == r2
    assert r1 != r3
    assert sorted(r1) == list(range(52))


def test_deal_hands_and_community():
    deck = list(range(52))
    hands = pe.deal_hands(deck, 3)
    assert len(hands) == 3
    assert all(len(h) == 2 for h in hands)
    assert pe.community_cards(deck, 3) == tuple(range(6, 11))


def test_deal_hands_errors():
    with pytest.raises(ValueError):
        pe.deal_hands(pe.FULL_DECK, 0)
    with pytest.raises(ValueError):
        pe.deal_hands(pe.FULL_DECK[:5], 3)  # not enough cards


def test_dead_cards_and_duplicate():
    dead = pe.dead_cards([(0, 1)], (2,))
    assert dead == {0, 1, 2}
    with pytest.raises(ValueError):
        pe.dead_cards([(0, 0)], ())  # duplicate within a hand


# ----------------------------------------------------- exact turn/river ----
def test_exact_equity_turn_river_partitions():
    a = pe.parse_cards(["Ah", "Ad"])
    b = pe.parse_cards(["Kh", "Kd"])
    flop = pe.parse_cards(["2c", "7d", "9h"])
    win_a, tie, win_b = pe.exact_equity_turn_river(a, b, flop)
    assert win_a + tie + win_b == pytest.approx(1.0)
    assert win_a > 0.7  # pocket aces dominate here


def test_exact_equity_turn_river_requires_flop():
    with pytest.raises(ValueError):
        pe.exact_equity_turn_river((0, 1), (2, 3), (4, 5))  # only 2 board cards


# ----------------------------------------------------------- monte carlo ----
def test_monte_carlo_equity_deterministic_and_valid():
    holes = (pe.parse_cards(["Ah", "Ad"]), pe.parse_cards(["Kh", "Kd"]))
    board = pe.parse_cards(["2c", "7d", "9h"])
    r1 = pe.monte_carlo_equity(holes, board, 500, random.Random(1))
    r2 = pe.monte_carlo_equity(holes, board, 500, random.Random(1))
    assert r1 == r2
    win, tie = r1[0]
    assert 0.0 <= win <= 1.0 and 0.0 <= tie <= 1.0
    assert win > 0.5


def test_monte_carlo_equity_multiway():
    holes = (
        pe.parse_cards(["Ah", "Ad"]),
        pe.parse_cards(["Kh", "Kd"]),
        pe.parse_cards(["Qs", "Qc"]),
    )
    results = pe.monte_carlo_equity(holes, (), 500, random.Random(2))
    assert len(results) == 3


def test_monte_carlo_equity_errors():
    with pytest.raises(ValueError):
        pe.monte_carlo_equity(
            (pe.parse_cards(["Ah", "Ad"]), pe.parse_cards(["Kh", "Kd"])), (), 0, random.Random(1)
        )
    with pytest.raises(ValueError):
        pe.monte_carlo_equity(
            (pe.parse_cards(["Ah", "Ad"]),), (), 10, random.Random(1)
        )  # one player


# --------------------------------------------------------- equity vs range ----
def test_equity_vs_range_positive_and_deterministic():
    hole = pe.parse_cards(["Kh", "Kc"])
    board = pe.parse_cards(["As", "7h", "2d"])
    dead = set(hole) | set(board)
    rng = random.Random(3)
    opps = list(pe.iter_opponent_hands(tuple(pe.RANGE_ARCHETYPES["tight"]), dead, rng, 8))
    e1 = pe.equity_vs_range(hole, opps, board, 200, random.Random(4))
    e2 = pe.equity_vs_range(hole, opps, board, 200, random.Random(4))
    assert e1 == e2
    assert 0.0 < e1 < 1.0


def test_equity_vs_range_empty_range():
    with pytest.raises(ValueError):
        pe.equity_vs_range((0, 1), [], (), 100, random.Random(1))


def test_iter_opponent_hands_respects_dead():
    hole = pe.parse_cards(["As", "Ad"])
    dead = set(hole)
    rng = random.Random(1)
    hands = list(pe.iter_opponent_hands(("AKs",), dead, rng, 5))
    assert len(hands) == 5
    for hand in hands:
        assert set(hand).isdisjoint(dead)  # no dead/hole cards reused


# ------------------------------------------------------------ pot odds -----
def test_pot_odds_functions():
    assert pe.pot_odds_ratio(500.0, 100.0) == 5.0
    assert pe.break_even_equity(4.0, 1.0) == pytest.approx(0.2)
    # EV of a 60% equity call into 4:1 pot is strongly positive
    assert pe.ev_of_call(0.6, 4.0, 1.0) == pytest.approx(2.0)
    assert pe.equity_margin(0.3, 4.0, 1.0) == pytest.approx(0.1)


def test_pot_odds_errors():
    with pytest.raises(ValueError):
        pe.pot_odds_ratio(-1.0, 1.0)
    with pytest.raises(ValueError):
        pe.pot_odds_ratio(4.0, 0.0)
    with pytest.raises(ValueError):
        pe.ev_of_call(1.5, 4.0, 1.0)
    with pytest.raises(ValueError):
        pe.break_even_equity(4.0, -1.0)


def test_recommend_action_branches():
    # Low equity -> fold
    assert pe.recommend_action(4.0, 1.0, 0.05) == "fold"
    # Healthy margin -> raise
    assert pe.recommend_action(4.0, 1.0, 0.6) == "raise"
    # Between thresholds -> call
    assert pe.recommend_action(4.0, 1.0, 0.3) == "call"
    # Exact-at-fold boundary with custom fold_margin
    assert pe.recommend_action(4.0, 1.0, 0.2, raise_margin=0.5, fold_margin=0.2) == "fold"


# -------------------------------------------------------- opponent model ----
def test_opponent_model_updates_and_metrics():
    model = pe.OpponentModel(name="LeChiffre")
    for action in ("raise", "raise", "bet", "call", "fold", "call"):
        model.update(action)
    assert model.hands_seen == 6
    assert model.raises == 2 and model.bets == 1 and model.calls == 2 and model.folds == 1
    assert model.vpip == pytest.approx(5 / 6)
    assert model.aggression_factor == pytest.approx(3 / 2)
    assert model.archetype() == "loose-aggressive"


def test_opponent_model_unknown_action():
    model = pe.OpponentModel(name="x")
    with pytest.raises(ValueError):
        model.update("allin")


def test_opponent_model_zero_calls_aggression():
    model = pe.OpponentModel(name="e")
    model.update("raise")
    model.update("bet")
    assert model.aggression_factor == 2.0


def test_opponent_model_passive_archetype():
    model = pe.OpponentModel(name="p")
    model.update("call")
    model.update("fold")
    model.update("fold")
    model.update("fold")
    assert model.archetype() == "tight-passive"


def test_opponent_model_empty_vpip():
    assert pe.OpponentModel(name="x").vpip == 0.0


# ------------------------------------------------------------- ranges -------
def test_starting_hand_class():
    assert pe.starting_hand_class(pe.parse_cards(["Ah", "Ad"])) == "AA"
    assert pe.starting_hand_class(pe.parse_cards(["As", "Ks"])) == "AKs"
    assert pe.starting_hand_class(pe.parse_cards(["As", "Kd"])) == "AKo"


def test_range_archetype_keys_and_raise_margins():
    assert set(pe.RANGE_ARCHETYPES) == {"tight", "loose"}
    assert pe.recommended_raise_margin("loose-passive") == 0.06
    assert pe.recommended_raise_margin("loose-aggressive") == 0.10
    assert pe.recommended_raise_margin("tight-aggressive") == 0.14
    assert pe.recommended_raise_margin("tight-passive") == 0.10
