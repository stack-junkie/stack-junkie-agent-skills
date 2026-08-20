param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Name,
    [string]$SkillsDir = $(if ($env:CODEX_SKILLS_DIR) { $env:CODEX_SKILLS_DIR } else { Join-Path $env:USERPROFILE '.codex\skills' })
)

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$SourceSkill = Join-Path $RepoRoot "skills\$Name"
if (-not (Test-Path -LiteralPath (Join-Path $SourceSkill 'SKILL.md') -PathType Leaf)) {
    throw "Unknown or invalid skill package: $Name"
}
$VersionFile = Join-Path $SourceSkill 'VERSION'
if (-not (Test-Path -LiteralPath $VersionFile -PathType Leaf)) {
    throw "Skill package is missing VERSION: $Name"
}
$SkillVersion = (Get-Content -LiteralPath $VersionFile -Raw).Trim()
if ($SkillVersion -notmatch '^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-((?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*))*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$') {
    throw "Skill package has an invalid Semantic Version: $Name ($SkillVersion)"
}

New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null
$ResolvedSkillsDir = (Resolve-Path -LiteralPath $SkillsDir).Path
$DestinationSkill = Join-Path $ResolvedSkillsDir $Name
if ((Split-Path -Parent $DestinationSkill) -ne $ResolvedSkillsDir) {
    throw "Refusing to install outside the requested skills directory: $DestinationSkill"
}

if (Test-Path -LiteralPath $DestinationSkill) {
    Remove-Item -LiteralPath $DestinationSkill -Recurse -Force
}
Copy-Item -LiteralPath $SourceSkill -Destination $DestinationSkill -Recurse -Force

function Get-Sha256([string]$Path) {
    $Stream = [System.IO.File]::OpenRead($Path)
    try {
        $Hasher = [System.Security.Cryptography.SHA256]::Create()
        try {
            return ([System.BitConverter]::ToString($Hasher.ComputeHash($Stream))).Replace('-', '')
        }
        finally {
            $Hasher.Dispose()
        }
    }
    finally {
        $Stream.Dispose()
    }
}

function Get-PackageHashes([string]$Root) {
    Get-ChildItem -LiteralPath $Root -Recurse -File |
        Where-Object { $_.FullName -notmatch '[\\/]__pycache__[\\/]' -and $_.Extension -notin '.pyc', '.pyo' } |
        ForEach-Object {
            $Relative = $_.FullName.Substring($Root.Length).TrimStart('\', '/')
            "$Relative|$(Get-Sha256 $_.FullName)"
        }
}

$Difference = Compare-Object -ReferenceObject @(Get-PackageHashes $SourceSkill) -DifferenceObject @(Get-PackageHashes $DestinationSkill)
if ($Difference) {
    throw "Installed package does not match its monorepo source: $Name"
}
Write-Host "[install] Wrote and verified $DestinationSkill (version $SkillVersion)"
