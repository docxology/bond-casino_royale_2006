"""Tests for manuscript token hydration (manuscript_variables.py)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from casino_royale_2006 import manuscript_variables as mv


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
    variables = mv.generate_variables(now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    for key in (
        "MISSION_TITLE",
        "MISSION_CODENAME",
        "POKER_EQUITY_PCT",
        "LAUNDER_FLAGGED",
        "ROUTE_FASTEST_ROOF",
        "POISON_GRADE",
        "CONCEPT_MODULES",
        "NUM_CONCEPT_MODULES",
        "GENERATION_TIMESTAMP",
    ):
        assert key in variables
        assert isinstance(variables[key], str)


def test_generate_variables_deterministic_with_now():
    stamp = datetime(2026, 2, 3, 12, 30, tzinfo=timezone.utc)
    a = mv.generate_variables(now=stamp)
    b = mv.generate_variables(now=stamp)
    assert a == b


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


def test_net_flagged_token_is_the_named_verdict():
    """NET_FLAGGED must reflect the launderer specifically, not "somebody"."""
    variables = mv.generate_variables()
    snap = mv.scenarios.network_snapshot()
    expected = "yes" if snap["launderer_flagged"] else "no"
    assert variables["NET_FLAGGED"] == expected


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
