"""Digitalis (foxglove) poison detection (Bond's spiked martini).

In *Casino Royale* Le Chiffre's people lace Bond's martini with digitalis -
the cardiac glycoside family (digoxin/digitoxin) with a famously narrow
therapeutic index. This module is the clinical-forensics triage the agent
runs on a suspected exposure: from a tox panel (digoxin serum concentration,
heart rate, serum potassium, ECG PR interval, reported symptoms) it returns a
deterministic toxicity grade, a Bayesian posterior probability of toxicity, a
forensic ``identify_poisoned_sample`` that picks the spiked drink out of a
group, and an antidote plan.

The reference ranges (therapeutic 0.5-2.0 ng/mL digoxin; toxicity above ~2.0,
severe above ~3.5; bradycardia < 60 bpm; hyperkalemia > 5.5 mmol/L; prolonged
PR > 200 ms) follow standard cardiac-glycoside toxicology references and are
declared as module constants so the manuscript ``claim_ledger.yaml`` can point
at them. Likelihood ratios are deliberately modest, documented heuristics on
the same published signs, not clinical claims.

Pure stdlib; the seeded :func:`synthetic_panels` generator supports tests and
manuscript vignettes deterministically.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

#: Digoxin serum concentration describing a normal therapeutic range (ng/mL).
THERAPEUTIC_LOW = 0.5
#: Concentration above which toxicity risk clearly rises (ng/mL).
TOXIC_CONC = 2.0
#: Concentration above which toxicity is severe / life-threatening (ng/mL).
SEVERE_CONC = 3.5
#: Heart rate below which bradycardia is flagged (bpm).
BRADYCARDIA_BPM = 60.0
#: Serum potassium above which hyperkalemia is flagged (mmol/L).
HYPERKALEMIA_MMOL = 5.5
#: PR interval above which first-degree AV block is flagged (ms).
PR_LONG_MS = 200.0

#: Likelihood ratios for the toxicity signs (documented heuristics).
TOXICITY_LR = {
    "concentration": 12.0,
    "bradycardia": 3.0,
    "hyperkalemia": 4.0,
    "pr_prolongation": 2.5,
}


@dataclass(frozen=True)
class ToxPanel:
    """A patient's digitalis tox panel. All fields are non-negative."""

    digoxin_ng_ml: float
    heart_rate_bpm: float
    potassium_mmol_l: float
    pr_interval_ms: float
    symptoms: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for label, value in (
            ("digoxin_ng_ml", self.digoxin_ng_ml),
            ("heart_rate_bpm", self.heart_rate_bpm),
            ("potassium_mmol_l", self.potassium_mmol_l),
            ("pr_interval_ms", self.pr_interval_ms),
        ):
            if value < 0:
                raise ValueError(f"{label} must be >= 0")


def concentration_band(ng_ml: float) -> int:
    """Map a digoxin concentration to a severity band 0..3.

    ``0`` = sub/non-therapeutic (< 0.5), ``1`` = therapeutic (0.5-2.0),
    ``2`` = toxic (2.0-3.5), ``3`` = severe (>= 3.5).
    """
    if ng_ml < THERAPEUTIC_LOW:
        return 0
    if ng_ml < TOXIC_CONC:
        return 1
    if ng_ml < SEVERE_CONC:
        return 2
    return 3


def _feature_score(panel: ToxPanel) -> tuple[bool, bool, bool]:
    brady = panel.heart_rate_bpm < BRADYCARDIA_BPM
    hyperk = panel.potassium_mmol_l > HYPERKALEMIA_MMOL
    pr_long = panel.pr_interval_ms > PR_LONG_MS
    return brady, hyperk, pr_long


def toxicity_score(panel: ToxPanel) -> float:
    """Composite deterministic toxicity score (drives the grade).

    Contribution: ``max(0, band - 1) * 1.5`` from concentration plus +1 for
    each of bradycardia / hyperkalemia / PR prolongation, plus 0.5 per symptom
    (capped at +1.5). The scale is [0, ~7.5].
    """
    band = concentration_band(panel.digoxin_ng_ml)
    conc = max(0, band - 1) * 1.5
    brady, hyperk, pr_long = _feature_score(panel)
    symptoms = min(len(panel.symptoms), 3) * 0.5
    return round(
        conc + int(brady) + int(hyperk) + int(pr_long) + symptoms,
        3,
    )


def toxicity_grade(panel: ToxPanel) -> str:
    """Return ``"none"``, ``"mild"``, ``"moderate"``, or ``"severe"``.

    Thresholds on :func:`toxicity_score`: < 1.0 none, < 2.5 mild, < 4.0
    moderate, >= 4.0 severe. A clean therapeutic panel scores 0 -> ``none``.
    """
    score = toxicity_score(panel)
    if score < 1.0:
        return "none"
    if score < 2.5:
        return "mild"
    if score < 4.0:
        return "moderate"
    return "severe"


def posterior_toxicity(panel: ToxPanel, prior: float = 0.05) -> float:
    """Bayesian posterior probability of clinically significant toxicity.

    Converts the prior into odds, multiplies by the likelihood ratio of each
    present sign (concentration above toxic, bradycardia, hyperkalemia, PR
    prolongation), then converts back to a probability. Deterministic given
    the panel and prior.
    """
    if not 0.0 <= prior <= 1.0:
        raise ValueError("prior must be in [0, 1]")
    odds = prior / (1.0 - prior) if prior < 1.0 else float("inf")
    if concentration_band(panel.digoxin_ng_ml) >= 2:
        odds *= TOXICITY_LR["concentration"]
    brady, hyperk, pr_long = _feature_score(panel)
    if brady:
        odds *= TOXICITY_LR["bradycardia"]
    if hyperk:
        odds *= TOXICITY_LR["hyperkalemia"]
    if pr_long:
        odds *= TOXICITY_LR["pr_prolongation"]
    if odds == float("inf"):
        return 1.0
    return odds / (1.0 + odds)


def identify_poisoned_sample(
    samples: tuple[ToxPanel, ...],
) -> tuple[int, ToxPanel, str]:
    """Pick the spiked drink from a group by highest posterior toxicity.

    Returns ``(index, panel, reason)``. Among equal posterior maxima the
    highest raw digoxin concentration breaks the tie (then the lowest index),
    keeping the result deterministic.
    """
    if not samples:
        raise ValueError("samples must not be empty")
    best_idx = 0
    best_post = -1.0
    best_conc = -1.0
    for i, panel in enumerate(samples):
        post = posterior_toxicity(panel)
        if (post, panel.digoxin_ng_ml, -i) > (best_post, best_conc, -best_idx):
            best_idx, best_post, best_conc = i, post, panel.digoxin_ng_ml
    return (
        best_idx,
        samples[best_idx],
        f"highest posterior toxicity {best_post:.3f} at digoxin {best_conc:.2f} ng/mL",
    )


def antidote_plan(panel: ToxPanel) -> tuple[str, ...]:
    """Deterministic intervention list for a tox panel.

    Severe toxicity -> digoxin-specific Fab antibody fragments; marked
    bradycardia -> atropine; dangerous hyperkalemia -> potassium management.
    Any non-trivial finding carries the patient onto cardiac telemetry.
    """
    grade = toxicity_grade(panel)
    plan: list[str] = []
    if grade == "severe" or panel.digoxin_ng_ml >= SEVERE_CONC:
        plan.append("digoxin-specific Fab antibody fragments (Digibind)")
    if panel.heart_rate_bpm < 50:
        plan.append("atropine for bradycardia")
    if panel.potassium_mmol_l > 6.0:
        plan.append("hyperkalemia management (insulin/glucose + serial labs)")
    if not plan:
        plan.append("supportive care + serial digoxin levels")
    plan.append("continuous ECG + telemetry monitoring")
    return tuple(plan)


def synthetic_panels(
    seed: int,
    n: int,
    *,
    poisoned_index: int | None = None,
    poisoned_ng_range: tuple[float, float] = (3.0, 6.0),
) -> tuple[ToxPanel, ...]:
    """Deterministically generate ``n`` tox panels, optionally one poisoned.

    Healthy panels sit inside the therapeutic window with unremarkable vitals.
    The panel at ``poisoned_index`` (when given) carries a toxic digoxin
    concentration, bradycardia, hyperkalemia, a prolonged PR interval and the
    classic symptoms - the shape :func:`identify_poisoned_sample` should pick.
    """
    rng = random.Random(seed)
    samples: list[ToxPanel] = []
    for i in range(n):
        poisoned = poisoned_index is not None and i == poisoned_index
        if poisoned:
            samples.append(
                ToxPanel(
                    digoxin_ng_ml=rng.uniform(*poisoned_ng_range),
                    heart_rate_bpm=rng.uniform(38.0, 52.0),
                    potassium_mmol_l=rng.uniform(5.6, 6.8),
                    pr_interval_ms=rng.uniform(205.0, 260.0),
                    symptoms=("nausea", "vomiting", "visual_disturbance", "bradycardia"),
                )
            )
        else:
            samples.append(
                ToxPanel(
                    digoxin_ng_ml=rng.uniform(0.6, 1.8),
                    heart_rate_bpm=rng.uniform(62.0, 92.0),
                    potassium_mmol_l=rng.uniform(3.6, 5.0),
                    pr_interval_ms=rng.uniform(140.0, 190.0),
                )
            )
    return tuple(samples)
