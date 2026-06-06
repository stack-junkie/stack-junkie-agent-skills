from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_PATH = ROOT / "src" / "version.py"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[0-9A-Za-z]+(\.[0-9A-Za-z]+)*)?$")


def read_version() -> str:
    content = VERSION_PATH.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        raise SystemExit("Could not find __version__ in src/version.py")
    version = match.group(1)
    if not SEMVER.match(version):
        raise SystemExit(f"Invalid semantic version: {version}")
    return version


def update_file(path: Path, next_content: str, check: bool) -> bool:
    previous = path.read_text(encoding="utf-8") if path.exists() else ""
    if previous == next_content:
        print(f"  {path.relative_to(ROOT)} already synced")
        return False
    if check:
        print(f"[drift] {path.relative_to(ROOT)}")
        return True
    path.write_text(next_content, encoding="utf-8", newline="\n")
    print(f"[sync] {path.relative_to(ROOT)}")
    return True


def sync_readme(version: str, check: bool) -> bool:
    path = ROOT / "README.md"
    content = path.read_text(encoding="utf-8")
    content = re.sub(r"^# Repo Readiness ckvam v[^\n]+", f"# Repo Readiness ckvam v{version}", content, count=1, flags=re.MULTILINE)
    content = re.sub(r"^- Version: `[^`]+`", f"- Version: `{version}`", content, count=1, flags=re.MULTILINE)
    return update_file(path, content, check)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync version from src/version.py")
    parser.add_argument("--check", action="store_true", help="Report drift without writing")
    args = parser.parse_args()

    version = read_version()
    drift = 0

    drift += update_file(ROOT / "VERSION", version + "\n", args.check)

    package_path = ROOT / "package.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    package["version"] = version
    drift += update_file(package_path, json.dumps(package, indent=2) + "\n", args.check)

    drift += sync_readme(version, args.check)

    if args.check and drift:
        print(f"\nVersion sync drift detected for {drift} file(s). Run: scripts\\run_python.cmd scripts\\sync_version.py")
        return 1

    print(f"\n[sync] Version sync complete: v{version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
