# Style Guide

Seven style rules for the LE CHIFFRE package. Rules 1-3 govern code; 4-5
govern documentation; 6-7 govern type hints and error messages.

1. **Zero-mock, real computation.** Tests use real data and real algorithms;
   never a mock. (See `testing_philosophy.md`.)
2. **Pure core, thin adapter.** Domain modules import stdlib only; only
   `mission.py` touches `bond_api`. Never add an `infrastructure.*` or
   `bond_api` import to a core module.
3. **Thin orchestrators.** `scripts/` bootstraps and forwards; no math.
4. **Tokens, not hand-authored metrics.** Every computed number in the
   manuscript is a `{{TOKEN}}` from `manuscript_variables.py`.
5. **Explicit paths, show-not-tell.** Reference exact
   `module.py::function` locations; anchor prose to real code.
6. **Type hints everywhere.** Public APIs fully annotated; generic containers
   salted; mypy (`src/` + `scripts/`) must be clean.
7. **Actionable errors.** Raise `ValueError`/`KeyError` with context and the
   offending value; chain from the cause with `from`.

Formatting: `uv run ruff format` (100-char lines). Linting: `uv run ruff check`.
Docstrings: module-level narrative + one-liner summaries with Args/Returns/
Raises where non-obvious. Logging: not required in the pure core; the phase
CLIs print to stdout.
