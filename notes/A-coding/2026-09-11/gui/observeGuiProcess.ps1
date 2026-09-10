param([Parameter(Mandatory=$true)][int]$ObservedProcessId)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../..')).Path
if ((Get-Location).Path -ne $projectRoot) { throw 'Observer must run in this contest workspace.' }
$processInfo = Get-CimInstance Win32_Process -Filter ('ProcessId=' + $ObservedProcessId)
if (-not $processInfo -or $processInfo.CommandLine -notlike '*runDelivery.py*gui_camel_final_v2*') {
    throw 'PID does not identify the intended GUI delivery worker.'
}
$observedProcess = Get-Process -Id $ObservedProcessId
# 提前持有进程句柄，以便在实际退出后读取退出码；不控制或中止该进程。
$pinnedHandle = $observedProcess.Handle
$observationStartedAt = [DateTime]::UtcNow.ToString('o')
$processStartedAt = $observedProcess.StartTime.ToUniversalTime().ToString('o')
$sourcePath = Join-Path $projectRoot 'paper_output/code/review_delivery/runDelivery.py'
$sourceHashBefore = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash.ToLowerInvariant()
while (-not $observedProcess.WaitForExit(1000)) { }
$exitRecord = [ordered]@{
    runId = 'gui_camel_final_v2'
    role = 'External read-only observer of the already GUI-launched Python worker'
    processId = $ObservedProcessId
    executable = $processInfo.ExecutablePath
    processStartedAtUtc = $processStartedAt
    observationStartedAtUtc = $observationStartedAt
    observedExitAtUtc = [DateTime]::UtcNow.ToString('o')
    actualExitCode = $observedProcess.ExitCode
    sourceSha256AtObservationStart = $sourceHashBefore
    sourceSha256AtObservedExit = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash.ToLowerInvariant()
    guiEvidence = 'IDE运行观察.md and saved Computer Use screenshots; separate from this process observer'
    processWasStoppedByObserver = $false
    humanReview = 'pending'
    timingScope = 'Process start and observed exit include GUI breakpoint pauses; not pure solver performance'
}
$exitRecord | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'guiProcessExit.json') -Encoding utf8
$exitRecord | ConvertTo-Json -Depth 4
exit $observedProcess.ExitCode
