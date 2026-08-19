# Repository Instructions

<!-- repo-readiness:v1 -->

This repository is the source of truth for the `repo-readiness` skill. The installable payload is under `skill/repo-readiness/`. Never treat the copy under `C:\Users\stack-junkie\.codex\skills` as source.

## Rules of engagement

- Inspect the live working tree and applicable instructions before editing.
- Preserve unrelated dirty work. Do not stage, clean, revert, move, or rewrite files outside the active scope.
- Add only files that serve the product, the operator, or deterministic enforcement. Do not create process documentation for appearance.
- Keep one writer per file or module. Repartition or serialize overlapping work. Use separate worktrees only for disjoint ownership.
- Keep `main` as the normal source of truth. Use short-lived `codex/*` branches only for risky or parallel work.
- Do not start unrelated work on a branch with unintegrated commits. Integrate, deliberately park, or report it first.
- Run focused checks for the changed behavior, then inspect the final diff.
- Do not stage, commit, tag, push, publish, or create a pull request unless the user explicitly requests that action.
- Do not claim independent verification when the implementing agent performed the review.

## Version and release policy

- `VERSION` is the only manually edited version source. Other version fields are generated mirrors.
- Ordinary edits do not change `VERSION`. Record notable user-facing or operator-facing changes under `CHANGELOG.md` `[Unreleased]`.
- Every release requires the exact version from the user. Never infer or automatically select a patch, minor, major, alpha, beta, or release-candidate version.
- Prepare releases with `scripts\run_python.cmd scripts\repo_policy.py prepare-release --repo . <version>`.
- Require Gitleaks for redacted staged, current-tree, and history scans.
- Keep `.gitignore` relevant to the actual stack and do not create repository clutter.
- Keep GitHub Actions absent unless the user approves a concrete hosted-check, matrix-test, packaging, or deployment need.
- Require a concise, current README for maintained products, libraries, tools, and skills. When README.md is touched, review the entire file and repair stale commands, paths, behavior, configuration, links, and limitations.

## Required checks

- Audit: `scripts\run_python.cmd scripts\repo_policy.py audit --repo .`
- Repository health: `scripts\run_python.cmd scripts\repo_policy.py repo-health --repo .`
- Full history secret scan: `scripts\run_python.cmd scripts\repo_policy.py scan-secrets --repo . --scope history`
- Full verification: `scripts\run_python.cmd scripts\repo_policy.py verify --repo .`
- Skill validation: `scripts\run_python.cmd C:\Users\stack-junkie\.codex\skills\.system\skill-creator\scripts\quick_validate.py skill\repo-readiness`
- Install after validation: `scripts\install_skill.cmd`
