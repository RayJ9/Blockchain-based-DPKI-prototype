param(
    [int]$MeanBlockMs = 80,
    [switch]$KeepChains
)

$ErrorActionPreference = "Stop"
$PrototypeRoot = Resolve-Path $PSScriptRoot
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$session = Join-Path $PrototypeRoot "outputs\three_chain_$stamp"
$archiveDir = Join-Path $PrototypeRoot "archives"
$consoleLog = Join-Path $session "console.log"
New-Item -ItemType Directory -Force -Path $session, $archiveDir | Out-Null
$env:SIDECHAIN_OUTPUT_DIR = $session

$exitCode = 0
try {
    & (Join-Path $PrototypeRoot "scripts\start-three-chains.ps1") -MeanBlockMs $MeanBlockMs -Clean
    node (Join-Path $PrototypeRoot "run-sidechain-smoke.js") 2>&1 | Tee-Object -LiteralPath $consoleLog
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "Three-chain smoke experiment failed with exit code $exitCode"
    }
} finally {
    $runtime = Join-Path $PrototypeRoot "runtime"
    $chainLogs = Join-Path $session "blockchain_logs"
    if (Test-Path -LiteralPath $runtime) {
        New-Item -ItemType Directory -Force -Path $chainLogs | Out-Null
        foreach ($name in @("configs", "logs", "chains.json")) {
            $source = Join-Path $runtime $name
            if (Test-Path -LiteralPath $source) {
                Copy-Item -LiteralPath $source -Destination $chainLogs -Recurse -Force
            }
        }
    }
    if (-not $KeepChains) {
        & (Join-Path $PrototypeRoot "scripts\stop-three-chains.ps1")
    }
    Remove-Item Env:SIDECHAIN_OUTPUT_DIR -ErrorAction SilentlyContinue
}

$sessionFull = [System.IO.Path]::GetFullPath($session)
Get-ChildItem -LiteralPath $session -Recurse -File -Filter *.key.pem -ErrorAction SilentlyContinue | ForEach-Object {
    $keyFull = [System.IO.Path]::GetFullPath($_.FullName)
    if (-not $keyFull.StartsWith($sessionFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove an ephemeral key outside $sessionFull"
    }
    Remove-Item -LiteralPath $keyFull -Force
}

$archive = Join-Path $archiveDir "three_chain_$stamp.zip"
Compress-Archive -Path (Join-Path $session "*") -DestinationPath $archive -Force
Write-Host "Experiment session: $session"
Write-Host "Archive: $archive"
