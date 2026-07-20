param([int]$SampleCount = 0, [switch]$PaperScale, [switch]$KeepChain)

$Requests = if ($SampleCount -gt 0) { $SampleCount } else { 0 }
& (Join-Path $PSScriptRoot "..\..\scripts\Run-FigureExperiment.ps1") `
    -Figure 3 -Requests $Requests -PaperScale:$PaperScale -KeepChain:$KeepChain
