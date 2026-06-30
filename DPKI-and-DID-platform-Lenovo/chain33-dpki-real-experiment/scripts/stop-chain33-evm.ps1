$ErrorActionPreference = "Stop"

$StopScript = Resolve-Path (Join-Path $PSScriptRoot "..\..\omnilink-pow-4nodes\scripts\stop-omnilink-pow-4nodes.ps1")
Write-Host "Stopping Omnilink PoW 4-node EVM network for DPKI."
& $StopScript
