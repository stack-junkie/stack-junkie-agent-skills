from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "skills" / "repo-readiness" / "scripts" / "repo_policy.py"
FAKE_GITLEAKS = ROOT / "tests" / "repo-readiness" / "fake_gitleaks.py"


def run(
    *args: str,
    cwd: Path | None = None,
    expected: int = 0,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["REPO_POLICY_GITLEAKS"] = str(FAKE_GITLEAKS)
    if extra_env:
        environment.update(extra_env)
    result = subprocess.run(
        [*args], cwd=cwd, text=True, capture_output=True, encoding="utf-8", env=environment
    )
    if result.returncode != expected:
        raise AssertionError(
            f"Expected exit {expected}, got {result.returncode}\n"
            f"command: {' '.join(args)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def policy(
    repo: Path,
    *args: str,
    expected: int = 0,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return run(
        sys.executable,
        str(POLICY),
        *args,
        "--repo",
        str(repo),
        expected=expected,
        extra_env=extra_env,
    )


def configure(repo: Path) -> None:
    path = repo / ".repo-policy.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["verification_commands"] = [f'"{sys.executable}" -c "print(123)"']
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def configure_git(repo: Path) -> None:
    run("git", "config", "user.name", "Repo Policy Test", cwd=repo)
    run("git", "config", "user.email", "repo-policy-test@example.invalid", cwd=repo)


def write_readme(repo: Path) -> None:
    (repo / "README.md").write_text(
        "# Example Project\n\n"
        "A focused example project used to exercise the repository policy safely.\n\n"
        "## Install\n\nRun the repository's supported installation command.\n\n"
        "## Use\n\nRun the documented primary workflow.\n",
        encoding="utf-8",
        newline="\n",
    )


def commit_all(repo: Path, subject: str, impact: str = "none", no_verify: bool = False) -> None:
    run("git", "add", "--all", cwd=repo)
    args = ["git", "commit"]
    if no_verify:
        args.append("--no-verify")
    run(*args, "-m", subject, "-m", f"Release-Impact: {impact}", cwd=repo)


def scaffold_skill(repo: Path) -> None:
    policy(repo, "scaffold", "--project-type", "skill", "--init-git")
    configure(repo)
    configure_git(repo)
    write_readme(repo)


class RepoPolicyTests(unittest.TestCase):
    def test_scaffold_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            product = root / "product"
            result = policy(
                product,
                "scaffold",
                "--project-type",
                "maintained-product",
                "--init-git",
                expected=1,
            )
            self.assertIn("exact initial version", result.stdout)

            skill = root / "skill"
            policy(skill, "scaffold", "--project-type", "skill", "--init-git")
            self.assertEqual("1.0.0", (skill / "VERSION").read_text(encoding="utf-8").strip())
            self.assertIn("No project verification commands", policy(skill, "audit", expected=1).stdout)
            configure(skill)
            missing_readme = policy(skill, "audit", expected=1)
            self.assertIn("Missing required README.md", missing_readme.stdout)
            (skill / "README.md").write_text(
                "# Example\n\nTODO: describe your project.\n",
                encoding="utf-8",
                newline="\n",
            )
            incomplete_readme = policy(skill, "audit", expected=1)
            self.assertIn("installation, setup, build, or run guidance", incomplete_readme.stdout)
            self.assertIn("unfinished template text", incomplete_readme.stdout)
            write_readme(skill)
            policy(skill, "audit")

            existing = root / "existing"
            existing.mkdir()
            (existing / "AGENTS.md").write_text("# Existing rules\n", encoding="utf-8")
            refused = policy(
                existing,
                "scaffold",
                "--project-type",
                "skill",
                "--init-git",
                expected=1,
            )
            self.assertIn("Refusing to overwrite", refused.stdout)
            self.assertFalse((existing / ".git").exists())

            parent = root / "parent"
            parent.mkdir()
            run("git", "init", "-b", "main", cwd=parent)
            child = parent / "child"
            policy(child, "scaffold", "--project-type", "skill", "--init-git")
            top = run("git", "rev-parse", "--show-toplevel", cwd=child).stdout.strip()
            self.assertEqual(child.resolve(), Path(top).resolve())

    def test_release_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "release"
            scaffold_skill(repo)
            commit_all(repo, "chore(repo): establish baseline")

            changelog = repo / "CHANGELOG.md"
            content = changelog.read_text(encoding="utf-8").replace(
                "## [Unreleased]\n",
                "## [Unreleased]\n\n### Added\n\n- Added a user-visible command.\n",
                1,
            )
            changelog.write_text(content, encoding="utf-8", newline="\n")
            commit_all(repo, "feat(cli): add visible command", "minor")

            policy(repo, "prepare-release", "1.1.0")
            self.assertEqual("1.1.0", (repo / "VERSION").read_text(encoding="utf-8").strip())
            self.assertIn("## [1.1.0]", changelog.read_text(encoding="utf-8"))
            commit_all(repo, "chore(release): 1.1.0")
            policy(repo, "verify")

    def test_notable_commit_requires_unreleased_note(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "missing-note"
            scaffold_skill(repo)
            commit_all(repo, "chore(repo): establish baseline")
            (repo / "feature.txt").write_text("feature\n", encoding="utf-8")
            run("git", "add", "feature.txt", cwd=repo)
            result = run(
                "git",
                "commit",
                "-m",
                "feat(core): add feature",
                "-m",
                "Release-Impact: minor",
                cwd=repo,
                expected=1,
            )
            self.assertIn("changelog bullet", result.stdout + result.stderr)

    def test_release_requires_clean_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "dirty-release"
            scaffold_skill(repo)
            commit_all(repo, "chore(repo): establish baseline")
            (repo / "unrelated.txt").write_text("dirty\n", encoding="utf-8")
            result = policy(repo, "prepare-release", "1.1.0", expected=1)
            self.assertIn("clean working tree", result.stdout)
            self.assertEqual("1.0.0", (repo / "VERSION").read_text(encoding="utf-8").strip())

    def test_bad_mirror_does_not_partially_prepare(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "bad-mirror"
            scaffold_skill(repo)
            changelog = repo / "CHANGELOG.md"
            content = changelog.read_text(encoding="utf-8").replace(
                "## [Unreleased]\n",
                "## [Unreleased]\n\n### Added\n\n- Added a visible capability.\n",
                1,
            )
            changelog.write_text(content, encoding="utf-8", newline="\n")
            config_path = repo / ".repo-policy.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["version_mirrors"] = [
                {"path": "missing.json", "kind": "json", "key": "version"}
            ]
            config_path.write_text(
                json.dumps(config, indent=2) + "\n", encoding="utf-8", newline="\n"
            )
            commit_all(repo, "chore(test): create invalid mirror fixture", no_verify=True)

            before = changelog.read_text(encoding="utf-8")
            result = policy(repo, "prepare-release", "1.1.0", expected=1)
            self.assertIn("Version mirror does not exist", result.stdout)
            self.assertEqual("1.0.0", (repo / "VERSION").read_text(encoding="utf-8").strip())
            self.assertEqual(before, changelog.read_text(encoding="utf-8"))

    def test_secret_scopes_redaction_allowlist_and_missing_binary(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "secrets"
            scaffold_skill(repo)
            (repo / "example.txt").write_text("safe\n", encoding="utf-8")
            run("git", "add", "example.txt", cwd=repo)

            capture = Path(temp) / "gitleaks-args.txt"
            clean = policy(
                repo,
                "scan-secrets",
                "--scope",
                "staged",
                extra_env={"FAKE_GITLEAKS_CAPTURE": str(capture)},
            )
            self.assertIn("Gitleaks staged scan passed", clean.stdout)
            self.assertIn("--redact=100", capture.read_text(encoding="utf-8"))

            finding = policy(
                repo,
                "scan-secrets",
                "--scope",
                "history",
                expected=1,
                extra_env={
                    "FAKE_GITLEAKS_EXIT": "1",
                    "FAKE_GITLEAKS_OUTPUT": "generic-api-key config.txt:1 Secret: REDACTED",
                },
            )
            self.assertIn("REDACTED", finding.stdout)
            self.assertNotIn("actual-secret-value", finding.stdout)

            missing = policy(
                repo,
                "scan-secrets",
                "--scope",
                "tracked",
                expected=1,
                extra_env={"REPO_POLICY_GITLEAKS": str(Path(temp) / "missing.exe")},
            )
            self.assertIn("Gitleaks is required but unavailable", missing.stdout)

            (repo / ".gitleaksignore").write_text("fingerprint\n", encoding="utf-8")
            unexplained = policy(repo, "scan-secrets", "--scope", "tracked", expected=1)
            self.assertIn("needs a preceding '# Reason:", unexplained.stdout)
            (repo / ".gitleaksignore").write_text(
                "# Reason: documented false positive fixture\nfingerprint\n", encoding="utf-8"
            )
            policy(repo, "scan-secrets", "--scope", "tracked")

    def test_repository_health_blocks_unmerged_work_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "health"
            repo.mkdir()
            run("git", "init", "-b", "main", cwd=repo)
            configure_git(repo)
            (repo / "baseline.txt").write_text("baseline\n", encoding="utf-8")
            commit_all(repo, "chore(repo): establish baseline")
            run("git", "switch", "-c", "agent/unique", cwd=repo)
            (repo / "unique.txt").write_text("unique\n", encoding="utf-8")
            commit_all(repo, "chore(test): unique branch commit")
            unique_tip = run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
            run("git", "switch", "main", cwd=repo)
            report = policy(repo, "repo-health", "--settled", expected=1)
            self.assertIn("Unintegrated local branch agent/unique", report.stdout)
            self.assertEqual(unique_tip, run("git", "rev-parse", "agent/unique", cwd=repo).stdout.strip())
            run("git", "merge", "--ff-only", "agent/unique", cwd=repo)
            settled = policy(repo, "repo-health", "--settled")
            self.assertIn("Merged local branch remains: agent/unique", settled.stdout)


if __name__ == "__main__":
    unittest.main()
