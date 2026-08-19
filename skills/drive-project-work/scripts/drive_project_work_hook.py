#!/usr/bin/env python3
"""Codex lifecycle entrypoint for the installed drive-project-work guard."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


def load_guard():
    codex_home = Path(__file__).resolve().parents[1]
    guard_path = codex_home / "skills" / "drive-project-work" / "scripts" / "slice_guard.py"
    if not guard_path.is_file():
        raise RuntimeError(f"Installed slice guard not found: {guard_path}")
    specification = importlib.util.spec_from_file_location("drive_project_work_slice_guard", guard_path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"Could not load installed slice guard: {guard_path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def main() -> int:
    return int(load_guard().hook_main())


if __name__ == "__main__":
    sys.exit(main())
