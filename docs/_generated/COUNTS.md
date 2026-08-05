# COUNTS — LE CHIFFRE (live, regenerated — do not hand-edit)

Generated from the actual gate run; update after any edit by running:

```bash
cd projects/working/bond/casino_royale_2006
uv run pytest tests/ --cov=src --cov-fail-under=90 -q 2>&1 | tail -18
```

## Test suite

- **155 tests passed**, 0 skipped, 0 failed (2026-08, Python 3.14).
- Zero mocks: no `unittest.mock` / `MagicMock` / `@patch` / `create_autospec`
  in tests/ or src/.
- Deterministic: fixed seeds, seeded RNG, fully enumerated CFR, no wall-clock
  in provenance.

## Coverage on `src/`

- **96.86%** line + branch (gate: `--cov-fail-under=90`), `branch = true`.
- All eight domain modules plus the adapter, scenarios, manuscript variables,
  and figures are individually above 92%; `mission.py`, `scenarios.py`,
  `poison_detect.py`, and `figures/plotting.py` are at 100%.
