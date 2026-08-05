"""Q-branch gadget catalogue for the LE CHIFFRE film package (pure).

The BOND protocol lets a film package publish *gadgets* - plain callables that
another package (the CLI, the coordinator, the orchestrator) can look up by
name and invoke without importing this package's internals. The registration
itself belongs to :mod:`mission`, which is the only module allowed to touch
``bond_api``; this module owns the **catalogue** - the name-to-callable mapping
- and stays pure stdlib so the catalogue can be inspected, counted, and tested
without the protocol dependency present.

Keeping the catalogue here has two concrete consequences:

* ``manuscript_variables`` can emit ``{{NUM_GADGETS}}`` / ``{{GADGET_NAMES}}``
  tokens from the real mapping, so the manuscript never hand-authors the count.
* ``tests/test_gadgets.py`` can assert every advertised gadget is callable
  without a ``bond_api`` import, which is what a consumer actually depends on.

``mission.register_gadgets`` passes :data:`GADGETS` straight to
``GadgetRegistry.register``; its public shape is unchanged by this split.
"""

from __future__ import annotations

from collections.abc import Callable

from casino_royale_2006 import icm
from casino_royale_2006.laundering_detect import detect
from casino_royale_2006.laundering_network import network_risk_report
from casino_royale_2006.opponent_bayes import BayesianOpponentModel
from casino_royale_2006.poison_detect import identify_poisoned_sample
from casino_royale_2006.poker_cfr import cfr_solve
from casino_royale_2006.poker_engine import equity_vs_range
from casino_royale_2006.urban_routes import MobilityGraph, ParkourProfile, build_city_quarter

__all__ = ["GADGETS", "GADGET_NAMES", "gadget"]

#: The film's published gadgets: ``name -> callable``. Insertion order is the
#: advertised order and is stable; consumers look up by name, never by index.
GADGETS: dict[str, Callable[..., object]] = {
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
}

#: The advertised gadget names, in catalogue order.
GADGET_NAMES: tuple[str, ...] = tuple(GADGETS)


def gadget(name: str) -> Callable[..., object]:
    """Return the catalogue entry ``name``.

    Args:
        name: an advertised gadget name (see :data:`GADGET_NAMES`).

    Returns:
        The callable published under that name.

    Raises:
        KeyError: if ``name`` is not in the catalogue, listing what is.
    """
    try:
        return GADGETS[name]
    except KeyError:
        raise KeyError(f"no gadget {name!r}; available: {', '.join(GADGET_NAMES)}") from None
