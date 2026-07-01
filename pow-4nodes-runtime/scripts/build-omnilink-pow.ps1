$ErrorActionPreference = "Stop"

$DpkiRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$WorkspaceRoot = $DpkiRoot
$PluginRoot = Join-Path $WorkspaceRoot "omnilink\omnilink-plugin"
$BuildDir = Join-Path $PluginRoot "build"
$Exe = Join-Path $BuildDir "omni.exe"
$PortableGo = Join-Path $WorkspaceRoot ".tools\go1.20.14\go\bin\go.exe"

if (Test-Path $PortableGo) {
  $Go = $PortableGo
} else {
  $Go = "go"
}

New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null

if (-not $env:GOPROXY) {
  $env:GOPROXY = "https://goproxy.cn,direct"
}

Write-Host "Building Omnilink PoW node with $Go"
Push-Location $PluginRoot
try {
  & $Go build -o $Exe .
  if ($LASTEXITCODE -ne 0) {
    throw "go build failed with exit code $LASTEXITCODE"
  }
} finally {
  Pop-Location
}

Write-Host "Built $Exe"
