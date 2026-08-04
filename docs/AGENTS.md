# docs/ — Mission Documentation Hub

**Quick reference:** [Agent Instructions](agent_instructions.md) ·
[Architecture](architecture.md) · [Testing](testing_philosophy.md) ·
[Style](style_guide.md) · [Protocol](protocol.md)

## Purpose

The `docs/` directory is the behavioral rulebook for the **Casino Royale
(2006) / LE CHIFFRE** mission package. Every document here is a hard
constraint, not a suggestion.

| File | Purpose | Audience |
|---|---|---|
| `README.md` | This file — quick navigation. | Everyone |
| `agent_instructions.md` | Read-first behavioral constraints (7 hard rules + verification checklist). | Agents |
| `architecture.md` | Layered structure: pure core vs. adapter vs. scripts; forbidden patterns. | Developers |
| `testing_philosophy.md` | Zero-mock policy; coverage mechanics; live counts in `docs/_generated/COUNTS.md`. | Test authors |
| `style_guide.md` | 7 style rules for code, docs, type hints, error messages. | Code authors |
| `protocol.md` | How this film binds to the frozen BOND-API `MissionProvider`. | Integrators |
| `_generated/COUNTS.md` | Generated live test + coverage counts (regenerated, not hand-edited). | Everyone |

## Key conventions

- **Read-first.** Read `agent_instructions.md` before modifying any file;
  `testing_philosophy.md` before writing tests; `architecture.md` before
  touching `src/` or `scripts/` boundaries.
- **Purity of the core.** The four domain modules (`poker_engine.py`,
  `laundering_detect.py`, `urban_routes.py`, `poison_detect.py`) must not
  import `infrastructure.*` or `bond_api`; they stay importable standalone.
- **Thin orchestrators.** `scripts/` is glue (bootstrap + argv forwarding);
  all business logic lives in `src/`.
- **Zero mocks.** No `unittest.mock` / `MagicMock` / `@patch` /
  `create_autospec` anywhere in `tests/`.
- **Tokens, not prose numbers.** Manuscript metrics come from
  `manuscript_variables.py` + `scenarios.py`, injected as `{{TOKEN}}`s.

## Reading order

1. `agent_instructions.md`
2. `architecture.md`
3. `testing_philosophy.md`
4. `style_guide.md`
5. `protocol.md`
