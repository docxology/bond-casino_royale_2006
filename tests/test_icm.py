"""Tests for the tournament Independent Chip Model (icm.py)."""

from __future__ import annotations

import random

import pytest

from casino_royale_2006 import icm


def test_exact_icm_heads_up_linear():
    # Heads-up ICM is linear: eq_i = last_prize + (s_i/total)*(top-last).
    stacks, prizes = (1000, 3000), (70.0, 30.0)
    expected = 30.0 + (1000 / 4000) * 40.0
    assert icm.exact_icm_equity(stacks, prizes, 0) == pytest.approx(expected)


def test_exact_icm_equal_stacks_equal_equity():
    stacks, prizes = (1000, 1000, 1000), (50.0, 30.0, 20.0)
    e0 = icm.exact_icm_equity(stacks, prizes, 0)
    e2 = icm.exact_icm_equity(stacks, prizes, 2)
    assert e0 == pytest.approx(e2)
    # Equal three-way with prizes 50/30/20: each has 1/3 chance of each? No -
    # just assert the average of all three equals the mean prize (33.33).
    avg = sum(icm.exact_icm_equity(stacks, prizes, i) for i in range(3)) / 3
    assert avg == pytest.approx(sum(prizes) / 3)


def test_exact_icm_validation():
    with pytest.raises(ValueError):
        icm.exact_icm_equity((), (50.0, 30.0), 0)
    with pytest.raises(ValueError):
        icm.exact_icm_equity((-5, 100), (50.0, 30.0), 0)
    with pytest.raises(ValueError):
        icm.exact_icm_equity((0, 0), (50.0, 30.0), 0)
    with pytest.raises(ValueError):
        icm.exact_icm_equity((100, 100), (50.0, 30.0), 5)


def test_monte_carlo_icm_deterministic_and_close():
    stacks, prizes = (4000, 3000, 1500, 500), (50.0, 30.0, 20.0)
    exact = icm.exact_icm_equity(stacks, prizes, 1)
    mc = icm.monte_carlo_icm(stacks, prizes, 1, 30000, random.Random(7))
    assert mc == icm.monte_carlo_icm(stacks, prizes, 1, 30000, random.Random(7))
    assert mc == pytest.approx(exact, abs=0.5)


def test_monte_carlo_icm_validation():
    with pytest.raises(ValueError):
        icm.monte_carlo_icm((100, 100), (50.0, 30.0), 0, 0, random.Random(1))
    with pytest.raises(ValueError):
        icm.monte_carlo_icm((), (50.0, 30.0), 0, 10, random.Random(1))


def test_bubble_factor_heads_up_is_one():
    # Heads-up ICM is linear, so the insurance quotient is exactly 1.
    assert icm.bubble_factor((3000, 1000), (70.0, 30.0), 1) == pytest.approx(1.0, abs=1e-6)


def test_bubble_factor_squeeze():
    stacks, prizes = (4000, 3000, 1500, 500), (50.0, 30.0, 20.0)
    short_bf = icm.bubble_factor(stacks, prizes, 3)
    assert short_bf > 1.0  # on the bubble, risking chips is -EV in equity terms
    leader_bf = icm.bubble_factor(stacks, prizes, 0)
    assert leader_bf > short_bf  # the chip leader risks the most prize equity


def test_bubble_factor_validation():
    stacks, prizes = (4000, 3000, 1500, 500), (50.0, 30.0, 20.0)
    with pytest.raises(ValueError):
        icm.bubble_factor(stacks, prizes, 3, all_in_amount=99999)  # > stack
    # A zero-stack (already-busted) player cannot have a bubble factor.
    with pytest.raises(ValueError):
        icm.bubble_factor((0, 1000, 1000), (50.0, 30.0, 20.0), 0)


def test_icm_call_ev_and_decision_heads_up():
    stacks, prizes = (1000, 1000), (100.0, 0.0)
    # Calling is -prize-equity when unlikely to win, +prize-equity when favoured.
    assert icm.icm_call_ev(stacks, prizes, 0, 1000, 0.5, 2000) < 0.0
    assert icm.icm_call_ev(stacks, prizes, 0, 1000, 0.9, 2000) > 0.0
    assert icm.icm_decision(stacks, prizes, 0, 1000, 0.5, 2000) == "fold"
    assert icm.icm_decision(stacks, prizes, 0, 1000, 0.9, 2000) == "call"


def test_icm_call_ev_monotonic_in_win_prob():
    stacks, prizes = (2000, 1000, 1000), (100.0, 60.0, 30.0)
    values = [icm.icm_call_ev(stacks, prizes, 0, 200, wp, 400) for wp in (0.2, 0.5, 0.8)]
    assert values[0] < values[1] < values[2]


def test_icm_call_ev_validation():
    stacks, prizes = (1000, 1000), (100.0, 0.0)
    with pytest.raises(ValueError):
        icm.icm_call_ev(stacks, prizes, 0, 1500, 0.5, 2000)  # to_call > stack
    with pytest.raises(ValueError):
        icm.icm_call_ev(stacks, prizes, 0, 100, 1.5, 2000)  # win_prob out of range
