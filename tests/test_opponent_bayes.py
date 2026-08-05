"""Tests for Bayesian opponent-archetype inference (opponent_bayes.py)."""

from __future__ import annotations

import pytest

from casino_royale_2006 import opponent_bayes as ob


def test_update_and_counts():
    model = ob.BayesianOpponentModel("x")
    for a in ("raise", "call", "fold"):
        model.update(a)
    assert model.history == ("raise", "call", "fold")
    assert model.counts()["raise"] == 1
    assert model.counts()["fold"] == 1
    with pytest.raises(ValueError):
        model.update("allin")


def test_posterior_sums_to_one_and_prior_flat():
    empty = ob.BayesianOpponentModel("e")
    post = empty.posterior()
    assert sum(post.values()) == pytest.approx(1.0)
    assert post["tight-passive"] == pytest.approx(0.25)
    assert empty.map_archetype() == "tight-passive"  # tie -> first archetype


def test_raise_heavy_history_favours_aggressive():
    model = ob.BayesianOpponentModel("LC")
    for _ in range(8):
        model.update("raise")
    for _ in range(2):
        model.update("bet")
    post = model.posterior()
    aggressive = post["tight-aggressive"] + post["loose-aggressive"]
    passive = post["tight-passive"] + post["loose-passive"]
    assert aggressive > passive
    assert model.map_archetype() in {"tight-aggressive", "loose-aggressive"}
    assert model.expected_aggression() > 0.5


def test_passive_history_favours_passive():
    model = ob.BayesianOpponentModel("p")
    for _ in range(8):
        model.update("fold")
    for _ in range(2):
        model.update("call")
    passive = model.posterior()["tight-passive"] + model.posterior()["loose-passive"]
    assert passive > 0.5
    assert model.expected_aggression() < 0.5


def test_log_likelihood_discriminates_archetypes():
    model = ob.BayesianOpponentModel("m")
    for _ in range(10):
        model.update("raise")
    aggressive_like = model.log_likelihood("tight-aggressive") + model.log_likelihood(
        "loose-aggressive"
    )
    passive_like = model.log_likelihood("tight-passive") + model.log_likelihood("loose-passive")
    assert aggressive_like > passive_like


def test_predictive_distribution_sums_to_one_and_shapes():
    model = ob.BayesianOpponentModel("q")
    for _ in range(6):
        model.update("raise")
    predictive = {a: model.predictive(a) for a in ob.ACTIONS}
    assert sum(predictive.values()) == pytest.approx(1.0)
    assert predictive["raise"] > predictive["fold"]
    with pytest.raises(ValueError):
        model.predictive("allin")


def test_expected_aggression_range():
    model = ob.BayesianOpponentModel("r")
    for _ in range(10):
        model.update("call")
    assert 0.0 <= model.expected_aggression() <= 1.0
