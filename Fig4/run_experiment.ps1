param([int]$Requests = 0, [switch]$PaperScale, [switch]$KeepChain, [switch]$UseRunningChain)
& (Join-Path $PSScriptRoot "..\scripts\Run-FigureExperiment.ps1") -Figure 4 -Requests $Requests -PaperScale:$PaperScale -KeepChain:$KeepChain -UseRunningChain:$UseRunningChain
