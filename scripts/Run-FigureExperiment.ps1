param(
    [Parameter(Mandatory = $true)][ValidateRange(4, 10)][int]$Figure,
    [int]$Requests = 0,
    [switch]$PaperScale,
    [switch]$KeepChain,
    [switch]$UseRunningChain
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$PaperRequests = @{ 4 = 1000; 5 = 10000; 6 = 2000; 7 = 2000; 8 = 10000; 9 = 10000; 10 = 10000 }
$ExperimentNames = @{
    4 = "baseline-comparison"
    5 = "arrival-rate"
    6 = "cross-domain-ratio"
    7 = "management-ratio"
    8 = "service-ca-number"
    9 = "availability-timeout"
    10 = "availability-service-ca-number"
}
$ExperimentName = $ExperimentNames[$Figure]
if ($Requests -le 0) {
    $Requests = if ($PaperScale) { $PaperRequests[$Figure] } else { 50 }
}

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$SessionDir = Join-Path $Root ("experiment_artifacts\{0}\{0}_{1}" -f $ExperimentName, $Stamp)
$ResultsDir = Join-Path $SessionDir "results"
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
$TranscriptPath = Join-Path $SessionDir "console.log"
$CommandLogDir = Join-Path $SessionDir "command_logs"
New-Item -ItemType Directory -Force -Path $CommandLogDir | Out-Null
$env:DPKI_LIVE_TRACE = "1"
$env:DPKI_VERBOSE_TRACE = "1"
$env:PYTHONUNBUFFERED = "1"

$StopScript = Join-Path $Root "pow-4nodes-runtime\scripts\stop-omnilink-pow-4nodes.ps1"
$StartScript = Join-Path $Root "pow-4nodes-runtime\scripts\start-omnilink-pow-4nodes.ps1"
$StartedHere = $false
$Succeeded = $false
$StopPowArg = if ($KeepChain) { "--no-stop-pow" } else { "--stop-pow" }
$CommandIndex = 0

function Invoke-Checked {
    param([string]$Command, [string[]]$Arguments)
    $script:CommandIndex += 1
    $CommandName = [System.IO.Path]::GetFileNameWithoutExtension($Command)
    $CommandLog = Join-Path $CommandLogDir ("{0:D2}_{1}.log" -f $script:CommandIndex, $CommandName)
    Write-Host "RUN: $Command $($Arguments -join ' ')"
    $PreviousErrorAction = $ErrorActionPreference
    try {
        # Native programs routinely use stderr for non-fatal diagnostics. Keep
        # those lines visible and archived, and use the exit code for failure.
        $ErrorActionPreference = "Continue"
        & $Command @Arguments 2>&1 | Tee-Object -LiteralPath $CommandLog
        $ExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $PreviousErrorAction
    }
    if ($ExitCode -ne 0) { throw "Command failed with exit code ${ExitCode}: $Command" }
}

Start-Transcript -LiteralPath $TranscriptPath -Force | Out-Null
try {
    Write-Host "$ExperimentName real experiment session (paper Fig. $Figure)"
    Write-Host "Requests per selected point/class: $Requests"
    Write-Host "Results are isolated under: $ResultsDir"

    if ($Figure -eq 4) {
        if (-not $UseRunningChain) {
            & $StopScript -ErrorAction SilentlyContinue
            & $StartScript -MeanBlockMs 20 -MineEmpty -AggregateMiningOnNode0 -WarmupSeconds 10
            $StartedHere = $true
            Write-Host "Waiting 10 seconds for peer synchronization before contract deployment..."
            Start-Sleep -Seconds 10
        }
        Invoke-Checked "node" @(
            "experiments/baseline-comparison/prototype_baseline_benchmark/run_prototype_baseline_benchmark.js",
            "--requests", [string]$Requests,
            "--noop-probes", [string][Math]::Max(20, [Math]::Min($Requests, 200)),
            "--out", $ResultsDir
        )
    } elseif ($Figure -eq 5) {
        Invoke-Checked "python" @(
            "experiments/arrival-rate/run_fig5_lambda.py",
            "--lambda-values", $(if ($PaperScale) { "2,3,4,5,6,7,8,10,12,14" } else { "4,8" }),
            "--mean-block-ms-values", $(if ($PaperScale) { "80,90,100" } else { "80" }),
            "--requests", [string]$Requests,
            "--tag", "github_arrival_rate_$Stamp",
            "--output-dir", $ResultsDir,
            $StopPowArg
        )
    } elseif ($Figure -eq 6) {
        Invoke-Checked "python" @(
            "experiments/cross-domain-ratio/run_fig6_epsilon.py",
            "--epsilon-points", $(if ($PaperScale) { "0.05,0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5" } else { "0.1,0.3" }),
            "--requests", [string]$Requests,
            "--tag", "github_cross_domain_ratio_$Stamp",
            "--output-dir", $ResultsDir,
            $StopPowArg
        )
    } elseif ($Figure -eq 7) {
        Invoke-Checked "python" @(
            "experiments/management-ratio/run_fig7_p.py",
            "--p-values", $(if ($PaperScale) { "0,0.05,0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5" } else { "0.2" }),
            "--requests", [string]$Requests,
            "--tag", "github_management_ratio_$Stamp",
            "--output-dir", $ResultsDir,
            $StopPowArg
        )
    } elseif ($Figure -eq 8) {
        Invoke-Checked "python" @(
            "experiments/service-ca-number/run_fig8_m.py",
            "--m-values", $(if ($PaperScale) { "2,3,4,5,6,7,8,9" } else { "4,6" }),
            "--requests", [string]$Requests,
            "--tag", "github_service_ca_number_$Stamp",
            "--output-dir", $ResultsDir,
            $StopPowArg
        )
    } elseif ($Figure -eq 9) {
        $ProbeDir = Join-Path $ResultsDir "real_chain_probe"
        Invoke-Checked "python" @(
            "experiments/management-ratio/run_fig7_p.py", "--p-values", "0.2", "--requests", [string]$Requests,
            "--epsilon", "0.1", "--mean-block-ms", "20", "--tag", "github_availability_timeout_probe_$Stamp",
            "--output-dir", $ProbeDir, $StopPowArg
        )
        Invoke-Checked "python" @(
            "scripts/Extract-TailProbe.py", "--figure", "9", "--result-dir", $ProbeDir,
            "--output-dir", (Join-Path $ResultsDir "tail_probe")
        )
    } elseif ($Figure -eq 10) {
        $ProbeDir = Join-Path $ResultsDir "real_chain_probe"
        Invoke-Checked "python" @(
            "experiments/service-ca-number/run_fig8_m.py", "--m-values", "6", "--requests", [string]$Requests,
            "--epsilon", "0.1", "--mean-block-ms", "20", "--tag", "github_availability_service_ca_number_probe_$Stamp",
            "--output-dir", $ProbeDir, $StopPowArg
        )
        Invoke-Checked "python" @(
            "scripts/Extract-TailProbe.py", "--figure", "10", "--result-dir", $ProbeDir,
            "--output-dir", (Join-Path $ResultsDir "tail_probe")
        )
    }
    $Succeeded = $true
} finally {
    Stop-Transcript | Out-Null
    $FullConsole = Join-Path $SessionDir "console_full.log"
    Copy-Item -LiteralPath $TranscriptPath -Destination $FullConsole -Force
    foreach ($CommandLog in (Get-ChildItem -LiteralPath $CommandLogDir -Filter "*.log" -File | Sort-Object Name)) {
        Add-Content -LiteralPath $FullConsole -Value "`r`n===== $($CommandLog.Name) =====`r`n"
        Get-Content -LiteralPath $CommandLog.FullName | Add-Content -LiteralPath $FullConsole
    }
    if ($StartedHere -and -not $KeepChain) {
        & $StopScript -ErrorAction SilentlyContinue
    }
    & (Join-Path $Root "scripts\Collect-ExperimentArtifacts.ps1") -Figure $Figure -Experiment $ExperimentName -SessionDir $SessionDir -ResultsDir $(if ($Figure -ge 9) { Join-Path $ResultsDir "real_chain_probe" } else { $ResultsDir })
    Remove-Item Env:DPKI_LIVE_TRACE -ErrorAction SilentlyContinue
    Remove-Item Env:DPKI_VERBOSE_TRACE -ErrorAction SilentlyContinue
    Remove-Item Env:PYTHONUNBUFFERED -ErrorAction SilentlyContinue
}

if (-not $Succeeded) { throw "$ExperimentName experiment did not complete." }
Write-Host "$ExperimentName experiment completed: $SessionDir"
