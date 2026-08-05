"""Tests for manuscript token hydration (manuscript_variables.py)."""

from __future__ import annotations

import time

import pytest
import yaml

from casino_royale_2006 import laundering_network as ln
from casino_royale_2006 import manuscript_variables as mv
from casino_royale_2006 import poker_engine as pe
from casino_royale_2006 import scenarios
from casino_royale_2006.laundering_detect import ChipTransaction, synthetic_flow


def _wait_for_wall_clock_tick(limit_s: float = 2.0) -> None:
    """Block until the wall clock's whole-second field advances.

    Bounded by ``limit_s`` so a frozen clock fails the caller's assertion
    rather than hanging the suite.
    """
    start = time.time()
    while int(time.time()) == int(start):
        if time.time() - start > limit_s:  # pragma: no cover - clock never froze
            raise AssertionError("wall clock did not advance")
        time.sleep(0.02)


def test_load_mission_config_default():
    config = mv.load_mission_config()
    assert config["film"] == "casino_royale_2006"
    assert config["codename"] == "LE CHIFFRE"


def test_load_mission_config_missing():
    with pytest.raises(FileNotFoundError):
        mv.load_mission_config("/no/such/config.yaml")


def test_load_mission_config_non_mapping(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("- item\n- other\n", encoding="utf-8")
    with pytest.raises(ValueError):
        mv.load_mission_config(bad)


def test_generate_variables_keys_and_types():
    variables = mv.generate_variables()
    for key in (
        "MISSION_TITLE",
        "MISSION_CODENAME",
        "POKER_EQUITY_PCT",
        "LAUNDER_FLAGGED",
        "ROUTE_FASTEST_ROOF",
        "POISON_GRADE",
        "CONCEPT_MODULES",
        "NUM_CONCEPT_MODULES",
        "MANUSCRIPT_DATE",
    ):
        assert key in variables
        assert isinstance(variables[key], str)


def test_manuscript_date_comes_from_the_committed_config():
    """The publication stamp is read from config.yaml, not from the clock."""
    config = mv.load_mission_config()
    assert mv.generate_variables()["MANUSCRIPT_DATE"] == config["publication"]["date"]


def test_manuscript_date_tracks_an_edited_config(tmp_path):
    """Change the committed date, and the token changes with it.

    Without this, ``MANUSCRIPT_DATE`` could be a hardcoded literal that happens
    to equal the config value; here the config is the only thing that moves.
    """
    config = mv.load_mission_config()
    config["publication"]["date"] = "1953-04-13"  # Fleming's Casino Royale, first edition
    edited = tmp_path / "config.yaml"
    edited.write_text(yaml.safe_dump(config), encoding="utf-8")
    assert mv.generate_variables(config_path=edited)["MANUSCRIPT_DATE"] == "1953-04-13"


@pytest.mark.parametrize(
    "publication",
    [
        None,
        {},
        {"date": ""},
        {"date": "2026/08/05"},
        {"date": "August 5, 2026"},
        "not-a-mapping",
    ],
)
def test_manuscript_date_rejects_a_missing_or_malformed_stamp(publication):
    config: dict = {"title": "x"}
    if publication is not None:
        config["publication"] = publication
    with pytest.raises(ValueError, match=r"publication\.date"):
        mv.manuscript_date(config)


def test_generate_variables_is_a_pure_function_of_committed_inputs():
    """Two calls straddling a wall-clock tick must produce an equal mapping.

    The straddle is the point. ``generate_variables()`` used to stamp
    ``datetime.now(timezone.utc)`` at second resolution, so two back-to-back
    calls inside the same second compared equal and a naive repeat-call test
    passed while the artifacts on disk changed hourly. Waiting for the clock's
    seconds field to advance is the condition that made that version fail.
    """
    first = mv.generate_variables()
    _wait_for_wall_clock_tick()
    second = mv.generate_variables()
    assert first == second


def test_project_root_exists():
    assert mv.project_root().is_dir()


def test_all_manuscript_tokens_are_generated():
    """Every {{TOKEN}} referenced in a numbered prose section must exist."""
    variables = mv.generate_variables()
    prose = sorted((mv.project_root() / "manuscript").glob("[0-9]*.md"))
    assert prose, "expected numbered manuscript sections"
    for section in prose:
        for token in mv._find_tokens(section.read_text(encoding="utf-8")):
            assert token in variables, f"unresolved token {token!r} in {section.name}"


def test_fmt_renders_large_money_without_scientific_notation():
    """A five-million-chip pot must not print as "5e+06" in the manuscript."""
    assert mv._fmt(5_000_000.0) == "5,000,000"
    assert mv._fmt(1_000_000.0) == "1,000,000"
    # Below the separator threshold, compact %g is kept.
    assert mv._fmt(1500.0) == "1500"
    assert mv._fmt(0.981) == "0.981"
    assert mv._fmt(True) == "yes"
    assert mv._fmt(False) == "no"
    assert mv._fmt([1, 2.5, "x"]) == "1, 2.5, x"


def test_money_tokens_are_readable_in_the_live_mapping():
    variables = mv.generate_variables()
    for key in ("POKER_POT", "POKER_TO_CALL"):
        assert "e+" not in variables[key], f"{key} rendered in scientific notation"


def test_find_malformed_tokens_catches_single_braces():
    """The detector must fire on {NAME} and stay silent on {{NAME}}."""
    assert mv.find_malformed_tokens("core of {NUM_CONCEPT_MODULES} modules") == [
        "NUM_CONCEPT_MODULES"
    ]
    assert mv.find_malformed_tokens("core of {{NUM_CONCEPT_MODULES}} modules") == []
    # Lower-case braces are ordinary prose (e.g. set notation), not tokens.
    assert mv.find_malformed_tokens("the set {cash_in, cash_out}") == []
    # Both forms present: only the broken one is reported.
    assert mv.find_malformed_tokens("{{GOOD}} and {BAD}") == ["BAD"]


def test_no_manuscript_section_uses_a_single_brace_token():
    """Regression gate: {TOKEN} renders its own braces into the published PDF.

    It also slips past ``test_all_manuscript_tokens_are_generated``, which only
    scans for ``{{...}}`` - which is exactly how a broken
    ``{NUM_CONCEPT_MODULES}`` reached ``output/manuscript/01_introduction.md``.
    """
    prose = sorted((mv.project_root() / "manuscript").glob("[0-9]*.md"))
    assert prose, "expected numbered manuscript sections"
    offenders: dict[str, list[str]] = {}
    for section in prose:
        bad = mv.find_malformed_tokens(section.read_text(encoding="utf-8"))
        if bad:
            offenders[section.name] = bad
    assert not offenders, f"single-brace tokens (use {{{{NAME}}}}): {offenders}"


def test_gadget_tokens_track_the_real_catalogue():
    """NUM_GADGETS must be derived from the catalogue, never hand-written."""
    from casino_royale_2006 import gadgets

    variables = mv.generate_variables()
    assert variables["NUM_GADGETS"] == str(len(gadgets.GADGET_NAMES))
    assert variables["GADGET_NAMES"] == ", ".join(gadgets.GADGET_NAMES)
    assert int(variables["NUM_GADGETS"]) > 0


def test_concept_module_tokens_match_the_shipped_modules():
    """Every named concept module must exist on disk under src/."""
    variables = mv.generate_variables()
    src = mv.project_root() / "src" / "casino_royale_2006"
    named = [name.strip() for name in variables["CONCEPT_MODULES"].split(",")]
    assert len(named) == int(variables["NUM_CONCEPT_MODULES"])
    for module in named:
        assert (src / f"{module}.py").is_file(), f"{module}.py named in tokens but missing"


def test_net_flagged_token_is_a_named_verdict_not_merely_any_flagged():
    """NET_FLAGGED must mean "LeChiffre was flagged", not "somebody was".

    The previous version of this gate compared the token against the same
    snapshot function that produced it, so it could not fail. This drives the
    *production* verdict rule (``scenarios.named_verdict``, the exact callable
    ``network_snapshot`` uses) with a negative control: a flow whose only
    flagged account is somebody else. There ``any_flagged`` is True while the
    named verdict is False. Degrade the rule to ``bool(report.flagged)`` - the
    laundering this token invites - and the negative control goes red.
    """
    ghost_flow = (
        ChipTransaction("cage", "ghost", 10_000.0, 0, "cash_in"),
        ChipTransaction("ghost", "cage", 10_000.0, 1, "cash_out"),
    )
    ghost_report = ln.network_risk_report(ghost_flow)
    assert ghost_report.as_dict()["any_flagged"] is True  # somebody was flagged
    assert scenarios.named_verdict(ghost_report.flagged) is False  # ...but not him

    # On the canonical flow the same rule answers True, and that - not
    # any_flagged - is what the published token carries.
    canonical = ln.network_risk_report(
        synthetic_flow(
            scenarios.SEED,
            num_players=scenarios.LAUNDERING_PLAYERS,
            ticks=scenarios.LAUNDERING_TICKS,
        )
    )
    assert scenarios.named_verdict(canonical.flagged) is True
    assert mv.generate_variables()["NET_FLAGGED"] == "yes"


def test_poker_range_tokens_are_derived_from_the_real_range_table():
    """POKER_RANGE_CLASSES must count the shipped range, never a prose numeral.

    The manuscript once claimed 169 canonical hand classes (the size of the
    full hold'em starting-hand space) for a table that enumerates far fewer.
    This binds the token to ``RANGE_ARCHETYPES`` itself.
    """
    variables = mv.generate_variables()
    archetype = variables["POKER_OPPONENT_ARCHETYPE"]
    selected = pe.range_for_archetype(archetype)
    assert variables["POKER_RANGE"] == pe.range_key_for_archetype(archetype)
    assert variables["POKER_RANGE_CLASSES"] == str(len(selected))
    assert int(variables["POKER_RANGE_CLASSES"]) < 169  # not the full class space
    assert variables["POKER_RAISE_MARGIN_PCT"] == mv._fmt(
        round(100.0 * pe.recommended_raise_margin(archetype), 2)
    )


def test_resolve_manuscript_tree(tmp_path):
    src = tmp_path / "src"
    out = tmp_path / "out"
    src.mkdir()
    (src / "00_abstract.md").write_text(
        "Equity {{POKER_EQUITY_PCT}}% and unknown {{NOPE}}.", encoding="utf-8"
    )
    variables = {"POKER_EQUITY_PCT": "41.17"}
    out_dir, written, unresolved = mv.resolve_manuscript_tree(variables, src, out)
    assert written == 1
    assert unresolved == ["NOPE"]
    resolved = (out_dir / "00_abstract.md").read_text(encoding="utf-8")
    assert "41.17%" in resolved
    assert "unknown {{NOPE}}." in resolved  # unknown left in place
