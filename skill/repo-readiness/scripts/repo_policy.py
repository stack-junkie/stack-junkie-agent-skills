from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
CONVENTIONAL = re.compile(
    r"^(?P<type>feat|fix|docs|refactor|perf|test|build|ci|chore|revert)"
    r"(?:\([a-z0-9._/-]+\))?(?P<breaking>!)?: .+"
)
IMPACT = re.compile(r"^Release-Impact: (none|patch|minor|major)$", re.MULTILINE)
BANNED_CHANGELOG = re.compile(
    r"\b(as discussed|continued work|in this chat|chat history|conversation|user prompt|"
    r"agent process|tests? (?:run|passed)|files? touched|miscellaneous improvements|various fixes)\b",
    re.IGNORECASE,
)
MARKER = "<!-- repo-readiness:v1 -->"
POLICY_KEYS = {
    "default_branch": "main",
    "branch_prefix": "codex/",
    "secret_scanning": "gitleaks-required",
}
README_PROJECT_TYPES = {"maintained-product", "library-or-tool", "skill"}
README_PLACEHOLDER = re.compile(
    r"\b(todo:\s*(?:describe|write|add)|replace (?:this|me)|your project description|lorem ipsum)\b",
    re.IGNORECASE,
)

HOOKS = {
    "_python.sh": """#!/bin/sh
run_repo_python() {
  if command -v py >/dev/null 2>&1; then py -3 "$@"
  elif command -v python3 >/dev/null 2>&1; then python3 "$@"
  else python "$@"; fi
}
""",
    "pre-commit": """#!/bin/sh
. "$(dirname "$0")/_python.sh"
run_repo_python scripts/repo_policy.py check-staged --repo .
""",
    "commit-msg": """#!/bin/sh
. "$(dirname "$0")/_python.sh"
run_repo_python scripts/repo_policy.py check-message --repo . "$1"
""",
    "pre-push": """#!/bin/sh
. "$(dirname "$0")/_python.sh"
run_repo_python scripts/repo_policy.py verify --repo .
""",
}

INSTALL_HOOKS = r'''$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
git -C $RepoRoot config core.hooksPath .githooks
if ((git -C $RepoRoot config --get core.hooksPath) -ne ".githooks") {
    throw "Failed to configure core.hooksPath"
}
Write-Host "[hooks] core.hooksPath=.githooks"
'''

AGENTS = f"""# Repository Instructions

{MARKER}

- Read the live repository, applicable instructions, and Git state before editing.
- Preserve unrelated dirty work and active processes.
- Add only files, features, documentation, tests, and automation required by the requested outcome.
- Repartition or serialize overlapping work. Use worktrees only for disjoint ownership.
- Keep `main` as the normal source of truth. Use short-lived `codex/*` branches only for risky or parallel work.
- Do not start unrelated work on a branch with unintegrated commits. Integrate, deliberately park, or report it first.
- Run focused checks, exercise the changed workflow when practical, and inspect the final diff.
- Do not stage, commit, tag, push, publish, create a remote, or open a pull request unless requested.
- `VERSION` is the only manually edited version source.
- Put notable ordinary changes under `CHANGELOG.md` `[Unreleased]` without bumping the version.
- Require the owner's exact version before preparing a release.
- Require a concise, current README for maintained products, libraries, tools, and skills. Review the whole README whenever it is touched.
- Require redacted Gitleaks checks for staged work, the current tree, and repository history when governing or releasing.
- Keep `.gitignore` relevant to the actual stack and do not add repository clutter.
- Keep GitHub Actions absent unless a concrete hosted need is approved.
"""


def fail(message: str) -> int:
    print(f"[error] {message}")
    return 1


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, encoding="utf-8")
    if check and result.returncode:
        raise ValueError(result.stderr.strip() or result.stdout.strip() or "Git command failed")
    return result


def is_repo_root(repo: Path) -> bool:
    result = git(repo, "rev-parse", "--show-toplevel", check=False)
    return result.returncode == 0 and Path(result.stdout.strip()).resolve() == repo.resolve()


def has_head(repo: Path) -> bool:
    return git(repo, "rev-parse", "--verify", "HEAD", check=False).returncode == 0


def valid_version(version: str) -> str:
    version = version.strip()
    if not SEMVER.fullmatch(version):
        raise ValueError(f"Invalid Semantic Version: {version!r}")
    return version


def version_key(version: str) -> tuple[Any, ...]:
    match = SEMVER.fullmatch(valid_version(version))
    assert match
    core = tuple(int(match.group(index)) for index in (1, 2, 3))
    prerelease = match.group(4)
    if prerelease is None:
        return (*core, (1,))
    parts = tuple((0, int(part)) if part.isdigit() else (1, part) for part in prerelease.split("."))
    return (*core, (0, *parts))


def load_config(repo: Path) -> dict[str, Any]:
    path = repo / ".repo-policy.json"
    if not path.exists():
        raise ValueError("Missing .repo-policy.json")
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != 1:
        raise ValueError("Unsupported policy schema_version")
    return config


def config_errors(config: dict[str, Any]) -> list[str]:
    errors = []
    for key, expected in POLICY_KEYS.items():
        if key not in config:
            errors.append(f"Policy config lacks {key}")
            continue
        value = config[key]
        if isinstance(expected, str) and not isinstance(value, str):
            errors.append(f"Policy config {key} must be a string")
        if isinstance(expected, list) and not isinstance(value, list):
            errors.append(f"Policy config {key} must be a list")
    if config.get("secret_scanning") != "gitleaks-required":
        errors.append("secret_scanning must be gitleaks-required")
    return errors


def repo_path(repo: Path, relative: str) -> Path:
    path = (repo / relative).resolve()
    try:
        path.relative_to(repo.resolve())
    except ValueError as exc:
        raise ValueError(f"Configured path leaves repository: {relative}") from exc
    return path


def read_version(repo: Path, config: dict[str, Any]) -> str:
    relative = str(config.get("canonical_version_file", "VERSION"))
    path = repo_path(repo, relative)
    if not path.exists():
        raise ValueError(f"Missing canonical version file: {relative}")
    return valid_version(path.read_text(encoding="utf-8"))


def json_value(document: dict[str, Any], dotted_key: str) -> Any:
    current: Any = document
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            raise ValueError(f"JSON key not found: {dotted_key}")
        current = current[part]
    return current


def set_json_value(document: dict[str, Any], dotted_key: str, value: str) -> None:
    parts = dotted_key.split(".")
    current: Any = document
    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            raise ValueError(f"JSON key not found: {dotted_key}")
        current = current[part]
    if not isinstance(current, dict) or parts[-1] not in current:
        raise ValueError(f"JSON key not found: {dotted_key}")
    current[parts[-1]] = value


def render_mirror(content: str, mirror: dict[str, Any], version: str) -> tuple[str, str]:
    kind = mirror.get("kind")
    if kind == "json":
        document = json.loads(content)
        key = str(mirror.get("key", "version"))
        current = json_value(document, key)
        if not isinstance(current, str):
            raise ValueError(f"Version mirror is not a string: {mirror.get('path')}")
        set_json_value(document, key, version)
        return current, json.dumps(document, indent=2) + "\n"
    if kind == "regex":
        pattern = mirror.get("pattern")
        replacement = mirror.get("replacement")
        if not isinstance(pattern, str) or not isinstance(replacement, str):
            raise ValueError(f"Regex mirror needs pattern and replacement: {mirror.get('path')}")
        match = re.search(pattern, content, re.MULTILINE)
        if not match or "version" not in match.groupdict():
            raise ValueError(f"Regex mirror must capture (?P<version>...): {mirror.get('path')}")
        updated, count = re.subn(pattern, replacement.replace("{version}", version), content, count=1, flags=re.MULTILINE)
        if count != 1:
            raise ValueError(f"Regex mirror matched {count} times: {mirror.get('path')}")
        return match.group("version"), updated
    raise ValueError(f"Unsupported mirror kind: {kind!r}")


def mirror_updates(repo: Path, config: dict[str, Any], version: str) -> list[tuple[Path, str, str]]:
    updates = []
    for mirror in config.get("version_mirrors", []):
        relative = mirror.get("path")
        if not isinstance(relative, str):
            raise ValueError("Every version mirror needs a path")
        path = repo_path(repo, relative)
        if not path.exists():
            raise ValueError(f"Version mirror does not exist: {relative}")
        current, rendered = render_mirror(path.read_text(encoding="utf-8"), mirror, version)
        updates.append((path, current, rendered))
    return updates


def tracked_files(repo: Path) -> list[str]:
    output = git(repo, "ls-files", "-z").stdout
    return [item.replace("\\", "/") for item in output.split("\0") if item]


def gitignore_errors(repo: Path) -> list[str]:
    if not (repo / ".gitignore").exists():
        return ["Missing .gitignore"]
    errors = []
    for relative in (".env", "credentials.json"):
        if git(repo, "check-ignore", "--no-index", "--quiet", relative, check=False).returncode != 0:
            errors.append(f".gitignore does not ignore {relative}")
    for relative in (".env.example", ".env.template"):
        if git(repo, "check-ignore", "--no-index", "--quiet", relative, check=False).returncode == 0:
            errors.append(f".gitignore incorrectly ignores {relative}")
    return errors


def readme_content_errors(content: str) -> list[str]:
    errors = []
    if not re.search(r"(?m)^#\s+\S", content):
        errors.append("README.md needs a project title")
    prose = [
        line.strip()
        for line in content.splitlines()
        if len(line.strip()) >= 40 and not line.lstrip().startswith(("#", "-", "*", "`", "![", "<"))
    ]
    if not prose:
        errors.append("README.md needs a concise project description")
    headings = [match.group(1).strip().lower() for match in re.finditer(r"(?m)^#{2,6}\s+(.+?)\s*$", content)]
    if not any(re.search(r"\b(install|installation|setup|getting started|run|running|build)\b", heading) for heading in headings):
        errors.append("README.md needs installation, setup, build, or run guidance")
    if not any(re.search(r"\b(use|usage|quick start|getting started|examples|commands|api)\b", heading) for heading in headings):
        errors.append("README.md needs essential usage guidance")
    if README_PLACEHOLDER.search(content):
        errors.append("README.md contains unfinished template text")
    return errors


def readme_errors(repo: Path, config: dict[str, Any]) -> list[str]:
    if config.get("project_type") not in README_PROJECT_TYPES:
        return []
    path = repo / "README.md"
    if not path.exists():
        return ["Missing required README.md"]
    return readme_content_errors(path.read_text(encoding="utf-8"))


def gitleaks_command() -> list[str] | None:
    override = os.environ.get("REPO_POLICY_GITLEAKS")
    if override:
        candidate = Path(override)
        if not candidate.exists():
            return None
        if candidate.suffix.lower() == ".py":
            return [sys.executable, str(candidate)]
        if candidate.suffix.lower() in {".cmd", ".bat"}:
            return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", str(candidate)]
        return [str(candidate)]
    found = shutil.which("gitleaks")
    if found:
        return [found]
    if os.name == "nt":
        local = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
        matches = sorted(local.glob("Gitleaks.Gitleaks_*/*gitleaks.exe"))
        if matches:
            return [str(matches[-1])]
    return None


def allowlist_errors(repo: Path) -> list[str]:
    path = repo / ".gitleaksignore"
    if not path.exists():
        return []
    errors = []
    reason = False
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            reason = False
        elif line.startswith("#"):
            reason = line.lower().startswith("# reason:") and bool(line.split(":", 1)[1].strip())
        else:
            if not reason:
                errors.append(f".gitleaksignore:{number} needs a preceding '# Reason: ...' comment")
            reason = False
    return errors


def scan_secrets(repo: Path, scope: str) -> int:
    if scope not in {"staged", "tracked", "history"}:
        return fail(f"Unsupported secret scan scope: {scope}")
    try:
        config = load_config(repo)
        if config.get("secret_scanning") != "gitleaks-required":
            return fail("Repository policy must require Gitleaks")
        errors = allowlist_errors(repo)
        if errors:
            for error in errors:
                print(f"[error] {error}")
            return 1
        command = gitleaks_command()
        if not command:
            return fail(
                "Gitleaks is required but unavailable. Install it with "
                "'winget install --id Gitleaks.Gitleaks --exact' or the platform package manager."
            )
        common = ["--redact=100", "--no-banner", "--no-color"]
        ignore = repo / ".gitleaksignore"
        if ignore.exists():
            common.extend(["--gitleaks-ignore-path", str(ignore)])
        if scope == "tracked":
            with tempfile.TemporaryDirectory(prefix="repo-policy-secrets-") as temp:
                scan_root = Path(temp)
                for relative in tracked_files(repo):
                    source = repo / relative
                    if source.is_file():
                        target = scan_root / relative
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, target)
                result = subprocess.run(
                    [*command, "dir", *common, str(scan_root)],
                    cwd=repo,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                )
        else:
            mode = ["git", "--staged"] if scope == "staged" else ["git"]
            result = subprocess.run(
                [*command, *mode, *common, "."],
                cwd=repo,
                text=True,
                capture_output=True,
                encoding="utf-8",
            )
        output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
        if output:
            print(output)
        if result.returncode == 1:
            return fail(f"Gitleaks found potential secrets in {scope} scope; rotate or narrowly allowlist after review")
        if result.returncode:
            return fail(f"Gitleaks {scope} scan failed with exit code {result.returncode}")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return fail(str(exc))
    print(f"[ok] Gitleaks {scope} scan passed")
    return 0


def worktree_records(repo: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    record: dict[str, str] = {}
    for line in git(repo, "worktree", "list", "--porcelain").stdout.splitlines() + [""]:
        if not line:
            if record:
                records.append(record)
                record = {}
            continue
        key, _, value = line.partition(" ")
        record[key] = value
    return records


def repository_health(repo: Path, config: dict[str, Any], settled: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    default = str(config.get("default_branch", "main"))
    current = git(repo, "branch", "--show-current", check=False).stdout.strip()
    if not has_head(repo):
        symbolic = git(repo, "symbolic-ref", "--short", "HEAD", check=False).stdout.strip()
        if symbolic and symbolic != default:
            errors.append(f"Unborn repository branch is {symbolic}, expected {default}")
        return errors, warnings
    if git(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{default}", check=False).returncode:
        errors.append(f"Default branch is missing locally: {default}")
        return errors, warnings
    if current != default:
        message = f"Current branch is {current or '(detached)'}; settled repository state requires {default}"
        (errors if settled else warnings).append(message)

    upstream = git(repo, "rev-parse", "--abbrev-ref", f"{default}@{{upstream}}", check=False)
    if upstream.returncode == 0:
        upstream_name = upstream.stdout.strip()
        counts = git(repo, "rev-list", "--left-right", "--count", f"{upstream_name}...{default}")
        behind, ahead = (int(item) for item in counts.stdout.split())
        if behind:
            message = f"{default} is behind {upstream_name} by {behind} and ahead by {ahead}"
            (errors if settled else warnings).append(message)
        elif ahead:
            warnings.append(f"{default} is ahead of {upstream_name} by {ahead}")

    branches = git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads").stdout.splitlines()
    for branch in branches:
        if branch == default:
            continue
        merged = git(repo, "merge-base", "--is-ancestor", branch, default, check=False).returncode == 0
        if merged:
            warnings.append(f"Merged local branch remains: {branch}")
            continue
        unique = git(repo, "rev-list", "--count", f"{default}..{branch}").stdout.strip()
        message = f"Unintegrated local branch {branch} has {unique} unique commit(s)"
        (errors if settled else warnings).append(message)

    remote_branches = git(repo, "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin", check=False).stdout.splitlines()
    for remote_branch in remote_branches:
        short = remote_branch.removeprefix("origin/")
        if short in {default, "HEAD"} or remote_branch.endswith("/HEAD"):
            continue
        if git(repo, "merge-base", "--is-ancestor", remote_branch, default, check=False).returncode == 0:
            warnings.append(f"Merged remote branch remains: {remote_branch}")
            continue
        unique = git(repo, "rev-list", "--count", f"{default}..{remote_branch}", check=False).stdout.strip()
        message = f"Unintegrated remote branch {remote_branch} has {unique or '?'} unique commit(s)"
        (errors if settled else warnings).append(message)

    root = repo.resolve()
    for record in worktree_records(repo):
        path_text = record.get("worktree", "")
        if "prunable" in record:
            message = f"Prunable worktree record: {path_text}"
            (errors if settled else warnings).append(message)
        if "detached" in record:
            message = f"Detached worktree: {path_text}"
            (errors if settled else warnings).append(message)
        if path_text:
            path = Path(path_text)
            if path.exists() and path.resolve() != root:
                dirty = git(path, "status", "--porcelain", "--untracked-files=all", check=False).stdout.strip()
                if dirty:
                    message = f"Linked worktree is dirty: {path_text}"
                    (errors if settled else warnings).append(message)
    return errors, warnings


def print_repository_inventory(repo: Path, config: dict[str, Any]) -> None:
    default = str(config.get("default_branch", "main"))
    current = git(repo, "branch", "--show-current", check=False).stdout.strip() or "(detached)"
    print(f"[repo] current={current} default={default}")
    for branch in git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads").stdout.splitlines():
        if branch == default:
            state = "main"
        elif git(repo, "merge-base", "--is-ancestor", branch, default, check=False).returncode == 0:
            state = "merged"
        else:
            unique = git(repo, "rev-list", "--count", f"{default}..{branch}").stdout.strip()
            state = f"{unique} unique commit(s)"
        print(f"[branch] {branch}\t{state}")
    for record in worktree_records(repo):
        state = "prunable" if "prunable" in record else "detached" if "detached" in record else "attached"
        print(f"[worktree] {record.get('worktree', '?')}\t{state}")


def repository_health_command(repo: Path, settled: bool) -> int:
    try:
        config = (
            load_config(repo)
            if (repo / ".repo-policy.json").exists()
            else {"default_branch": "main", "branch_prefix": "codex/"}
        )
        print_repository_inventory(repo, config)
        errors, warnings = repository_health(repo, config, settled)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return fail(str(exc))
    for warning in warnings:
        print(f"[warn] {warning}")
    for error in errors:
        print(f"[error] {error}")
    if errors:
        return 1
    print(f"[ok] repository health {'is settled' if settled else 'inventory completed'}")
    return 0


def audit(repo: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        if not is_repo_root(repo):
            return ["Path is not the Git repository root"], warnings
        config = load_config(repo)
        errors.extend(config_errors(config))
        version = read_version(repo, config)
        agents = repo / "AGENTS.md"
        if not agents.exists() or MARKER not in agents.read_text(encoding="utf-8"):
            errors.append("AGENTS.md lacks the repository contract marker")
        changelog_rel = str(config.get("changelog_file", "CHANGELOG.md"))
        changelog_path = repo_path(repo, changelog_rel)
        if not changelog_path.exists():
            errors.append(f"Missing changelog: {changelog_rel}")
        else:
            changelog = changelog_path.read_text(encoding="utf-8")
            if "## [Unreleased]" not in changelog:
                errors.append("Changelog lacks [Unreleased]")
            if f"## [{version}]" not in changelog:
                errors.append(f"Changelog lacks current release heading [{version}]")
        for path, current, _ in mirror_updates(repo, config, version):
            if current != version:
                errors.append(f"Version mirror drift: {path.relative_to(repo)}")
        for name in HOOKS:
            if not (repo / ".githooks" / name).exists():
                errors.append(f"Missing tracked hook: .githooks/{name}")
        if git(repo, "config", "--get", "core.hooksPath", check=False).stdout.strip() != ".githooks":
            errors.append("core.hooksPath is not .githooks")
        commands = config.get("verification_commands", [])
        if config.get("project_type") in {"maintained-product", "library-or-tool", "skill"} and not commands:
            errors.append("No project verification commands are configured")
        if not isinstance(commands, list) or any(not isinstance(item, str) or not item.strip() for item in commands):
            errors.append("verification_commands must contain non-empty strings")
        if not gitleaks_command():
            errors.append(
                "Gitleaks is required but unavailable; install Gitleaks.Gitleaks with winget or the platform package manager"
            )
        errors.extend(allowlist_errors(repo))
        errors.extend(gitignore_errors(repo))
        errors.extend(readme_errors(repo, config))
        workflows = list((repo / ".github" / "workflows").glob("*.y*ml"))
        if config.get("github_actions", "off") == "off" and workflows:
            warnings.append("GitHub Actions exist while repository policy says off")
        dirty = [line for line in git(repo, "status", "--porcelain", "--untracked-files=all").stdout.splitlines() if line]
        if dirty:
            warnings.append(f"Working tree is dirty ({len(dirty)} paths)")
        health_errors, health_warnings = repository_health(repo, config, settled=False)
        errors.extend(health_errors)
        warnings.extend(health_warnings)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
    return errors, warnings


def audit_command(repo: Path) -> int:
    errors, warnings = audit(repo)
    for warning in warnings:
        print(f"[warn] {warning}")
    for error in errors:
        print(f"[error] {error}")
    if errors:
        return 1
    label = "structural policy audit passed with warnings" if warnings else "repository policy audit passed"
    print(f"[ok] {label}")
    return 0


def staged_files(repo: Path) -> set[str]:
    output = git(repo, "diff", "--cached", "--name-only", "--diff-filter=ACMR").stdout
    return {line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()}


def index_file(repo: Path, relative: str) -> str | None:
    result = git(repo, "show", f":{relative}", check=False)
    return result.stdout if result.returncode == 0 else None


def unreleased_bullets(content: str) -> list[str]:
    match = re.search(r"(?ms)^## \[Unreleased\]\s*\n(.*?)(?=^## \[|\Z)", content)
    if not match:
        return []
    return [line.strip() for line in match.group(1).splitlines() if re.match(r"^-\s+\S", line.strip())]


def new_unreleased_bullets(repo: Path, changelog: str) -> list[str]:
    current = unreleased_bullets(index_file(repo, changelog) or "")
    previous_text = git(repo, "show", f"HEAD:{changelog}", check=False).stdout if has_head(repo) else ""
    previous = unreleased_bullets(previous_text)
    return [bullet for bullet in current if current.count(bullet) > previous.count(bullet)]


def check_staged(repo: Path) -> int:
    if audit_command(repo):
        return 1
    config = load_config(repo)
    files = staged_files(repo)
    version_file = str(config.get("canonical_version_file", "VERSION")).replace("\\", "/")
    changelog = str(config.get("changelog_file", "CHANGELOG.md")).replace("\\", "/")
    errors = []
    if "README.md" in files:
        errors.extend(readme_content_errors(index_file(repo, "README.md") or ""))
    if version_file in files:
        version = valid_version((index_file(repo, version_file) or "").strip())
        required = {changelog, *(str(item["path"]).replace("\\", "/") for item in config.get("version_mirrors", []))}
        missing = sorted(required - files)
        if missing:
            errors.append("Staged version change is missing: " + ", ".join(missing))
        for mirror in config.get("version_mirrors", []):
            relative = str(mirror["path"]).replace("\\", "/")
            content = index_file(repo, relative)
            if content is None or render_mirror(content, mirror, version)[0] != version:
                errors.append(f"Staged version mirror drift: {relative}")
    for bullet in new_unreleased_bullets(repo, changelog):
        if BANNED_CHANGELOG.search(bullet):
            errors.append(f"Process-oriented or vague changelog bullet: {bullet}")
    for error in errors:
        print(f"[error] {error}")
    if errors:
        return 1
    if scan_secrets(repo, "staged"):
        return 1
    print("[ok] staged policy checks passed")
    return 0


def parse_message(message: str) -> tuple[str, str]:
    if not message:
        raise ValueError("Commit message is empty")
    subject = message.splitlines()[0]
    match = CONVENTIONAL.fullmatch(subject)
    if not match:
        raise ValueError("Commit subject must follow Conventional Commits")
    impacts = IMPACT.findall(message)
    if len(impacts) != 1:
        raise ValueError("Commit message needs exactly one Release-Impact footer")
    impact = impacts[0]
    if match.group("type") == "feat" and impact not in {"minor", "major"}:
        raise ValueError("feat commits require minor or major impact")
    if match.group("type") == "fix" and impact not in {"patch", "major"}:
        raise ValueError("fix commits require patch or major impact")
    if (match.group("breaking") or "BREAKING CHANGE:" in message) and impact != "major":
        raise ValueError("Breaking changes require major impact")
    return subject, impact


def check_message(repo: Path, message_file: Path) -> int:
    try:
        message = "\n".join(
            line for line in message_file.read_text(encoding="utf-8").splitlines()
            if not line.lstrip().startswith("#")
        ).strip()
        subject, impact = parse_message(message)
        config = load_config(repo)
        files = staged_files(repo)
        version_file = str(config.get("canonical_version_file", "VERSION")).replace("\\", "/")
        changelog = str(config.get("changelog_file", "CHANGELOG.md")).replace("\\", "/")
        if version_file in files and has_head(repo):
            version = valid_version((index_file(repo, version_file) or "").strip())
            previous = git(repo, "show", f"HEAD:{version_file}", check=False).stdout.strip()
            if previous and version_key(version) <= version_key(previous):
                raise ValueError(f"Release version must be greater than {previous}")
            if subject != f"chore(release): {version}" or impact != "none":
                raise ValueError(f"Version changes require 'chore(release): {version}' and Release-Impact: none")
            if f"## [{version}]" not in (index_file(repo, changelog) or ""):
                raise ValueError(f"Staged changelog lacks release heading [{version}]")
        elif version_file not in files and impact != "none":
            if changelog not in files or not new_unreleased_bullets(repo, changelog):
                raise ValueError("Non-none impact requires a new [Unreleased] changelog bullet")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return fail(str(exc))
    print("[ok] commit message policy passed")
    return 0


def sync_version(repo: Path, check: bool) -> int:
    try:
        config = load_config(repo)
        version = read_version(repo, config)
        drift = []
        for path, current, rendered in mirror_updates(repo, config, version):
            if current != version:
                drift.append(str(path.relative_to(repo)))
                if not check:
                    write(path, rendered)
                    print(f"[sync] {path.relative_to(repo)} -> {version}")
        if check and drift:
            return fail("Version mirror drift: " + ", ".join(drift))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return fail(str(exc))
    print("[ok] version mirrors are synchronized")
    return 0


def prepare_release(repo: Path, requested: str) -> int:
    try:
        requested = valid_version(requested)
        if git(repo, "status", "--porcelain", "--untracked-files=all").stdout.strip():
            return fail("Release preparation requires a clean working tree")
        if audit_command(repo):
            return 1
        config = load_config(repo)
        health_errors, _ = repository_health(repo, config, settled=True)
        if health_errors:
            return fail("Release preparation requires settled repository health: " + "; ".join(health_errors))
        if scan_secrets(repo, "history"):
            return 1
        current = read_version(repo, config)
        if version_key(requested) <= version_key(current):
            return fail(f"Requested version {requested} must be greater than {current}")
        changelog_path = repo_path(repo, str(config.get("changelog_file", "CHANGELOG.md")))
        changelog = changelog_path.read_text(encoding="utf-8")
        match = re.search(r"(?ms)^## \[Unreleased\]\s*\n(?P<body>.*?)(?=^## \[|\Z)", changelog)
        if not match or not unreleased_bullets(changelog):
            return fail("[Unreleased] has no notable change bullets")
        body = match.group("body").strip()
        released = f"## [Unreleased]\n\n## [{requested}] - {dt.date.today().isoformat()}\n\n{body}\n\n"
        next_changelog = changelog[: match.start()] + released + changelog[match.end() :]
        updates = mirror_updates(repo, config, requested)
        write(repo_path(repo, str(config.get("canonical_version_file", "VERSION"))), requested + "\n")
        write(changelog_path, next_changelog)
        for path, _, rendered in updates:
            write(path, rendered)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return fail(str(exc))
    print(f"[release] prepared {current} -> {requested}")
    return 0


def verify(repo: Path) -> int:
    if audit_command(repo):
        return 1
    if scan_secrets(repo, "tracked"):
        return 1
    config = load_config(repo)
    for command in config.get("verification_commands", []):
        print(f"[verify] {command}")
        result = subprocess.run(command, cwd=repo, shell=True)
        if result.returncode:
            return fail(f"Verification failed with exit code {result.returncode}")
    print("[ok] repository verification passed")
    return 0


def scaffold(repo: Path, project_type: str, version: str | None, init_git: bool) -> int:
    if version is None:
        if project_type != "skill":
            return fail("An exact initial version is required for non-skill repositories")
        version = "1.0.0"
    try:
        version = valid_version(version)
        repo.mkdir(parents=True, exist_ok=True)
        required = [
            ".repo-policy.json", ".gitignore", "AGENTS.md", "VERSION", "CHANGELOG.md",
            "scripts/repo_policy.py", "scripts/Install-RepoHooks.ps1",
            *(f".githooks/{name}" for name in HOOKS),
        ]
        existing = [relative for relative in required if (repo / relative).exists()]
        if existing:
            return fail("Refusing to overwrite existing policy files: " + ", ".join(existing))
        if not is_repo_root(repo):
            if not init_git:
                return fail("Target is not a Git repository; pass --init-git only with owner authorization")
            result = git(repo, "init", "-b", "main", check=False)
            if result.returncode:
                return fail(result.stderr.strip() or "git init failed")
        config = {
            "schema_version": 1,
            "project_type": project_type,
            "canonical_version_file": "VERSION",
            "changelog_file": "CHANGELOG.md",
            "tag_prefix": "v",
            "default_branch": "main",
            "branch_prefix": "codex/",
            "secret_scanning": "gitleaks-required",
            "github_actions": "off",
            "version_mirrors": [],
            "verification_commands": [],
        }
        write(repo / ".repo-policy.json", json.dumps(config, indent=2) + "\n")
        write(repo / ".gitignore", """.env
.env.*
!.env.example
!.env.template
credentials.json
secrets.json
*.key
*.p12
*.pfx
__pycache__/
node_modules/
build/
dist/
*.tmp
*.log
""")
        write(repo / "AGENTS.md", AGENTS)
        write(repo / "VERSION", version + "\n")
        write(repo / "CHANGELOG.md", f"""# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [{version}] - {dt.date.today().isoformat()}

### Added

- Established the initial versioned project baseline.
""")
        (repo / "scripts").mkdir(parents=True, exist_ok=True)
        shutil.copy2(Path(__file__).resolve(), repo / "scripts" / "repo_policy.py")
        write(repo / "scripts" / "Install-RepoHooks.ps1", INSTALL_HOOKS)
        for name, content in HOOKS.items():
            write(repo / ".githooks" / name, content)
        git(repo, "config", "core.hooksPath", ".githooks")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return fail(str(exc))
    print(f"[scaffold] initialized {project_type} repository policy at {version}")
    print("[next] add a project-specific README when required, configure real verification commands, then run audit")
    return 0


def add_repo(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", required=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Lean repository policy for solo agent-led development")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("audit", "check-staged", "verify"):
        add_repo(commands.add_parser(name))
    health = commands.add_parser("repo-health")
    add_repo(health)
    health.add_argument("--settled", action="store_true")
    secrets = commands.add_parser("scan-secrets")
    add_repo(secrets)
    secrets.add_argument("--scope", required=True, choices=["staged", "tracked", "history"])
    message = commands.add_parser("check-message")
    add_repo(message)
    message.add_argument("message_file")
    sync = commands.add_parser("sync-version")
    add_repo(sync)
    sync.add_argument("--check", action="store_true")
    release = commands.add_parser("prepare-release")
    add_repo(release)
    release.add_argument("version")
    create = commands.add_parser("scaffold")
    add_repo(create)
    create.add_argument("--project-type", required=True, choices=[
        "maintained-product", "library-or-tool", "skill", "prototype", "planning-only"
    ])
    create.add_argument("--version")
    create.add_argument("--init-git", action="store_true")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    if args.command == "audit": return audit_command(repo)
    if args.command == "check-staged": return check_staged(repo)
    if args.command == "repo-health": return repository_health_command(repo, args.settled)
    if args.command == "scan-secrets": return scan_secrets(repo, args.scope)
    if args.command == "check-message": return check_message(repo, Path(args.message_file).resolve())
    if args.command == "sync-version": return sync_version(repo, args.check)
    if args.command == "prepare-release": return prepare_release(repo, args.version)
    if args.command == "verify": return verify(repo)
    if args.command == "scaffold": return scaffold(repo, args.project_type, args.version, args.init_git)
    return fail("Unsupported command")


if __name__ == "__main__":
    raise SystemExit(main())
