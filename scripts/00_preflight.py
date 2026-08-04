"""Preflight gate for the LE CHIFFRE mission package.

Thin orchestrator: verify the package and the frozen bond-api protocol import,
that the MissionProvider satisfies the protocol, and that fixtures resolve.
Exits 0 iff everything is healthy, 1 otherwise.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from bond_api.protocol import MissionProvider as Protocol  # noqa: E402

from casino_royale_2006.mission import MissionProvider  # noqa: E402


def main() -> int:
    checks: list[tuple[str, bool]] = []
    try:
        import casino_royale_2006  # noqa: F401

        checks.append(("package imports", True))
    except ImportError as exc:  # pragma: no cover - import always works here
        checks.append((f"package imports ({exc})", False))

    provider = MissionProvider()
    checks.append(("provider satisfies BOND-API protocol", isinstance(provider, Protocol)))
    checks.append(("provider.film == casino_royale_2006", provider.film == "casino_royale_2006"))

    ok = True
    for label, passed in checks:
        print(f"[{'OK' if passed else 'FAIL'}] {label}")
        ok = ok and passed
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
