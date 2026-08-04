# Manuscript Syntax & Token Protocol (LE CHIFFRE)

## `TOKEN` placeholders

Numeric results and identity values are injected as `{{NAME}}` tokens,
computed by `src/casino_royale_2006/manuscript_variables.py::generate_variables()`
from `manuscript/config.yaml` plus live engine output via `scenarios.py`.
Never hand-author a computed number in prose.

Pipeline: `scripts/z_generate_manuscript_variables.py` ->
`output/data/manuscript_variables.json` + resolved `output/manuscript/*.md`
+ figures. The strict gate fails on any unresolved token in a numbered prose
section (`[0-9]*.md`); pass `--allow-draft` to relax for early drafts.

## Adding a token

1. Add the key/value to `generate_variables()`.
2. Reference it as `{{NAME}}` in a `[0-9]*.md` section. The live cross-reference
   test (`tests/test_manuscript_variables.py`) fails if any prose token is
   missing from the mapping.
3. Re-run `scripts/z_generate_manuscript_variables.py`.

## Figures

Pandoc-crossref syntax. Define a figure with a `{#fig:label}` anchor and
reference it with `[@fig:label]` (parenthetical) or `@fig:label` (narrative).

| Label | File (PNG) | Renderer in `src/casino_royale_2006/figures/` |
|---|---|---|
| `{#fig:poker}` | `../output/figures/poker_decision.png` | `render_poker_decision()` |
| `{#fig:digitalis}` | `../output/figures/digitalis_curve.png` | `render_digitalis_curve()` |

## Citations

Use `@key` Pandoc citations backed by `references.bib`. Because the BOND tree
is local-only, entries are descriptive rather than DOI-linked.
