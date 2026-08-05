# Repository Instructions

This repository is the maintained source of truth for the `drive-project-work` Codex skill.

## Layout

- `skill/drive-project-work/` is the installable skill payload.
- Repository release files, hooks, and install tooling stay outside the payload.
- `scripts/install_skill.cmd` replaces the runtime copy under `C:\Users\ckvam\.codex\skills\drive-project-work` from this source.

## Editing Process

- Never edit the installed runtime copy as the source of truth.
- When user feedback suggests a process deviation, explain the current rule, the deviation, the recommendation, and the reasoning.
- Ask whether the deviation is task-only, a future default, or not a process change.
- Change this source only after the user confirms a future default.
- Make the narrowest durable change and avoid duplicate or conflicting rules.
- Validate, reinstall, and compare source with the installed copy after every process update.

## Release Discipline

- Treat `src/version.py` as the version source.
- Every material source-skill change must bump the semantic version and add a `CHANGELOG.md` entry.
- Run `scripts\check.ps1` before committing.
- Keep the installable payload lean. Add only instructions, references, scripts, and metadata that directly affect future runs.

## Git Safety

- Inspect the full diff and stage reviewed paths intentionally.
- Preserve unrelated work.
- A local commit is authorized after checks pass. Push only when an existing remote and branch policy authorize it.
- Never create a remote, tag, publish, or rewrite history without explicit approval.
