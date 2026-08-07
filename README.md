# Drive Project Work v0.2.0-alpha.0

A personal Codex skill and lifecycle guard for delivering one bounded, checkable implementation candidate without scope drift or inflated completion claims.

## Use

Invoke it explicitly with `$drive-project-work`, or ask Codex to implement, continue, finish, or ship consequential project work.

Examples:

- `Use $drive-project-work to fix project reopening as one verified slice.`
- `Continue the active implementation slice, but do not start another package.`
- `Deliver a candidate for this persistence bug and leave owner-only checks open.`

The guard stores a disposable slice lease outside the repository, records predeclared checks, blocks
out-of-scope patches and undeclared commands, invalidates stale verification after later edits, protects
pre-existing dirty and ignored state, latches explicit owner stop instructions, keeps the optional single
reviewer read-only, and limits the final claim to the evidence reached.

## Source and installation

- Source payload: `skill\drive-project-work`
- Lifecycle entrypoint: `hooks\drive_project_work_hook.py`
- Installed runtime copy: `C:\Users\stack-junkie\.codex\skills\drive-project-work`
- Install: `scripts\install_skill.cmd`
- Validate: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check.ps1`
- Hook trust: use `/hooks` after installation; enforcement begins only after Codex loads and the owner trusts the definitions.

## Release metadata

- Version: `0.2.0-alpha.0`
- Version source: `src\version.py`
- Changelog: `CHANGELOG.md`
