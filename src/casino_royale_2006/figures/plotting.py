"""Deterministic figure renderers for the LE CHIFFRE manuscript.

Each renderer takes an explicit output path, draws a real engine-derived
figure, saves it, and closes the figure - no global pyplot state leaks between
calls. Backend is forced to ``Agg`` at import so rendering works headless and
deterministically in CI and on agents.

Figure set:

* :func:`render_poker_decision` - equity vs. pot-odds break-even for the final
  hand (the decision the whole casino finale turns on).
* :func:`render_digitalis_curve` - digitalis toxicity score vs. serum digoxin
  concentration with the none/mild/moderate/severe grade bands shaded (a
  drug-monogram-style dose-response used to explain the poison triage).
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import matplotlib

matplotlib.use("Agg")  # headless, deterministic - no display backend
import matplotlib.pyplot as plt

from casino_royale_2006 import poison_detect as pd
from casino_royale_2006 import scenarios


def render_poker_decision(
    output_path: str | Path,
    snapshot: dict[str, object] | None = None,
) -> str:
    """Bar chart of final-hand equity vs. pot-odds break-even, with the call.

    Reads equity/break-even/margin/action from ``snapshot`` (default: the
    canonical :func:`scenarios.poker_snapshot`). Writes ``output_path`` (PNG)
    and returns it as a string.
    """
    snap = snapshot if snapshot is not None else scenarios.poker_snapshot()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    equity = cast(float, snap["equity_pct"])
    break_even = cast(float, snap["break_even_pct"])
    margin = cast(float, snap["margin_pct"])
    labels = ("hero equity", "pot-odds break-even")
    values = (equity, break_even)
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    bars = ax.bar(labels, values, color=("#1e88e5", "#e53935"))
    ax.axhline(0.0, color="gray", lw=0.8)
    for bar, value in zip(bars, values, strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.5,
            f"{value:.1f}%",
            ha="center",
            va="bottom",
        )
    ax.set_ylabel("equity / price (%)")
    ax.set_ylim(0, max(max(values) * 1.2, 20))
    ax.set_title(
        f"Final hand {snap['hero']} vs {snap['range']} range on {snap['board']}\n"
        f"margin {margin:.1f}% -> {snap['action']}"
    )
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)


def render_digitalis_curve(output_path: str | Path) -> str:
    """Digitalis toxicity score vs. serum digoxin, with severity bands shaded.

    Sweeps digoxin ``0..6`` ng/mL under a neutral panel profile (normal cardiac
    signs, one mild symptom) so the concentration response cleanly traverses
    the none/mild/moderate bands; a genuinely severe panel additionally
    requires the cardiac feature flags, which the prose section explains.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    concentrations = [i / 20.0 for i in range(0, 121)]  # 0.0 .. 6.0
    scores = [
        pd.toxicity_score(
            pd.ToxPanel(
                digoxin_ng_ml=conc,
                heart_rate_bpm=74.0,
                potassium_mmol_l=4.9,
                pr_interval_ms=160.0,
                symptoms=("nausea",),
            )
        )
        for conc in concentrations
    ]

    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.axhspan(0.0, 1.0, color="#c8e6c9", alpha=0.5, label="none")
    ax.axhspan(1.0, 2.5, color="#fff59d", alpha=0.5, label="mild")
    ax.axhspan(2.5, 4.0, color="#ffcc80", alpha=0.5, label="moderate")
    ax.axhspan(4.0, 8.0, color="#ef9a9a", alpha=0.5, label="severe")
    ax.plot(concentrations, scores, color="#1e88e5", lw=2)
    ax.axvline(pd.TOXIC_CONC, color="#333", ls="--", lw=1)
    ax.axvline(pd.SEVERE_CONC, color="#333", ls=":", lw=1)
    ax.text(pd.TOXIC_CONC, 7.4, f"toxic {pd.TOXIC_CONC:g}", rotation=90, va="top")
    ax.text(pd.SEVERE_CONC, 7.8, f"severe {pd.SEVERE_CONC:g}", rotation=90, va="top")
    ax.set_xlabel("serum digoxin (ng/mL)")
    ax.set_ylabel("toxicity score")
    ax.set_ylim(0, 8)
    ax.set_title("Digitalis toxicity score vs. serum concentration")
    ax.legend(loc="upper left", fontsize="small")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return str(path)
