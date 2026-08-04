"""Mission phase CLI: EXECUTE - run the engines and print real results.

Thin orchestrator: bootstrap src/, build the provider, drive brief -> plan ->
execute, and print the outcome results plus provenance (deterministic seed).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from casino_royale_2006.mission import MissionProvider  # noqa: E402


def main() -> int:
    provider = MissionProvider()
    brief = provider.brief()
    plan = provider.plan(brief)
    outcome = provider.execute(plan)
    print(f"SUCCESS   : {outcome.success}")
    print(f"SEED      : {outcome.provenance.seed}")
    print(f"INPUT_HASH: {outcome.provenance.input_hash}")
    print(f"RESULTS   : {json.dumps(outcome.results, indent=2, sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
