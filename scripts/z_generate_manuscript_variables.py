"""Hydrate manuscript ``{{TOKEN}}``s and render figures for LE CHIFFRE.

Thin orchestrator: bootstrap src/, compute the token variables, write
``output/data/manuscript_variables.json``, resolve ``manuscript/[0-9]*.md`` to
``output/manuscript/``, and render the four manuscript figures
(``poker_decision``, ``digitalis_curve``, ``cfr_convergence``, ``icm_bubble``)
to ``output/figures/``.

Deterministic given config. Two gates run at the end and both fail the script
(exit 1) rather than warning: an *unresolved* ``{{TOKEN}}`` left in the output,
and a *malformed* single-brace ``{TOKEN}`` in the source that would never have
been substituted at all. ``--allow-draft`` downgrades both to warnings for
early drafts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from casino_royale_2006 import scenarios  # noqa: E402
from casino_royale_2006.figures.plotting import (  # noqa: E402
    render_cfr_convergence,
    render_digitalis_curve,
    render_icm_bubble,
    render_poker_decision,
)
from casino_royale_2006.manuscript_variables import (  # noqa: E402
    find_malformed_tokens,
    generate_variables,
    project_root,
    resolve_manuscript_tree,
)


def main(argv: list[str] | None = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]
    allow_draft = "--allow-draft" in args

    root = project_root()
    variables = generate_variables()

    data_dir = root / "output" / "data"
    figures_dir = root / "output" / "figures"
    data_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    json_path = data_dir / "manuscript_variables.json"
    json_path.write_text(json.dumps(variables, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    _out_dir, written, unresolved = resolve_manuscript_tree(variables)

    poker_fig = render_poker_decision(
        figures_dir / "poker_decision.png", scenarios.poker_snapshot()
    )
    poison_fig = render_digitalis_curve(figures_dir / "digitalis_curve.png")
    cfr_fig = render_cfr_convergence(figures_dir / "cfr_convergence.png")
    icm_fig = render_icm_bubble(figures_dir / "icm_bubble.png")

    print(f"wrote {len(variables)} tokens -> {json_path}")
    print(f"resolved {written} manuscript sections -> {_out_dir}")
    print(f"figure -> {poker_fig}")
    print(f"figure -> {poison_fig}")
    print(f"figure -> {cfr_fig}")
    print(f"figure -> {icm_fig}")

    malformed = sorted(
        {
            name
            for section in sorted((root / "manuscript").glob("[0-9]*.md"))
            for name in find_malformed_tokens(section.read_text(encoding="utf-8"))
        }
    )

    failed = False
    if unresolved:
        print(f"UNRESOLVED TOKENS: {', '.join(unresolved)}", file=sys.stderr)
        failed = True
    if malformed:
        print(
            f"MALFORMED SINGLE-BRACE TOKENS (use {{{{NAME}}}}): {', '.join(malformed)}",
            file=sys.stderr,
        )
        failed = True
    return 1 if (failed and not allow_draft) else 0


if __name__ == "__main__":
    raise SystemExit(main())
