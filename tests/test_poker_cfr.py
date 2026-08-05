"""Tests for the CFR river toy-game solver (poker_cfr.py)."""

from __future__ import annotations

import pytest

from casino_royale_2006 import poker_cfr as pc


def test_cfr_solve_structure():
    result = pc.cfr_solve(16, 300)
    assert result.num_strengths == 16
    assert len(result.regret_trace) == 300
    assert set(result.p1_strategy) == {"check", "bet"}
    assert set(result.p2_strategy) == {"fold", "call"}
    assert all(len(v) == 16 for v in result.p1_strategy.values())


def test_cfr_converges_low_regret_and_positive_value():
    result = pc.cfr_solve(16, 300)
    assert result.avg_regret < 0.01
    assert result.avg_regret >= 0.0
    assert 0.0 < result.game_value < 1.0


def test_cfr_more_iterations_lower_regret():
    low = pc.cfr_solve(8, 100).avg_regret
    high = pc.cfr_solve(8, 600).avg_regret
    assert high < low


def test_cfr_deterministic():
    assert pc.cfr_solve(16, 200) == pc.cfr_solve(16, 200)


def test_polar_betting_shape():
    result = pc.cfr_solve(16, 400)
    n = result.num_strengths
    bet = result.p1_strategy["bet"]
    # Value-bet the strongest hand, bluff the weakest, and check the middle.
    assert bet[n - 1] > 0.9  # top of range bets almost always
    assert bet[0] > 0.5  # the bluffs live at the very bottom
    assert bet[n // 2] < 0.5  # the middle checks more often than it bets


def test_betting_profile_keys_and_ranges():
    profile = pc.betting_profile(pc.cfr_solve(16, 200))
    for key in ("bluff_frequency", "value_bet_frequency", "call_frequency", "fold_frequency"):
        assert 0.0 <= profile[key] <= 1.0


def test_cfr_solve_validation():
    with pytest.raises(ValueError):
        pc.cfr_solve(1, 10)
    with pytest.raises(ValueError):
        pc.cfr_solve(8, 0)
