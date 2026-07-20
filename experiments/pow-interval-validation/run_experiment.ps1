param(
    [ValidateRange(100, 1000000)][int]$SampleCount = 1000,
    [ValidateRange(1, 60000)][int]$MeanBlockMs = 100,
    [ValidateRange(30, 3600)][int]$TimeoutSeconds = 300,
    [switch]$KeepChain
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ExperimentRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Resolve-Path (Join-Path $ExperimentRoot "..\..")
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ExperimentName = "pow-interval-validation"
$SessionDir = Join-Path $Root ("experiment_artifacts\{0}\{0}_{1}" -f $ExperimentName, $Stamp)
$ResultsDir = Join-Path $SessionDir "results"
$LogDir = Join-Path $Root "pow-4nodes-runtime\runtime\logs"
$StartScript = Join-Path $Root "pow-4nodes-runtime\scripts\start-omnilink-pow-4nodes.ps1"
$StopScript = Join-Path $Root "pow-4nodes-runtime\scripts\stop-omnilink-pow-4nodes.ps1"
$ExtractScript = Join-Path $ExperimentRoot "extract_strict_pow_clock.py"
$TranscriptPath = Join-Path $SessionDir "console.log"

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
Start-Transcript -LiteralPath $TranscriptPath -Force | Out-Null
$Succeeded = $false
try {
    Write-Host "PoW interval validation experiment (paper Fig. 3)"
    Write-Host "Strict PoW samples: $SampleCount"
    Write-Host "Configured aggregate mean interval: $MeanBlockMs ms"
    $Started = $false
    for ($Attempt = 1; $Attempt -le 3; $Attempt += 1) {
        try {
            & $StopScript -ErrorAction SilentlyContinue
            & $StartScript -Clean -MeanBlockMs $MeanBlockMs -MineEmpty `
                -AggregateMiningOnNode0 -WarmupSeconds 1
            $Started = $true
            break
        } catch {
            & $StopScript -ErrorAction SilentlyContinue
            if ($Attempt -eq 3) { throw }
            Write-Warning "Omnilink startup attempt $Attempt failed; retrying after port release."
            Start-Sleep -Seconds 3
        }
    }
    if (-not $Started) { throw "Omnilink PoW runtime did not start." }

    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $Observed = 0
    while ((Get-Date) -lt $Deadline) {
        $Observed = 0
        foreach ($Log in (Get-ChildItem -LiteralPath $LogDir -Filter "node*.stdout.log" -File -ErrorAction SilentlyContinue)) {
            $Observed += @(Select-String -LiteralPath $Log.FullName -Pattern "msg=PowNewBlock.*poissonDelay=" -AllMatches -ErrorAction SilentlyContinue).Count
        }
        Write-Progress -Activity "Collecting strict PoW clock samples" -Status "$Observed / $SampleCount" `
            -PercentComplete ([Math]::Min(100, 100 * $Observed / $SampleCount))
        if ($Observed -ge $SampleCount) { break }
        Start-Sleep -Milliseconds ([Math]::Max(100, [Math]::Min(1000, $MeanBlockMs)))
    }
    Write-Progress -Activity "Collecting strict PoW clock samples" -Completed
    if ($Observed -lt $SampleCount) {
        throw "Collected $Observed strict PoW samples before timeout; required $SampleCount."
    }

    $OutputCsv = Join-Path $ResultsDir "strict_pow_clock_samples.csv"
    $Manifest = Join-Path $ResultsDir "strict_pow_clock_manifest.json"
    & python $ExtractScript --log-dir $LogDir --sample-count $SampleCount `
        --target-mean-ms $MeanBlockMs --output-csv $OutputCsv --manifest $Manifest
    if ($LASTEXITCODE -ne 0) { throw "Strict PoW sample extraction failed with exit code $LASTEXITCODE." }
    $Succeeded = $true
} finally {
    Stop-Transcript | Out-Null
    if (-not $KeepChain) { & $StopScript -ErrorAction SilentlyContinue }
    & (Join-Path $Root "scripts\Collect-ExperimentArtifacts.ps1") -Figure 3 `
        -Experiment $ExperimentName -SessionDir $SessionDir -ResultsDir $ResultsDir
}

if (-not $Succeeded) { throw "PoW interval validation experiment did not complete." }
Write-Host "PoW interval validation completed: $SessionDir"
