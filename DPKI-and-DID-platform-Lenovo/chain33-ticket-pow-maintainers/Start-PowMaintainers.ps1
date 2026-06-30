param(
  [int]$Maintainers = 4,
  [int]$Difficulty = 1,
  [int]$ControlPort = 9899,
  [int]$BlockDelayMs = 0,
  [int]$NetworkLatencyMs = 1,
  [int]$MaxTxPerBlock = 0
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Script = Join-Path $Root "pow-maintainer-network.js"
$PidFile = Join-Path $Root "pow-maintainers.pid"
$LogDir = Join-Path $Root "logs"
$Stdout = Join-Path $LogDir "pow.stdout.log"
$Stderr = Join-Path $LogDir "pow.stderr.log"

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  throw "Node.js is required to run the local PoW maintainer network."
}

if (Test-Path -LiteralPath $PidFile) {
  $ExistingPid = Get-Content -LiteralPath $PidFile | Select-Object -First 1
  if ($ExistingPid -and (Get-Process -Id $ExistingPid -ErrorAction SilentlyContinue)) {
    Write-Host "PoW maintainer network is already running with PID $ExistingPid."
    Write-Host "Control API: http://127.0.0.1:$ControlPort"
    exit 0
  }
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Args = @(
  "`"$Script`"",
  "--maintainers", "$Maintainers",
  "--difficulty", "$Difficulty",
  "--control-port", "$ControlPort",
  "--block-delay-ms", "$BlockDelayMs",
  "--network-latency-ms", "$NetworkLatencyMs",
  "--max-tx-per-block", "$MaxTxPerBlock",
  "--mine-empty"
)

$Process = Start-Process -FilePath "node" `
  -ArgumentList $Args `
  -WorkingDirectory $Root `
  -WindowStyle Hidden `
  -RedirectStandardOutput $Stdout `
  -RedirectStandardError $Stderr `
  -PassThru

Set-Content -LiteralPath $PidFile -Value $Process.Id

Write-Host "Started PoW maintainer network with PID $($Process.Id)."
Write-Host "Control API: http://127.0.0.1:$ControlPort"
Write-Host "Logs: $Stdout and $Stderr"
