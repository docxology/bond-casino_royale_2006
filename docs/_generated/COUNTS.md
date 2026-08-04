# COUNTS — LE CHIFFRE (live, regenerated — do not hand-edit)

Generated from the actual gate run; update after any edit by running:

```bash
cd projects/working/bond/casino_royale_2006
uv run pytest tests/ --cov=src --cov-fail-under=90 -q 2>&1 | tail -15
```

## Test suite

- **114 tests passed**, 0 skipped, 0 failed (2026-08, Python 3.14).
- Zero mocks: no `unittest.mock` / `MagicMock` / `@patch` / `create_autospec`.
- Deterministic: fixed seeds, seeded RNG, no wall-clock in provenance.

## Coverage on `src/`

- **96.91%** line + branch (gate: `--cov-fail-under=90`), `branch = true`.
- Module breakdown (statements):
  - `poker_engine.py` — 95.71%
  - `laundering_detect.py` — 95.22%
  - `urban_routes.py` — 97.49%
  - `poison_detect.py` — 100.00%
  - `scenarios.py` — 100.00%
  - `mission.py` — 100.00%
  - `manuscript_variables.py` — 95.18%
  - `figures/plotting.py` — 100.00%
