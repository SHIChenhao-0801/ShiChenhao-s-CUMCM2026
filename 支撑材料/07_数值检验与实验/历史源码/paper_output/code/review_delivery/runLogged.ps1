param(
    [ValidateSet('final', 'audit')][string]$Profile = 'final',
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$')][string]$RunId,
    [string]$PythonPath = 'C:\Python314\python.exe'
)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
if ((Get-Location).Path -ne $projectRoot) { throw '请在2026CUMCM根目录执行此脚本。' }
if (-not $RunId) { $RunId = $Profile + '_' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ') }
$driverRoot = Join-Path $projectRoot ('paper_output/results/code_delivery/driver_' + $RunId)
if (Test-Path -LiteralPath $driverRoot) { throw '运行编号已存在；请指定新的RunId。' }
New-Item -ItemType Directory -Path $driverRoot | Out-Null
$scriptPath = Join-Path $PSScriptRoot 'runDelivery.py'
$argumentText = '-B "' + $scriptPath + '" --profile ' + $Profile + ' --run-id ' + $RunId
$startedAt = [DateTime]::UtcNow.ToString('o')
$timer = [Diagnostics.Stopwatch]::StartNew()
$sourceShaBefore = (Get-FileHash -LiteralPath $scriptPath -Algorithm SHA256).Hash.ToLowerInvariant()
# 此监督进程观察真实退出码；模型程序本身不能自证进程已经退出。
$taskProcess = Start-Process -FilePath $PythonPath -ArgumentList $argumentText `
    -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $driverRoot 'process.stdout.log') `
    -RedirectStandardError (Join-Path $driverRoot 'process.stderr.log')
$observedPeakWorkingSetBytes = 0L
$timedOut = $false
while (-not $taskProcess.WaitForExit(1000)) {
    $taskProcess.Refresh()
    $observedPeakWorkingSetBytes = [Math]::Max($observedPeakWorkingSetBytes, $taskProcess.WorkingSet64)
    if ($Profile -eq 'audit' -and $timer.Elapsed.TotalSeconds -gt 1800) {
        $timedOut = $true
        $taskProcess.Kill($true)
        $taskProcess.WaitForExit()
        break
    }
}
$timer.Stop()
$processRecord = [ordered]@{
    runId = $RunId; profile = $Profile; executable = $PythonPath
    argumentText = $argumentText; cwd = $projectRoot; processId = $taskProcess.Id
    startedAtUtc = $startedAt; finishedAtUtc = [DateTime]::UtcNow.ToString('o')
    elapsedSeconds = $timer.Elapsed.TotalSeconds; actualExitCode = $taskProcess.ExitCode
    sourceSha256AtLaunch = $sourceShaBefore
    sourceSha256AtExit = (Get-FileHash -LiteralPath $scriptPath -Algorithm SHA256).Hash.ToLowerInvariant()
    observedPeakWorkingSetBytes = $observedPeakWorkingSetBytes
    memoryScope = 'One-second observed process working set; excludes transient peaks and child processes'
    timedOut = $timedOut
    humanReview = 'pending'; guiObserved = $false
}
$processRecord | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $driverRoot 'processResult.json') -Encoding utf8
$processRecord | ConvertTo-Json -Depth 8
exit $taskProcess.ExitCode
