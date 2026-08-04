# Casino Royale (2006) — LE CHIFFRE — PROJECT BOND film package

**Mission codename:** LE CHIFFRE · **Film:** Casino Royale (2006) · **BOND
suite:** projects/working/bond/ · **Local-only** (no remote, never pushed).

This package is one of the BOND suite's 27 film packages. It implements the
frozen **BOND-API** `MissionProvider` protocol (THE PROTOCOL) over four pure,
deterministic domain cores drawn from the film's set pieces:

| Module | Concept | Film anchor |
|---|---|---|
| `poker_engine.py` | Texas hold'em game theory (pot odds, equity, opponent modelling) | the high-stakes finale |
| `laundering_detect.py` | chip-movement money-laundering detection | the stake's funding |
| `urban_routes.py` | parkour mobility-graph routing | the rooftop/street pursuit |
| `poison_detect.py` | digitalis (cardiac glycoside) poison triage | the spiked martini |

`scenarios.py` owns the single canonical scenario; `mission.py` is the thin
adapter to `bond_api`; `manuscript_variables.py` + `figures/` produce the
manuscript tokens and figures.

## Hard guardrails (shared BOND preamble)

- Scope = exactly this package dir. Never touch siblings, bond root, or the
  template repo. Local-only; never push.
- Path-scoped commits, `git add -A` inside this repo only.
- No mock framework. Real data + computation only.
- ≥90% line+branch coverage: `uv run pytest tests/ --cov=src --cov-fail-under=90`.
- Deterministic: fixed seeds, seeded RNG, no wall-clock in provenance.
- Thin orchestrators in `scripts/`; business logic in `src/`.
- Pure core imports no `infrastructure.*` and no `bond_api`.
- Manuscript metrics are `{{TOKEN}}`s (never hand-authored in prose).

## Architecture

```
tests/  ->  src/                         (zero mocks, real algorithms)
scripts/ ->  src/ + bond_api             (thin phase CLIs)
src/casino_royale_2006/mission.py -> bond_api + domain core   (adapter)
src/casino_royale_2006/{4 domain modules,scenarios} -> stdlib  (pure core)
```

## Verification

```bash
uv run sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
uv run ruff check src/ scripts/ && uv run ruff format --check src/ scripts/
uv run mypy src/ scripts/
rg "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo Clean
```

See [`docs/agent_instructions.md`](docs/agent_instructions.md) (read-first),
[`docs/architecture.md`](docs/architecture.md), [`docs/protocol.md`](docs/protocol.md).
Live test/coverage counts: [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md).
