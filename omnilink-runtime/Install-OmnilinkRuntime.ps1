param(
    [switch]$Force,
    [switch]$VerifyOnly
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManifestPath = Join-Path $PackageRoot "runtime-manifest.json"
if (-not (Test-Path -LiteralPath $ManifestPath)) {
    throw "Omnilink runtime manifest not found: $ManifestPath"
}

$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$ArchivePath = Join-Path $PackageRoot ([string]$Manifest.archive).Replace("/", "\")
$ExecutablePath = Join-Path $PackageRoot ([string]$Manifest.executable).Replace("/", "\")
$ExecutableDir = Split-Path -Parent $ExecutablePath

$IsWindowsHost = [Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
if (-not $IsWindowsHost) {
    throw "This repository currently distributes the Omnilink runtime for Windows x64 only."
}
if (-not [Environment]::Is64BitOperatingSystem) {
    throw "The bundled Omnilink executable requires 64-bit Windows."
}
if (-not (Test-Path -LiteralPath $ArchivePath)) {
    throw "Omnilink runtime archive not found: $ArchivePath"
}

function Assert-FileHash {
    param(
        [string]$Path,
        [string]$ExpectedHash,
        [long]$ExpectedBytes,
        [string]$Label
    )
    $File = Get-Item -LiteralPath $Path
    if ($File.Length -ne $ExpectedBytes) {
        throw "$Label size mismatch: expected $ExpectedBytes bytes, got $($File.Length)."
    }
    $ActualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
    if ($ActualHash -ne $ExpectedHash) {
        throw "$Label SHA-256 mismatch: expected $ExpectedHash, got $ActualHash."
    }
}

Assert-FileHash -Path $ArchivePath -ExpectedHash $Manifest.archive_sha256 `
    -ExpectedBytes $Manifest.archive_bytes -Label "Omnilink archive"

if ($VerifyOnly) {
    if (Test-Path -LiteralPath $ExecutablePath) {
        Assert-FileHash -Path $ExecutablePath -ExpectedHash $Manifest.executable_sha256 `
            -ExpectedBytes $Manifest.executable_bytes -Label "Omnilink executable"
        Write-Host "Omnilink archive and installed executable passed SHA-256 verification."
    } else {
        Write-Host "Omnilink archive passed SHA-256 verification; executable will be extracted on first run."
    }
    exit 0
}

$InstallRequired = $Force -or -not (Test-Path -LiteralPath $ExecutablePath)
if (-not $InstallRequired) {
    try {
        Assert-FileHash -Path $ExecutablePath -ExpectedHash $Manifest.executable_sha256 `
            -ExpectedBytes $Manifest.executable_bytes -Label "Omnilink executable"
    } catch {
        Write-Warning $_.Exception.Message
        $InstallRequired = $true
    }
}

if ($InstallRequired) {
    New-Item -ItemType Directory -Force -Path $ExecutableDir | Out-Null
    Expand-Archive -LiteralPath $ArchivePath -DestinationPath $ExecutableDir -Force
    Assert-FileHash -Path $ExecutablePath -ExpectedHash $Manifest.executable_sha256 `
        -ExpectedBytes $Manifest.executable_bytes -Label "Omnilink executable"
    Write-Host "Installed Omnilink runtime: $ExecutablePath"
} else {
    Write-Host "Omnilink runtime is installed and verified: $ExecutablePath"
}
