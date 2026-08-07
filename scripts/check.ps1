param()

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$skillPath = Join-Path $repoRoot "skill\drive-project-work"
$validator = "C:\Users\stack-junkie\.codex\skills\.system\skill-creator\scripts\quick_validate.py"

& (Join-Path $PSScriptRoot "run_python.cmd") (Join-Path $PSScriptRoot "sync_version.py") --check
if ($LASTEXITCODE -ne 0) { throw "Version synchronization check failed." }

if (-not (Test-Path -LiteralPath $validator)) {
    throw "Skill validator not found: $validator"
}
& (Join-Path $PSScriptRoot "run_python.cmd") $validator $skillPath
if ($LASTEXITCODE -ne 0) { throw "Skill validation failed." }

& (Join-Path $PSScriptRoot "run_python.cmd") -m py_compile (Join-Path $repoRoot "hooks\drive_project_work_hook.py")
if ($LASTEXITCODE -ne 0) { throw "Lifecycle hook compilation failed." }

& (Join-Path $PSScriptRoot "run_python.cmd") -m unittest discover -s (Join-Path $repoRoot "tests") -p "test_*.py" -v
if ($LASTEXITCODE -ne 0) { throw "Slice guard tests failed." }

Write-Host "[check] Version sync, skill validation, and slice guard tests passed."
