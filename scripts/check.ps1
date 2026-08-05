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

$inspectionJson = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $skillPath "scripts\inspect_project.ps1") $repoRoot
if ($LASTEXITCODE -ne 0) { throw "Project inspection smoke test failed." }
$inspection = $inspectionJson | ConvertFrom-Json
if ($inspection.project_root -ne (Resolve-Path -LiteralPath $repoRoot).Path) {
    throw "Project inspection returned the wrong project root."
}

Write-Host "[check] Version sync, skill validation, and project inspection passed."
