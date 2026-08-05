param(
    [Parameter(Position = 0)]
    [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

$resolvedRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$markers = @(
    "AGENTS.override.md",
    "AGENTS.md",
    ".codex\config.toml",
    "VERSION",
    "CHANGELOG.md",
    "README.md",
    "CONTRIBUTING.md",
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "CMakeLists.txt",
    "docs\planning\DECISIONS.md",
    "docs\planning\REQUIREMENTS.md",
    "docs\planning\MASTER_PLAN.md"
)

$presentMarkers = @()
foreach ($marker in $markers) {
    if (Test-Path -LiteralPath (Join-Path $resolvedRoot $marker)) {
        $presentMarkers += $marker
    }
}

$gitRoot = $null
$branch = $null
$head = $null
$remoteNames = @()
$statusEntries = @()
$isGitRepository = $false

$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
$gitProbe = & git -C $resolvedRoot rev-parse --show-toplevel 2>$null
$gitProbeExitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorActionPreference
if ($gitProbeExitCode -eq 0 -and $gitProbe) {
    $isGitRepository = $true
    $gitRoot = ($gitProbe | Select-Object -First 1).Trim()
    $branch = (& git -C $resolvedRoot branch --show-current 2>$null | Select-Object -First 1)
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    $headProbe = & git -C $resolvedRoot rev-parse --short HEAD 2>$null
    $headProbeExitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorActionPreference
    if ($headProbeExitCode -eq 0) {
        $head = ($headProbe | Select-Object -First 1)
    }
    $remoteNames = @(& git -C $resolvedRoot remote 2>$null)
    $statusEntries = @(& git -C $resolvedRoot status --porcelain=v1 --untracked-files=all 2>$null)
}

$version = $null
$versionPath = Join-Path $resolvedRoot "VERSION"
if (Test-Path -LiteralPath $versionPath) {
    $version = (Get-Content -LiteralPath $versionPath -TotalCount 1).Trim()
}

$statusSummary = [ordered]@{
    total = $statusEntries.Count
    staged = @($statusEntries | Where-Object { $_.Length -ge 2 -and $_[0] -ne " " -and $_[0] -ne "?" }).Count
    unstaged = @($statusEntries | Where-Object { $_.Length -ge 2 -and $_[1] -ne " " -and $_[1] -ne "?" }).Count
    untracked = @($statusEntries | Where-Object { $_.StartsWith("??") }).Count
}

$result = [ordered]@{
    project_root = $resolvedRoot
    git = [ordered]@{
        is_repository = $isGitRepository
        root = $gitRoot
        branch = $branch
        head = $head
        remotes = $remoteNames
        status = $statusSummary
    }
    version = $version
    markers = $presentMarkers
}

$result | ConvertTo-Json -Depth 5
