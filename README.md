# Drive Project Work v0.1.0-alpha.0

A personal Codex controller skill that drives project tasks from a requested outcome through decision extraction, implementation, verification, release hygiene, and an authorized checkpoint.

## Use

Invoke it explicitly with `$drive-project-work`, or ask Codex to drive, build, implement, fix, change, ship, diagnose, plan, audit, release, or standardize project work.

Examples:

- `Drive this: fix project reopening and prove saved state survives.`
- `Diagnose this crash without changing files.`
- `Plan this feature and extract the decisions you need from me.`
- `Prepare this project for release.`

The skill watches for feedback that suggests the process itself should change. It must explain the current rule and recommendation, then ask whether the deviation is task-only or a future default.

## Source and installation

- Source payload: `skill\drive-project-work`
- Installed runtime copy: `C:\Users\stack-junkie\.codex\skills\drive-project-work`
- Install: `scripts\install_skill.cmd`
- Validate: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check.ps1`

## Release metadata

- Version: `0.1.0-alpha.0`
- Version source: `src\version.py`
- Changelog: `CHANGELOG.md`
