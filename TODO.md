# TODO — Casino Royale (2006) / LE CHIFFRE

Open work only. Completed build phases live in git history and in the
manuscript, not here — a TODO that lists finished work stops being read.

## Open — suite integration (blocked on siblings)

These are declared integration points, not gaps in this package. Each states
the current state and the acceptance criterion that closes it, so the swap can
be verified rather than assumed.

- [ ] **Delegate provenance persistence to `bond_utilities.mission_io.
      record_provenance_outcome`** once bond-utilities is converted.
      *Current:* `mission.py::execute` builds a `Provenance` inline (the frozen
      protocol requires the object) and persists nothing to disk.
      *Acceptance:* `execute` writes through the shared helper, with
      `MissionOutcome`'s public shape, its field values, and byte-identical
      reruns all unchanged — proven by `tests/test_mission.py` passing
      untouched.
- [ ] **Bind the film through an entry-point registry** if the suite adopts one
      in `bond-orchestrator` / `bond-cli`.
      *Current:* discovery is by slug import of `casino_royale_2006.mission` on
      `sys.path`, the frozen bond-api convention; `scripts/00_preflight.py`
      performs exactly the orchestrator's check.
      *Acceptance:* the package is discoverable both ways during the
      transition, with `film == "casino_royale_2006"` still authoritative.
- [ ] **Adopt `bond-utilities` ciphers/clock** for mission naming and timestamp
      handling if a later phase needs them.
      *Current:* not used; the codename is a module constant and provenance
      carries no clock at all.
      *Acceptance:* the dependency appears only in `mission.py`/`scripts/`, and
      the eight cores still import with bond-utilities absent.

## Open — package work

- [ ] **Reach the residual uncovered branches in `poker_engine.py` and
      `icm.py`.** Coverage clears the 90% gate comfortably, but the remaining
      misses are real error/edge branches, not dead code. Add the inputs that
      reach them rather than treating the gate margin as done.
- [ ] **Bind cross-detector agreement in one test.** The conclusion argues that
      the typology detector and the network detector independently converge on
      the same account. Each is currently asserted in its own test file; a
      single test that asserts *agreement* would make that claim falsifiable in
      one place instead of inferred from two.
- [ ] **Sharpen the AA-vs-KK external oracle, or replace it.** The published
      preflop equity check pins the equity pipeline to +/-2.0 points, which
      catches gross showdown-comparison defects (`best_hand` taking the worst
      subset measures 72.6%) but — measured, not assumed — is nearly blind to
      category-ranking swaps: demoting a full house below a flush moved it 0.03
      points. Those are caught instead by
      `test_category_ranking_matches_the_published_order`. An exact preflop
      enumeration (or a published matchup chosen so category order actually
      decides it) would make one oracle cover both.
- [ ] **Negative control on the poker recommendation.** The canonical scenario
      always clears the pot-odds threshold, so the snapshot path has never
      demonstrated a `fold`. A second scenario whose correct answer is `fold`
      would prove `recommend_action` can say no on the real path, not only in
      unit tests.

## Verification gate (must pass before any commit)

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
uv run ruff check src/ scripts/ && uv run ruff format --check src/ scripts/
uv run mypy src/ scripts/
uv run python scripts/z_generate_manuscript_variables.py   # exits 1 on token defects
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo Clean
rg "template[_]code_project" . --glob '!uv.lock' --glob '!.git/**' || echo Clean
git status --short   # clean after commit
```
