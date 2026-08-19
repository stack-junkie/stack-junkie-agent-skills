#!/usr/bin/env python3
"""Run the canonical repo-readiness policy implementation from its skill package."""

from pathlib import Path
import runpy


POLICY = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "repo-readiness"
    / "scripts"
    / "repo_policy.py"
)


if __name__ == "__main__":
    runpy.run_path(str(POLICY), run_name="__main__")
