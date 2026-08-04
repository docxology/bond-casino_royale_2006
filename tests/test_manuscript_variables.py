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
