# Repo Readiness stack-junkie v0.1.0-alpha.0

Source repo for the personal Codex skill `repo-readiness`.

- Version: `0.1.0-alpha.0`
- Source repo target: `C:\Users\stack-junkie\Documents\Development\02 Projects\Agent Skills\repo-readiness`
- Install target: `C:\Users\stack-junkie\.codex\skills\repo-readiness`

## Install

```powershell
scripts\install_skill.cmd
```

The skill may require a new Codex session or skill refresh before it appears in the available skills list.

## Validate

```powershell
scripts\run_python.cmd scripts\sync_version.py --check
python C:\Users\stack-junkie\.codex\skills\.system\skill-creator\scripts\quick_validate.py skill\repo-readiness
```

## Release Guardrails

```powershell
scripts\run_python.cmd scripts\check_release_metadata.py --staged
```

Use `scripts\bump_version.py` for version bumps, then add the matching `CHANGELOG.md` entry before committing.
