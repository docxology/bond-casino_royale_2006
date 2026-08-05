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
import time
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


#: The artifact set the package's byte-identical-regeneration claim covers
#: (``manuscript/06_reproducibility.md``): the token mapping and the resolved
#: prose. Figures are excluded there and excluded here, in the same words.
_CLAIMED_ARTIFACTS = ("output/data/*.json", "output/manuscript/*.md")


def _claimed_artifact_bytes() -> dict[str, bytes]:
    """Read every artifact covered by the byte-identical claim, keyed by path."""
    found: dict[str, bytes] = {}
    for pattern in _CLAIMED_ARTIFACTS:
        for path in sorted(ROOT.glob(pattern)):
            found[str(path.relative_to(ROOT))] = path.read_bytes()
    return found


def _wait_for_wall_clock_tick(limit_s: float = 2.0) -> None:
    """Block until the wall clock's whole-second field advances."""
    start = time.time()
    while int(time.time()) == int(start):
        if time.time() - start > limit_s:  # pragma: no cover - clock never froze
            raise AssertionError("wall clock did not advance")
        time.sleep(0.02)


def test_regeneration_is_byte_identical_across_a_clock_tick():
    """Run the real generator twice; the claimed artifacts must not move a byte.

    This is the end-to-end binding for the package's stated reproducibility
    property. It deliberately does *not* inject a fixed timestamp: an injected
    clock is exactly how a wall-clock leak survived here before, because the
    injected-``now`` test never exercised the production default. The only
    thing that changes between the two runs is real time, and the second run
    is forced across a whole-second boundary so a second-resolution stamp
    cannot coincide.
    """
    first_run = _run("z_generate_manuscript_variables.py")
    assert first_run.returncode == 0, first_run.stderr
    before = _claimed_artifact_bytes()
    assert before, "expected claimed artifacts on disk after a generator run"

    _wait_for_wall_clock_tick()

    second_run = _run("z_generate_manuscript_variables.py")
    assert second_run.returncode == 0, second_run.stderr
    after = _claimed_artifact_bytes()

    assert sorted(after) == sorted(before), "regeneration changed the artifact set"
    drifted = sorted(name for name in before if before[name] != after[name])
    assert not drifted, (
        "regeneration is not byte-identical; these artifacts changed between "
        f"two runs of the same generator: {', '.join(drifted)}"
    )


def test_manifest_variables_script_writes_artifacts():
    result = _run("z_generate_manuscript_variables.py")
    assert result.returncode == 0, result.stderr
    data = json.loads((ROOT / "output/data/manuscript_variables.json").read_text(encoding="utf-8"))
    assert data["POKER_ACTION"] in {"fold", "call", "raise"}
    assert (ROOT / "output/figures/poker_decision.png").is_file()
    assert (ROOT / "output/figures/digitalis_curve.png").is_file()
