from __future__ import annotations

import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION = ROOT / "skill" / "repo-readiness" / "scripts" / "repo_policy.py"

if not IMPLEMENTATION.exists():
    raise SystemExit(f"Policy implementation not found: {IMPLEMENTATION}")

runpy.run_path(str(IMPLEMENTATION), run_name="__main__")
