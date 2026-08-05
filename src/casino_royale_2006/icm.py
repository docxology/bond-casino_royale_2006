"""Tournament poker economy: the Independent Chip Model (ICM).

The finale of *Casino Royale* is a winner-take-the-stake freezeout escalation
(a tournament the agent must survive to the money). In tournament poker, chips
are **not** linear in cash value - the last chips are worth more than the first
because they buy survival toward flatter, safer prize money. ICM is the
canonical model of that nonlinearity (Chen & Ankenman, *The Mathematics of
Poker*, 2006): under the random-tournament assumption a player's probability of
finishing in each paid place is computed from their chip share, and prize
equity follows.

This module implements:

* :func:`exact_icm_equity` - the exact recursion for small fields (O(exponential)
  but memo-safe for the 3-6 player bubble decisions the mission cares about).
* :func:`monte_carlo_icm` - a seeded, deterministic simulation of random finish
  order for larger fields.
* :func:`bubble_factor` - the ratio of prize-equity lost per chip when losing to
  prize-equity gained per chip when winning; > 1 means "being short-chipped and
  safe is worth more than doubling up" - the bubble squeeze.
* :func:`icm_call_ev` / :func:`icm_decision` - whether calling a bet is
  +prize-equity, the correct tournament decision when a call risks elimination.

All math is deterministic; the only randomness is the seeded RNG inside
:func:`monte_carlo_icm`, never the global state.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from functools import cache

__all__ = [
    "bubble_factor",
    "exact_icm_equity",
    "icm_call_ev",
    "icm_decision",
    "monte_carlo_icm",
]


def _validate(stacks: Sequence[int], prizes: Sequence[float], player: int) -> None:
    if not stacks:
        raise ValueError("stacks must not be empty")
    if any(s < 0 for s in stacks):
        raise ValueError("stack sizes must be non-negative")
    if sum(stacks) <= 0:
        raise ValueError("at least one stack must be positive")
    if not prizes:
        raise ValueError("prizes must not be empty")
    if not (0 <= player < len(stacks)):
        raise ValueError(f"player index {player} out of range")


def exact_icm_equity(stacks: Sequence[int], prizes: Sequence[float], player: int) -> float:
    """Exact ICM prize equity for ``player`` (small fields, memoised recursion).

    The recurrence: ``E_i(S, P) = (s_i/S).P[0] + sum over j != i of
    (s_j/S).E_i(S without j, P[1:])``. A player reaching the final money place
    collects ``prizes[place]``; fields larger than the prize count leave the
    tail players with zero.
    """
    _validate(stacks, prizes, player)
    stacks_t = tuple(stacks)
    prizes_t = tuple(prizes)

    @cache
    def _eq(remaining: tuple[int, ...], prize_slice: tuple[float, ...], target: int) -> float:
        total = sum(remaining)
        if len(remaining) == 1:
            return prize_slice[0] if prize_slice else 0.0
        if not prize_slice:
            return 0.0
        first = (remaining[target] / total) * prize_slice[0]
        rest = 0.0
        for j in range(len(remaining)):
            if j == target:
                continue
            sub = remaining[:j] + remaining[j + 1 :]
            new_target = target - 1 if j < target else target
            rest += (remaining[j] / total) * _eq(sub, prize_slice[1:], new_target)
        return first + rest

    return _eq(stacks_t, prizes_t, player)


def monte_carlo_icm(
    stacks: Sequence[int],
    prizes: Sequence[float],
    player: int,
    num_simulations: int,
    rng: random.Random,
) -> float:
    """ICM prize equity by seeded random-finish-order simulation.

    For each simulation, players are eliminated one at a time with probability
    proportional to current stack; eliminated players collect the next prize.
    Large fields use this; small fields should prefer the exact recursion.
    """
    _validate(stacks, prizes, player)
    if num_simulations < 1:
        raise ValueError("num_simulations must be >= 1")
    n = len(stacks)
    total = 0.0
    for _ in range(num_simulations):
        remaining = list(range(n))  # player indices still in the running
        chips = list(stacks)
        prize_idx = 0
        equity = 0.0
        while len(remaining) > 1 and prize_idx < len(prizes):
            total_chips = sum(chips)
            draw = rng.random() * total_chips
            acc = 0.0
            picked_pos = len(remaining) - 1
            for pos, chip_count in enumerate(chips):
                acc += chip_count
                if draw < acc:
                    picked_pos = pos
                    break
            eliminated_player = remaining[picked_pos]
            if eliminated_player == player:
                equity += prizes[prize_idx]
            del remaining[picked_pos]
            del chips[picked_pos]
            prize_idx += 1
        # The last surviving player collects the final remaining prize.
        if remaining and prize_idx < len(prizes) and remaining[0] == player:
            equity += prizes[prize_idx]
        total += equity
    return total / num_simulations


def bubble_factor(
    stacks: Sequence[int],
    prizes: Sequence[float],
    player: int,
    *,
    all_in_amount: int | None = None,
) -> float:
    """Prize-equity "tournament insurance" quotient for risking the stack.

    Computes ``loss_if_busted / gain_if_doubled``: the equity a short stack
    loses by busting an all-in versus the equity it gains by calling and
    doubling (the call half of the pot coming out of the biggest opponent's
    stack). A value > 1 means risking your stack is negative tournament
    equity - the bubble squeeze. Uses exact ICM, so it is meant for the
    short/end-game stacks.
    """
    _validate(stacks, prizes, player)
    stack = stacks[player]
    risked = stack if all_in_amount is None else all_in_amount
    if risked < 0 or risked > stack:
        raise ValueError("all_in_amount must be in [0, stack]")
    if stack == 0:
        raise ValueError("cannot compute bubble factor for a busted player")

    eq_now = exact_icm_equity(stacks, prizes, player)

    # Win: player's stack grows by the risked amount, taken from the biggest
    # opponent (the one most able to pay the doubling pot).
    win = list(stacks)
    win[player] = stack + risked
    opponent = max((j for j in range(len(stacks)) if j != player), key=lambda j: stacks[j])
    win[opponent] = max(0, win[opponent] - risked)
    eq_win = exact_icm_equity(win, prizes, player)

    # Lose: bust to zero - eliminated, no prize (more players than paid places).
    lose = list(stacks)
    lose[player] = 0
    eq_bust = exact_icm_equity(lose, prizes, player)

    gain = eq_win - eq_now
    loss = eq_now - eq_bust
    if gain <= 1e-12:
        return float("inf")
    return loss / gain


def icm_call_ev(
    stacks: Sequence[int],
    prizes: Sequence[float],
    player: int,
    to_call: int,
    win_prob: float,
    pot_after_call: int,
) -> float:
    """Prize-equity expected value of calling vs. folding.

    Folding leaves the stack unchanged. Calling costs ``to_call`` chips: on a
    win the stack becomes ``S - to_call + pot_after_call`` (pot includes the
    call), on a loss it becomes ``S - to_call`` (possibly busted to 0). The EV
    difference is in **prize-equity** units, not chips - the correct tournament
    decision metric.
    """
    _validate(stacks, prizes, player)
    if not 0.0 <= win_prob <= 1.0:
        raise ValueError("win_prob must be in [0, 1]")
    s = stacks[player]
    if to_call < 0 or to_call > s:
        raise ValueError("to_call must be in [0, stack]")
    if pot_after_call < 0:
        raise ValueError("pot_after_call must be >= 0")

    fold_ev = exact_icm_equity(stacks, prizes, player)
    win_stack = list(stacks)
    win_stack[player] = s - to_call + pot_after_call
    lose_stack = list(stacks)
    lose_stack[player] = s - to_call

    call_ev = win_prob * exact_icm_equity(win_stack, prizes, player)
    call_ev += (1.0 - win_prob) * exact_icm_equity(lose_stack, prizes, player)
    return call_ev - fold_ev


def icm_decision(
    stacks: Sequence[int],
    prizes: Sequence[float],
    player: int,
    to_call: int,
    win_prob: float,
    pot_after_call: int,
) -> str:
    """Tournament decision rule: call when calling is positive prize equity."""
    return (
        "call"
        if icm_call_ev(stacks, prizes, player, to_call, win_prob, pot_after_call) >= 0.0
        else "fold"
    )
