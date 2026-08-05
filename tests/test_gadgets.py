"""Tests for the pure gadget catalogue (gadgets.py).

The property consumers actually depend on is that the catalogue is inspectable
and callable *without* ``bond_api`` installed - so nothing in this file imports
``bond_api`` or ``mission``. The protocol binding is tested separately in
``test_mission.py``.
"""

from __future__ import annotations

import inspect

import pytest

from casino_royale_2006 import gadgets, scenarios


def test_catalogue_is_non_empty():
    """Guard against a catalogue that silently empties (a vacuous count)."""
    assert len(gadgets.GADGETS) > 0
    assert len(gadgets.GADGET_NAMES) == len(gadgets.GADGETS)


def test_names_match_mapping_keys_in_order():
    assert tuple(gadgets.GADGETS) == gadgets.GADGET_NAMES


def test_every_gadget_is_callable():
    for name, entry in gadgets.GADGETS.items():
        assert callable(entry), f"gadget {name!r} is not callable"


def test_every_gadget_has_a_docstring():
    """A published callable another package invokes must document itself."""
    for name, entry in gadgets.GADGETS.items():
        assert inspect.getdoc(entry), f"gadget {name!r} has no docstring"


def test_gadget_lookup_returns_the_mapped_callable():
    assert gadgets.gadget("poker_cfr_solve") is gadgets.GADGETS["poker_cfr_solve"]


def test_gadget_lookup_unknown_name_raises_with_the_valid_names():
    with pytest.raises(KeyError) as excinfo:
        gadgets.gadget("martini_shaker")
    message = str(excinfo.value)
    assert "martini_shaker" in message
    assert "poker_cfr_solve" in message  # the error lists what IS available


def test_a_published_gadget_actually_computes():
    """Invoke one end-to-end so the catalogue cannot advertise a broken entry."""
    solve = gadgets.gadget("poker_cfr_solve")
    result = solve(scenarios.CFR_STRENGTHS, scenarios.CFR_ITERATIONS)
    assert result.avg_regret >= 0.0
    assert 0.0 < result.game_value < 1.0


def test_bubble_factor_gadget_matches_the_engine():
    factor = gadgets.gadget("icm_bubble_factor")(
        scenarios.ICM_STACKS, scenarios.ICM_PRIZES, scenarios.ICM_PLAYER
    )
    assert factor > 1.0  # the short stack is squeezed on the bubble
