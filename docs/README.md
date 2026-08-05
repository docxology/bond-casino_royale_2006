# docs/ — LE CHIFFRE documentation

This directory is the behavioural rulebook for the **Casino Royale (2006) / LE
CHIFFRE** mission package. Everything here is a hard constraint on agents and
contributors working inside the package, not background reading. It documents
*this* package — the eight domain modules, the frozen protocol binding, and the
gates — never the exemplar the tree was forked from.

## What is here

| File | Holds | Read it before |
|---|---|---|
| `agent_instructions.md` | Seven hard operating rules, each with the failure it prevents, plus the full verification checklist. | Touching **any** file. |
| `architecture.md` | Module-by-module architecture of `src/`: what each of the eight cores computes, how `scenarios.py` and `gadgets.py` compose them, how `mission.py` implements the frozen `MissionProvider` stage by stage, and the forbidden patterns. | Editing `src/` or `scripts/`. |
| `testing_philosophy.md` | The no-mock / real-data / determinism doctrine as it applies here: what replaces a mock in each module, which seeds are fixed, what makes an assertion count, and the per-file test inventory. | Writing or changing a test. |
| `protocol.md` | How this package binds to the frozen BOND-API: the path dependency, the adapter, the five stages, gadget registration, and slug discovery. | Changing `mission.py` or `pyproject.toml`. |
| `style_guide.md` | Seven style rules for code, docs, type hints, and error messages. | Writing code or prose. |
| `AGENTS.md` | The index/hub view of this directory with the key conventions restated. | Orienting. |
| `_generated/COUNTS.md` | Live test count and measured coverage, regenerated from a real gate run — never hand-edited. | Quoting any number. |

## Reading order

1. `agent_instructions.md` — the rules.
2. `architecture.md` — where code is allowed to live.
3. `testing_philosophy.md` — how it must be proved.
4. `style_guide.md` — how it must read.
5. `protocol.md` — how it binds to the rest of the suite.

## The two things that most often go wrong here

- **Reshaping `mission.py`.** Its five stages, `film`, `register_gadgets`, and
  `GADGET_REGISTRY` are consumed by bond-cli, the coordinator, and the
  orchestrator across packages. Deepen inside the package; leave the surface
  alone. See `protocol.md`.
- **Hand-authoring a number.** Every measured value in the manuscript is a
  `{{TOKEN}}` from `manuscript_variables.py`. Note the *double* braces: a
  single-brace `{TOKEN}` is never substituted and used to slip straight past
  the unresolved-token gate, which is why `find_malformed_tokens()` now exists
  and fails the generator. See `testing_philosophy.md`.
