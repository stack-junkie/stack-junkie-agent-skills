#!/usr/bin/env python3
"""Validate the portable Agent Skills packages in this collection."""

from __future__ import annotations

import py_compile
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER = re.compile(r"\A---\r?\n(?P<body>.*?)\r?\n---\r?\n", re.DOTALL)
LOCAL_ABSOLUTE = re.compile(r"(?:[A-Za-z]:[\\/]+Users[\\/]|/Users/[^/]+/|/home/[^/]+/)")


def metadata(text: str) -> dict[str, str]:
    match = FRONTMATTER.match(text)
    if not match:
        raise ValueError("SKILL.md lacks YAML frontmatter")
    values: dict[str, str] = {}
    for raw in match.group("body").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        key, separator, value = raw.partition(":")
        if not separator or not key.strip() or not value.strip():
            raise ValueError(f"Unsupported frontmatter line: {raw}")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def validate_skill(skill: Path) -> list[str]:
    errors: list[str] = []
    entrypoint = skill / "SKILL.md"
    if not entrypoint.is_file():
        return [f"{skill.name}: missing SKILL.md"]
    try:
        values = metadata(entrypoint.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        return [f"{skill.name}: {exc}"]
    if set(values) != {"name", "description"}:
        errors.append(f"{skill.name}: frontmatter must contain only name and description")
    name = values.get("name", "")
    description = values.get("description", "")
    if name != skill.name:
        errors.append(f"{skill.name}: frontmatter name does not match directory")
    if not NAME.fullmatch(name) or len(name) > 64:
        errors.append(f"{skill.name}: invalid Agent Skills name")
    if not description or len(description) > 1024:
        errors.append(f"{skill.name}: description must contain 1 to 1024 characters")
    for path in skill.rglob("*"):
        if not path.is_file() or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeError:
            continue
        if LOCAL_ABSOLUTE.search(content):
            errors.append(f"{path.relative_to(ROOT)}: contains a user-specific absolute path")
        if path.suffix.lower() == ".py":
            try:
                py_compile.compile(str(path), doraise=True)
            except py_compile.PyCompileError as exc:
                errors.append(f"{path.relative_to(ROOT)}: {exc.msg}")
    return errors


def main() -> int:
    if not SKILLS.is_dir():
        print("[error] missing skills directory")
        return 1
    skill_dirs = sorted(path for path in SKILLS.iterdir() if path.is_dir())
    if not skill_dirs:
        print("[error] no skills found")
        return 1
    errors = [error for skill in skill_dirs for error in validate_skill(skill)]
    for error in errors:
        print(f"[error] {error}")
    if errors:
        return 1
    print(f"[ok] validated {len(skill_dirs)} portable Agent Skills packages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
