# Repository Instructions

This repo is the source of truth for the `repo-readiness` Codex skill.

## Layout

- `skill/repo-readiness/` is the installable skill payload.
- Repo-level docs, scripts, hooks, and changelog stay outside the installable skill.
- `scripts/install_skill.cmd` copies the payload to `C:\Users\ckvam\.codex\skills\repo-readiness`.

## Release Discipline

- Treat `src/version.py` as the version source.
- Run `scripts\run_python.cmd scripts\sync_version.py --check` before committing.
- Every material change must bump the semantic version and add a `CHANGELOG.md` entry.
- Keep the skill payload lean: `SKILL.md`, `agents/openai.yaml`, and only resources that directly help future Codex runs.

## Editing Rules

- Do not edit the installed copy under `.codex\skills` as the source of truth.
- Edit this repo, validate it, then run `scripts\install_skill.cmd`.
- Keep Windows paths explicit because this workflow runs on Windows.
