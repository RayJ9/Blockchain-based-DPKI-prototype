param(
  [int]$MeanBlockMs = 200,
  [UInt32]$DifficultyBits = 521142271,
  [switch]$Build,
  [switch]$Clean
)

$ErrorActionPreference = "Stop"

$StartScript = Resolve-Path (Join-Path $PSScriptRoot "..\..\omnilink-pow-4nodes\scripts\start-omnilink-pow-4nodes.ps1")
Write-Host "Starting Omnilink PoW 4-node EVM network for DPKI."
& $StartScript @PSBoundParameters
