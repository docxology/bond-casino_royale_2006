"""Canonical LE CHIFFRE mission scenario + deterministic computed snapshots.

This module owns the *single* scenario the mission, the manuscript, and the
CLI all draw from, so a claim computed once is the claim shown everywhere
("never hand-author metrics in prose"). It stays pure stdlib and imports only
the eight domain cores (``poker_engine``, ``poker_cfr``, ``icm``,
``opponent_bayes``, ``laundering_detect``, ``laundering_network``,
``urban_routes``, ``poison_detect``) - bond-api is deliberately absent so
manuscript variable generation and the domain stay importable even if the path
dependency is missing.

Each ``*_snapshot`` runs the corresponding engine and returns a
JSON-serializable dict of real numbers (equity percentages, alert scores, route
costs, toxicity grades), which :mod:`mission` folds into its
``MissionOutcome.results`` and :mod:`manuscript_variables` turns into
``{{TOKEN}}``s.

Every snapshot takes the same ``seed`` argument so ``full_snapshot`` can drive
them uniformly. Three engines are *exactly* enumerated rather than sampled
(:func:`cfr_snapshot`, :func:`icm_snapshot`, :func:`bayes_snapshot`), so they
accept the seed for signature parity and legitimately ignore it - their output
is already seed-invariant. Each docstring states this explicitly.
"""

from __future__ import annotations

import random
from collections.abc import Sequence

from casino_royale_2006 import (
    icm,
)
from casino_royale_2006 import (
    laundering_detect as ld,
)
from casino_royale_2006 import (
    laundering_network as ln,
)
from casino_royale_2006 import (
    opponent_bayes as ob,
)
from casino_royale_2006 import (
    poison_detect as pd,
)
from casino_royale_2006 import (
    poker_cfr as pc,
)
from casino_royale_2006 import (
    poker_engine as pe,
)
from casino_royale_2006 import (
    urban_routes as ur,
)

#: Fixed determinism seed for every snapshot in this film.
SEED = 17

#: Canonical final-hand scenario. The opponent's range is *not* a constant: it
#: is selected from his observed action history (:data:`BAYES_HISTORY`) through
#: ``OpponentModel.archetype`` -> ``poker_engine.range_for_archetype``, which is
#: the whole point of carrying an opponent model.
POKER_HERO: tuple[str, str] = ("Kh", "Kc")
POKER_BOARD: tuple[str, str, str] = ("As", "7h", "2d")
POKER_RANGE_HANDS: int = 24
POKER_SIMULATIONS: int = 2400
POKER_POT: float = 5_000_000.0
POKER_TO_CALL: float = 1_000_000.0

#: Canonical opponent-action history observed of Le Chiffre (aggressive). It
#: feeds both the frequentist ``OpponentModel`` (range selection, above) and the
#: Bayesian archetype posterior (:func:`bayes_snapshot`).
BAYES_HISTORY: tuple[str, ...] = (
    "raise",
    "raise",
    "bet",
    "raise",
    "call",
    "raise",
    "bet",
    "raise",
    "raise",
    "raise",
)


def observed_opponent_model(name: str = "LeChiffre") -> pe.OpponentModel:
    """The frequentist tendency model built from :data:`BAYES_HISTORY`."""
    model = pe.OpponentModel(name=name)
    for action in BAYES_HISTORY:
        model.update(action)
    return model


#: The compound archetype the observed history implies, and the
#: :data:`poker_engine.RANGE_ARCHETYPES` key it selects. Both are derived, never
#: hand-set - change the history and these move with it.
POKER_OPPONENT_ARCHETYPE: str = observed_opponent_model().archetype()
POKER_RANGE_ARCHETYPE: str = pe.range_key_for_archetype(POKER_OPPONENT_ARCHETYPE)

#: Scenario dict (opaque payload used by the mission adapter/provenance hash).
POKER_SCENARIO: dict[str, object] = {
    "hero": POKER_HERO,
    "board": POKER_BOARD,
    "opponent_archetype": POKER_OPPONENT_ARCHETYPE,
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
#: The two objective functions the route planner is run under: (distance,
#: difficulty, risk) weights for "get there fast" and "don't get shot".
ROUTE_FAST_WEIGHTS: tuple[float, float, float] = (1.0, 0.3, 0.3)
ROUTE_SAFE_WEIGHTS: tuple[float, float, float] = (0.1, 0.4, 1.0)

#: Canonical poison scenario (a martini tray with one spiked glass).
POISON_N_SAMPLES = 5
POISON_INDEX = 3

#: Canonical CFR toy-game solve (discrete strengths x regret-matching sweeps).
CFR_STRENGTHS = 16
CFR_ITERATIONS = 300

#: Canonical tournament freezeout (the bubble): 4 players, 3 paid.
ICM_STACKS: tuple[int, int, int, int] = (4000, 3000, 1500, 500)
ICM_PRIZES: tuple[float, float, float] = (50.0, 30.0, 20.0)
ICM_PLAYER = 3  # the short stack on the bubble
ICM_TO_CALL = 400
ICM_WIN_PROB = 0.30
ICM_POT_AFTER_CALL = 1800


def poker_snapshot(seed: int = SEED) -> dict[str, object]:
    """Compute the final-hand equity, pot-odds price, and recommended action.

    The opponent's range and the raise threshold are both derived from his
    observed tendencies: ``OpponentModel.archetype()`` on :data:`BAYES_HISTORY`
    picks the :data:`poker_engine.RANGE_ARCHETYPES` range through
    :func:`poker_engine.range_for_archetype` and the ``raise_margin`` through
    :func:`poker_engine.recommended_raise_margin`.
    """
    rng = random.Random(seed)
    hero = pe.parse_cards(POKER_HERO)
    board = pe.parse_cards(POKER_BOARD)
    # `sorted`, not bare `tuple`: RANGE_ARCHETYPES values are frozensets, and
    # frozenset iteration order over strings depends on PYTHONHASHSEED. Bare
    # `tuple(...)` therefore fed `iter_opponent_hands` a different class order
    # in every process, and the published equity moved run to run (37.7-49.4%)
    # while the provenance input_hash stayed identical - a silent audit hole.
    opp_range = pe.range_for_archetype(POKER_OPPONENT_ARCHETYPE)
    opp_classes = tuple(sorted(opp_range))
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
    raise_margin = pe.recommended_raise_margin(POKER_OPPONENT_ARCHETYPE)
    break_even = pe.break_even_equity(pot, to_call)
    margin = pe.equity_margin(equity, pot, to_call)
    action = pe.recommend_action(pot, to_call, equity, raise_margin=raise_margin)
    return {
        "hero": "".join(POKER_HERO),
        "board": " ".join(POKER_BOARD),
        "range": POKER_RANGE_ARCHETYPE,
        "opponent_archetype": POKER_OPPONENT_ARCHETYPE,
        "range_classes": len(opp_range),
        "range_hands": POKER_RANGE_HANDS,
        "raise_margin_pct": round(raise_margin * 100.0, 2),
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

    The two routes are optimal under *different* objective functions
    (:data:`ROUTE_FAST_WEIGHTS` vs. :data:`ROUTE_SAFE_WEIGHTS`), so their own
    costs are in different units and are not comparable. Each route is therefore
    also re-priced under the *other* weighting (``*_under_*`` keys); those are
    the pairs a reader may legitimately compare.
    """
    graph = ur.build_city_quarter(seed, grid=ROUTE_GRID)
    profile = ur.ParkourProfile(max_climb=13.0, max_drop=13.0)
    fastest = graph.shortest_path(ROUTE_FROM, ROUTE_TO, profile, weights=ROUTE_FAST_WEIGHTS)
    safest = graph.shortest_path(ROUTE_FROM, ROUTE_TO, profile, weights=ROUTE_SAFE_WEIGHTS)
    if fastest is None or safest is None:  # pragma: no cover - grid is connected
        raise RuntimeError("canonical city quarter must be traversable under both objectives")
    return {
        "grid": ROUTE_GRID,
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "fast_weights": list(ROUTE_FAST_WEIGHTS),
        "safe_weights": list(ROUTE_SAFE_WEIGHTS),
        "fastest_cost": round(fastest[1], 2),
        "fastest_length": len(fastest[0]) - 1,
        "fastest_uses_roof": any(n.startswith("r") for n in fastest[0]),
        "safest_cost": round(safest[1], 2),
        "safest_length": len(safest[0]) - 1,
        "safest_uses_roof": any(n.startswith("r") for n in safest[0]),
        # Cross-priced: same route, other objective. These make the comparison
        # commensurable instead of juxtaposing two incomparable numbers.
        "safest_cost_under_fast": round(graph.path_cost(safest[2], ROUTE_FAST_WEIGHTS), 2),
        "fastest_cost_under_safe": round(graph.path_cost(fastest[2], ROUTE_SAFE_WEIGHTS), 2),
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


def cfr_snapshot(seed: int = SEED) -> dict[str, object]:
    """Solve the river toy game by CFR and report the equilibrium shape.

    The solve is fully enumerated (no RNG), so ``seed`` is accepted for
    signature parity with the sampled snapshots and does not affect the result.
    """
    result = pc.cfr_solve(CFR_STRENGTHS, CFR_ITERATIONS)
    profile = pc.betting_profile(result)
    return {
        "strengths": CFR_STRENGTHS,
        "iterations": CFR_ITERATIONS,
        "avg_regret": round(result.avg_regret, 4),
        "game_value": round(result.game_value, 4),
        "bluff_frequency": round(profile["bluff_frequency"], 4),
        "value_bet_frequency": round(profile["value_bet_frequency"], 4),
        "call_frequency": round(profile["call_frequency"], 4),
    }


def icm_snapshot(seed: int = SEED) -> dict[str, object]:
    """Report exact ICM equities, the bubble squeeze, and the tournament call decision.

    Uses the exact ICM recursion, so ``seed`` is accepted for signature parity
    with the sampled snapshots and does not affect the result.
    """
    stacks, prizes, player = ICM_STACKS, ICM_PRIZES, ICM_PLAYER
    equities = [round(icm.exact_icm_equity(stacks, prizes, i), 2) for i in range(len(stacks))]
    bubble = round(icm.bubble_factor(stacks, prizes, player), 3)
    leader_bubble = round(icm.bubble_factor(stacks, prizes, 0), 3)
    call_ev = round(
        icm.icm_call_ev(stacks, prizes, player, ICM_TO_CALL, ICM_WIN_PROB, ICM_POT_AFTER_CALL),
        3,
    )
    decision = icm.icm_decision(
        stacks, prizes, player, ICM_TO_CALL, ICM_WIN_PROB, ICM_POT_AFTER_CALL
    )
    return {
        "players": len(ICM_STACKS),
        "stacks": list(ICM_STACKS),
        "prizes": list(ICM_PRIZES),
        "equities": equities,
        "bubble_factor": bubble,
        "leader_bubble_factor": leader_bubble,
        "call_ev": call_ev,
        "decision": decision,
    }


def named_verdict(flagged: Sequence[str], name: str = LAUNDERER) -> bool:
    """Whether a *named* account is in a flagged set.

    This is the film-specific verdict rule, deliberately living here rather
    than in the film-agnostic :mod:`laundering_network`. It is a named function
    (not an inline expression) so a test can drive it with a flow whose flagged
    account is *somebody else* and prove it answers False there - the failure
    mode being guarded against is silently degrading this to
    ``bool(report.flagged)``, which would report "caught" for any flow that
    flags anyone at all.
    """
    return name in flagged


def network_snapshot(seed: int = SEED) -> dict[str, object]:
    """Run the structural (network-level) laundering detector on the canonical flow."""
    flow = ld.synthetic_flow(seed, num_players=LAUNDERING_PLAYERS, ticks=LAUNDERING_TICKS)
    report = ln.network_risk_report(flow)
    base = report.as_dict()
    top_centrality = (
        max(report.centrality, key=lambda p: report.centrality[p]) if report.centrality else ""
    )
    base.update(
        {
            # Named-suspect verdict, decided here rather than in the film-agnostic
            # network module: the launderer specifically, not "somebody".
            "launderer_flagged": named_verdict(report.flagged),
            "launderer_risk": round(report.risk.get(LAUNDERER, 0.0), 3),
            "launderer_hhi": round(report.hhi.get(LAUNDERER, 0.0), 3),
            "top_centrality_player": top_centrality,
        }
    )
    return base


def bayes_snapshot(seed: int = SEED) -> dict[str, object]:
    """Infer Le Chiffre's archetype posterior from his observed action history.

    The Dirichlet-multinomial posterior is computed in closed form, so ``seed``
    is accepted for signature parity and does not affect the result.
    """
    model = ob.BayesianOpponentModel(LAUNDERER, BAYES_HISTORY)
    posterior = model.posterior()
    return {
        "archetype": model.map_archetype(),
        "aggressive_posterior": round(
            posterior["tight-aggressive"] + posterior["loose-aggressive"], 3
        ),
        "predictive_raise": round(model.predictive("raise"), 3),
        "expected_aggression": round(model.expected_aggression(), 3),
    }


def full_snapshot(seed: int = SEED) -> dict[str, dict[str, object]]:
    """Compute all concept snapshots under a single seed."""
    return {
        "poker": poker_snapshot(seed),
        "laundering": laundering_snapshot(seed),
        "routes": route_snapshot(seed),
        "poison": poison_snapshot(seed),
        "cfr": cfr_snapshot(seed),
        "icm": icm_snapshot(seed),
        "network": network_snapshot(seed),
        "opponent_bayes": bayes_snapshot(seed),
    }
