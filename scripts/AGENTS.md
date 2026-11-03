# scripts/ — the phase CLIs

`00_preflight.py`, `run_brief.py`, `run_recon.py`, `run_plan.py`, `run_execute.py`,
`run_debrief.py`, `z_generate_manuscript_variables.py` and `__init__.py`.

## Rules

- **Thin phase CLIs.** They bootstrap `sys.path` and forward to `src/casino_royale_2006/`; the
  algorithms live in the domain modules.
- **`00_preflight.py` is part of the gate**: it checks protocol conformance and the slug. Run it
  before a phase, not instead of one.
- **`z_generate_manuscript_variables.py` writes tokens, prose and four figures**, and exits 1 on an
  unresolved `{{TOKEN}}` or a malformed single-brace `{TOKEN}` — `find_malformed_tokens` exists so
  double-brace substitution cannot pass silently.
- **Exit 0 iff the phase succeeded.** Report the code; do not describe a failed phase as complete.
- **`output/` is regenerable and git-ignored.** Never hand-edit it, and never hand-author a number
  into prose that a token should carry.
- **No sibling writes**: scope is this package directory, not `../bond-api`, the bond root or the
  template repository.
