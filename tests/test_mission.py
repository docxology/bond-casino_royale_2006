"""Tests for the BOND-API mission adapter (mission.py).

Verifies conformance to the frozen protocol, the full deterministic mission
flow, gadget registration, and discovery by slug. No mocks - the provider is
the real thing.
"""

from __future__ import annotations

from pathlib import Path

from bond_api.discovery import load_provider
from bond_api.protocol import (
    MissionProvider as Protocol,
)
from bond_api.protocol import (
    ReconRequest,
    run_mission,
)
from bond_api.registry import GadgetRegistry

from casino_royale_2006 import scenarios
from casino_royale_2006.mission import (
    GADGET_REGISTRY,
    MissionProvider,
    register_gadgets,
)

ROOT = Path(__file__).resolve().parent.parent


def test_provider_satisfies_protocol():
    provider = MissionProvider()
    assert isinstance(provider, Protocol)
    assert provider.film == "casino_royale_2006"


def test_brief_identity():
    brief = MissionProvider().brief()
    assert brief.film == "casino_royale_2006"
    assert brief.codename == "LE CHIFFRE"
    assert brief.objectives
    assert brief.assets and brief.constraints


def test_recon_reflects_goal():
    report = MissionProvider().recon(ReconRequest(goal="recover the stake"))
    labels = [f.label for f in report.findings]
    assert "objective" in labels
    assert any(f.detail == "recover the stake" for f in report.findings)


def test_plan_has_eight_engines():
    provider = MissionProvider()
    plan = provider.plan(provider.brief())
    assert {s.name for s in plan.steps} == {
        "poker",
        "cfr",
        "icm",
        "laundering",
        "network",
        "routes",
        "poison",
        "opponent",
    }


def test_execute_results_and_provenance():
    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))
    assert outcome.success is True
    assert outcome.results["film"] == "casino_royale_2006"
    assert outcome.results["codename"] == "LE CHIFFRE"
    assert set(outcome.results) >= {
        "poker",
        "laundering",
        "extraction",
        "poison",
        "cfr",
        "icm",
        "network",
        "opponent_bayes",
    }
    # Deepened internals expose the new concept outputs.
    assert outcome.results["cfr"]["avg_regret"] < 0.01
    assert outcome.results["icm"]["bubble_factor"] > 1.0
    assert outcome.results["network"]["launderer_flagged"] is True
    assert str(outcome.results["opponent_bayes"]["archetype"]).endswith("aggressive")
    assert outcome.provenance.seed == scenarios.SEED
    assert outcome.provenance.wall_time_s == 0.0
    assert outcome.provenance.input_hash


def test_execute_deterministic():
    provider = MissionProvider()
    plan = provider.plan(provider.brief())
    results_a = provider.execute(plan).results
    results_b = provider.execute(plan).results
    assert results_a == results_b


def test_debrief_lessons():
    provider = MissionProvider()
    outcome = provider.execute(provider.plan(provider.brief()))
    debrief = provider.debrief(outcome)
    assert debrief.outcome is outcome
    assert len(debrief.lessons) >= 4


def test_run_mission_full_flow():
    debrief = run_mission(MissionProvider(), ReconRequest(goal="neutralize Le Chiffre"))
    assert debrief.outcome.success
    assert debrief.outcome.results["steps_completed"] == 8


# ------------------------------------------------------------- gadgets -----
def test_gadget_registry_has_film_gadgets():
    assert GADGET_REGISTRY.contains("casino_royale_2006", "poker_equity_vs_range")
    gadgets = GADGET_REGISTRY.gadgets_for("casino_royale_2006")
    assert len(gadgets) == 11
    assert set(gadgets) >= {
        "chip_flow_detect",
        "network_laundering_risk",
        "poker_cfr_solve",
        "icm_exact_equity",
        "icm_bubble_factor",
        "bayesian_opponent",
        "poison_identify_sample",
        "parkour_shortest_path",
    }


def test_register_gadgets_on_fresh_registry():
    registry = GadgetRegistry()
    register_gadgets(registry)
    assert registry.lookup("casino_royale_2006", "poker_equity_vs_range") is not None
    assert registry.lookup("casino_royale_2006", "network_laundering_risk") is not None


# ----------------------------------------------------------- discovery -----
def test_load_provider_by_slug():
    provider = load_provider("casino_royale_2006", search_paths=[str(ROOT / "src")])
    assert provider.film == "casino_royale_2006"
    assert isinstance(provider, Protocol)
