"""Mission phase CLI: DEBRIEF - run the full five-stage mission and summarize.

Thin orchestrator: bootstrap src/, build the provider, call bond_api.run_mission
(brief -> recon -> plan -> execute -> debrief), then print outcome + lessons.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from bond_api.protocol import ReconRequest, run_mission  # noqa: E402

from casino_royale_2006.mission import MissionProvider  # noqa: E402


def main() -> int:
    debrief = run_mission(MissionProvider(), ReconRequest(goal="neutralize Le Chiffre"))
    outcome = debrief.outcome
    print(f"MISSION    : {outcome.results['film']} / {outcome.results['codename']}")
    print(f"SUCCESS    : {outcome.success}")
    print(f"STEPS DONE : {outcome.results['steps_completed']}")
    print(
        f"FLAGGED    : {outcome.results['laundering']['launderer_flagged']} "
        f"(score {outcome.results['laundering']['launderer_score']})"
    )
    print(
        f"EXTRACTION : fastest {outcome.results['extraction']['fastest_cost']} "
        f"(roof={outcome.results['extraction']['fastest_uses_roof']})"
    )
    print(
        f"POISON     : {outcome.results['poison']['toxicity_grade']} at "
        f"{outcome.results['poison']['digoxin_ng_ml']} ng/mL digoxin"
    )
    print("LESSONS:")
    for lesson in debrief.lessons:
        print(f"  - {lesson}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
