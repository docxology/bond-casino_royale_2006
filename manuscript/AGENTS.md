---
title: "Manuscript directory: casino_royale_2006"
type: "manuscript_guide"
version: "0.1.0"
---

# Manuscript (`projects/working/bond/casino_royale_2006/manuscript/`)

Agent rules for this film's manuscript. The repository-wide read-first rules
live in `docs/agent_instructions.md`; this file covers manuscript-specific
editing: token protocol, figure protocol, and section workflow.

## File inventory

| File / Pattern | Role |
|---|---|
| `00_abstract.md` .. `07_scope_and_related_work.md`, `99_references.md` | The prose sections. Every computed number must be a `{{TOKEN}}`. |
| `config.yaml` | Identity + keywords + publication metadata. Consumed by `manuscript_variables.py`. |
| `SYNTAX.md` | Token + figure + citation syntax reference (may contain literal `{{VARIABLE}}` illustrations). |
| `references.bib` | Descriptive bibliography (local-only tree: no remote DOIs). |
| `preamble.md`, `layer_contract.yaml`, `AGENTS.md`, `README.md` | LaTeX injection, layer contract, and human/agent guides. |

## Token protocol

- Numeric/identity values from `manuscript/config.yaml` or the engines **must**
  use `{{NAME}}` syntax; never hardcode a computed metric in prose.
- Source of truth: `src/casino_royale_2006/manuscript_variables.py::generate_variables()`.
- Gate: `tests/test_manuscript_variables.py` — every `{{NAME}}` appearing in a
  numbered prose section must exist in the mapping.

## Figure protocol

All figures rendered by `src/casino_royale_2006/figures/plotting.py` to
`output/figures/`, referenced with Pandoc-crossref (`{#fig:...}` /
`[@fig:...]`). See `SYNTAX.md` for the label registry.

## Section modification workflow

1. Change behavior in `src/`; update `scenarios.py` constants if the scenario
   changed.
2. Update the affected prose section(s); use `{{TOKEN}}`s for any numeric result.
3. If a new token is introduced, add it to `generate_variables()`.
4. Run `scripts/z_generate_manuscript_variables.py` (strict by default).
5. Run the full gate: `pytest`, `ruff`, `mypy`, lineage `rg`, clean tree.
