param([int]$Requests = 0, [switch]$PaperScale, [switch]$KeepChain, [switch]$UseRunningChain,
    [int]$Rounds = 10, [int]$WarmupRequests = 20, [string]$PfValues = "0,0.2,0.6,1",
    [string]$MValues = "6", [string]$Timeouts = "0.08,0.10",
    [ValidateSet("both", "nonresponding", "malicious")][string]$Scenario = "both", [int]$Seed = 20260916,
    [ValidateRange(1, 60000)][int]$MeanBlockMs = 60)
& (Join-Path $PSScriptRoot "..\..\scripts\Run-FigureExperiment.ps1") -Figure 9 @PSBoundParameters
