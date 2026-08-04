# Protocol Integration — binding to BOND-API

This film package implements the **frozen** BOND-API `MissionProvider`
protocol (codename THE PROTOCOL), defined in the `bond-api` sibling package
(`src/bond_api/protocol.py`). bond-api is FROZEN — this package codes to it and
never invents its own protocol types.

## How this package binds

- **Path dependency.** `pyproject.toml` pins `bond-api` via
  `[tool.uv.sources]` to the local sibling path, and lists it in
  `[project] dependencies`. Run `uv sync --extra dev` before testing.
- **Adapter.** `src/casino_royale_2006/mission.py` imports the frozen types
  (`MissionBrief`, `ReconRequest`, `ReconReport`, `MissionPlan`, `MissionOutcome`,
  `Provenance`, `Debrief`, `Asset`, `Constraint`, `Finding`, `Step`) and
  implements `MissionProvider` with `film = "casino_royale_2006"`.
- **Five stages.** `brief -> recon -> plan -> execute -> debrief`. `execute`
  computes real engine snapshots via `scenarios.full_snapshot(SEED)` and wraps
  them (plus deterministic provenance) in a `MissionOutcome`.
- **Gadgets.** At import, `mission.py` calls
  `register_gadgets(GADGET_REGISTRY)`, registering six callables with
  `bond_api.registry.GadgetRegistry` under the film slug.
- **Discovery.** The orchestrator imports `casino_royale_2006.mission` by slug
  and checks `isinstance(provider, MissionProvider)`. `scripts/00_preflight.py`
  and `tests/test_mission.py` run exactly this check.

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
