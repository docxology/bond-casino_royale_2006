# Casino Royale (2006) — LE CHIFFRE — PROJECT BOND film package

**Mission codename:** LE CHIFFRE · **Film:** Casino Royale (2006) · **BOND
suite:** sibling `bond-api` checkout at `../bond-api` · **Remote:**
<https://github.com/docxology/bond-casino_royale_2006> (`main`).

This package is one of the BOND suite's 27 film packages. It implements the
frozen **BOND-API** `MissionProvider` protocol (THE PROTOCOL) over eight pure,
deterministic domain cores drawn from the film's set pieces and the analysis
they demand:

| Module | Concept | Film anchor |
|---|---|---|
| `poker_engine.py` | Texas hold'em game theory (pot odds, equity, opponent modelling) | the high-stakes finale |
| `poker_cfr.py` | counterfactual regret minimization (river toy game) | the equilibrium behind the finale |
| `icm.py` | tournament Independent Chip Model (prize equity, bubble) | surviving the freezeout |
| `opponent_bayes.py` | Bayesian opponent archetype inference | reading Le Chiffre |
| `laundering_detect.py` | chip-movement money-laundering typology detection | the stake's funding |
| `laundering_network.py` | network-level financial crime (HHI/PageRank/communities) | the laundering structure |
| `urban_routes.py` | parkour mobility-graph routing | the rooftop/street pursuit |
| `poison_detect.py` | digitalis (cardiac glycoside) poison triage | the spiked martini |

`scenarios.py` owns the single canonical scenario; `gadgets.py` is the pure
catalogue of published callables; `mission.py` is the thin adapter to
`bond_api`; `manuscript_variables.py` + `figures/` produce the manuscript
tokens and the four figures.

## Hard guardrails (shared BOND preamble)

- Scope = exactly this package dir. Never touch siblings, bond root, or the
  template repo. Commit here only; publish to `origin` `main` when green.
- Path-scoped commits, `git add -A` inside this repo only.
- No mock framework. Real data + computation only.
- ≥90% line+branch coverage: `uv run pytest tests/ --cov=src --cov-fail-under=90`.
- Deterministic: fixed seeds, seeded RNG, no wall-clock anywhere on the
  persisted-artifact path. `output/data/manuscript_variables.json` and
  `output/manuscript/*.md` are byte-identical across reruns (figures are
  outside that claim). Dates belong in `manuscript/config.yaml`
  (`publication.date` → `{{MANUSCRIPT_DATE}}`), never `datetime.now()`. If you
  ever need a real run timestamp, put it in a record the claim excludes and say
  so in `manuscript/06_reproducibility.md`.
- Thin orchestrators in `scripts/`; business logic in `src/`.
- Pure core imports no `infrastructure.*` and no `bond_api` — `mission.py` is
  the sole exception.
- Manuscript metrics are `{{TOKEN}}`s (never hand-authored in prose). Double
  braces: `{TOKEN}` never substitutes and is caught by
  `manuscript_variables.find_malformed_tokens`.

## Architecture

```
tests/    ->  src/                                    (zero mocks, real algorithms)
scripts/  ->  src/ + bond_api                         (thin phase CLIs)
src/casino_royale_2006/mission.py -> bond_api + gadgets + scenarios  (adapter)
src/casino_royale_2006/{8 domain modules, scenarios, gadgets} -> stdlib  (pure core)
```

`mission.py`'s public surface is **frozen**: `film`, the five stages
(`brief`/`recon`/`plan`/`execute`/`debrief`), `register_gadgets`, and
`GADGET_REGISTRY` are consumed by bond-cli, the coordinator, and the
orchestrator. Deepen inside the package; do not reshape them.

## Build & verify

```bash
cd bond-casino_royale_2006

# 1. install (bond-api is the ../bond-api sibling; --extra dev adds the gates)
uv sync --extra dev

# 2. run it
uv run python scripts/00_preflight.py                      # protocol conformance + slug
uv run python scripts/run_debrief.py                       # full five-stage mission
uv run python scripts/z_generate_manuscript_variables.py   # tokens, prose, 4 figures
#    ^ exits 1 on an unresolved {{TOKEN}} or a malformed single-brace {TOKEN}

# 3. the gates (all must pass before declaring done)
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
uv run ruff check src/ scripts/ && uv run ruff format --check src/ scripts/
uv run mypy src/ scripts/
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo "Clean - no mocks"
rg "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo "Clean - no lineage strings"
git status --short                                          # clean after commit
```

If `uv` reports `Failed to initialize cache` or `Operation not permitted`, that
is a sandbox restriction, not a package failure — re-run with the sandbox
disabled.

See [`docs/agent_instructions.md`](docs/agent_instructions.md) (read-first),
[`docs/architecture.md`](docs/architecture.md), [`docs/protocol.md`](docs/protocol.md).
Live test/coverage counts: [`docs/_generated/COUNTS.md`](docs/_generated/COUNTS.md).
