param(
    [Parameter(Mandatory = $true)][int]$Figure,
    [Parameter(Mandatory = $true)][string]$Experiment,
    [Parameter(Mandatory = $true)][string]$SessionDir,
    [Parameter(Mandatory = $true)][string]$ResultsDir
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$Root = Split-Path -Parent $PSScriptRoot
$SessionPath = [System.IO.Path]::GetFullPath($SessionDir)
$ResultsPath = [System.IO.Path]::GetFullPath($ResultsDir)
$ChainLogDest = Join-Path $SessionPath "blockchain_logs"
$RunLogDest = Join-Path $SessionPath "prototype_run_logs"
New-Item -ItemType Directory -Force -Path $ChainLogDest, $RunLogDest | Out-Null

$PowLogs = Join-Path $Root "pow-4nodes-runtime\runtime\logs"
if (Test-Path -LiteralPath $PowLogs) {
    Copy-Item -LiteralPath $PowLogs -Destination $ChainLogDest -Recurse -Force
}
$PowConfigs = Join-Path $Root "pow-4nodes-runtime\runtime\configs"
if (Test-Path -LiteralPath $PowConfigs) {
    Copy-Item -LiteralPath $PowConfigs -Destination $ChainLogDest -Recurse -Force
}

$RunSources = Join-Path $ResultsPath "logs\run_sources.csv"
if (Test-Path -LiteralPath $RunSources) {
    $Index = 0
    foreach ($Row in (Import-Csv -LiteralPath $RunSources)) {
        if (-not $Row.runDir) { continue }
        $Source = [System.IO.Path]::GetFullPath([string]$Row.runDir)
        if (-not (Test-Path -LiteralPath $Source)) { continue }
        $Index += 1
        $Dest = Join-Path $RunLogDest ("run_{0:D3}" -f $Index)
        New-Item -ItemType Directory -Force -Path $Dest | Out-Null
        foreach ($Name in @(
            "run.log",
            "run_config.json",
            "real_chain_observation.json",
            "real_chain_tx_breakdown.csv",
            "real_stage_statistics.csv",
            "real_delay_statistics.csv",
            "real_simulation_results_by_epsilon_detailed.csv"
        )) {
            $SourceFile = Join-Path $Source $Name
            if (Test-Path -LiteralPath $SourceFile) {
                Copy-Item -LiteralPath $SourceFile -Destination (Join-Path $Dest $Name) -Force
            }
        }
    }
}

$Files = Get-ChildItem -LiteralPath $SessionPath -Recurse -File
$Manifest = [ordered]@{
    experiment = $Experiment
    paperFigure = $Figure
    createdAt = (Get-Date).ToString("o")
    resultsDir = $ResultsPath
    fileCount = $Files.Count
    files = @($Files | ForEach-Object { $_.FullName.Substring($SessionPath.Length + 1) })
}
$Manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $SessionPath "artifact_manifest.json") -Encoding UTF8

$ArchiveRoot = Join-Path $Root "experiment_archives"
New-Item -ItemType Directory -Force -Path $ArchiveRoot | Out-Null
$ArchivePath = Join-Path $ArchiveRoot ((Split-Path -Leaf $SessionPath) + ".zip")
if (Test-Path -LiteralPath $ArchivePath) { Remove-Item -LiteralPath $ArchivePath -Force }
Compress-Archive -Path (Join-Path $SessionPath "*") -DestinationPath $ArchivePath -CompressionLevel Optimal
Write-Host "Experiment archive: $ArchivePath"
