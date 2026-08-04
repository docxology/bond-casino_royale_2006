"""Shared pytest configuration for the LE CHIFFRE mission package.

Pins the matplotlib backend to Agg (headless, deterministic) and ensures the
package's ``src/`` is importable regardless of the working directory.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Matplotlib must be Agg BEFORE any plotting import so tests never open a
# display window or hang on a backend.
os.environ.setdefault("MPLBACKEND", "Agg")

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
