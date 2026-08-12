#!/usr/bin/env python3
"""Run the canonical Repo Readiness policy shipped in this collection."""

from pathlib import Path
import runpy


POLICY = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "repo-readiness"
    / "scripts"
    / "repo_policy.py"
)

runpy.run_path(str(POLICY), run_name="__main__")
