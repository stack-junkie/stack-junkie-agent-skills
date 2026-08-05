from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = "src/version.py"
CHANGELOG_FILE = "CHANGELOG.md"
RELEASE_ONLY = {"VERSION", VERSION_FILE, CHANGELOG_FILE, "package.json", "README.md"}
MATERIAL_PREFIXES = ("skill/", "scripts/", ".githooks/")
MATERIAL_FILES = {"AGENTS.md", "LICENSE", ".gitignore"}
VERSION_RE = re.compile(r'__version__\s*=\s*["\']([^"\']+)["\']')


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if check and result.returncode != 0:
        raise SystemExit(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def version_from_text(text: str) -> str | None:
    match = VERSION_RE.search(text)
    return match.group(1) if match else None


def current_version() -> str:
    version = version_from_text((ROOT / VERSION_FILE).read_text(encoding="utf-8"))
    if not version:
        raise SystemExit(f"Could not read current version from {VERSION_FILE}")
    return version


def version_at(ref: str) -> str | None:
    return version_from_text(git("show", f"{ref}:{VERSION_FILE}", check=False))


def is_material(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized in RELEASE_ONLY:
        return False
    return normalized in MATERIAL_FILES or normalized.startswith(MATERIAL_PREFIXES)


def changelog_has(version: str, ref: str | None = None) -> bool:
    if ref:
        content = git("show", f"{ref}:{CHANGELOG_FILE}", check=False)
    else:
        content = (ROOT / CHANGELOG_FILE).read_text(encoding="utf-8")
    return f"## [{version}]" in content


def staged_files() -> list[str]:
    return [line for line in git("diff", "--cached", "--name-only", "--diff-filter=ACMR").splitlines() if line]


def fail(message: str) -> int:
    print("Release metadata check failed:")
    print(f"  {message}")
    print(f"Every material source-skill change needs {VERSION_FILE} and {CHANGELOG_FILE} updates.")
    return 1


def check_staged() -> int:
    files = staged_files()
    material = [path for path in files if is_material(path)]
    if not material:
        print("  no material staged changes requiring release metadata")
        return 0

    missing = [path for path in [VERSION_FILE, CHANGELOG_FILE] if path not in files]
    if missing:
        return fail("Missing staged file(s): " + ", ".join(missing))

    new_version = current_version()
    old_version = version_at("HEAD")
    if old_version == new_version:
        return fail(f"{VERSION_FILE} is staged but version did not change from HEAD ({new_version}).")
    if not changelog_has(new_version):
        return fail(f"{CHANGELOG_FILE} does not contain a '## [{new_version}]' entry.")

    print(f"  release metadata present for v{new_version}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Require release metadata for source-skill changes")
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args()
    if args.staged:
        return check_staged()
    parser.error("Choose --staged")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
