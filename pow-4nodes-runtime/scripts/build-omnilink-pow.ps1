param([switch]$Force)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Installer = Join-Path $WorkspaceRoot "omnilink-runtime\Install-OmnilinkRuntime.ps1"

Write-Warning "build-omnilink-pow.ps1 is retained for compatibility. It now installs the verified precompiled runtime; no source build is performed."
& $Installer -Force:$Force
