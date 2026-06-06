---
name: repo-readiness
description: Personal repo-readiness workflow for stack-junkie projects. Use when Codex is asked to create, convert, publish, or audit a local project/repo with stack-junkie versioning, changelog, git hooks, GitHub handoff, agent-skill source layout, or RimWorld mod source layout under C:\Users\stack-junkie\Documents\Development\02 Projects.
---

# Repo Readiness stack-junkie

Use this workflow to make stack-junkie projects ready to maintain as real repos while preserving the local Windows project layout.

## Defaults

- Project home: `C:\Users\stack-junkie\Documents\Development\02 Projects`.
- Personal agent skill source repos: `C:\Users\stack-junkie\Documents\Development\02 Projects\Agent Skills\<skill-name>`.
- RimWorld mod source repos: `C:\Users\stack-junkie\Documents\Development\02 Projects\RimWorld Mods\<mod-name>`.
- Runtime installs are deployment targets, not source repos. Examples: `C:\Users\stack-junkie\.codex\skills` for installed skills and `C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods` for local RimWorld mods.

## Workflow

1. Inspect before changing. Check cwd, git state, nearby comparable projects, and any project-specific instructions.
2. If the user asks to infer their methodology, report findings first and wait for confirmation before implementing.
3. Keep source repos in `Development\02 Projects`; use explicit install/deploy scripts for runtime locations.
4. Add repo guardrails: `AGENTS.md`, `README.md`, `CHANGELOG.md`, `VERSION`, `src/version.py`, `package.json`, `scripts\run_python.cmd`, `scripts\sync_version.py`, `scripts\bump_version.py`, `scripts\check_release_metadata.py`, `.githooks\pre-commit`, and `.githooks\pre-push`.
5. Configure git with `git init -b main` and `git config core.hooksPath .githooks` for new repos.
6. Validate the repo before the final answer and report exact commands/results.

## Versioning

- Use `src/version.py` as the code-readable version source.
- Sync that version into `VERSION`, `package.json`, README, and package-specific metadata.
- Use semantic versions, including prerelease forms like `0.1.0-alpha.0`.
- Every material change needs both a version bump and a `CHANGELOG.md` entry.
- Hooks should fail when staged material changes lack release metadata.

## Agent Skill Repos

- Keep the repo root maintainable, but keep the installable skill payload lean.
- Put the installable payload at `skill\<skill-name>\SKILL.md`.
- Include `agents\openai.yaml` when creating a new skill through the system skill initializer.
- Do not add README/changelog files inside the installable skill payload unless a user explicitly asks; repo docs belong at the source repo root.
- Install by copying the payload to `C:\Users\stack-junkie\.codex\skills\<skill-name>`.

## RimWorld Mod Repos

- Put the installable mod folder under `mod\` inside the source repo.
- Keep compiled assemblies tracked when RimWorld loads them directly.
- Add build and install scripts that can reproduce the local DLL and copy the mod into RimWorld's `Mods` folder.
- Preserve `About\PublishedFileId.txt` locally but do not commit it.
- Verify live mod behavior from `ModsConfig.xml` and the current `Player.log` when the task is about an active game issue.

## Decision Format

When defaults are proposals rather than explicit user instructions, present:

- `decision needed`
- `why it matters`
- `options`
- `recommendation`
- `what approval means`
