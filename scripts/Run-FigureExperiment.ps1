param(
    [Parameter(Mandatory = $true)][ValidateRange(3, 10)][int]$Figure,
    [int]$Requests = 0,
    [switch]$PaperScale,
    [switch]$KeepChain,
    [switch]$UseRunningChain,
    [int]$Rounds = 10,
    [int]$WarmupRequests = 20,
    [string]$PfValues = "0,0.2,0.6,1",
    [string]$MValues = "",
    [string]$Timeouts = "",
    [ValidateSet("both", "nonresponding", "malicious")][string]$Scenario = "both",
    [int]$Seed = 20260916,
    [ValidateRange(1, 60000)][int]$MeanBlockMs = 60
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$PaperRequests = @{ 3 = 1000; 4 = 1000; 5 = 10000; 6 = 2000; 7 = 2000; 8 = 10000; 9 = 10000; 10 = 10000 }
$ExperimentNames = @{
    3 = "pow-interval-validation"
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

$BlockchainRoot = Join-Path $Root "blockchain"
$ThreeChainRoot = Join-Path $BlockchainRoot "sidechain-three-chain"
$StopScript = Join-Path $ThreeChainRoot "scripts\stop-three-chains.ps1"
$StartScript = Join-Path $ThreeChainRoot "scripts\start-three-chains.ps1"
$BootstrapScript = Join-Path $ThreeChainRoot "run-sidechain-smoke.js"
$LegacyPowStopScript = Join-Path $BlockchainRoot "pow-4nodes-runtime\scripts\stop-omnilink-pow-4nodes.ps1"
$StartedHere = $false
$Succeeded = $false
$StopPowArg = "--no-stop-pow"
$CommandIndex = 0

$env:DPKI_USE_SIDECHAINS = "1"
$env:DPKI_EXPERIMENT_RPC = "http://127.0.0.1:18745"
$env:DPKI_EXPERIMENT_JRPC = "http://127.0.0.1:18901"
$env:DPKI_CHAIN_ID = "4101"
if (-not $UseRunningChain -or -not $env:DPKI_CHAIN_RUNTIME) {
    $env:DPKI_CHAIN_RUNTIME = Join-Path $ThreeChainRoot "runtime"
}
if ($Figure -ge 9 -and -not $UseRunningChain) {
    $env:DPKI_CHAIN_RUNTIME = Join-Path $ThreeChainRoot "runtime\availability_$Stamp"
}
$env:SIDECHAIN_OUTPUT_DIR = Join-Path $SessionDir "sidechain_bootstrap"

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
    Write-Host "$ExperimentName prototype session (repository Fig. $Figure)"
    Write-Host "Requests per selected point/class: $Requests"
    Write-Host "Results are isolated under: $ResultsDir"

    if (-not $UseRunningChain) {
        if ($Figure -ge 9) {
            & $StartScript -MeanBlockMs $MeanBlockMs -RuntimeDirectory $env:DPKI_CHAIN_RUNTIME
        } else {
            & $LegacyPowStopScript -ErrorAction SilentlyContinue
            & $StopScript -ErrorAction SilentlyContinue
            & $StartScript -MeanBlockMs 20 -Clean
        }
        $StartedHere = $true
        Write-Host "Bootstrapping the main-chain CA registry and both domain sidechains..."
        Invoke-Checked "node" @($BootstrapScript)
    }

    if ($Figure -eq 3) {
        Start-Sleep -Seconds ([Math]::Max(12, [Math]::Ceiling($Requests * 0.02 / 3.0) + 5))
        Invoke-Checked "python" @(
            "experiments/pow-interval-validation/extract_strict_pow_clock.py",
            "--log-dir", (Join-Path $ThreeChainRoot "runtime\logs"),
            "--sample-count", [string]$Requests,
            "--output-csv", (Join-Path $ResultsDir "strict_pow_clock_samples.csv"),
            "--manifest", (Join-Path $ResultsDir "strict_pow_clock_manifest.json")
        )
    } elseif ($Figure -eq 4) {
        Invoke-Checked "node" @(
            "experiments/baseline-comparison/prototype_baseline_benchmark/run_prototype_baseline_benchmark.js",
            "--requests", [string]$Requests,
            "--noop-probes", [string][Math]::Max(20, [Math]::Min($Requests, 200)),
            "--rpc", $env:DPKI_EXPERIMENT_RPC,
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
    } elseif ($Figure -ge 9) {
        $AvailabilityArgs = @(
            "-m", "figure_dpki_pki_runtime.availability_experiment", "--figure", [string]$Figure,
            "--requests", [string]$Requests, "--rounds", [string]$Rounds,
            "--warmup-requests", [string]$WarmupRequests, "--pf-values", $PfValues,
            "--scenario", $Scenario, "--seed", [string]$Seed, "--output-dir", $ResultsDir
        )
        if ($MValues) { $AvailabilityArgs += @("--m-values", $MValues) }
        if ($Timeouts) { $AvailabilityArgs += @("--timeouts", $Timeouts) }
        Invoke-Checked "python" $AvailabilityArgs
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
        & $StopScript -RuntimeDirectory $env:DPKI_CHAIN_RUNTIME -ErrorAction SilentlyContinue
    }
    $BootstrapRoot = [System.IO.Path]::GetFullPath($env:SIDECHAIN_OUTPUT_DIR)
    if (Test-Path -LiteralPath $BootstrapRoot) {
        Get-ChildItem -LiteralPath $BootstrapRoot -Recurse -File -Filter "*.key.pem" -ErrorAction SilentlyContinue | ForEach-Object {
            $KeyPath = [System.IO.Path]::GetFullPath($_.FullName)
            if (-not $KeyPath.StartsWith($BootstrapRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
                throw "Refusing to remove an ephemeral key outside $BootstrapRoot"
            }
            Remove-Item -LiteralPath $KeyPath -Force
        }
    }
    & (Join-Path $Root "scripts\Collect-ExperimentArtifacts.ps1") -Figure $Figure -Experiment $ExperimentName -SessionDir $SessionDir -ResultsDir $ResultsDir
    Remove-Item Env:DPKI_LIVE_TRACE -ErrorAction SilentlyContinue
    Remove-Item Env:DPKI_VERBOSE_TRACE -ErrorAction SilentlyContinue
    Remove-Item Env:PYTHONUNBUFFERED -ErrorAction SilentlyContinue
    Remove-Item Env:DPKI_USE_SIDECHAINS -ErrorAction SilentlyContinue
    Remove-Item Env:DPKI_EXPERIMENT_RPC -ErrorAction SilentlyContinue
    Remove-Item Env:DPKI_EXPERIMENT_JRPC -ErrorAction SilentlyContinue
    Remove-Item Env:DPKI_CHAIN_ID -ErrorAction SilentlyContinue
    Remove-Item Env:DPKI_CHAIN_RUNTIME -ErrorAction SilentlyContinue
    Remove-Item Env:SIDECHAIN_OUTPUT_DIR -ErrorAction SilentlyContinue
}

if (-not $Succeeded) { throw "$ExperimentName experiment did not complete." }
Write-Host "$ExperimentName experiment completed: $SessionDir"
