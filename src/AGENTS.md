# src/ — eight domain cores, the catalogues and the adapter

`casino_royale_2006/`: `poker_engine.py`, `poker_cfr.py`, `icm.py`, `opponent_bayes.py`,
`laundering_detect.py`, `laundering_network.py`, `urban_routes.py`, `poison_detect.py`, plus
`scenarios.py` (the single canonical scenario), `gadgets.py` (the pure catalogue of published
callables), `mission.py`, `manuscript_variables.py`, `figures/` and `__init__.py`.

## Rules

- **The eight domain modules are pure**: standard library and the scientific stack only, importing no
  `infrastructure.*` and no `bond_api`. `mission.py` is the sole adapter to the frozen `bond_api`
  protocol.
- **`scenarios.py` owns the one canonical scenario.** A second scenario defined in a module or a
  script splits the experiment in two.
- **The adapter's public surface is frozen**: `film`, the five stages
  (`brief`/`recon`/`plan`/`execute`/`debrief`), `register_gadgets` and `GADGET_REGISTRY` are consumed
  by bond-cli, the coordinator and the orchestrator. Deepen inside the package; do not reshape them.
- **Determinism**: fixed seeds, no wall clock on the persisted-artifact path.
  `output/data/manuscript_variables.json` and `output/manuscript/*.md` are byte-identical across
  reruns (figures are outside that claim). Dates come from `manuscript/config.yaml`
  (`publication.date` → `{{MANUSCRIPT_DATE}}`), never `datetime.now()`.
- **Manuscript metrics are `{{TOKEN}}`s**, hydrated by `manuscript_variables.py`; never hand-authored
  in prose.
- **Coverage floor: 90% line and branch on `src/`.**
- **Publishing state as observed**: `origin` is
  `github.com/docxology/bond-casino_royale_2006` on `main`, and the package publishes there when
  green. The BOND suite copy under `projects/working/bond/` has no remote of its own — that is the
  arrangement the metadata comments describe, not a claim that this repository lacks its own remote.
