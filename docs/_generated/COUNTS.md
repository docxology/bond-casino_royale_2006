# COUNTS — LE CHIFFRE (live, regenerated — do not hand-edit)

Generated from an actual gate run; update after any edit by running:

```bash
cd projects/working/bond/casino_royale_2006
uv run pytest tests/ --cov=src --cov-fail-under=90 -q 2>&1 | tail -20
```

## Test suite

- **172 tests passed**, 0 skipped, 0 failed (2026-08-04, Python 3.14.6).
- Zero mocks: no `unittest.mock` / `MagicMock` / `@patch` / `create_autospec`
  in `tests/` or `src/`.
- Deterministic: fixed seeds, seeded RNG, fully enumerated CFR / ICM / Bayesian
  engines, no wall-clock in provenance.

## Coverage on `src/`

- **97.10%** line + branch (gate: `--cov-fail-under=90`), `branch = true`.
- At 100%: `mission.py`, `scenarios.py`, `gadgets.py`, `poison_detect.py`,
  `figures/plotting.py`.
- Lowest module: `icm.py` at 92.81%. The residual misses across `icm.py` and
  `poker_engine.py` are real error and edge branches — tracked in `TODO.md`,
  not dead code.

## Static gates

- `uv run ruff check src/ scripts/` — all checks passed.
- `uv run ruff format --check src/ scripts/` — 23 files already formatted.
- `uv run mypy src/ scripts/` — no issues found in 23 source files.
- `uv run python scripts/z_generate_manuscript_variables.py` — exit 0; 60
  tokens, 9 sections, 4 figures.
