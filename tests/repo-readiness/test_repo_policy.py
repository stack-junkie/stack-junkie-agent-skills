from __future__ import annotations

import json
import importlib.util
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


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


def load_policy_module():
    spec = importlib.util.spec_from_file_location("repo_policy_under_test", POLICY)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RepoPolicyTests(unittest.TestCase):
    def test_configuration_values_and_shapes_are_validated(self) -> None:
        invalid_values = [
            ("project_type", "unknown", "project_type must be one of"),
            ("canonical_version_file", "../VERSION", "safe non-empty repository-relative path"),
            ("changelog_file", "../CHANGELOG.md", "safe non-empty repository-relative path"),
            ("default_branch", "bad branch", "valid Git branch name"),
            ("branch_prefix", "agent", "valid Git branch prefix"),
            ("tag_prefix", "bad lock", "Git-ref-safe string"),
            ("github_actions", "sometimes", "github_actions must be off or on"),
            ("version_mirrors", {}, "version_mirrors must be a list"),
            ("verification_commands", [123], "verification_commands must contain non-empty strings"),
            ("verification_timeout_seconds", 0, "must be an integer from 1 to 3600"),
        ]
        for key, value, expected_message in invalid_values:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temp:
                repo = Path(temp) / "invalid-config"
                scaffold_skill(repo)
                config_path = repo / ".repo-policy.json"
                config = json.loads(config_path.read_text(encoding="utf-8"))
                config[key] = value
                config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
                result = policy(repo, "audit", expected=1)
                self.assertIn(expected_message, result.stdout)

    def test_scaffold_gitignore_is_minimal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "minimal-ignore"
            policy(repo, "scaffold", "--project-type", "skill", "--init-git")
            content = (repo / ".gitignore").read_text(encoding="utf-8")
            for required in (".env", "credentials.json", ".DS_Store", "Thumbs.db"):
                self.assertIn(required, content)
            for stack_specific in ("__pycache__/", "node_modules/", "build/", "dist/", "*.log"):
                self.assertNotIn(stack_specific, content)

    def test_verification_timeout_reports_exact_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "timeout"
            scaffold_skill(repo)
            marker = Path(temp) / "descendant-survived.txt"
            child = Path(temp) / "timeout-child.py"
            child.write_text(
                "import time\n"
                "from pathlib import Path\n"
                "time.sleep(1.5)\n"
                f"Path({str(marker)!r}).write_text('survived', encoding='utf-8')\n",
                encoding="utf-8",
            )
            launcher = Path(temp) / "timeout-launcher.py"
            launcher.write_text(
                "import subprocess\nimport sys\nimport time\n"
                f"subprocess.Popen([sys.executable, {str(child)!r}])\n"
                "time.sleep(5)\n",
                encoding="utf-8",
            )
            config_path = repo / ".repo-policy.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            command = f'"{sys.executable}" "{launcher}"'
            config["verification_commands"] = [command]
            config["verification_timeout_seconds"] = 1
            config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
            result = policy(repo, "verify", expected=1)
            self.assertIn("timed out after 1s", result.stdout)
            self.assertIn(command, result.stdout)
            time.sleep(1)
            self.assertFalse(marker.exists(), "timed-out descendant process was not terminated")

    def test_mirror_configuration_is_fully_validated(self) -> None:
        invalid_mirrors = [
            (["VERSION"], "must be an object"),
            ([{"path": "../outside", "kind": "json"}], ".path must be a safe"),
            ([{"path": "package.json", "kind": "json", "key": "bad..key"}], ".key must be"),
            ([{"path": "version.txt", "kind": "regex", "pattern": "(1.0.0)", "replacement": "{version}"}], "named 'version' group"),
            ([{"path": "version.txt", "kind": "regex", "pattern": "(?P<version>.+)", "replacement": "fixed"}], ".replacement must contain"),
            ([{"path": "version.txt", "kind": "other"}], ".kind must be json or regex"),
        ]
        for mirrors, expected_message in invalid_mirrors:
            with self.subTest(mirrors=mirrors), tempfile.TemporaryDirectory() as temp:
                repo = Path(temp) / "invalid-mirror"
                scaffold_skill(repo)
                config_path = repo / ".repo-policy.json"
                config = json.loads(config_path.read_text(encoding="utf-8"))
                config["version_mirrors"] = mirrors
                config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
                result = policy(repo, "audit", expected=1)
                self.assertIn(expected_message, result.stdout)

    def test_release_impact_must_be_a_real_unique_trailer(self) -> None:
        module = load_policy_module()
        with self.assertRaisesRegex(ValueError, "exactly one"):
            module.parse_message("feat(core): add feature\n\nRelease-Impact: minor\nbody continues")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            module.parse_message(
                "feat(core): add feature\n\nRelease-Impact: minor\nRelease-Impact: minor"
            )
        subject, impact = module.parse_message(
            "feat(core): add feature\n\nA useful body.\n\nRelease-Impact: minor"
        )
        self.assertEqual("feat(core): add feature", subject)
        self.assertEqual("minor", impact)

    def test_atomic_release_writes_roll_back_on_replacement_failure(self) -> None:
        module = load_policy_module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "VERSION"
            second = root / "CHANGELOG.md"
            first.write_text("1.0.0\n", encoding="utf-8")
            second.write_text("before\n", encoding="utf-8")
            real_replace = module.os.replace
            forward_replacements = 0

            def fail_second_forward(source, target):
                nonlocal forward_replacements
                if ".repo-policy-rollback-" not in str(source):
                    forward_replacements += 1
                    if forward_replacements == 2:
                        raise OSError("simulated replacement failure")
                return real_replace(source, target)

            with mock.patch.object(module.os, "replace", side_effect=fail_second_forward):
                with self.assertRaisesRegex(OSError, "was rolled back"):
                    module.atomic_write_set([(first, "1.1.0\n"), (second, "after\n")])
            self.assertEqual("1.0.0\n", first.read_text(encoding="utf-8"))
            self.assertEqual("before\n", second.read_text(encoding="utf-8"))
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

    def test_tracked_secret_scan_uses_index_blobs_and_skips_links(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "index-scan"
            scaffold_skill(repo)
            commit_all(repo, "chore(repo): establish scan fixture")
            tracked = repo / "tracked.txt"
            tracked.write_text("indexed-content\n", encoding="utf-8")
            run("git", "add", "tracked.txt", cwd=repo)
            tracked.write_text("working-tree-content\n", encoding="utf-8")

            blob_result = subprocess.run(
                ["git", "hash-object", "-w", "--stdin"],
                cwd=repo,
                input="outside-target.txt\n",
                text=True,
                capture_output=True,
                encoding="utf-8",
                env={**os.environ, "REPO_POLICY_GITLEAKS": str(FAKE_GITLEAKS)},
            )
            self.assertEqual(0, blob_result.returncode, blob_result.stderr)
            run(
                "git", "update-index", "--add", "--cacheinfo",
                f"120000,{blob_result.stdout.strip()},linked.txt", cwd=repo,
            )

            object_ids = {}
            for label, content in (
                ("upper", "secret-from-upper-case\n"),
                ("lower", "safe-from-lower-case\n"),
                ("base", "conflict-base\n"),
                ("ours", "conflict-ours\n"),
                ("theirs", "conflict-theirs\n"),
            ):
                result = subprocess.run(
                    ["git", "hash-object", "-w", "--stdin"], cwd=repo, input=content,
                    text=True, capture_output=True, encoding="utf-8",
                )
                self.assertEqual(0, result.returncode, result.stderr)
                object_ids[label] = result.stdout.strip()
            run("git", "update-index", "--add", "--cacheinfo", f"100644,{object_ids['upper']},Case.txt", cwd=repo)
            run("git", "update-index", "--add", "--cacheinfo", f"100644,{object_ids['lower']},case.txt", cwd=repo)
            conflict = "".join(
                f"100644 {object_ids[label]} {stage}\tconflict.txt\n"
                for stage, label in ((1, "base"), (2, "ours"), (3, "theirs"))
            )
            conflict_result = subprocess.run(
                ["git", "update-index", "--index-info"], cwd=repo, input=conflict.encode("utf-8"),
                capture_output=True,
            )
            self.assertEqual(0, conflict_result.returncode, conflict_result.stderr.decode("utf-8", errors="replace"))
            head = run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
            run("git", "update-index", "--add", "--cacheinfo", f"160000,{head},nested-module", cwd=repo)
            indexed = load_policy_module().tracked_index_blobs(repo)
            index_listing = run("git", "ls-files", "--stage", cwd=repo).stdout
            self.assertEqual(
                ["1", "2", "3"],
                [stage for path, _, stage in indexed if path == "conflict.txt"],
                index_listing,
            )

            capture = Path(temp) / "tree.txt"
            policy(
                repo,
                "scan-secrets",
                "--scope",
                "tracked",
                extra_env={"FAKE_GITLEAKS_CAPTURE_TREE": str(capture)},
            )
            scanned = capture.read_text(encoding="utf-8")
            self.assertIn("tracked.txt=indexed-content", scanned)
            self.assertIn("Case.txt=secret-from-upper-case", scanned)
            self.assertIn("case.txt=safe-from-lower-case", scanned)
            self.assertIn("conflict.txt=conflict-base", scanned)
            self.assertIn("conflict.txt=conflict-ours", scanned)
            self.assertIn("conflict.txt=conflict-theirs", scanned)
            self.assertNotIn("working-tree-content", scanned)
            self.assertNotIn("linked.txt", scanned)
            self.assertNotIn("nested-module", scanned)

    def test_repository_health_governs_upstream_remote_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "work"
            origin = root / "origin.git"
            vendor = root / "vendor.git"
            run("git", "init", "--bare", str(origin))
            run("git", "init", "--bare", str(vendor))
            scaffold_skill(repo)
            commit_all(repo, "chore(repo): establish baseline")
            run("git", "remote", "add", "origin", str(origin), cwd=repo)
            run("git", "push", "-u", "origin", "main", cwd=repo)
            run("git", "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main", cwd=repo)
            run("git", "remote", "add", "vendor", str(vendor), cwd=repo)
            run("git", "push", "vendor", "main", cwd=repo)

            run("git", "switch", "-c", "agent/remote-only", cwd=repo)
            (repo / "remote.txt").write_text("remote\n", encoding="utf-8")
            commit_all(repo, "chore(test): add remote-only work")
            run("git", "push", "origin", "agent/remote-only", cwd=repo)
            run("git", "switch", "main", cwd=repo)
            run("git", "branch", "-D", "agent/remote-only", cwd=repo)
            run("git", "fetch", "--all", cwd=repo)

            result = policy(repo, "repo-health", "--settled", expected=1)
            self.assertIn("Unintegrated remote branch origin/agent/remote-only", result.stdout)
            self.assertIn("Additional remote branch observed: vendor/main (not governed)", result.stdout)
            self.assertNotIn("Unintegrated remote branch vendor/", result.stdout)
            self.assertNotIn("[remote-branch] origin\t", result.stdout)
            self.assertNotIn("Merged remote branch remains: origin", result.stdout)

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
