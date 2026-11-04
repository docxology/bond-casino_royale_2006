# tests/ — per-core real-data tests

One module per domain core (`test_poker_engine.py`, `test_poker_cfr.py`, `test_icm.py`,
`test_opponent_bayes.py`, `test_laundering_detect.py`, `test_laundering_network.py`,
`test_urban_routes.py`, `test_poison_detect.py`), plus `test_scenarios.py`, `test_gadgets.py`,
`test_figures.py`, `test_mission.py`, `test_manuscript_variables.py`, `test_scripts_smoke.py` and
`conftest.py`.

## Rules

- **Zero mocks.** Real data and real computation only — no `MagicMock`, `mocker.patch` or
  `unittest.mock`.
- **Each domain core keeps its own test module**, so a core that stops working is visible as itself
  rather than as a mission failure.
- **Determinism tests are the point, not a formality**: fixed seeds and no wall clock are what make
  regeneration byte-identical, and a test that stops checking it removes the guarantee.
- **The mission test needs `bond-api`**; the core tests do not, so keep the split that lets the core
  be verified without importing it.
- **Coverage floor 90% line and branch on `src/`** (`uv run pytest tests/ --cov=src
  --cov-fail-under=90`). Do not lower it to admit new code.
- **`test_scripts_smoke.py` covers the phase CLIs**; a new script needs a smoke path.
