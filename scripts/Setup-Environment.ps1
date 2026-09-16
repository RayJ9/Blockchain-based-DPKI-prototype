param(
    [switch]$SkipPython,
    [switch]$SkipNode,
    [switch]$SkipOmnilinkBuild
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Require-Command {
    param([string]$Name, [string]$InstallHint)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing command '$Name'. $InstallHint"
    }
}

Require-Command python "Install Python 3.10 or newer and add it to PATH."
Require-Command openssl "Install OpenSSL 3.x and add it to PATH."
Require-Command node "Install Node.js 18 or newer and add it to PATH."
Require-Command npm "Install npm together with Node.js."
if (-not $SkipOmnilinkBuild) {
    Require-Command go "Install Go and add it to PATH before building Omnilink."
}

if (-not $SkipPython) {
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "Python dependency installation failed." }
}

if (-not $SkipNode) {
    Push-Location (Join-Path $Root "blockchain\dpki-experiment")
    try {
        npm ci
        if ($LASTEXITCODE -ne 0) { throw "Node dependency installation failed." }
    } finally {
        Pop-Location
    }
}

if (-not $SkipOmnilinkBuild) {
    & (Join-Path $Root "blockchain\pow-4nodes-runtime\scripts\build-omnilink-pow.ps1")
}

node (Join-Path $Root "scripts\Check-ModuleContracts.js")
if ($LASTEXITCODE -ne 0) { throw "Module contract check failed." }
Write-Host "Environment setup completed."
