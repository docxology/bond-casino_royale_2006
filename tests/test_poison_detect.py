"""Tests for digitalis poison triage (poison_detect.py).

Reference-range grading, Bayesian posterior, spiked-sample identification, and
antidote planning over real deterministic panels.
"""

from __future__ import annotations

import pytest

from casino_royale_2006 import poison_detect as pd


def test_tox_panel_validation():
    with pytest.raises(ValueError):
        pd.ToxPanel(-1.0, 60.0, 4.0, 150.0)  # negative digoxin
    pd.ToxPanel(1.0, 60.0, 4.0, 150.0)  # valid


def test_concentration_band_boundaries():
    assert pd.concentration_band(0.49) == 0
    assert pd.concentration_band(0.5) == 1
    assert pd.concentration_band(1.99) == 1
    assert pd.concentration_band(2.0) == 2
    assert pd.concentration_band(3.49) == 2
    assert pd.concentration_band(3.5) == 3


def test_toxicity_grade_of_clean_panel_is_none():
    clean = pd.ToxPanel(1.0, 72.0, 4.2, 150.0)
    assert pd.toxicity_grade(clean) == "none"
    assert pd.toxicity_score(clean) < 1.0


def test_toxicity_features_boost_grade():
    # Therapeutic concentration but bradycardia + hyperkalemia + PR prolong.
    panel = pd.ToxPanel(1.0, 52.0, 6.0, 220.0, symptoms=("nausea",))
    assert pd.toxicity_score(panel) >= 2.5  # mild -> moderate boundary territory
    assert pd.toxicity_grade(panel) in {"moderate", "severe"}


def test_toxicity_grade_severe():
    panel = pd.ToxPanel(
        4.2, 45.0, 6.3, 240.0, symptoms=("nausea", "vomiting", "visual_disturbance")
    )
    assert pd.toxicity_grade(panel) == "severe"
    assert pd.toxicity_score(panel) >= 4.0


def test_toxicity_grade_mild_from_concentration():
    # Band 2 only (no features) -> 1.5 -> mild
    assert pd.toxicity_grade(pd.ToxPanel(2.5, 70.0, 4.0, 150.0)) == "mild"


def test_posterior_toxicity_clean_equals_prior():
    clean = pd.ToxPanel(1.0, 72.0, 4.2, 150.0)
    assert pd.posterior_toxicity(clean) == pytest.approx(0.05)


def test_posterior_toxicity_high():
    toxic = pd.ToxPanel(4.0, 45.0, 6.3, 240.0)
    assert pd.posterior_toxicity(toxic) > 0.9


def test_posterior_toxicity_prior_edge():
    with pytest.raises(ValueError):
        pd.posterior_toxicity(pd.ToxPanel(1.0, 72.0, 4.2, 150.0), prior=1.5)
    # prior of 1.0 -> odds infinite -> posterior 1.0
    assert pd.posterior_toxicity(pd.ToxPanel(1.0, 72.0, 4.2, 150.0), prior=1.0) == 1.0


def test_identify_poisoned_sample():
    samples = pd.synthetic_panels(9, 4, poisoned_index=2)
    idx, panel, reason = pd.identify_poisoned_sample(samples)
    assert idx == 2
    assert panel.digoxin_ng_ml > 2.0
    assert "posterior" in reason


def test_identify_poisoned_sample_empty():
    with pytest.raises(ValueError):
        pd.identify_poisoned_sample(())


def test_identify_poisoned_sample_high_conc_tiebreak():
    # Two tox panels, one higher concentration -> picks the higher one even if
    # both are already toxic.
    low = pd.ToxPanel(2.5, 72.0, 4.2, 150.0)
    high = pd.ToxPanel(5.0, 72.0, 4.2, 150.0)
    idx, _panel, _reason = pd.identify_poisoned_sample((high, low))
    assert idx == 0


def test_antidote_plan_severe_includes_fab():
    panel = pd.ToxPanel(4.5, 45.0, 6.5, 240.0)
    plan = pd.antidote_plan(panel)
    assert any("Fab" in p for p in plan)
    assert any("atropine" in p for p in plan)
    assert any("hyperkalemia" in p for p in plan)
    assert any("telemetry" in p for p in plan)


def test_antidote_plan_atropine_threshold():
    # HR 40 -> atropine even though grade may be mild/moderate
    panel = pd.ToxPanel(2.5, 40.0, 4.0, 150.0)
    plan = pd.antidote_plan(panel)
    assert any("atropine" in p for p in plan)


def test_antidote_plan_supportive_when_benign():
    panel = pd.ToxPanel(1.2, 75.0, 4.0, 150.0)
    plan = pd.antidote_plan(panel)
    assert any("supportive" in p for p in plan)
    assert any("telemetry" in p for p in plan)


def test_synthetic_panels_deterministic_and_poisoned():
    s1 = pd.synthetic_panels(11, 5, poisoned_index=3)
    s2 = pd.synthetic_panels(11, 5, poisoned_index=3)
    assert s1 == s2
    assert len(s1) == 5
    assert s1[3].digoxin_ng_ml > 2.0  # poisoned
    assert all(p.digoxin_ng_ml <= 2.0 for i, p in enumerate(s1) if i != 3)
