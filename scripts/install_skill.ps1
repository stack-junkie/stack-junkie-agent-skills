param(
    [string]$CodexSkillsDir = $(if ($env:CODEX_SKILLS_DIR) { $env:CODEX_SKILLS_DIR } else { "C:\Users\ckvam\.codex\skills" })
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$skillName = "drive-project-work"
$sourceSkill = Join-Path $repoRoot "skill\$skillName"
$destinationSkill = Join-Path $CodexSkillsDir $skillName

if (-not (Test-Path -LiteralPath $sourceSkill)) {
    throw "Source skill folder not found: $sourceSkill"
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
