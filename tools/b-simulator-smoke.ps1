[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$RobotId,
    [Parameter(Mandatory)][ValidateSet(3,4)][int]$Problem,
    [Parameter(Mandatory)][string]$OutputPath
)

# Transport-only probe based on attachment 2, section 10. This is not a solver.
# First open the corresponding PRACTICE session through the simulator GUI.
# The account identifier is provided at runtime and removed from saved evidence.
$ErrorActionPreference = 'Stop'
$baseUrl = 'http://127.0.0.1:2026'
$runId = [guid]::NewGuid().ToString('N')
$records = [Collections.Generic.List[object]]::new()
$watch = [Diagnostics.Stopwatch]::StartNew()
$entered = $false
$exited = $false
$sequence = 0
$checks = [ordered]@{}
$failure = $null

function Send-ProbeAction {
    param([string]$Route, [hashtable]$Extra = @{}, [string]$ReuseId = '')
    if (!$ReuseId) { $script:sequence++; $ReuseId = "smoke-$runId-$script:sequence" }
    $payload = @{ arena_id='default'; robot_id=$RobotId; request_id=$ReuseId }
    foreach ($key in $Extra.Keys) { $payload[$key] = $Extra[$key] }
    $body = $payload | ConvertTo-Json -Depth 10 -Compress
    $timer = [Diagnostics.Stopwatch]::StartNew()
    $response = Invoke-WebRequest -Uri ($baseUrl+$Route) -Method Post -ContentType 'application/json;charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 5
    $result = $response.Content | ConvertFrom-Json
    $timer.Stop()
    $safeRequest = $body.Replace($RobotId, '<runtime-robot-id>') | ConvertFrom-Json
    $safeResponse = $response.Content.Replace($RobotId, '<runtime-robot-id>') | ConvertFrom-Json
    $records.Add([ordered]@{ route=$Route; request=$safeRequest; http_status=[int]$response.StatusCode; latency_ms=$timer.Elapsed.TotalMilliseconds; response=$safeResponse })
    if ($response.StatusCode -ne 200 -or $result.accepted -ne $true) { throw "Rejected $Route; inspect sanitized evidence." }
    return $result
}

try {
    $enter = Send-ProbeAction '/enter'
    $entered = $true
    $checks.remaining_real_time_positive = $enter.remaining_real_duration_s -gt 0
    $m1 = Send-ProbeAction '/measure' @{ position=@{x=300;y=400}; channel=1 }
    $m2payload = @{ position=@{x=300;y=400}; channel=2 }
    $m2 = Send-ProbeAction '/measure' $m2payload
    $m2id = $records[$records.Count-1].request.request_id
    $m2repeat = Send-ProbeAction '/measure' $m2payload $m2id
    $checks.idempotent_retry_unchanged_time = [math]::Abs($m2repeat.virtual_time_s-$m2.virtual_time_s) -lt 1e-8
    $clear = Send-ProbeAction '/clear' @{ position=@{x=300;y=0}; channel=3 }
    $m3 = Send-ProbeAction '/measure' @{ position=@{x=300;y=0}; channel=2 }
    $exit = Send-ProbeAction '/exit'
    $exited = $true
    $expectedClear = if ($clear.clear_result -eq 'success') {196.0} else {194.0}
    $checks.first_move_and_measure_105s = [math]::Abs($m1.virtual_time_s-105) -lt 1e-8
    $checks.channel_switch_and_measure_111s = [math]::Abs($m2.virtual_time_s-111) -lt 1e-8
    $checks.clear_time_matches_rule = [math]::Abs($clear.virtual_time_s-$expectedClear) -lt 1e-8
    $checks.clear_does_not_change_measurement_channel = [math]::Abs($m3.virtual_time_s-$expectedClear-5) -lt 1e-8
    $checks.exit_time_unchanged = [math]::Abs($exit.virtual_time_s-$m3.virtual_time_s) -lt 1e-8
    $checks.exit_reason_user_exit = $exit.exit_reason -eq 'user_exit'
} catch {
    $failure = $_.Exception.Message.Replace($RobotId, '<runtime-robot-id>')
} finally {
    if ($entered -and !$exited) {
        try { $null = Send-ProbeAction '/exit'; $exited=$true } catch { $failure += '; cleanup exit failed: ' + $_.Exception.Message.Replace($RobotId,'<runtime-robot-id>') }
    }
    $watch.Stop()
    $passed = !$failure -and $checks.Count -eq 8 -and !($checks.Values -contains $false)
    $evidence = [ordered]@{
        schema_version='1.0'; timestamp=(Get-Date -Format o); purpose='simulator_transport_smoke_test_not_solver'; practice_problem=$Problem;
        source='B attachment 2 section 10, plus one identical request replay';
        base_url=$baseUrl; program_elapsed_s=$watch.Elapsed.TotalSeconds;
        entered=$entered; exited=$exited; checks=$checks; passed=$passed; error=$failure; records=$records.ToArray()
    }
    $parent=Split-Path -Parent $OutputPath
    $null=New-Item -ItemType Directory -Force -Path $parent
    $evidence | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $OutputPath -Encoding utf8
    [ordered]@{ passed=$passed; checks=$checks; error=$failure; requests=$records.Count; output=$OutputPath } | ConvertTo-Json -Depth 5
}
if (!$passed) { throw 'Simulator transport probe failed; see sanitized evidence.' }
