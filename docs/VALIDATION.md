# Validation

Run from the repository root:

```powershell
scripts\run_python.cmd scripts\sync_version.py --check
python C:\Users\ckvam\.codex\skills\.system\skill-creator\scripts\quick_validate.py skill\repo-readiness
```

For staged commits:

```powershell
scripts\run_python.cmd scripts\check_release_metadata.py --staged
```

For installation:

```powershell
scripts\install_skill.cmd
```

Start a new Codex session or refresh skills before relying on the newly installed skill being discoverable.
