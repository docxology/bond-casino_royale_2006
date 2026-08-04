"""Tests for the manuscript figure renderers (figures/plotting.py).

Renders both figures in-process to a tmp dir and asserts real PNG output.
"""

from __future__ import annotations

from pathlib import Path

from casino_royale_2006 import scenarios
from casino_royale_2006.figures.plotting import (
    render_digitalis_curve,
    render_poker_decision,
)


def test_render_poker_decision_writes_png(tmp_path: Path):
    out = tmp_path / "poker_decision.png"
    returned = render_poker_decision(out, scenarios.poker_snapshot())
    assert returned == str(out)
    assert out.is_file() and out.stat().st_size > 0


def test_render_poker_decision_default_snapshot(tmp_path: Path):
    out = tmp_path / "poker.png"
    render_poker_decision(out)  # defaults to canonical snapshot
    assert out.is_file() and out.stat().st_size > 0


def test_render_digitalis_curve_writes_png(tmp_path: Path):
    out = tmp_path / "digitalis_curve.png"
    returned = render_digitalis_curve(out)
    assert returned == str(out)
    assert out.is_file() and out.stat().st_size > 0
