"""Manuscript ``{{TOKEN}}`` hydration for the LE CHIFFRE mission manuscript.

Token values come from ``manuscript/config.yaml`` (identity) plus **live
engine computations** via :mod:`scenarios` - never hand-authored numbers in
prose. The module is pure (stdlib + pyyaml) and deliberately does **not** import
bond-api, so manuscript generation works even if the path dependency is absent.

The produced mapping is written to ``output/data/manuscript_variables.json``
by ``scripts/z_generate_manuscript_variables.py``; the live cross-reference
test over ``manuscript/[0-9]*.md`` guarantees every ``{{TOKEN}}`` referenced
in a prose section exists in this mapping.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from casino_royale_2006 import __version__, scenarios

#: The pure domain concept modules (source of the printed concept tokens).
CONCEPT_MODULES: tuple[str, ...] = (
    "poker_engine",
    "poker_cfr",
    "icm",
    "opponent_bayes",
    "laundering_detect",
    "laundering_network",
    "urban_routes",
    "poison_detect",
)


def project_root() -> Path:
    """Absolute path to this package's repository root (three levels up)."""
    return Path(__file__).resolve().parent.parent.parent


def load_mission_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load ``manuscript/config.yaml`` (defaults to this project's config)."""
    path = Path(config_path) if config_path else project_root() / "manuscript" / "config.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"mission config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        raise ValueError(f"mission config must be a mapping: {path}")
    return loaded


def _fmt(value: Any) -> str:
    """Render a snapshot value as a compact stable string for a token."""
    if isinstance(value, float):
        return f"{value:g}"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (list, tuple)):
        return ", ".join(_fmt(v) for v in value)
    return str(value)


def generate_variables(
    config_path: str | Path | None = None,
    now: datetime | None = None,
) -> dict[str, str]:
    """Compute the full mission ``{{TOKEN}}`` mapping.

    Args:
        config_path: override path to ``manuscript/config.yaml``.
        now: explicit timestamp override for ``GENERATION_TIMESTAMP`` (keeps
            tests deterministic); defaults to the current UTC time.

    Returns:
        A ``{TOKEN: value}`` mapping, every value a string.
    """
    config = load_mission_config(config_path)
    snap = scenarios.full_snapshot(scenarios.SEED)
    poker = snap["poker"]
    cfr = snap["cfr"]
    icm = snap["icm"]
    laundering = snap["laundering"]
    network = snap["network"]
    routes = snap["routes"]
    poison = snap["poison"]
    opponent = snap["opponent_bayes"]

    stamp = now if now is not None else datetime.now(timezone.utc)
    variables: dict[str, str] = {
        # identity (from config.yaml)
        "MISSION_TITLE": str(config.get("title", "")),
        "MISSION_SUBTITLE": str(config.get("subtitle", "")),
        "MISSION_VERSION": str(config.get("version", __version__)),
        "MISSION_IDENTITY": str(config.get("film", "casino_royale_2006")),
        "MISSION_CODENAME": str(config.get("codename", "LE CHIFFRE")),
        "MISSION_KEYWORDS": ", ".join(map(str, config.get("keywords", []))),
        "CONCEPT_MODULES": ", ".join(CONCEPT_MODULES),
        "NUM_CONCEPT_MODULES": str(len(CONCEPT_MODULES)),
        "PYTHON_VERSION": f"{sys.version_info.major}.{sys.version_info.minor}",
        "GENERATION_TIMESTAMP": stamp.isoformat(timespec="seconds"),
        # poker
        "POKER_HERO": str(poker["hero"]),
        "POKER_BOARD": str(poker["board"]),
        "POKER_RANGE": str(poker["range"]),
        "POKER_EQUITY_PCT": _fmt(poker["equity_pct"]),
        "POKER_BREAK_EVEN_PCT": _fmt(poker["break_even_pct"]),
        "POKER_MARGIN_PCT": _fmt(poker["margin_pct"]),
        "POKER_ACTION": str(poker["action"]),
        "POKER_POT": _fmt(poker["pot"]),
        "POKER_TO_CALL": _fmt(poker["to_call"]),
        # laundering
        "LAUNDER_PLAYERS": _fmt(laundering["num_players"]),
        "LAUNDER_TRANSACTIONS": _fmt(laundering["num_transactions"]),
        "LAUNDER_ALERTS": _fmt(laundering["num_alerts"]),
        "LAUNDER_FLAGGED": _fmt(laundering["launderer_flagged"]),
        "LAUNDER_SCORE": _fmt(laundering["launderer_score"]),
        # extraction routes
        "ROUTE_GRID": _fmt(routes["grid"]),
        "ROUTE_NODES": _fmt(routes["nodes"]),
        "ROUTE_EDGES": _fmt(routes["edges"]),
        "ROUTE_FASTEST_COST": _fmt(routes["fastest_cost"]),
        "ROUTE_FASTEST_ROOF": _fmt(routes["fastest_uses_roof"]),
        "ROUTE_SAFEST_COST": _fmt(routes["safest_cost"]),
        # poison
        "POISON_SAMPLES": _fmt(poison["num_samples"]),
        "POISON_SPIKED_INDEX": _fmt(poison["spiked_index"]),
        "POISON_DIGOXIN": _fmt(poison["digoxin_ng_ml"]),
        "POISON_HEART_RATE": _fmt(poison["heart_rate_bpm"]),
        "POISON_POTASSIUM": _fmt(poison["potassium_mmol_l"]),
        "POISON_GRADE": str(poison["toxicity_grade"]),
        "POISON_POSTERIOR": _fmt(poison["posterior"]),
        # cfr
        "CFR_STRENGTHS": _fmt(cfr["strengths"]),
        "CFR_ITERATIONS": _fmt(cfr["iterations"]),
        "CFR_AVG_REGRET": _fmt(cfr["avg_regret"]),
        "CFR_GAME_VALUE": _fmt(cfr["game_value"]),
        "CFR_BLUFF_FREQ": _fmt(cfr["bluff_frequency"]),
        "CFR_VALUE_BET_FREQ": _fmt(cfr["value_bet_frequency"]),
        "CFR_CALL_FREQ": _fmt(cfr["call_frequency"]),
        # icm
        "ICM_PLAYERS": _fmt(icm["players"]),
        "ICM_DECISION": str(icm["decision"]),
        "ICM_CALL_EV": _fmt(icm["call_ev"]),
        "ICM_BUBBLE_FACTOR": _fmt(icm["bubble_factor"]),
        "ICM_LEADER_BUBBLE_FACTOR": _fmt(icm["leader_bubble_factor"]),
        # network
        "NET_COMMUNITIES": _fmt(network["num_communities"]),
        "NET_TOP_CENTRALITY": str(network["top_centrality_player"]),
        "NET_FLAGGED": _fmt(bool(network["flagged"])),
        "NET_LAUNDERER_RISK": _fmt(network["launderer_risk"]),
        "NET_LAUNDERER_HHI": _fmt(network["launderer_hhi"]),
        # opponent bayes
        "BAYES_ARCHETYPE": str(opponent["archetype"]),
        "BAYES_AGGRESSIVE_POSTERIOR": _fmt(opponent["aggressive_posterior"]),
        "BAYES_PREDICTIVE_RAISE": _fmt(opponent["predictive_raise"]),
        "BAYES_EXPECTED_AGGRESSION": _fmt(opponent["expected_aggression"]),
    }
    return variables


def resolve_manuscript_tree(
    variables: dict[str, str],
    manuscript_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> tuple[Path, int, list[str]]:
    """Substitute ``{{TOKEN}}`` in each ``[0-9]*.md`` prose section.

    Writes resolved copies to ``output_dir`` (one per source section) and
    returns ``(output_dir, files_written, unresolved_tokens)``. Unresolved
    tokens are reported but not fatal so early drafts can be inspected; the
    strict gate lives in the tests.
    """
    src_dir = Path(manuscript_dir) if manuscript_dir else project_root() / "manuscript"
    out_dir = Path(output_dir) if output_dir else project_root() / "output" / "manuscript"
    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    unresolved: list[str] = []
    for section in sorted(src_dir.glob("[0-9]*.md")):
        text = section.read_text(encoding="utf-8")
        for token, value in variables.items():
            text = text.replace(f"{{{{{token}}}}}", value)
        left_over = _find_tokens(text)
        unresolved.extend(left_over)
        out_dir.joinpath(section.name).write_text(text, encoding="utf-8")
        written += 1
    return out_dir, written, unresolved


def _find_tokens(text: str) -> list[str]:
    """Return the sorted list of ``{{...}}`` placeholders still left in ``text``."""
    found: set[str] = set()
    start = 0
    while True:
        begin = text.find("{{", start)
        if begin < 0:
            break
        end = text.find("}}", begin)
        if end < 0:
            break
        found.add(text[begin + 2 : end].strip())
        start = end + 2
    return sorted(found)
