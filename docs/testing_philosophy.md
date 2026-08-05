# Testing Philosophy

The LE CHIFFRE test suite follows four hard rules: **real data**, **zero
mocks**, **determinism**, and **≥90% line-and-branch coverage on `src/`**.
Nothing below is aspiration; each rule names the mechanism that enforces it in
this package.

## Zero mocks — and what replaces them

No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec` appears
anywhere in `tests/` or `src/`. That costs nothing here, because every module
is a pure function of its inputs, so the "test double" is simply *real input*.
Concretely, per module:

| Module | What stands in for a mock |
|---|---|
| `poker_engine.py` | Literal card vectors with known hand ranks; the published heads-up preflop AA-vs-KK equity (81.94% = 81.71% wins + half of 0.46% ties) as an external oracle, measured in `test_preflop_aa_vs_kk_matches_published_equity` over all 36 suit combinations. |
| `poker_cfr.py` | The toy game is fully enumerated, so the equilibrium *shape* (polar: bet the top, bluff the bottom, call the middle) is itself the assertion. |
| `icm.py` | Hand-computable exact equities on small stacks; the heads-up bubble factor, which must be exactly 1.0 by construction. |
| `opponent_bayes.py` | Two contrasting real action histories (raise-heavy vs. fold-heavy) that must move the posterior in opposite directions. |
| `laundering_detect.py` | `synthetic_flow(seed)` — a seeded scene with one deliberately planted smurfer, so there is a known right answer. |
| `laundering_network.py` | The same seeded flow, plus small hand-built graphs whose HHI, turnover, and communities can be worked out by hand. |
| `urban_routes.py` | `brute_force_path` — an independent exhaustive search used as the ground-truth oracle Dijkstra is checked against. |
| `poison_detect.py` | `synthetic_panels(seed, poisoned_index=...)` — the spiked glass is known, so identification is checkable. |
| `gadgets.py` | The real callables; the catalogue is exercised without `bond_api` present, which is the property consumers actually rely on. |
| `mission.py` | The real frozen `bond_api` types and a real `GadgetRegistry`; nothing is stubbed. |

The pattern worth copying: where a module could otherwise only be checked
against itself, a *second independent implementation* or an *external published
value* is introduced, so the test is capable of failing.

## Determinism

- One fixed, documented seed: `scenarios.SEED = 17`.
- Every RNG is a caller-supplied `random.Random(seed)`. The global RNG is never
  used and never seeded by tests, so test order cannot change a result.
- Three engines carry no RNG at all — `poker_cfr`, `icm` (exact recursion), and
  `opponent_bayes` (closed-form log-space posterior). They accept a `seed`
  argument only for snapshot-signature parity, and their docstrings say so.
- Figures render under the Agg backend; `Provenance.wall_time_s` is pinned to
  `0.0` and `input_hash` is a SHA-256 over scenario constants, so no artifact
  carries a clock reading.
- `generate_variables()` takes no clock argument and reads none. Its publication
  stamp, `MANUSCRIPT_DATE`, comes from the committed `publication.date` field of
  `manuscript/config.yaml`. The determinism tests therefore inject nothing: they
  run the generator twice across a real whole-second boundary and compare bytes
  (`test_generate_variables_is_a_pure_function_of_committed_inputs`,
  `test_regeneration_is_byte_identical_across_a_clock_tick`). An earlier version
  stamped `datetime.now()` and was "pinned" by a test that passed its own `now=`
  — the injected value hid the production default, and the JSON artifact changed
  on every run while the suite stayed green.

## Coverage command

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```

`pyproject.toml` sets `branch = true` and `fail_under = 90`; coverage is
measured on `src/casino_royale_2006` only. The live test count and achieved
coverage are recorded in `docs/_generated/COUNTS.md` — regenerated from a real
run, never hand-edited. Prose elsewhere in this package describes the *gate*
(≥90%) rather than quoting a figure that would silently go stale.

## Test-file inventory

| File | Covers |
|---|---|
| `test_poker_engine.py` | hand-eval vectors, exact turn/river equity, Monte-Carlo, pot odds/EV, opponent model, ranges |
| `test_poker_cfr.py` | CFR convergence, polar equilibrium shape, determinism, error branches |
| `test_icm.py` | exact/heads-up ICM, Monte-Carlo, bubble factor (incl. heads-up = 1), call EV/decision |
| `test_opponent_bayes.py` | Dirichlet posterior, MAP/predictive/aggression, history discrimination |
| `test_laundering_detect.py` | structuring/round-trip/velocity/parking primitives, `detect` on seeded synthetic scenes |
| `test_laundering_network.py` | HHI, PageRank, label-propagation determinism, conservation, composite risk report, `any_flagged` semantics, and a negative control where the film's launderer is absent |
| `test_urban_routes.py` | feasibility, Dijkstra vs. brute force, tie-break determinism, unreachable |
| `test_poison_detect.py` | grade thresholds, posterior, source identification, antidote plan |
| `test_gadgets.py` | catalogue non-empty, every entry callable, names match, lookup error path — all without importing `bond_api` |
| `test_mission.py` | protocol conformance, `run_mission` flow, gadget registration, discovery |
| `test_manuscript_variables.py` | config load, token map, live `{{TOKEN}}` cross-reference, malformed single-brace guard, resolve tree |
| `test_scenarios.py` | canonical snapshots for all eight concept modules; derived opponent range; single-objective route comparison |
| `test_figures.py` | all four figures: plotted data asserted against the engine values they claim to show, plus a decoded, non-uniform PNG |
| `test_scripts_smoke.py` | subprocess runs of each phase CLI + the manuscript variables script |

## What counts as a passing test

Real assertions on real outputs: exact known hand-rank vectors, equity bounds
against published preflop equities, determinism (two runs identical), error
branches (`ValueError` / `KeyError`), and the presence and validity of
generated artifacts.

What does *not* count: an assertion that cannot fail. `assert x is not None`
after a call that cannot return `None`, a threshold no input could cross, or a
check on a field whose name implies more than the field measures — the
`any_flagged` rename came out of exactly that. Before adding a gate, construct
the input that *should* fail it and confirm that it does.

Two gates in this suite were rewritten for exactly that reason, and both now
carry the falsifying input inside the test:

- **`NET_FLAGGED` (`test_manuscript_variables.py`).** The old version compared
  the token against the same snapshot call that produced it — one source on
  both sides, so it could only fail if the snapshot were nondeterministic. It
  now drives the production verdict rule (`scenarios.named_verdict`) with a
  flow whose only flagged account is *somebody else*: `any_flagged` is True
  there while the named verdict is False. Weakening the rule to
  `bool(report.flagged)` turns that assertion red.
- **Figures (`test_figures.py`).** The old version asserted only that a
  non-empty file appeared, so any regression that still emitted bytes passed.
  Each figure is now built in-process and its plotted series compared against
  the engine values it claims to show (`toxicity_score` point by point, the CFR
  regret trace, `icm.bubble_factor`, the poker snapshot's own numbers), with
  axis labels and titles pinned; the saved PNG is additionally decoded and
  required to contain more than one colour.
