"""Mission phase CLI: BRIEF - print the LE CHIFFRE mission brief.

Thin orchestrator: bootstrap src/, build the provider, print its brief.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from casino_royale_2006.mission import MissionProvider  # noqa: E402


def main() -> int:
    brief = MissionProvider().brief()
    print(f"FILM      : {brief.film}")
    print(f"CODENAME  : {brief.codename}")
    print("OBJECTIVES:")
    for objective in brief.objectives:
        print(f"  - {objective}")
    print("ASSETS:")
    for asset in brief.assets:
        print(f"  - {asset.kind}/{asset.name} = {asset.payload}")
    print("CONSTRAINTS:")
    for constraint in brief.constraints:
        print(f"  - {constraint.kind}: {constraint.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
