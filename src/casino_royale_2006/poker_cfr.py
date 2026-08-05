"""Counterfactual regret minimization (CFR) on a river toy game.

CFR is the workhorse equilibrium-finding algorithm behind modern poker AI
(Zinkevich et al., 2007). This module solves a classic *river toy game* —
heads-up, both players ante 1, out-of-position player (P1) checks or bets 1,
in-position player (P2) folds or calls — with discrete hand strengths drawn
uniformly and independently. It returns a near-Nash strategy profile by
iteratively minimising counterfactual regret.

Why a toy game: full no-limit hold'em has ~10^18 information sets; the toy
game is the smallest imperfect-information game that still exhibits the real
strategic structure — P1 must bet a *value* range and a *bluff* range, and P2
must call with a bluff-catching range — and CFR solves it exactly, so the
equilibrium shape is verifiable in tests.

Determinism: the whole game is enumerated (no sampling, no RNG) and all
iteration orders are fixed, so repeated solves are byte-identical.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = [
    "ACTIONS_P1",
    "ACTIONS_P2",
    "CFRResult",
    "betting_profile",
    "cfr_solve",
]

#: P1 (out of position) actions, in order.
ACTIONS_P1: tuple[str, ...] = ("check", "bet")
#: P2 (in position, facing a bet) actions, in order.
ACTIONS_P2: tuple[str, ...] = ("fold", "call")

_EPSILON = 1e-12


class _InfoSet:
    """Regret-matched decision node for one player-hand pair."""

    __slots__ = ("cumulative", "num_actions", "reach_sum", "regrets", "strategy")

    def __init__(self, num_actions: int) -> None:
        self.num_actions = num_actions
        self.regrets: list[float] = [0.0] * num_actions
        self.strategy: list[float] = [1.0 / num_actions] * num_actions
        self.cumulative: list[float] = [0.0] * num_actions
        self.reach_sum: float = 0.0

    def update_strategy(self) -> None:
        """Regret matching: play each action in proportion to positive regret."""
        positive = [max(r, 0.0) for r in self.regrets]
        total = sum(positive)
        if total <= _EPSILON:
            self.strategy = [1.0 / self.num_actions] * self.num_actions
        else:
            self.strategy = [p / total for p in positive]

    def accumulate(self, reach: float) -> None:
        """Weight the current strategy into the average (reach-weighted)."""
        self.reach_sum += reach
        for i in range(self.num_actions):
            self.cumulative[i] += reach * self.strategy[i]

    def average_strategy(self) -> tuple[float, ...]:
        """The reach-weighted average strategy over all iterations."""
        if self.reach_sum <= _EPSILON:
            return tuple(1.0 / self.num_actions for _ in range(self.num_actions))
        return tuple(c / self.reach_sum for c in self.cumulative)


def _showdown_pot2(h1: int, h2: int) -> float:
    """P1 net payoff of a check-down showdown (pot 2 from antes)."""
    if h1 > h2:
        return 1.0
    if h1 < h2:
        return -1.0
    return 0.0


def _showdown_pot4(h1: int, h2: int) -> float:
    """P1 net payoff of a called-bet showdown (pot 4)."""
    if h1 > h2:
        return 2.0
    if h1 < h2:
        return -2.0
    return 0.0


@dataclass(frozen=True)
class CFRResult:
    """The solved toy game: average strategy profile plus convergence data.

    ``p1_strategy`` / ``p2_strategy`` map each action name to the per-strength
    probability tuple (index 0 = weakest hand). ``avg_regret`` is the final
    average positive counterfactual regret (lower = closer to Nash); a value
    under ~1e-2 indicates a good approximation on this toy game.
    """

    num_strengths: int
    iterations: int
    p1_strategy: dict[str, tuple[float, ...]] = field(default_factory=dict)
    p2_strategy: dict[str, tuple[float, ...]] = field(default_factory=dict)
    avg_regret: float = 0.0
    regret_trace: tuple[float, ...] = field(default_factory=tuple)
    game_value: float = 0.0


def cfr_solve(num_strengths: int = 16, iterations: int = 300) -> CFRResult:
    """Solve the river toy game by CFR.

    Args:
        num_strengths: size of the discrete hand grid (uniform prior).
        iterations: number of full CFR sweeps.

    Returns:
        A :class:`CFRResult` with the average strategy, the final average
        regret, the regret trace, and the game value under the average
        profile (P1's expected payoff).
    """
    if num_strengths < 2:
        raise ValueError("num_strengths must be >= 2")
    if iterations < 1:
        raise ValueError("iterations must be >= 1")

    n = num_strengths
    chance = 1.0 / n
    p1 = [_InfoSet(2) for _ in range(n)]
    p2 = [_InfoSet(2) for _ in range(n)]
    trace: list[float] = []

    for _t in range(1, iterations + 1):
        for node in p1:
            node.update_strategy()
        for node in p2:
            node.update_strategy()

        # Reach-weighted average-strategy accumulation (uniform chance hands).
        for h1 in range(n):
            p1[h1].accumulate(chance)
        for h2 in range(n):
            p2_reach = chance * sum(p1[h1].strategy[1] for h1 in range(n))
            p2[h2].accumulate(p2_reach)

        # P1 counterfactual regrets.
        for h1 in range(n):
            cfu_check = sum(chance * _showdown_pot2(h1, h2) for h2 in range(n))
            cfu_bet = sum(
                chance * (p2[h2].strategy[0] * 1.0 + p2[h2].strategy[1] * _showdown_pot4(h1, h2))
                for h2 in range(n)
            )
            sigma = p1[h1].strategy
            cfu_current = sigma[0] * cfu_check + sigma[1] * cfu_bet
            p1[h1].regrets[0] += cfu_check - cfu_current
            p1[h1].regrets[1] += cfu_bet - cfu_current

        # P2 counterfactual regrets (only reachable when P1 bets).
        for h2 in range(n):
            cfu_fold = sum(chance * p1[h1].strategy[1] * -1.0 for h1 in range(n))
            cfu_call = sum(chance * p1[h1].strategy[1] * _showdown_pot4(h2, h1) for h1 in range(n))
            sigma = p2[h2].strategy
            cfu_current = sigma[0] * cfu_fold + sigma[1] * cfu_call
            p2[h2].regrets[0] += cfu_fold - cfu_current
            p2[h2].regrets[1] += cfu_call - cfu_current

        total_positive = sum(max(r, 0.0) for node in p1 for r in node.regrets)
        total_positive += sum(max(r, 0.0) for node in p2 for r in node.regrets)
        trace.append(total_positive / (2 * n * 2 * _t))

    p1_strategy: dict[str, tuple[float, ...]] = {}
    for action, i in (("check", 0), ("bet", 1)):
        p1_strategy[action] = tuple(p1[h].average_strategy()[i] for h in range(n))
    p2_strategy: dict[str, tuple[float, ...]] = {}
    for action, i in (("fold", 0), ("call", 1)):
        p2_strategy[action] = tuple(p2[h].average_strategy()[i] for h in range(n))

    # Game value for P1 under the average profile.
    value = 0.0
    for h1 in range(n):
        for h2 in range(n):
            pr = chance * chance
            value += pr * (
                p1_strategy["check"][h1] * _showdown_pot2(h1, h2)
                + p1_strategy["bet"][h1]
                * (p2_strategy["fold"][h2] * 1.0 + p2_strategy["call"][h2] * _showdown_pot4(h1, h2))
            )

    return CFRResult(
        num_strengths=n,
        iterations=iterations,
        p1_strategy=p1_strategy,
        p2_strategy=p2_strategy,
        avg_regret=trace[-1],
        regret_trace=tuple(trace),
        game_value=value,
    )


def betting_profile(result: CFRResult) -> dict[str, float]:
    """Compact equilibrium shape: bluff/value bet frequencies and call range.

    Returns ``{"bluff_frequency", "value_bet_frequency", "call_frequency",
    "fold_frequency"}`` - the bet probability at the weakest strength, at the
    strongest strength, and P2's call/fold probabilities at the median
    strength. These are the interpretable numbers the manuscript reports.
    """
    n = result.num_strengths
    return {
        "bluff_frequency": result.p1_strategy["bet"][0],
        "value_bet_frequency": result.p1_strategy["bet"][n - 1],
        "call_frequency": result.p2_strategy["call"][n // 2],
        "fold_frequency": result.p2_strategy["fold"][n // 2],
    }
