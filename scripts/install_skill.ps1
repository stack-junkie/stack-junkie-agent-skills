param(
    [string]$CodexSkillsDir = $(if ($env:CODEX_SKILLS_DIR) { $env:CODEX_SKILLS_DIR } else { "C:\Users\stack-junkie\.codex\skills" })
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$SkillName = "repo-readiness"
$SourceSkill = Join-Path $RepoRoot "skill\$SkillName"
$DestSkill = Join-Path $CodexSkillsDir $SkillName

if (-not (Test-Path -LiteralPath $SourceSkill)) {
    throw "Source skill folder not found: $SourceSkill"
}

New-Item -ItemType Directory -Force -Path $CodexSkillsDir | Out-Null
$resolvedSkillsDir = (Resolve-Path -LiteralPath $CodexSkillsDir).Path
$destParent = Split-Path -Parent $DestSkill
if ((Resolve-Path -LiteralPath $destParent).Path -ne $resolvedSkillsDir) {
    throw "Refusing to install outside Codex skills folder: $DestSkill"
}

if (Test-Path -LiteralPath $DestSkill) {
    Remove-Item -LiteralPath $DestSkill -Recurse -Force
}

Copy-Item -LiteralPath $SourceSkill -Destination $DestSkill -Recurse -Force
Write-Host "[install] Wrote $DestSkill"
