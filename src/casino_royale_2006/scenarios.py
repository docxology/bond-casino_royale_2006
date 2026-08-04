"""Canonical LE CHIFFRE mission scenario + deterministic computed snapshots.

This module owns the *single* scenario the mission, the manuscript, and the
CLI all draw from, so a claim computed once is the claim shown everywhere
("never hand-author metrics in prose"). It stays pure stdlib and imports only
the four domain cores - bond-api is deliberately absent so manuscript variable
generation and the domain stay importable even if the path dependency is
missing.

Each ``*_snapshot`` runs the corresponding engine with a fixed seed and
returns a JSON-serializable dict of real numbers (equity percentages, alert
scores, route costs, toxicity grades), which :mod:`mission` folds into its
``MissionOutcome.results`` and :mod:`manuscript_variables` turns into
``{{TOKEN}}``s.
"""

from __future__ import annotations

import random

from casino_royale_2006 import (
    laundering_detect as ld,
)
from casino_royale_2006 import (
    poison_detect as pd,
)
from casino_royale_2006 import (
    poker_engine as pe,
)
from casino_royale_2006 import (
    urban_routes as ur,
)

#: Fixed determinism seed for every snapshot in this film.
SEED = 17

#: Canonical final-hand scenario (generic hero vs. Le Chiffre's tight range).
POKER_HERO: tuple[str, str] = ("Kh", "Kc")
POKER_BOARD: tuple[str, str, str] = ("As", "7h", "2d")
POKER_RANGE_ARCHETYPE: str = "tight"
POKER_RANGE_HANDS: int = 24
POKER_SIMULATIONS: int = 2400
POKER_POT: float = 5_000_000.0
POKER_TO_CALL: float = 1_000_000.0

#: Scenario dict (opaque payload used by the mission adapter/provenance hash).
POKER_SCENARIO: dict[str, object] = {
    "hero": POKER_HERO,
    "board": POKER_BOARD,
    "range_archetype": POKER_RANGE_ARCHETYPE,
    "range_hands": POKER_RANGE_HANDS,
    "simulations": POKER_SIMULATIONS,
    "pot": POKER_POT,
    "to_call": POKER_TO_CALL,
}

#: Canonical laundering scenario seed (one planted smurfer, ``LeChiffre``).
LAUNDERING_PLAYERS = 8
LAUNDERING_TICKS = 30
LAUNDERER = "LeChiffre"

#: Canonical extraction-route city quarter (ground vs. rooftop).
ROUTE_GRID = 6
ROUTE_FROM = "g0_0"
ROUTE_TO = "g5_5"

#: Canonical poison scenario (a martini tray with one spiked glass).
POISON_N_SAMPLES = 5
POISON_INDEX = 3


def poker_snapshot(seed: int = SEED) -> dict[str, object]:
    """Compute the final-hand equity, pot-odds price, and recommended action."""
    rng = random.Random(seed)
    hero = pe.parse_cards(POKER_HERO)
    board = pe.parse_cards(POKER_BOARD)
    opp_classes = tuple(pe.RANGE_ARCHETYPES[POKER_RANGE_ARCHETYPE])
    dead = set(hero) | set(board)
    opp_hands = list(pe.iter_opponent_hands(opp_classes, dead, rng, count=POKER_RANGE_HANDS))
    equity = pe.equity_vs_range(
        hero,
        opp_hands,
        board,
        num_simulations=POKER_SIMULATIONS,
        rng=rng,
    )
    pot = POKER_POT
    to_call = POKER_TO_CALL
    break_even = pe.break_even_equity(pot, to_call)
    margin = pe.equity_margin(equity, pot, to_call)
    action = pe.recommend_action(pot, to_call, equity)
    return {
        "hero": "".join(POKER_HERO),
        "board": " ".join(POKER_BOARD),
        "range": POKER_RANGE_ARCHETYPE,
        "equity_pct": round(equity * 100.0, 2),
        "break_even_pct": round(break_even * 100.0, 2),
        "margin_pct": round(margin * 100.0, 2),
        "action": action,
        "pot": pot,
        "to_call": to_call,
    }


def laundering_snapshot(seed: int = SEED) -> dict[str, object]:
    """Run chip-flow detection and report whether the planted smurfer is caught."""
    flow = ld.synthetic_flow(seed, num_players=LAUNDERING_PLAYERS, ticks=LAUNDERING_TICKS)
    alerts = ld.detect(flow)
    launderer_alert = next((a for a in alerts if a.player == LAUNDERER), None)
    return {
        "num_players": LAUNDERING_PLAYERS,
        "num_transactions": len(flow),
        "num_alerts": len(alerts),
        "launderer": LAUNDERER,
        "launderer_flagged": launderer_alert is not None,
        "launderer_score": launderer_alert.score if launderer_alert else 0.0,
        "alert_players": [a.player for a in alerts],
    }


def route_snapshot(seed: int = SEED) -> dict[str, object]:
    """Compare the fastest (rooftop) vs. safest (ground) extraction routes.

    The agent is profiled as a skilled free-runner (can climb the 12 m parapet
    and drop off the roof), so the fastest route legitimately shortcuts
    rooftops while the risk-priced route stays on the ground.
    """
    graph = ur.build_city_quarter(seed, grid=ROUTE_GRID)
    profile = ur.ParkourProfile(max_climb=13.0, max_drop=13.0)
    fastest = graph.shortest_path(ROUTE_FROM, ROUTE_TO, profile, weights=(1.0, 0.3, 0.3))
    safest = graph.shortest_path(ROUTE_FROM, ROUTE_TO, profile, weights=(0.1, 0.4, 1.0))
    return {
        "grid": ROUTE_GRID,
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "fastest_cost": round(fastest[1], 2) if fastest else None,
        "fastest_length": len(fastest[0]) - 1 if fastest else None,
        "fastest_uses_roof": any(n.startswith("r") for n in fastest[0]) if fastest else False,
        "safest_cost": round(safest[1], 2) if safest else None,
        "safest_length": len(safest[0]) - 1 if safest else None,
        "safest_uses_roof": any(n.startswith("r") for n in safest[0]) if safest else False,
    }


def poison_snapshot(seed: int = SEED) -> dict[str, object]:
    """Triage the martini tray and identify the single spiked glass."""
    samples = pd.synthetic_panels(seed, POISON_N_SAMPLES, poisoned_index=POISON_INDEX)
    idx, panel, reason = pd.identify_poisoned_sample(samples)
    grade = pd.toxicity_grade(panel)
    return {
        "num_samples": POISON_N_SAMPLES,
        "spiked_index": idx,
        "expected_index": POISON_INDEX,
        "digoxin_ng_ml": round(panel.digoxin_ng_ml, 2),
        "heart_rate_bpm": round(panel.heart_rate_bpm, 1),
        "potassium_mmol_l": round(panel.potassium_mmol_l, 2),
        "toxicity_grade": grade,
        "posterior": round(pd.posterior_toxicity(panel), 3),
        "reason": reason,
    }


def full_snapshot(seed: int = SEED) -> dict[str, dict[str, object]]:
    """Compute all four concept snapshots under a single seed."""
    return {
        "poker": poker_snapshot(seed),
        "laundering": laundering_snapshot(seed),
        "routes": route_snapshot(seed),
        "poison": poison_snapshot(seed),
    }
