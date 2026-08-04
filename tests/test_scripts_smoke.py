"""Subprocess smoke tests for the thin phase CLIs and manuscript generator.

Runs each script with the venv interpreter (``sys.executable``) from the
project root, asserting exit code 0 and meaningful output. Uses real files
under the git-ignored ``output/`` tree.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


def _run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


@pytest.mark.parametrize(
    ("script", "needle"),
    [
        ("00_preflight.py", "[OK]"),
        ("run_brief.py", "CODENAME"),
        ("run_recon.py", "FINDINGS"),
        ("run_plan.py", "PLAN"),
        ("run_execute.py", "SUCCESS"),
        ("run_debrief.py", "LESSONS"),
    ],
)
def test_phase_cli_exit_zero(script: str, needle: str):
    result = _run(script)
    assert result.returncode == 0, result.stderr
    assert needle in result.stdout


def test_manifest_variables_script_writes_artifacts():
    result = _run("z_generate_manuscript_variables.py")
    assert result.returncode == 0, result.stderr
    data = json.loads((ROOT / "output/data/manuscript_variables.json").read_text(encoding="utf-8"))
    assert data["POKER_ACTION"] in {"fold", "call", "raise"}
    assert (ROOT / "output/figures/poker_decision.png").is_file()
    assert (ROOT / "output/figures/digitalis_curve.png").is_file()
