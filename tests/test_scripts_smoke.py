"""Subprocess smoke tests for the thin phase CLIs and manuscript generator.

Runs each script with the venv interpreter (``sys.executable``) from the
project root, asserting exit code 0 and meaningful output. Uses real files
under the git-ignored ``output/`` tree.
"""

from __future__ import annotations

import json
import os
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


_SNAPSHOT_SNIPPET = (
    "import json,sys; sys.path.insert(0, 'src');"
    "from casino_royale_2006 import scenarios;"
    "print(json.dumps(scenarios.full_snapshot(scenarios.SEED), sort_keys=True))"
)


def test_full_snapshot_is_identical_across_processes():
    """Determinism must survive a *new interpreter*, not just a second call.

    ``scenarios.poker_snapshot() == scenarios.poker_snapshot()`` cannot fail:
    within one process every hash-ordered container iterates the same way.
    The real hazard is cross-process - a set/frozenset iterated under a
    different ``PYTHONHASHSEED`` reorders, and the published equity moves while
    ``Provenance.input_hash`` (a hash of the *inputs*) stays identical. Two
    interpreters with deliberately different hash seeds is the failing case.
    """
    outputs = set()
    for hash_seed in ("0", "1", "12345"):
        env = {**os.environ, "PYTHONHASHSEED": hash_seed}
        proc = subprocess.run(
            [sys.executable, "-c", _SNAPSHOT_SNIPPET],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=180,
            env=env,
        )
        assert proc.returncode == 0, proc.stderr
        outputs.add(proc.stdout.strip())
    assert len(outputs) == 1, f"full_snapshot differs across PYTHONHASHSEED values: {outputs}"


def test_manifest_variables_script_writes_artifacts():
    result = _run("z_generate_manuscript_variables.py")
    assert result.returncode == 0, result.stderr
    data = json.loads((ROOT / "output/data/manuscript_variables.json").read_text(encoding="utf-8"))
    assert data["POKER_ACTION"] in {"fold", "call", "raise"}
    assert (ROOT / "output/figures/poker_decision.png").is_file()
    assert (ROOT / "output/figures/digitalis_curve.png").is_file()
