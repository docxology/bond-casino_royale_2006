"""Casino Royale (2006) - LE CHIFFRE mission package.

Special-agent mission software for a single film package in the PROJECT BOND
suite. Eight pure domain cores (no framework, no ``infrastructure.*``, no
bond-api dependency) implement the concepts behind the 2006 film's set pieces:

* :mod:`poker_engine` - Texas hold'em game-theory engine (pot odds, hand
  strength/equity, opponent modelling) for the Casino Royale high-stakes finale.
* :mod:`poker_cfr` - counterfactual regret minimization on the river toy game,
  the equilibrium shape the finale turns on.
* :mod:`icm` - the tournament Independent Chip Model: prize equity, the bubble
  factor, and prize-equity call decisions on the freezeout.
* :mod:`opponent_bayes` - Dirichlet-multinomial posterior over opponent
  archetypes, the quantified "read" on Le Chiffre.
* :mod:`laundering_detect` - chip-movement money-laundering typology detection
  for the bank that funded Le Chiffre's game.
* :mod:`laundering_network` - the structural layer over the same chip flows:
  HHI concentration, PageRank, label-propagation communities, conservation.
* :mod:`urban_routes` - parkour routing over urban mobility graphs for the
  foot-and-rooftop pursuit.
* :mod:`poison_detect` - digitalis (foxglove) poison detection for Bond's
  spiked martini.

:mod:`scenarios` owns the one canonical scenario every consumer draws from;
:mod:`gadgets` is the pure catalogue of published callables; :mod:`mission` is
the thin adapter that binds the cores to the frozen ``bond_api``
``MissionProvider`` protocol (THE PROTOCOL); and :mod:`manuscript_variables`
hydrates manuscript ``{{TOKEN}}``s from ``manuscript/config.yaml`` plus live
engine computations.
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
