# TODO — casino_royale_2006 (LE CHIFFRE)

PROJECT BOND film package for *Casino Royale* (2006): eight pure, deterministic
domain cores (poker equity/pot-odds, river CFR, ICM, Bayesian opponent
archetypes, laundering typologies, laundering network analytics, parkour
routing, digitalis triage) plus `scenarios.py`, `gadgets.py`,
`manuscript_variables.py`, `figures/plotting.py`, and the frozen BOND-API
adapter `mission.py`. **Verified state, re-measured 2026-11-04 after the
`bond-api` vendoring round (Python 3.14.9, `uv run pytest tests/
--cov=src --cov-fail-under=90`): 208 tests passed, 0 skipped, 0 failed; 97.51%
line+branch coverage on `src/`.** `ruff check`, `ruff format --check`,
`mypy src/ scripts/`, and `scripts/z_generate_manuscript_variables.py` (66
tokens, 9 sections, 4 figures) all exit 0; `git status --short` is clean.

Open work only. Completed phases live in git history and in the manuscript.

## Open work

### Correctness

**None open.** All nine findings recorded in
`../output/verify/casino_royale_2006.json` were re-checked against the tree at
this commit and each is remediated in shipped code, not merely in prose:

| Audit finding | Where it was | Evidence it is closed |
|---|---|---|
| Fabricated AA-vs-KK oracle | `docs/testing_philosophy.md` | `tests/test_poker_engine.py:268` `test_preflop_aa_vs_kk_matches_published_equity` exists and runs |
| Archetype → range selection did not exist | `manuscript/02_methodology.md`, `docs/architecture.md` | `poker_engine.py:585 range_key_for_archetype`, `:610 range_for_archetype`, `ARCHETYPE_RANGE_KEYS` at `:570`; pinned by `tests/test_poker_engine.py:437-446` |
| False "169 canonical hand classes" numeral | `manuscript/02_methodology.md` | now `{{POKER_RANGE_CLASSES}}`; prose at `02_methodology.md:38-41` names 169 only as the space it is *not*; bound by `tests/test_manuscript_variables.py:171-186` |
| "never a named suspect" contradicted by `as_dict` | `docs/architecture.md` | rewritten at `docs/architecture.md:92-97` to the precise sense (only `any_flagged` is a verdict); named verdict decided in `scenarios.named_verdict` (`scenarios.py:314`) |
| Inverted pot-odds justification | `manuscript/03_results.md` | `03_results.md:16-18` now reads "the probability of winning exceeds the price the pot is laying" |
| Incommensurable route costs juxtaposed | `03_results.md`, `00_abstract.md` | both now price each route under both weightings via `{{ROUTE_SAFEST_COST_UNDER_FAST}}` / `{{ROUTE_FASTEST_COST_UNDER_SAFE}}` and state non-comparability explicitly |
| Tautological `NET_FLAGGED` gate | `tests/test_manuscript_variables.py` | replaced by `test_net_flagged_token_is_a_named_verdict_not_merely_any_flagged` (`:139`), which drives a ghost-flow negative control where `any_flagged` is True and the named verdict is False |
| Figure "coverage theatre" | `tests/test_figures.py` | 10 tests now; content assertions on plotted values (`:49`, `:69`, `:97`, `:136`, `:160`) not just file size |
| `recommended_raise_margin` dead export | `poker_engine.py` | now consumed on the production path: `scenarios.py:173` passes it into `recommend_action` |

### Verification (claims not yet bound by a test that can fail)

| # | What is unbound | Where | Done looks like | Command |
|---|---|---|---|---|
| V1 | The **round-trip typology never runs inside `detect()`**. `round_trips()` is unit-tested (`tests/test_laundering_detect.py:77-86`), but no test drives `detect()` with a flow containing a ring, so the branch that adds the ring score to the composite, appends the `roundtrip:N` reason, and widens the evidence set is never executed. A regression that dropped ring scoring from alerts entirely would keep every test green. | `src/casino_royale_2006/laundering_detect.py:284-289` (uncovered: 286, 287, 288, 289) | A test builds a flow whose only signal is a round-trip ring, asserts the resulting `Alert` carries a `roundtrip:` reason and the expected score contribution, and the coverage report no longer lists 286-289 as missed. | `uv run pytest tests/ --cov=src --cov-report=term-missing -q` — `laundering_detect.py` Missing column shows no `286-289` |
| V2 | **Residual uncovered error/edge branches.** These are real guard clauses and early returns, not dead code; the 90% gate passes over them. `icm.py`: 51 (empty `prizes` guard), 74 (zero-chip equity return), 116→121 (partial), 129, 176 (`inf` bubble factor), 203 (`pot_after_call` guard). `poker_engine.py`: 245 (duplicate-card guard), 257 (tie branch in showdown), 285 (>5-card board guard), 324, 350→346 (partial), 366/374/380 (`None` returns from category detectors), 414 (pot/to-call guard). `laundering_detect.py`: 78, 152, 208, 210. `laundering_network.py`: 162, 182, 220→233. `urban_routes.py`: 309, 316, 318. `opponent_bayes.py`: 103 (uniform prior fallback). `poker_cfr.py`: 70. `manuscript_variables.py`: 255. | as listed | Inputs added that reach each branch — the tie branch (`poker_engine.py:257`) and the `inf` bubble factor (`icm.py:176`) first, since both are silent-wrong-answer paths rather than raises. Per-module coverage rises and the named lines leave the Missing column. | `uv run pytest tests/ --cov=src --cov-report=term-missing -q` |
| V3 | **Cross-detector agreement is claimed but asserted only in two separate places.** The conclusion says two independent detectors converge on the same account; today `tests/test_scenarios.py:50` pins the typology detector and `:130-132` pins the network detector, each in isolation. Nothing fails if one detector silently starts naming a different account. | claim: `manuscript/04_conclusion.md:18-20`, `manuscript/03_results.md:100`; assertions: `tests/test_scenarios.py:50,130-132` | One test computes both snapshots and asserts they name the *same* account, with a negative control showing the assertion goes red when one detector's verdict is redirected to a different player. | `uv run pytest tests/test_scenarios.py -k agreement -v` |
| V4 | **The AA-vs-KK oracle is measurably blind to hand-category ranking swaps.** Measured, not assumed: `best_hand` selecting the worst five-card subset moves it to 72.6% (red), but 6 of 7 category-ranking swaps moved it by <0.1 point and passed inside the ±2.0 tolerance. Those swaps are caught only by the separate ranking oracle. Carried forward from `../output/verify/casino_royale_2006.unresolved.json` item 2. | `tests/test_poker_engine.py:268-290` (oracle), `:228` / `:243` (the ranking/kicker oracles that cover the gap) | One oracle covers both — either exact preflop enumeration (C(48,5) per matchup) replacing the sampled measurement, or a published matchup chosen so that category order decides the result. Demonstrated by re-running the 7 ranking-swap injections against the equity oracle alone and getting 7/7 red. | `uv run pytest tests/test_poker_engine.py -k published -v`, then re-inject each swap in `poker_engine.py` and confirm this test alone fails |
| V5 | **No `fold` has ever been produced on the production path.** The canonical scenario always clears the pot-odds threshold, so `scenarios.poker_snapshot` has only ever emitted `raise`/`call`. `recommend_action` returning `fold` is proven only in unit tests (`tests/test_poker_engine.py:354`, `:360`), never through the snapshot the manuscript, the figures, and `mission.execute` all read. | path: `src/casino_royale_2006/scenarios.py:143-192`; constants `POKER_POT`/`POKER_TO_CALL` at `:66-67` | A second scenario (parameterized pot/to-call, not a second canonical scene) whose correct answer is `fold` is run through `poker_snapshot` and asserted, so the snapshot path is shown able to say no. | `uv run pytest tests/test_scenarios.py -k fold -v` |

### Documentation

| # | What is wrong | Where | Done looks like | Command |
|---|---|---|---|---|
| D1 | **The no-mock table still presents the AA-vs-KK equity check as the poker oracle, full stop.** It names neither the measured blind spot (category-ranking swaps move it <0.1 point) nor the two oracles that actually cover ranking and kicker precedence. The split scope is stated on the tests themselves and in `docs/_generated/COUNTS.md`, but a reader of the doctrine doc gets an overstated claim — the same class of defect the audit opened as SEVERE against this exact row. | `docs/testing_philosophy.md:17` | The row names all three oracles and states the equity oracle's measured sensitivity boundary, matching the docstrings at `tests/test_poker_engine.py:14-22` and `:277-282`. | `grep -n "category_ranking\|kicker" docs/testing_philosophy.md` returns the row |

### Extension (genuine future work, suite-level)

These are declared integration points with sibling packages, not gaps in this
package. Each states today's state and the acceptance criterion, so the swap
can be verified rather than assumed.

| # | Work | Current state | Done looks like | Command |
|---|---|---|---|---|
| X1 | Delegate provenance persistence to `bond_utilities.mission_io.record_provenance_outcome`. **Now unblocked** — the helper exists at `../bond-utilities/src/bond_utilities/mission_io.py:153`. Note before adopting: it stamps `started_at` from `datetime.now(timezone.utc)` unless `started_at=`/`now=` are supplied, which would violate this package's zero-wall-clock determinism rule (see the "Deterministic" bullet in `AGENTS.md`) and break `tests/test_scripts_smoke.py::test_regeneration_is_byte_identical_across_a_clock_tick` if the value ever reached a persisted artifact. | `mission.py:237-242` builds a `Provenance` inline (the frozen protocol requires the object, `wall_time_s=0.0` at `:241`) and persists nothing to disk; `bond-utilities` is not a dependency (`pyproject.toml:18-22` lists only `bond-api`, `matplotlib`, `pyyaml`). | `execute` writes through the shared helper with an injected timestamp, `MissionOutcome`'s public shape and field values are unchanged, and reruns stay byte-identical — proven by `tests/test_mission.py` passing untouched. | `uv run pytest tests/test_mission.py -v` and `uv run python scripts/run_execute.py` twice, diffing the output |
| X2 | Bind the film through an entry-point registry if the suite adopts one. | No registry exists. `bond-orchestrator` binds real films by lazy slug import via `../bond-orchestrator/src/bond_orchestrator/film_providers.py` (`load_film_providers`); reference providers in `providers.py` are a separate, deliberately unrelated registry. `scripts/00_preflight.py` performs exactly the orchestrator's check. | The package is discoverable both ways during any transition, with `MissionProvider.film == "casino_royale_2006"` (`mission.py:68`) still authoritative. | `uv run python scripts/00_preflight.py` |
| X3 | Adopt `bond-utilities` ciphers/clock for mission naming and timestamp handling if a later phase needs them. | Not used. The codename is the module constant `_CODENAME` (`mission.py:46`) and provenance carries no clock (`wall_time_s=0.0`, `mission.py:241`). | The dependency appears only in `mission.py`/`scripts/`, and the eight domain cores still import with `bond-utilities` absent. | `uv run python -c "import casino_royale_2006.poker_engine, casino_royale_2006.icm"` in an env without bond-utilities |

## Known limitations (not bugs)

Accepted and deliberate. Recorded here so they are not re-litigated as defects.

- **The AA-vs-KK equity oracle's ±2.0-point tolerance is a judgement call, not
  a derived requirement.** It is justified by measurement — s.e. ≈ 0.46 points
  at 200 runouts × 36 suit combinations, so the tolerance is ≈4 s.e. — and the
  test is deterministic under the fixed seed, so it cannot flake. The honest
  scope: *if the sampling budget in
  `tests/test_poker_engine.py:268-290` is ever changed, the tolerance must be
  re-derived from the new standard error.* Nothing in the suite enforces that
  today. (From `../output/verify/casino_royale_2006.unresolved.json` item 3.)
- **The equity oracle covers the equity pipeline, not hand-category ranking.**
  This is the audit-forced softening of the original doc claim. Ranking and
  kicker precedence are covered instead by
  `test_category_ranking_matches_the_published_order` and
  `test_within_category_tiebreaks_follow_the_published_kicker_order` (red on
  7/7 injected evaluator defects). Unifying them into one oracle is V4 above;
  the *split* itself is accepted and sound.
- **The domain cores are engineering exemplars, not licensed systems.** The
  per-module non-claims (ICM's proportional-finish assumption, the untuned
  laundering thresholds, declared-not-fitted Dirichlet priors, the un-calibrated
  network risk score, the fixed-cost route model, non-medical toxicology) are
  stated in `manuscript/07_scope_and_related_work.md` and are deliberate scope,
  not backlog.
- **Only one canonical scenario exists** (`scenarios.py`, `SEED = 17`). That is
  the design: one number computed once is the number shown everywhere. V5 asks
  for a *parameterized* negative control, not a second canonical scene.
- **Published.** Canonical remote is
  <https://github.com/docxology/bond-casino_royale_2006> (`main`); `bond-api`
  is vendored at `vendor/bond-api`, not an index package.

## Verification

Every command below was run at the commit that introduced this file; the stated
outcome is what it produced.

```bash
cd bond-casino_royale_2006

uv run pytest tests/ --cov=src --cov-fail-under=90 -q
#   -> 190 passed; TOTAL 97.13% line+branch; "Required test coverage of 90% reached"

uv run ruff check src/ scripts/ tests/          # -> All checks passed!
uv run ruff format --check src/ scripts/ tests/ # -> 38 files already formatted
uv run mypy src/ scripts/                       # -> no issues found in 23 source files

uv run python scripts/00_preflight.py                    # -> protocol conformance + slug, exit 0
uv run python scripts/z_generate_manuscript_variables.py # -> 66 tokens, 9 sections, 4 figures, exit 0
#   exits 1 on an unresolved {{TOKEN}} or a malformed single-brace {TOKEN}

grep -rn "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ src/ || echo Clean
rg "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo Clean

git status --short   # -> empty after commit
```

If `uv` reports `Failed to initialize cache` or `Operation not permitted`, that
is a sandbox restriction, not a package failure — re-run with the sandbox
disabled. After any change that moves the numbers, regenerate
`docs/_generated/COUNTS.md` from a real run rather than editing it.


## Round-2 (2026-08-06) - hostile-review hardening + verification closure

**Agent:** round-2 improvement pass. Baseline to final: tests 199->207 passed (0
skipped / 0 failed); line+branch coverage **97.15% -> 97.51%** on `src/`
(`--cov-fail-under=90`). `ruff check`, `ruff format --check`, `mypy src/
scripts/`, `scripts/00_preflight.py`, and
`scripts/z_generate_manuscript_variables.py` (66 tokens, 9 sections, 4 figures)
all exit 0. Working tree committed clean.

### Findings (hostile review) and fixes, with test evidence

| # | Finding | Where | Fix | Regression / negative-control test |
|---|---|---|---|---|
| R2-1 | **Offsuit starting-hand classes could be drawn as *suited* pairs.** `_cards_for_class` picked the low card independently of the high card's suit, so `AKo`/`AQo`/`AJo`/`KQo` returned a same-suit pair ~25% of the time - silently substituting AKs for AKo and tilting the sampled opponent range (and the equity it prices) toward suited hands. Measured before the fix: 189 same-suit per 800 draws per class (approximately the published 25%). | `poker_engine.py::_cards_for_class` | The offsuit branch now constrains the low card to a suit the high card does not occupy; if no such live low card exists the class is declared un-drawable (`None`), which the caller already tolerates. | `tests/test_poker_engine.py::test_offsuit_range_hands_never_share_a_suit` - 0 same-suit pairs across 60 seeds x 4 offsuit classes over the canonical dead set (previously ~25%). |
| R2-2 | **`exact_icm_equity` raised `ZeroDivisionError` on multi-busted states.** The recursion divides by `total = sum(remaining)`; when an ICM win/lose probe leaves a surviving set with zero total chips (e.g. `bubble_factor` over a field that already holds a busted 0-stack short stack), `remaining[target]/total` divides by zero. Verified: `icm.bubble_factor((10,1,0),(20,0,0),0)` raised `division by zero` before the fix. | `icm.py::exact_icm_equity._eq` | When `total == 0` (all survivors busted) the next prize is shared equally among them - no division by zero; the probe now returns the hand-derived bubble factor 10.0. | `tests/test_icm.py::test_bubble_factor_tolerates_a_field_with_a_busted_short_stack` and `test_exact_icm_shares_the_next_prize_over_a_zero_stack_mass`. |

### Verification closure (previously-open TODO items now bound by a failing-capable test)

| Item | New test binding |
|---|---|
| **V1** (round-trip never ran inside `detect`) | `tests/test_laundering_detect.py::test_detect_round_trip_contributes_a_ring_reason` drives `detect` with a ring flow and asserts the `roundtrip:1` reason plus score; `laundering_detect.py` 286-289 leave the Missing column. |
| **V2** (residual edge branches) | Tie branch: `tests/test_poker_engine.py::test_exact_equity_records_ties_on_a_paired_flop`. `inf` bubble factor: `tests/test_icm.py::test_bubble_factor_returns_inf_when_doubling_cannot_grow_equity`. |
| **V3** (cross-detector agreement) | `tests/test_scenarios.py::test_cross_detector_agreement_on_the_named_suspect` - both layers catch Le Chiffre, and *only* Le Chiffre (negative control on the name). |
| **V5** (never a `fold` on the production snapshot path) | `poker_snapshot` gained optional `pot`/`to_call` overrides (defaults = the canonical constants; this is a *parameterized* negative control, not a second canonical scene); `tests/test_scenarios.py::test_poker_snapshot_can_recommend_fold_at_an_unfavourable_price` proves the same snapshot path can refuse a hand. |

### Manuscript

- `manuscript/02_methodology.md` now states the range-fidelity guarantee (an
  offsuit class is always sampled with two different suits).
- Regenerated `output/data/manuscript_variables.json` + resolved prose + the 4
  figures; byte-identical across a clock tick. The corrected range moved the
  live poker-equity token to **45.62%** - a direct, live consequence of R2-1.

### Final gate numbers (this commit)

- **207 passed, 0 skipped, 0 failed; 97.51% line+branch** on `src/`.
- `ruff check` / `ruff format --check` (38 files) / `mypy src/ scripts/` (23
  files) all clean; `00_preflight.py` exit 0.
- `z_generate_manuscript_variables.py`: 66 tokens, 9 sections, 4 figures, exit 0.

### Left for a future round

- `opponent_bayes.py:103` (uniform-posterior fallback on `total <= 0`) is
  *provably unreachable* - the maximum log-weight maps to `exp(0)=1`, so
  `total >= 1` always. Consider removing it as dead defensive code (low risk,
  low priority).
- `poker_engine.py` `None`-return branches from `_cards_for_class` (undrawable
  classes) are guarded by the caller but not individually pinned; a test showing
  `iter_opponent_hands` yields *fewer* hands (no crash) when a class is
  undrawable on a near-full board would close them.
- `urban_routes.py:309,316,318` (`brute_force_path` depth cap + infeasible-edge
  skip) remain un-pinned; a small-graph brute-force cross-check under a depth
  cap would cover them.
