"""LE CHIFFRE - the Casino Royale (2006) mission provider (BOND-API adapter).

This is the thin adapter that binds this film package to the frozen ``bond_api``
protocol (THE PROTOCOL). It implements :class:`MissionProvider` and registers
this film's gadgets with :class:`bond_api.registry.GadgetRegistry`.

Discovery contract (see ``bond_api.discovery``): the orchestrator imports
``<slug>.mission`` and expects a top-level ``MissionProvider`` class whose
``film`` equals the slug. ``film`` is declared here as ``casino_royale_2006``.

The heavy lifting lives in the pure domain cores (``poker_engine``,
``poker_cfr``, ``icm``, ``opponent_bayes``, ``laundering_detect``,
``laundering_network``, ``urban_routes``, ``poison_detect``) and the shared
``scenarios`` snapshot. ``execute`` calls each engine once (fixed seed) and
folds the real, computed results into ``MissionOutcome.results`` with full
provenance. Nothing here is a stub; the numbers are live engine output.
"""

from __future__ import annotations

import hashlib

from bond_api.protocol import (
    Asset,
    Constraint,
    Debrief,
    Finding,
    MissionBrief,
    MissionOutcome,
    MissionPlan,
    Provenance,
    ReconReport,
    ReconRequest,
    Step,
)
from bond_api.registry import GadgetRegistry

from casino_royale_2006 import __version__ as _mission_pkg_version
from casino_royale_2006 import icm, scenarios
from casino_royale_2006.laundering_detect import detect
from casino_royale_2006.laundering_network import network_risk_report
from casino_royale_2006.opponent_bayes import BayesianOpponentModel
from casino_royale_2006.poison_detect import identify_poisoned_sample
from casino_royale_2006.poker_cfr import cfr_solve
from casino_royale_2006.poker_engine import equity_vs_range
from casino_royale_2006.urban_routes import MobilityGraph, ParkourProfile, build_city_quarter

__all__ = ["GADGET_REGISTRY", "MissionProvider", "register_gadgets"]

_PACKAGE_VERSION = "0.1.0"
_FILM = "casino_royale_2006"
_CODENAME = "LE CHIFFRE"


def _input_hash() -> str:
    """Deterministic fingerprint of the canonical scenario (no wall clock)."""
    payload = (
        f"{_FILM}|{_mission_pkg_version}|"
        f"{scenarios.POKER_SCENARIO['hero']}|{scenarios.LAUNDERER}|"
        f"{scenarios.ROUTE_GRID}|{scenarios.POISON_N_SAMPLES}|"
        f"{scenarios.CFR_STRENGTHS}|{scenarios.ICM_STACKS}|{scenarios.ICM_PLAYER}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


class MissionProvider:
    """Deterministic LE CHIFFRE mission provider for the BOND-API protocol.

    The five lifecycle stages (`brief -> recon -> plan -> execute -> debrief`)
    are fully deterministic: every engine runs under the fixed ``scenarios.SEED``
    with a caller-seeded RNG, and provenance records no wall-clock dependence.
    """

    film = _FILM

    def brief(self) -> MissionBrief:
        """Declare the four-concept LE CHIFFRE mission and its constraints."""
        return MissionBrief(
            film=self.film,
            codename=_CODENAME,
            objectives=(
                "counter-play Le Chiffre at the high-stakes felt (pot odds + "
                "equity against his range)",
                "solve the river toy game by CFR to a near-Nash profile (game theory)",
                "price tournament survival with the Independent Chip Model (ICM)",
                "trace the chip flows funding the game and flag laundering "
                "(behavioural + network-level)",
                "plan an extraction route across the parkour city (ground/roof)",
                "triage the spiked martini and identify the digitalis source",
                "infer Le Chiffre's archetype posterior from his observed actions",
            ),
            assets=(
                Asset(kind="scenario", name="final-hand", payload=dict(scenarios.POKER_SCENARIO)),
                Asset(kind="scenario", name="chip-flow", payload={"seed": scenarios.SEED}),
                Asset(
                    kind="scenario", name="extraction-route", payload={"grid": scenarios.ROUTE_GRID}
                ),
                Asset(
                    kind="scenario",
                    name="martini-tray",
                    payload={"samples": scenarios.POISON_N_SAMPLES},
                ),
            ),
            constraints=(
                Constraint(
                    kind="determinism",
                    detail="fixed seed, seeded RNG, zero wall-clock in provenance",
                ),
                Constraint(
                    kind="purity", detail="domain cores import no bond-api and no infrastructure"
                ),
            ),
        )

    def recon(self, request: ReconRequest) -> ReconReport:
        """Survey the request and the fixed intel picture of Le Chiffre's operation."""
        return ReconReport(
            findings=(
                Finding(label="objective", detail=request.goal),
                Finding(
                    label="target", detail="Le Chiffre, the cipher behind the Casino Royale stake"
                ),
                Finding(
                    label="capital",
                    detail="the game is funded by laundered chip flows tracked by the detector",
                ),
                Finding(
                    label="terrain",
                    detail="a parkour city with ground streets and leapable rooftops",
                ),
                Finding(
                    label="threat",
                    detail="a poisoned martini carrying cardiac glycoside (digitalis)",
                ),
                Finding(
                    label="constraint",
                    detail="full determinism required; results must be auditable",
                ),
            )
        )

    def plan(self, brief: MissionBrief) -> MissionPlan:
        """Plan one deterministic step per concept engine."""
        return MissionPlan(
            steps=(
                Step(name="poker", action="equity_vs_range", params={"range": "tight"}),
                Step(
                    name="cfr",
                    action="solve_river_toy",
                    params={"strengths": scenarios.CFR_STRENGTHS},
                ),
                Step(name="icm", action="price_bubble", params={"player": scenarios.ICM_PLAYER}),
                Step(
                    name="laundering",
                    action="detect_chip_flow",
                    params={"scenario_seed": scenarios.SEED},
                ),
                Step(name="network", action="network_laundering_risk", params={}),
                Step(
                    name="routes", action="plan_extraction", params={"grid": scenarios.ROUTE_GRID}
                ),
                Step(
                    name="poison",
                    action="triage_martini",
                    params={"samples": scenarios.POISON_N_SAMPLES},
                ),
                Step(name="opponent", action="infer_archetype", params={}),
            )
        )

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        """Run each engine under the fixed seed and fold real results into the outcome."""
        snap = scenarios.full_snapshot(scenarios.SEED)
        poker = snap["poker"]
        cfr = snap["cfr"]
        icm_snap = snap["icm"]
        laundering = snap["laundering"]
        network = snap["network"]
        routes = snap["routes"]
        poison = snap["poison"]
        opponent = snap["opponent_bayes"]
        results: dict[str, object] = {
            "film": _FILM,
            "codename": _CODENAME,
            "steps_completed": len(plan.steps),
            "poker": {
                "hero": poker["hero"],
                "board": poker["board"],
                "equity_pct": poker["equity_pct"],
                "break_even_pct": poker["break_even_pct"],
                "margin_pct": poker["margin_pct"],
                "action": poker["action"],
            },
            "cfr": {
                "avg_regret": cfr["avg_regret"],
                "game_value": cfr["game_value"],
                "bluff_frequency": cfr["bluff_frequency"],
                "value_bet_frequency": cfr["value_bet_frequency"],
            },
            "icm": {
                "bubble_factor": icm_snap["bubble_factor"],
                "leader_bubble_factor": icm_snap["leader_bubble_factor"],
                "equities": icm_snap["equities"],
                "decision": icm_snap["decision"],
            },
            "laundering": {
                "num_transactions": laundering["num_transactions"],
                "num_alerts": laundering["num_alerts"],
                "launderer_flagged": laundering["launderer_flagged"],
                "launderer_score": laundering["launderer_score"],
                "alert_players": laundering["alert_players"],
            },
            "network": {
                "launderer_flagged": network["launderer_flagged"],
                "launderer_risk": network["launderer_risk"],
                "launderer_hhi": network["launderer_hhi"],
                "num_communities": network["num_communities"],
                "top_centrality_player": network["top_centrality_player"],
            },
            "extraction": {
                "fastest_cost": routes["fastest_cost"],
                "fastest_uses_roof": routes["fastest_uses_roof"],
                "safest_cost": routes["safest_cost"],
                "nodes": routes["nodes"],
            },
            "poison": {
                "spiked_index": poison["spiked_index"],
                "digoxin_ng_ml": poison["digoxin_ng_ml"],
                "heart_rate_bpm": poison["heart_rate_bpm"],
                "toxicity_grade": poison["toxicity_grade"],
                "posterior": poison["posterior"],
            },
            "opponent_bayes": {
                "archetype": opponent["archetype"],
                "aggressive_posterior": opponent["aggressive_posterior"],
                "predictive_raise": opponent["predictive_raise"],
                "expected_aggression": opponent["expected_aggression"],
            },
        }
        return MissionOutcome(
            success=True,
            results=results,
            provenance=Provenance(
                package_version=_PACKAGE_VERSION,
                seed=scenarios.SEED,
                input_hash=_input_hash(),
                wall_time_s=0.0,
            ),
        )

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        """Summarize the outcome and record the film's standing lessons."""
        return Debrief(
            outcome=outcome,
            lessons=(
                "the price the pot lays must clear the break-even equity - Le Chiffre "
                "counts on opponents calling without the odds",
                "CFR shows the river toy equilibrium is polar: bet the top and bluff "
                "the bottom, call with the middle - the shape, not the exact cards",
                "ICM prices survival: on the bubble a short stack's risk of busting "
                "costs more prize equity than doubling up gains",
                "chip structuring shows up as a velocity + small-leg signature across "
                "the movement graph, and as value-neutral churn in the network layer",
                "the fastest escape is over the rooftops, but the safest is on the "
                "ground when risk is priced",
                "digitalis is triaged by serum concentration plus cardiac signs; "
                "Fab fragments are the definitive antidote for severe toxicity",
                "Bayesian opponent inference beats a bare count: a raise-heavy history "
                "concentrates posterior mass on aggressive archetypes",
            ),
        )


def register_gadgets(registry: GadgetRegistry) -> None:
    """Register this film's callable gadgets with a ``bond_api`` gadget registry."""
    registry.register(
        _FILM,
        {
            "poker_equity_vs_range": equity_vs_range,
            "poker_cfr_solve": cfr_solve,
            "icm_exact_equity": icm.exact_icm_equity,
            "icm_bubble_factor": icm.bubble_factor,
            "chip_flow_detect": detect,
            "network_laundering_risk": network_risk_report,
            "parkour_shortest_path": MobilityGraph.shortest_path,
            "parkour_build_city_quarter": build_city_quarter,
            "parkour_profile": ParkourProfile,
            "poison_identify_sample": identify_poisoned_sample,
            "bayesian_opponent": BayesianOpponentModel,
        },
    )


#: Module-level registry, populated at import so coordinators can `lookup`
#: gadgets for this film without instantiating the provider.
GADGET_REGISTRY = GadgetRegistry()
register_gadgets(GADGET_REGISTRY)
