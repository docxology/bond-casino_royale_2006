# Agent Instructions — read this first

Operational constraints for the **Casino Royale (2006) / LE CHIFFRE** mission
package. These are hard rules; skipping them is the most common source of the
failures listed under each.

## Rule 1 — Zero mocks (real data + real computation)

No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec` anywhere in
`tests/`. Deterministic fakes implement the REAL protocol and REAL domain
interfaces. *Consequence of violating:* tests can pass while the actual logic
is wrong — they would assert call signatures, not outcomes.

## Rule 2 — Pure domain core

All eight cores — `poker_engine.py`, `poker_cfr.py`, `icm.py`,
`opponent_bayes.py`, `laundering_detect.py`, `laundering_network.py`,
`urban_routes.py`, `poison_detect.py` — plus `scenarios.py`, `gadgets.py`, and
`manuscript_variables.py` must not import `infrastructure.*` **or**
`bond_api`. They use stdlib only (plus `pyyaml` in `manuscript_variables.py`
and matplotlib in `figures/`). *Consequence:* they must import standalone even
if the bond-api path dependency is missing. `mission.py` is the ONLY module in
`src/` that imports `bond_api`.

A corollary that has already bitten once: a **film-agnostic** core module must
not encode this film's suspect. `laundering_network.py` reports `any_flagged`;
whether *Le Chiffre* specifically was caught is decided by the caller in
`scenarios.network_snapshot`. *Consequence of violating:* a field named for one
account that actually means "somebody" — a claim that reads stronger than it
is.

## Rule 3 — Thin orchestrators

All business logic lives in `src/`. `scripts/` files only bootstrap `src/`
onto `sys.path` and forward argv. *Consequence of violating:* unrepeatable,
untestable math buried in a CLI.

## Rule 4 — Tokens, not prose numbers

Manuscript numeric claims are `{{TOKEN}}`s computed by
`src/casino_royale_2006/manuscript_variables.py` from `manuscript/config.yaml`
plus live engine output in `scenarios.py`. Never hand-author a measured number
in manuscript prose. *Consequence of violating:* the manuscript drifts from
the code and the token cross-reference test fails.

Count the braces. `{{TOKEN}}` substitutes; `{TOKEN}` does not — it renders its
own braces into the PDF *and* passes the unresolved-token check, because that
check only looks for `{{...}}`. `manuscript_variables.find_malformed_tokens()`
is the gate for that exact typo; `scripts/z_generate_manuscript_variables.py`
exits 1 on it and `tests/test_manuscript_variables.py` asserts it stays clean.

## Rule 5 — Determinism

Fixed seeds; all RNG flows through caller-supplied `random.Random(seed)`;
`Provenance` records the seed and a deterministic `input_hash`, never wall
clock. *Consequence of violating:* runs diverge and results cannot be audited.

## Rule 6 — Explicit paths & show-not-tell

Reference files/functions by exact path (`src/casino_royale_2006/poker_engine.py::equity_vs_range`),
not vague descriptions. *Consequence of violating:* a reader cannot verify the claim.

## Rule 7 — Type hints & actionable errors

Public APIs are fully annotated (the `src/` gate runs mypy). Errors carry
actionable messages via `ValueError`/`KeyError` with context. *Consequence of
violating:* the mypy gate fails; debugging becomes guesswork.

## Verification checklist (run before declaring done)

```bash
cd projects/working/bond/casino_royale_2006
uv run pytest tests/ --cov=src --cov-fail-under=90 -q          # >=90% line+branch
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo Clean
grep -rnE "^(from|import) (infrastructure|bond_api)" \
    $(ls src/casino_royale_2006/*.py | grep -v '/mission.py$') \
    || echo "Clean - core is pure"
rg -n "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo Clean
uv run ruff check src/ scripts/ && uv run ruff format --check src/ scripts/
uv run mypy src/ scripts/
git status --short   # clean after commit
```
