# Protocol Integration — binding to BOND-API

This film package implements the **frozen** BOND-API `MissionProvider`
protocol (codename THE PROTOCOL), defined in the `bond-api` package vendored at
`vendor/bond-api` (`src/bond_api/protocol.py` inside the copy). bond-api is
FROZEN — this package codes to it and never invents its own protocol types.

## How this package binds

- **Path dependency.** `pyproject.toml` pins `bond-api` via
  `[tool.uv.sources]` to the copy at `vendor/bond-api`, and lists it in
  `[project] dependencies`. Run `uv sync --extra dev` before testing.
- **Adapter.** `src/casino_royale_2006/mission.py` imports the frozen types
  (`MissionBrief`, `ReconRequest`, `ReconReport`, `MissionPlan`, `MissionOutcome`,
  `Provenance`, `Debrief`, `Asset`, `Constraint`, `Finding`, `Step`) and
  implements `MissionProvider` with `film = "casino_royale_2006"`.
- **Five stages.** `brief -> recon -> plan -> execute -> debrief`. `execute`
  computes real engine snapshots via `scenarios.full_snapshot(SEED)` and wraps
  them (plus deterministic provenance) in a `MissionOutcome`.
- **Gadgets.** At import, `mission.py` calls
  `register_gadgets(GADGET_REGISTRY)`, binding the catalogue in the pure
  `casino_royale_2006.gadgets` module (`GADGETS`) to
  `bond_api.registry.GadgetRegistry` under the film slug. The catalogue
  currently publishes eleven callables — `poker_equity_vs_range`,
  `poker_cfr_solve`, `icm_exact_equity`, `icm_bubble_factor`,
  `chip_flow_detect`, `network_laundering_risk`, `parkour_shortest_path`,
  `parkour_build_city_quarter`, `parkour_profile`, `poison_identify_sample`,
  `bayesian_opponent` — but consumers should read `GADGET_NAMES` rather than
  hard-code the list, and the manuscript prints the count from that tuple
  (`{{NUM_GADGETS}}`) rather than stating it.
- **Discovery.** The orchestrator imports `casino_royale_2006.mission` by slug
  and checks `isinstance(provider, MissionProvider)`. `scripts/00_preflight.py`
  and `tests/test_mission.py` run exactly this check.

## The frozen surface (do not reshape)

These names and signatures are consumed by bond-cli, the coordinator reconcile,
and the orchestrator across packages. Changing any of them breaks discovery for
the whole suite; deepening happens *inside* the package.

| Symbol | Shape |
|---|---|
| `MissionProvider.film` | `str`, equal to the directory slug |
| `MissionProvider.brief()` | `() -> MissionBrief` |
| `MissionProvider.recon(request)` | `(ReconRequest) -> ReconReport` |
| `MissionProvider.plan(brief)` | `(MissionBrief) -> MissionPlan` |
| `MissionProvider.execute(plan)` | `(MissionPlan) -> MissionOutcome` |
| `MissionProvider.debrief(outcome)` | `(MissionOutcome) -> Debrief` |
| `register_gadgets(registry)` | `(GadgetRegistry) -> None` |
| `GADGET_REGISTRY` | module-level `GadgetRegistry`, populated at import |

`tests/test_mission.py` asserts protocol conformance, the full five-stage flow,
gadget registration, and slug/`film` agreement — so a reshape fails the gate
rather than failing another package at integration time.

## Facts about discovery that matter here

- `Film` must equal the slug (`casino_royale_2006`), matching
  `^[A-Za-z_][A-Za-z0-9_]*$`.
- `sys.modules` caches slug imports; tests that bind providers keep unique
  slugs/locations.
- `Asset.payload` is opaque — this package attaches JSON-serializable scenario
  dicts, which the protocol round-trips unchanged.

## Declared integration point

The mission binds directly to `bond_api` (frozen). It does **not** yet consume
`bond_utilities.mission_io.record_provenance_outcome`; that is a declared
integration point in `TODO.md` (acceptance: switch `execute`'s provenance
persistence to the shared helper once bond-utilities is converted). The domain
core remains importable today with zero bond-api dependency — the fallback the
guardrails require.
