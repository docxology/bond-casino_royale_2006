"""Casino Royale (2006) - LE CHIFFRE mission package.

Special-agent mission software for a single film package in the PROJECT BOND
suite. Four pure domain cores (no framework, no ``infrastructure.*``, no
bond-api dependency) implement the concepts behind the 2006 film's set pieces:

* :mod:`poker_engine` - Texas hold'em game-theory engine (pot odds, hand
  strength/equity, opponent modelling) for the Casino Royale high-stakes finale.
* :mod:`laundering_detect` - chip-movement money-laundering detection for the
  bank that funded Le Chiffre's game.
* :mod:`urban_routes` - parkour routing over urban mobility graphs for the
  foot-and-rooftop pursuit.
* :mod:`poison_detect` - digitalis (foxglove) poison detection for Bond's
  spiked martini.

:mod:`mission` is the thin adapter that binds these cores to the frozen
``bond_api`` ``MissionProvider`` protocol (THE PROTOCOL), and
:mod:`manuscript_variables` hydrates manuscript ``{{TOKEN}}``s from
``manuscript/config.yaml`` plus live engine computations.
"""

from __future__ import annotations

__version__ = "0.1.0"
VERSION = __version__

#: The BOND film slug this package answers to (also the package name and the
#: ``MissionProvider.film`` identity used for discovery).
FILM = "casino_royale_2006"
#: The special-agent mission codename for this film.
CODENAME = "LE CHIFFRE"

__all__ = [
    "CODENAME",
    "FILM",
    "VERSION",
    "__version__",
]
