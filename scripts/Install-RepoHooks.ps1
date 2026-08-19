$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
git -C $RepoRoot config core.hooksPath .githooks
if ((git -C $RepoRoot config --get core.hooksPath) -ne ".githooks") {
    throw "Failed to configure core.hooksPath"
}
Write-Host "[hooks] core.hooksPath=.githooks"
