param(
    [string]$Python = 'python',
    [ValidateSet('quick', 'final')][string]$Profile = 'quick',
    [string]$RunId = ''
)
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RunId)) {
    $RunId = $Profile + '_' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
}
if ($RunId -notmatch '^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$') {
    throw 'Invalid run identifier.'
}
$packageDirectory = $PSScriptRoot
$entryPath = Join-Path $packageDirectory 'runDelivery.py'
$resultDirectory = Join-Path (Join-Path $packageDirectory 'results') $RunId
if (Test-Path -LiteralPath $resultDirectory) {
    throw 'The run directory already exists; use a new run identifier.'
}
$startedUtc = [DateTime]::UtcNow.ToString('o')
$timer = [Diagnostics.Stopwatch]::StartNew()
$entryHash = (Get-FileHash -LiteralPath $entryPath -Algorithm SHA256).Hash.ToLowerInvariant()
& $Python -X utf8 -B $entryPath --profile $Profile --run-id $RunId
$processExit = $LASTEXITCODE
$timer.Stop()
if (Test-Path -LiteralPath $resultDirectory) {
    $record = [ordered]@{
        runId = $RunId
        profile = $Profile
        startedAtUtc = $startedUtc
        finishedAtUtc = [DateTime]::UtcNow.ToString('o')
        elapsedSeconds = $timer.Elapsed.TotalSeconds
        actualExitCode = $processExit
        entrySha256AtStart = $entryHash
        entrySha256AtEnd = (Get-FileHash -LiteralPath $entryPath -Algorithm SHA256).Hash.ToLowerInvariant()
        visualStudioGui = 'NOT_OBSERVED_BY_THIS_SCRIPT'
        humanReview = 'PENDING_USER_REVIEW'
    }
    $record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $resultDirectory 'processExit.json') -Encoding UTF8
}
exit $processExit
