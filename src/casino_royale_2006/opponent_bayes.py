"""Bayesian opponent-archetype inference over observed actions.

:mod:`poker_engine`'s :class:`OpponentModel` is frequentist - it tallies
observations. This module upgrades the same concept to a proper Bayesian
model: each of the four archetypes (tight/loose x passive/aggressive) owns a
Dirichlet prior over the action distribution (raise/bet/call/fold), and the
agent's observed history updates a posterior over archetypes via the
Dirichlet-multinomial likelihood.

This directly deepens the film's "read Le Chiffre" problem: instead of a bare
aggression count, the agent gets a full posterior - *P(archetype | history)* -
plus leave-one-out-free predictive action probabilities and an expected
aggression rate, which downstream feed the range selection in ``poker_engine``.

The Dirichlet-multinomial likelihood is computed in exact log space with
``math.lgamma``; no approximation, no RNG, fully deterministic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

__all__ = [
    "ACTIONS",
    "ARCHETYPES",
    "ARCHETYPE_ALPHAS",
    "ARCHETYPE_PRIOR",
    "BayesianOpponentModel",
]

#: The four action types, fixed order (raise, bet, call, fold).
ACTIONS: tuple[str, ...] = ("raise", "bet", "call", "fold")

#: The four opponent archetypes.
ARCHETYPES: tuple[str, ...] = (
    "tight-passive",
    "tight-aggressive",
    "loose-passive",
    "loose-aggressive",
)

#: Prior probability that an unknown adversary is each archetype (uniform).
ARCHETYPE_PRIOR: dict[str, float] = {a: 1.0 / len(ARCHETYPES) for a in ARCHETYPES}

#: Dirichlet prior alpha (over raise/bet/call/fold) per archetype. Tight players
#: fold a lot and rarely raise; aggressive players raise/bet heavily; loose
#: players put money in with a wide range (high call) more often.
ARCHETYPE_ALPHAS: dict[str, tuple[float, float, float, float]] = {
    "tight-passive": (0.5, 1.0, 2.5, 4.0),
    "tight-aggressive": (3.0, 2.0, 1.5, 1.5),
    "loose-passive": (1.0, 1.5, 3.0, 2.5),
    "loose-aggressive": (3.5, 2.5, 2.0, 1.0),
}


@dataclass
class BayesianOpponentModel:
    """A running Bayesian model of one adversary's tendencies."""

    name: str
    history: tuple[str, ...] = field(default_factory=tuple)

    def update(self, action: str) -> None:
        """Record one observed action, appending to the evidence history."""
        key = action.strip().lower()
        if key not in ACTIONS:
            raise ValueError(f"unknown action {action!r}")
        self.history = (*self.history, key)

    def counts(self) -> dict[str, int]:
        """Per-action counts of the observed history."""
        return {action: self.history.count(action) for action in ACTIONS}

    def log_likelihood(self, archetype: str) -> float:
        """Log of the Dirichlet-multinomial likelihood of the history.

        ``ln L(alpha, c) = ln Gamma(sum alpha) - sum ln Gamma(alpha_i)
        + sum ln Gamma(alpha_i + c_i) - ln Gamma(sum alpha + sum c)``.
        """
        alpha = ARCHETYPE_ALPHAS[archetype]
        counts = self.counts()
        alpha_total = sum(alpha)
        count_total = sum(counts.values())
        value = math.lgamma(alpha_total) - sum(math.lgamma(a) for a in alpha)
        value += sum(
            math.lgamma(a + counts[action]) for action, a in zip(ACTIONS, alpha, strict=True)
        )
        value -= math.lgamma(alpha_total + count_total)
        return value

    def posterior(self) -> dict[str, float]:
        """Normalised posterior ``P(archetype | history)`` over all archetypes.

        Computed in log space (log-sum-exp stabilisation) so long histories
        never underflow the weights to zero.
        """
        log_weights = {a: math.log(ARCHETYPE_PRIOR[a]) + self.log_likelihood(a) for a in ARCHETYPES}
        max_log = max(log_weights.values())
        weights = {a: math.exp(lw - max_log) for a, lw in log_weights.items()}
        total = sum(weights.values())
        if total <= 0.0:
            return {a: 1.0 / len(ARCHETYPES) for a in ARCHETYPES}
        return {a: weights[a] / total for a in ARCHETYPES}

    def predictive(self, action: str) -> float:
        """Bayesian-model-averaged probability the adversary next plays ``action``.

        ``sum_a P(a | hist) * alpha_a[action] / sum(alpha_a)`` - the predictive
        distribution over the next action given everything observed so far.
        """
        if action not in ACTIONS:
            raise ValueError(f"unknown action {action!r}")
        post = self.posterior()
        total = 0.0
        for archetype, prob in post.items():
            alpha = ARCHETYPE_ALPHAS[archetype]
            idx = ACTIONS.index(action)
            total += prob * (alpha[idx] / sum(alpha))
        return total

    def map_archetype(self) -> str:
        """The maximum-a-posteriori archetype (ties break to first in order)."""
        post = self.posterior()
        best: str = ARCHETYPES[0]
        best_score = -1.0
        for archetype in ARCHETYPES:
            if post[archetype] > best_score:
                best_score = post[archetype]
                best = archetype
        return best

    def expected_aggression(self) -> float:
        """Bayesian expectation of the aggression rate (raises+bets)/actions.

        A value > 0.5 indicates an aggressive adversary (raises/bets dominate
        calls); near 0 indicates a passive one.
        """
        post = self.posterior()
        total = 0.0
        for archetype, prob in post.items():
            alpha = ARCHETYPE_ALPHAS[archetype]
            aggressive = alpha[0] + alpha[1]
            passive = alpha[2]
            total += prob * (aggressive / (aggressive + passive))
        return total
