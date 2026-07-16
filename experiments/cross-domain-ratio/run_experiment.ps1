param([int]$Requests = 0, [switch]$PaperScale, [switch]$KeepChain)
& (Join-Path $PSScriptRoot "..\..\scripts\Run-FigureExperiment.ps1") -Figure 6 -Requests $Requests -PaperScale:$PaperScale -KeepChain:$KeepChain
