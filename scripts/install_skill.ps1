param(
    [string]$CodexSkillsDir = $(if ($env:CODEX_SKILLS_DIR) { $env:CODEX_SKILLS_DIR } else { "C:\Users\stack-junkie\.codex\skills" })
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$skillName = "drive-project-work"
$sourceSkill = Join-Path $repoRoot "skill\$skillName"
$destinationSkill = Join-Path $CodexSkillsDir $skillName
$sourceHook = Join-Path $repoRoot "hooks\drive_project_work_hook.py"

if (-not (Test-Path -LiteralPath $sourceSkill)) {
    throw "Source skill folder not found: $sourceSkill"
}
if (-not (Test-Path -LiteralPath $sourceHook)) {
    throw "Source lifecycle hook not found: $sourceHook"
}

New-Item -ItemType Directory -Force -Path $CodexSkillsDir | Out-Null
$resolvedSkillsDir = (Resolve-Path -LiteralPath $CodexSkillsDir).Path
$destinationParent = Split-Path -Parent $destinationSkill
if ((Resolve-Path -LiteralPath $destinationParent).Path -ne $resolvedSkillsDir) {
    throw "Refusing to install outside Codex skills folder: $destinationSkill"
}

if (Test-Path -LiteralPath $destinationSkill) {
    Remove-Item -LiteralPath $destinationSkill -Recurse -Force
}

Copy-Item -LiteralPath $sourceSkill -Destination $destinationSkill -Recurse -Force

$sourceHashes = Get-ChildItem -LiteralPath $sourceSkill -Recurse -File | ForEach-Object {
    $relative = $_.FullName.Substring($sourceSkill.Length).TrimStart('\')
    "$relative|$((Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash)"
}
$destinationHashes = Get-ChildItem -LiteralPath $destinationSkill -Recurse -File | ForEach-Object {
    $relative = $_.FullName.Substring($destinationSkill.Length).TrimStart('\')
    "$relative|$((Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash)"
}

$difference = Compare-Object -ReferenceObject $sourceHashes -DifferenceObject $destinationHashes
if ($difference) {
    throw "Installed skill does not match the maintained source."
}

Write-Host "[install] Wrote and verified $destinationSkill"

$codexHome = Split-Path -Parent $resolvedSkillsDir
$codexHooksDir = Join-Path $codexHome "hooks"
$hookScript = Join-Path $codexHooksDir "drive_project_work_hook.py"
New-Item -ItemType Directory -Force -Path $codexHooksDir | Out-Null
Copy-Item -LiteralPath $sourceHook -Destination $hookScript -Force
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $sourceHook).Hash -ne (Get-FileHash -Algorithm SHA256 -LiteralPath $hookScript).Hash) {
    throw "Installed lifecycle hook does not match the maintained source."
}
Write-Host "[install] Wrote and verified $hookScript"

& (Join-Path $PSScriptRoot "run_python.cmd") (Join-Path $PSScriptRoot "install_hooks.py") --codex-home $codexHome --hook-script $hookScript
if ($LASTEXITCODE -ne 0) {
    throw "Lifecycle hook installation failed."
}
