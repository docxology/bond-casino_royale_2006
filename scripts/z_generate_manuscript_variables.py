"""Hydrate manuscript ``{{TOKEN}}``s and render figures for LE CHIFFRE.

Thin orchestrator: bootstrap src/, compute the token variables, write
``output/data/manuscript_variables.json``, resolve ``manuscript/[0-9]*.md`` to
``output/manuscript/``, and render the two manuscript figures to
``output/figures/``. Deterministic given config; ``--allow-draft`` skips the
strict unresolved-token gate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from casino_royale_2006 import scenarios  # noqa: E402
from casino_royale_2006.figures.plotting import (  # noqa: E402
    render_digitalis_curve,
    render_poker_decision,
)
from casino_royale_2006.manuscript_variables import (  # noqa: E402
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

    print(f"wrote {len(variables)} tokens -> {json_path}")
    print(f"resolved {written} manuscript sections -> {_out_dir}")
    print(f"figure -> {poker_fig}")
    print(f"figure -> {poison_fig}")

    if unresolved:
        print(f"UNRESOLVED TOKENS: {', '.join(unresolved)}", file=sys.stderr)
        if not allow_draft:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
