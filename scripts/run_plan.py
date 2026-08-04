"""Mission phase CLI: PLAN - print the LE CHIFFRE mission plan.

Thin orchestrator: bootstrap src/, build the provider, log brief + plan.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from casino_royale_2006.mission import MissionProvider  # noqa: E402


def main() -> int:
    provider = MissionProvider()
    brief = provider.brief()
    plan = provider.plan(brief)
    print(f"PLAN for {brief.film} / {brief.codename}: {len(plan.steps)} steps")
    for step in plan.steps:
        print(f"  - {step.name}: {step.action} {step.params}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
