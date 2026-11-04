---
name: casino-royale-2006
description: Casino Royale (2006) LE CHIFFRE BOND film package — hold'em game theory and CFR, tournament ICM, Bayesian opponent inference, chip-flow and network-level laundering detection, parkour routing, digitalis triage, MissionProvider.
version: 0.1.0
author: Daniel Ari Friedman
license: MIT
tags: [bond, film-package, mission-provider, poker, cfr, icm, bayesian, anti-money-laundering, graph, poison]
---

# casino-royale-2006

Project-scoped skill for the BOND film package at the repository root
(`bond-casino_royale_2006`). Load this when working inside the project.

## When to Use

- Implementing or extending any part of the LE CHIFFRE mission: the eight pure
  domain cores, the gadget catalogue, the bond-api `MissionProvider` adapter,
  manuscript tokens, or the phase CLIs.
- Verifying the package against the shared BOND guardrails (coverage, no mocks,
  lineage, ruff/mypy, clean tree).

## Quick Reference

- Pure core (stdlib, no bond-api): `src/casino_royale_2006/{poker_engine,
  poker_cfr, icm, opponent_bayes, laundering_detect, laundering_network,
  urban_routes, poison_detect, scenarios, gadgets}.py`.
- Adapter: `src/casino_royale_2006/mission.py` (film `casino_royale_2006`,
  `GADGET_REGISTRY` populated at import).
- One canonical scenario: `scenarios.SEED = 17`; snapshots drive the mission
  outcome and manuscript `{{TOKEN}}`s.
- Manuscript tokens: `src/casino_royale_2006/manuscript_variables.py
  ::generate_variables()`; figures in `figures/plotting.py`.

## Key Commands

```bash
cd bond-casino_royale_2006
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
uv run ruff check src/ scripts/ && uv run ruff format --check src/ scripts/
uv run mypy src/ scripts/
rg "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo Clean
uv run python scripts/run_debrief.py        # full five-stage mission
uv run python scripts/z_generate_manuscript_variables.py
```

## Pitfalls

- Keep every core module (all eight engines plus `scenarios.py`, `gadgets.py`,
  `manuscript_variables.py`) free of any `infrastructure.*` or `bond_api`
  import — the guardrails require them importable standalone (fallback if the
  path dep fails). `mission.py` is the sole adapter.
- `mission.py`'s public surface is FROZEN: `film`, the five stages,
  `register_gadgets`, `GADGET_REGISTRY`. Other packages consume it. Deepen
  inside; never reshape.
- `bond-api` is FROZEN. Code to `bond_api.protocol`; do not invent protocol
  types.
- Determinism: always pass a seeded `random.Random`; never rely on the global
  RNG or wall-clock in provenance.
- Manuscript numeric claims must be `{{TOKEN}}`s from `generate_variables()`;
  the cross-reference test scans `manuscript/[0-9]*.md` only. Count the braces:
  a single-brace `{NAME}` never substitutes and is caught separately by
  `manuscript_variables.find_malformed_tokens`.
- After edits run the full gate, then clean up any stray `output/` state
  (git-ignored) before the path-scoped commit.

## Cross-Refs

- BOND protocol (frozen): `vendor/bond-api/src/bond_api/protocol.py`
- Suite guardrails: Hermes skill `bond-suite-package-development`
- Project rulebook: `docs/agent_instructions.md`
