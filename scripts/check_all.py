#!/usr/bin/env python3
"""Run every local validation and test suite in the Agent Skills monorepo."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"


def run(command: list[str], environment: dict[str, str]) -> int:
    print(f"[check] {' '.join(command)}", flush=True)
    return subprocess.run(command, cwd=ROOT, env=environment).returncode


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="agent-skills-pycache-") as cache:
        environment = os.environ.copy()
        environment["PYTHONPYCACHEPREFIX"] = cache
        if run([sys.executable, "scripts/check_collection.py"], environment):
            return 1
        suites = sorted(path for path in TESTS.iterdir() if path.is_dir() and not path.name.startswith("."))
        for suite in suites:
            relative = suite.relative_to(ROOT)
            if run(
                [sys.executable, "-m", "unittest", "discover", "-s", str(relative), "-p", "test_*.py"],
                environment,
            ):
                return 1
    print(f"[ok] validated the collection and {len(suites)} test suites")
    return 0


if __name__ == "__main__":
    sys.exit(main())
