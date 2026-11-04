# COUNTS — LE CHIFFRE (live, regenerated — do not hand-edit)

Generated from an actual gate run; update after any edit by running:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q 2>&1 | tail -20
```

## Test suite

- **208 tests passed**, 0 skipped, 0 failed (2026-11-04, Python 3.14.9; the
  208th is `tests/test_vendor_provenance.py`, added with the vendored `bond-api`
  copy).
- Zero mocks: no `unittest.mock` / `MagicMock` / `@patch` / `create_autospec`
  in `tests/` or `src/`.
- Deterministic: fixed seeds, seeded RNG, fully enumerated CFR / ICM / Bayesian
  engines, and no wall-clock anywhere on the persisted-artifact path — the
  manuscript's publication stamp is the committed `publication.date` in
  `manuscript/config.yaml`, not `datetime.now()`.

## Coverage on `src/`

- **97.51%** line + branch (gate: `--cov-fail-under=90`), `branch = true`.
- At 100%: `mission.py`, `scenarios.py`, `gadgets.py`, `poison_detect.py`,
  `figures/plotting.py`.
- Lowest module: `icm.py` at 94.27%. The residual misses across `icm.py` and
  `poker_engine.py` are real error and edge branches — tracked in `TODO.md`,
  not dead code.

## Static gates

- `uv run ruff check src/ scripts/ tests/` — all checks passed.
- `uv run ruff format --check src/ scripts/ tests/` — 43 files already formatted.
- `uv run mypy src/ scripts/` — no issues found in 24 source files.
- `uv run python scripts/vendor.py --check` — exit 0; `vendor/bond-api: ok`,
  0 findings.
- `uv run python scripts/z_generate_manuscript_variables.py` — exit 0; 66
  tokens, 9 sections, 4 figures.

## Falsifiability probes (run 2026-08-05, reverted after each)

Every gate repaired in the verifier-remediation pass was proven capable of
failing by breaking the thing it guards:

- Published hand-ranking oracle: red under 7/7 injected evaluator defects
  (full house below flush, quads as trips, trips above straight, one-pair
  kicker dropped, two-pair kicker dropped, ascending flush tiebreak, wheel
  straight undetected).
- AA-vs-KK equity oracle: red under `best_hand` selecting the worst subset
  (measured 72.6% vs published 81.94%). Not sensitive to category swaps — see
  the note on the test and in `TODO.md`.
- `NET_FLAGGED` named verdict: red when `scenarios.named_verdict` is degraded
  to `bool(flagged)`.
- Derived opponent range: red when `poker_snapshot` hard-codes the tight range
  again, and when the archetype's `raise_margin` is dropped.
- `path_cost`: red when it ignores its `weights` argument.
- Regeneration determinism (added 2026-08-05, after the wall-clock breach):
  `test_regeneration_is_byte_identical_across_a_clock_tick` and
  `test_generate_variables_is_a_pure_function_of_committed_inputs` both go red
  when `MANUSCRIPT_DATE` is temporarily restored to
  `datetime.now(timezone.utc)` — the artifact hash moved between the two runs,
  exactly as it had been doing in production while the old injected-`now` test
  stayed green.
- Figures: red when the poker chart plots break-even twice, the digitalis sweep
  uses a different panel, the ICM chart plots stacks instead of bubble factors,
  or the CFR chart plots a constant instead of the regret trace.
