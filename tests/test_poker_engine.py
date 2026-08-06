"""Tests for the Texas hold'em game-theory engine (poker_engine.py).

Zero mocks: exact hand-evaluation vectors, exact turn/river equity, seeded
Monte-Carlo, pure pot-odds arithmetic, and opponent-model updates over real
action sequences.

Two checks here are *external* oracles rather than self-consistency checks, and
they cover different failure modes - measured, not assumed:

* :func:`test_category_ranking_matches_the_published_order` pins the nine hand
  categories, and the within-category kicker order, against the published
  hold'em hand ranking. This is the sensitive one: swapping any two category
  codes, or dropping a kicker from a tiebreak tuple, turns it red.
* :func:`test_preflop_aa_vs_kk_matches_published_equity` measures heads-up
  preflop AA-vs-KK equity against the published figure (AA wins 81.71%, ties
  0.46% -> 81.94% equity). This one covers the *equity pipeline* - sampling,
  runout construction, showdown comparison. Its measured sensitivity is
  limited and is stated on the test itself: a defect big enough to break
  showdown comparison moves it far outside tolerance (``best_hand`` taking the
  worst subset instead of the best measures 72.6%), but because both players
  see the same board, several category-ranking swaps move it by under a tenth
  of a point. Those are the ranking test's job, not this one's.
"""

from __future__ import annotations

import itertools
import random

import pytest

from casino_royale_2006 import poker_engine as pe

#: Published heads-up preflop equity for AA vs KK (win 81.71% + half of the
#: 0.46% ties). Source: standard hold'em all-in equity tables (e.g. the
#: pokerstove/twodimes reference matchup grid); registered in
#: ``data/claim_ledger.yaml`` as ``poker_aa_vs_kk_preflop``.
PUBLISHED_AA_VS_KK_EQUITY_PCT = 81.94


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


#: The published hold'em hand ranking, weakest to strongest, one concrete
#: five-card example per category. External oracle: the order is the rules of
#: the game, not anything this package derives.
PUBLISHED_HAND_RANKING: tuple[tuple[tuple[str, ...], str], ...] = (
    (("Ad", "Kd", "Qc", "8h", "2s"), "high card"),
    (("Td", "Ts", "Kc", "4h", "2s"), "one pair"),
    (("Qd", "Qs", "7c", "7h", "3s"), "two pair"),
    (("9s", "9d", "9c", "4h", "2s"), "three of a kind"),
    (("Ah", "2c", "3d", "4s", "5h"), "straight"),
    (("Ah", "6h", "8h", "3h", "Kh"), "flush"),
    (("As", "Ad", "Ah", "Kc", "Ks"), "full house"),
    (("9s", "9d", "9c", "9h", "2c"), "four of a kind"),
    (("As", "Ks", "Qs", "Js", "Ts"), "straight flush"),
)


def test_category_ranking_matches_the_published_order():
    """External oracle: the nine categories must order as the rules say.

    One real hand per category, evaluated and then required to be strictly
    increasing in published order. Swap any two category codes in
    ``evaluate_5`` - full house below flush, quads scored as trips, a straight
    scored as a flush - and this goes red immediately. (The AA-vs-KK equity
    oracle does *not* catch those; see the module docstring.)
    """
    values = [pe.evaluate_5(pe.parse_cards(cards)) for cards, _ in PUBLISHED_HAND_RANKING]
    assert [pe.category_name(v[0]) for v in values] == [name for _, name in PUBLISHED_HAND_RANKING]
    for weaker, stronger in itertools.pairwise(values):
        assert weaker < stronger, f"{weaker} should rank below {stronger}"


def test_within_category_tiebreaks_follow_the_published_kicker_order():
    """External oracle: kickers decide, in the published precedence order."""
    better_worse = (
        # flush: A-K-Q-J-9 beats A-K-Q-J-8 (last card decides)
        (("Ah", "Kh", "Qh", "Jh", "9h"), ("Ah", "Kh", "Qh", "Jh", "8h")),
        # flush: the *highest* card decides first, even when every other card
        # is worse. A tiebreak tuple built in ascending order gets this wrong.
        (("Ah", "7h", "5h", "4h", "3h"), ("Ks", "Qs", "Js", "Ts", "8s")),
        # one pair: same pair, higher first kicker wins
        (("Td", "Ts", "Ac", "4h", "2s"), ("Td", "Ts", "Kc", "4h", "2s")),
        # one pair: same pair and first two kickers, last kicker decides
        (("Td", "Ts", "Kc", "4h", "3s"), ("Td", "Ts", "Kc", "4h", "2s")),
        # two pair: same two pairs, kicker decides
        (("Qd", "Qs", "7c", "7h", "Ks"), ("Qd", "Qs", "7c", "7h", "3s")),
        # two pair: higher top pair beats higher kicker
        (("Kd", "Ks", "3c", "3h", "2s"), ("Qd", "Qs", "Jc", "Jh", "As")),
        # straight: higher top card wins (and the wheel is the lowest)
        (("6h", "5c", "4d", "3s", "2h"), ("Ah", "5c", "4d", "3s", "2h")),
    )
    for better, worse in better_worse:
        hi = pe.evaluate_5(pe.parse_cards(better))
        lo = pe.evaluate_5(pe.parse_cards(worse))
        assert hi > lo, f"{better} should beat {worse} (got {hi} vs {lo})"


def test_preflop_aa_vs_kk_matches_published_equity():
    """External oracle: measured AA-vs-KK preflop equity vs. the published value.

    Averaged over all 6x6 suit combinations (suit overlap moves a single
    matchup by more than a point, so a single combination is not the published
    number). Seeded, hence deterministic; 200 runouts per matchup gives a
    standard error near 0.46 points, and the +/-2.0 tolerance is ~4 s.e., wide
    enough never to flake.

    Scope, measured rather than asserted: this covers the equity pipeline
    end to end - sampling, runout construction, showdown comparison. Making
    ``best_hand`` select the worst five-card subset instead of the best drops
    the measurement to 72.6% and turns this red. It is *not* sensitive to
    category-ranking swaps (both players see the same board, so most of the
    error cancels): demoting a full house below a flush moved it by 0.03
    points. Those defects are caught by
    :func:`test_category_ranking_matches_the_published_order`.
    """
    aces = [pe.parse_card("A" + s) for s in pe.SUIT_CHARS]
    kings = [pe.parse_card("K" + s) for s in pe.SUIT_CHARS]
    rng = random.Random(11)
    total_equity = 0.0
    matchups = 0
    for hero in itertools.combinations(aces, 2):
        for villain in itertools.combinations(kings, 2):
            (win, tie), _villain = pe.monte_carlo_equity((hero, villain), (), 200, rng)
            total_equity += win + tie / 2.0
            matchups += 1
    assert matchups == 36
    measured_pct = 100.0 * total_equity / matchups
    assert measured_pct == pytest.approx(PUBLISHED_AA_VS_KK_EQUITY_PCT, abs=2.0), (
        f"measured AA-vs-KK preflop equity {measured_pct:.2f}% is not the "
        f"published {PUBLISHED_AA_VS_KK_EQUITY_PCT}%"
    )


# --------------------------------------------------------- equity vs range ----
def test_equity_vs_range_positive_and_deterministic():
    hole = pe.parse_cards(["Kh", "Kc"])
    board = pe.parse_cards(["As", "7h", "2d"])
    dead = set(hole) | set(board)
    rng = random.Random(3)
    opps = list(pe.iter_opponent_hands(tuple(sorted(pe.RANGE_ARCHETYPES["tight"])), dead, rng, 8))
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


def test_archetype_range_map_covers_every_label_archetype_can_emit():
    """The label vocabulary and the range-selection table must not drift apart.

    ``archetype()`` builds its label from two binary splits; this enumerates
    both splits over real ``OpponentModel`` histories and requires the mapping
    table to have an entry for each label actually produced.
    """
    histories = {
        "loose-aggressive": ("raise", "raise", "call"),
        "loose-passive": ("call", "call", "call"),
        "tight-passive": ("call", "fold", "fold", "fold"),
        "tight-aggressive": ("raise", "fold", "fold", "fold"),
    }
    produced = set()
    for expected_label, actions in histories.items():
        model = pe.OpponentModel(name="x")
        for action in actions:
            model.update(action)
        assert model.archetype() == expected_label
        produced.add(model.archetype())
    assert produced == set(pe.ARCHETYPE_RANGE_KEYS)
    assert set(pe.ARCHETYPE_RANGE_KEYS.values()) == set(pe.RANGE_ARCHETYPES)


def test_range_for_archetype_selects_the_matching_range():
    assert pe.range_key_for_archetype("loose-aggressive") == "loose"
    assert pe.range_key_for_archetype("tight-passive") == "tight"
    assert pe.range_for_archetype("loose-passive") is pe.RANGE_ARCHETYPES["loose"]
    assert pe.range_for_archetype("tight-aggressive") is pe.RANGE_ARCHETYPES["tight"]
    # The two ranges are genuinely different, so selection is observable.
    assert pe.RANGE_ARCHETYPES["loose"] > pe.RANGE_ARCHETYPES["tight"]


def test_unknown_archetype_is_rejected_everywhere():
    for func in (pe.range_key_for_archetype, pe.range_for_archetype, pe.recommended_raise_margin):
        with pytest.raises(KeyError):
            func("maniac")


def test_raise_margin_changes_the_recommended_action():
    """The archetype-driven margin must be capable of flipping the decision.

    Equity margin here is exactly 0.10: above the loose-passive threshold
    (0.06 -> raise), below the tight-aggressive one (0.14 -> call). If
    ``recommend_action`` ignored ``raise_margin`` both lines would agree.
    """
    pot, to_call, equity = 4.0, 1.0, 0.30
    assert pe.equity_margin(equity, pot, to_call) == pytest.approx(0.10)
    loose = pe.recommended_raise_margin("loose-passive")
    tight = pe.recommended_raise_margin("tight-aggressive")
    assert pe.recommend_action(pot, to_call, equity, raise_margin=loose) == "raise"
    assert pe.recommend_action(pot, to_call, equity, raise_margin=tight) == "call"


# ------------------------------------------------- range sampling fidelity ----
def test_offsuit_range_hands_never_share_a_suit():
    """Negative control for the offsuit sampling defect (round-2).

    An \"offsuit\" starting-hand class (``AKo``, ``AQo``, ``KQo``, ``AJo``)
    is defined by holding two cards of *different* suits. The old sampler chose
    the low card independently of the high card's suit, so roughly 25% of the
    hands drawn for an offsuit class were actually suited (AKs masquerading as
    AKo) - silently tilting the opponent range and the equity it prices toward
    suited hands. Every drawn pair must keep distinct suits, across many seeds
    and over the dead-card-full canonical board.
    """
    hole = pe.parse_cards(["Kh", "Kc"])
    board = pe.parse_cards(["As", "7h", "2d"])
    dead = set(hole) | set(board)
    offsuit_classes = ("AKo", "AQo", "KQo", "AJo")
    seen = 0
    for i in range(60):
        rng = random.Random(i)
        for hand in pe.iter_opponent_hands(offsuit_classes, dead, rng, 4):
            assert pe.card_suit(hand[0]) != pe.card_suit(hand[1]), (
                f"offsuit class drew a same-suit pair {pe.card_str(hand[0])}"
                f"{pe.card_str(hand[1])} - range fidelity broken"
            )
            seen += 1
    assert seen > 0


def test_exact_equity_records_ties_on_a_paired_flop():
    """The exact turn/river enumerator must count tied runouts.

    When the flop pairs and both players hold the same rank for the kicker,
    most runouts leave both with the identical best hand (pair of the board,
    ace kicker) - so ``exact_equity_turn_river`` should report a non-zero tie
    fraction. This pins the previously-uncovered tie branch of the equity
    partition.
    """
    a = pe.parse_cards(["As", "Jd"])
    b = pe.parse_cards(["Ac", "Jc"])  # board kickers cancel on every runout
    flop = pe.parse_cards(["9d", "9c", "2h"])
    win_a, tie, win_b = pe.exact_equity_turn_river(a, b, flop)
    assert win_a + tie + win_b == pytest.approx(1.0)
    assert tie > 0.0
