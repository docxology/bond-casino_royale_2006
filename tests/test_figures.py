"""Tests for the manuscript figure renderers (figures/plotting.py).

Two layers, deliberately:

1. **Content** - every figure is built in-process and its *plotted data* is
   asserted against the engine values it claims to show (bar heights against
   the snapshot, curve points against ``toxicity_score``, regret trace against
   the CFR solve, bubble factors against ``icm.bubble_factor``), plus axis
   labels and titles. A plotting regression that still emits a valid PNG - the
   wrong series, a swapped axis, a dropped label - fails here.
2. **Artifact** - the PNG is written and decoded back with
   ``matplotlib.image.imread``, and the decoded pixels must not be uniform. A
   blank-but-non-empty PNG fails that check.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from matplotlib import image as mpimg

from casino_royale_2006 import icm, scenarios
from casino_royale_2006 import poison_detect as pd
from casino_royale_2006 import poker_cfr as pc
from casino_royale_2006.figures.plotting import (
    build_cfr_convergence_figure,
    build_digitalis_curve_figure,
    build_icm_bubble_figure,
    build_poker_decision_figure,
    render_cfr_convergence,
    render_digitalis_curve,
    render_icm_bubble,
    render_poker_decision,
)


def _assert_real_png(path: Path) -> None:
    """The file decodes as an image and is not a single flat colour."""
    assert path.is_file() and path.stat().st_size > 0
    pixels = mpimg.imread(path)
    assert pixels.ndim == 3 and pixels.shape[0] > 100 and pixels.shape[1] > 100
    flat = pixels.reshape(-1, pixels.shape[2])
    distinct = {tuple(row) for row in flat[::37]}
    assert len(distinct) > 1, "rendered PNG is a single flat colour"


# ------------------------------------------------------------- poker -------
def test_poker_decision_figure_plots_the_snapshot_values():
    snap = scenarios.poker_snapshot()
    fig = build_poker_decision_figure(snap)
    try:
        (ax,) = fig.axes
        heights = [bar.get_height() for bar in ax.patches]
        assert heights == [snap["equity_pct"], snap["break_even_pct"]]
        assert [t.get_text() for t in ax.get_xticklabels()] == [
            "hero equity",
            "pot-odds break-even",
        ]
        assert ax.get_ylabel() == "equity / price (%)"
        title = ax.get_title()
        assert str(snap["action"]) in title
        assert str(snap["board"]) in title
        assert str(snap["range"]) in title
    finally:
        fig.clf()


def test_poker_decision_figure_follows_a_different_snapshot():
    """The chart must track its input, not a hard-coded canonical scene."""
    other = dict(scenarios.poker_snapshot())
    other.update({"equity_pct": 12.5, "break_even_pct": 40.0, "margin_pct": -27.5})
    other["action"] = "fold"
    fig = build_poker_decision_figure(other)
    try:
        (ax,) = fig.axes
        assert [bar.get_height() for bar in ax.patches] == [12.5, 40.0]
        assert "fold" in ax.get_title()
    finally:
        fig.clf()


def test_render_poker_decision_writes_png(tmp_path: Path):
    out = tmp_path / "poker_decision.png"
    returned = render_poker_decision(out, scenarios.poker_snapshot())
    assert returned == str(out)
    _assert_real_png(out)


def test_render_poker_decision_default_snapshot(tmp_path: Path):
    out = tmp_path / "poker.png"
    render_poker_decision(out)  # defaults to canonical snapshot
    _assert_real_png(out)


# --------------------------------------------------------- digitalis ------
def test_digitalis_curve_plots_real_toxicity_scores():
    fig = build_digitalis_curve_figure()
    try:
        (ax,) = fig.axes
        (line,) = [ln for ln in ax.lines if len(ln.get_xdata()) > 2]
        xs, ys = list(line.get_xdata()), list(line.get_ydata())
        assert len(xs) == 121 and xs[0] == 0.0 and xs[-1] == pytest.approx(6.0)
        # Every plotted point must equal toxicity_score on the same panel.
        for conc, score in zip(xs, ys, strict=True):
            expected = pd.toxicity_score(
                pd.ToxPanel(
                    digoxin_ng_ml=conc,
                    heart_rate_bpm=74.0,
                    potassium_mmol_l=4.9,
                    pr_interval_ms=160.0,
                    symptoms=("nausea",),
                )
            )
            assert score == pytest.approx(expected)
        assert ax.get_xlabel() == "serum digoxin (ng/mL)"
        assert ax.get_ylabel() == "toxicity score"
        assert {t.get_text() for t in ax.get_legend().get_texts()} == {
            "none",
            "mild",
            "moderate",
            "severe",
        }
    finally:
        fig.clf()


def test_render_digitalis_curve_writes_png(tmp_path: Path):
    out = tmp_path / "digitalis_curve.png"
    returned = render_digitalis_curve(out)
    assert returned == str(out)
    _assert_real_png(out)


# --------------------------------------------------------------- cfr ------
def test_cfr_convergence_plots_the_real_regret_trace():
    fig = build_cfr_convergence_figure()
    try:
        (ax,) = fig.axes
        (line,) = ax.lines
        ys = list(line.get_ydata())
        expected = list(pc.cfr_solve(scenarios.CFR_STRENGTHS, 240).regret_trace)
        assert ys == pytest.approx(expected)
        assert list(line.get_xdata()) == list(range(1, len(expected) + 1))
        assert ax.get_yscale() == "log"
        assert ax.get_xlabel() == "CFR iteration"
        assert ys[-1] < ys[0]  # regret actually decays
    finally:
        fig.clf()


def test_render_cfr_convergence_writes_png(tmp_path: Path):
    out = tmp_path / "cfr_convergence.png"
    returned = render_cfr_convergence(out)
    assert returned == str(out)
    _assert_real_png(out)


# --------------------------------------------------------------- icm ------
def test_icm_bubble_figure_plots_real_bubble_factors():
    fig = build_icm_bubble_figure()
    try:
        (ax,) = fig.axes
        stacks = list(scenarios.ICM_STACKS)
        prizes = list(scenarios.ICM_PRIZES)
        expected = [icm.bubble_factor(stacks, prizes, i) for i in range(len(stacks))]
        heights = [bar.get_height() for bar in ax.patches]
        assert heights == pytest.approx(expected)
        assert [t.get_text() for t in ax.get_xticklabels()] == [str(s) for s in stacks]
        assert ax.get_ylabel() == "bubble factor (loss / gain)"
    finally:
        fig.clf()


def test_render_icm_bubble_writes_png(tmp_path: Path):
    out = tmp_path / "icm_bubble.png"
    returned = render_icm_bubble(out)
    assert returned == str(out)
    _assert_real_png(out)
