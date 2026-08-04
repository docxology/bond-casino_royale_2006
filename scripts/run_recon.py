"""Mission phase CLI: RECON - survey the LE CHIFFRE operation.

Thin orchestrator: bootstrap src/, build the provider, run recon against an
optional goal argument (default: neutralize Le Chiffre).

Usage: uv run python scripts/run_recon.py ["optional goal..."]
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from bond_api.protocol import ReconRequest  # noqa: E402

from casino_royale_2006.mission import MissionProvider  # noqa: E402

DEFAULT_GOAL = "neutralize Le Chiffre and recover the stake"


def main(argv: list[str] | None = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]
    goal = " ".join(args) if args else DEFAULT_GOAL
    report = MissionProvider().recon(ReconRequest(goal=goal))
    print(f"RECON GOAL: {goal}")
    print("FINDINGS:")
    for finding in report.findings:
        print(f"  - [{finding.label}] {finding.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
