$ErrorActionPreference = 'Stop'
$qa = $PSScriptRoot
$source = Join-Path $qa 'before/03_程序代码/runLogged.ps1'
$candidate = Join-Path $qa 'candidate/03_程序代码/runLogged.ps1'
$tokensBefore = $null
$errorsBefore = $null
$treeBefore = [System.Management.Automation.Language.Parser]::ParseFile($source, [ref]$tokensBefore, [ref]$errorsBefore)
if ($errorsBefore.Count) { throw 'Original PowerShell parse failed' }
$textBefore = [IO.File]::ReadAllText($source)
$textAfter = $textBefore
$comments = @($tokensBefore | Where-Object Kind -eq Comment)
foreach ($token in ($comments | Sort-Object {$_.Extent.StartOffset} -Descending)) {
    $first = $token.Extent.StartOffset
    $last = $token.Extent.EndOffset
    $replacement = [regex]::Replace($textAfter.Substring($first, $last-$first), '[^\r\n]', ' ')
    $textAfter = $textAfter.Substring(0,$first) + $replacement + $textAfter.Substring($last)
}
if ($comments.Count) { [IO.File]::WriteAllText($candidate, $textAfter, [Text.UTF8Encoding]::new($false)) }
$tokensAfter = $null
$errorsAfter = $null
$treeAfter = [System.Management.Automation.Language.Parser]::ParseFile($candidate, [ref]$tokensAfter, [ref]$errorsAfter)
if ($errorsAfter.Count) { throw 'Stripped PowerShell parse failed' }
$comparisonBefore = @($tokensBefore | Where-Object Kind -ne Comment | ForEach-Object { [string]$_.Kind + ':' + $_.Text })
$comparisonAfter = @($tokensAfter | Where-Object Kind -ne Comment | ForEach-Object { [string]$_.Kind + ':' + $_.Text })
if (($comparisonBefore -join [char]0) -cne ($comparisonAfter -join [char]0)) { throw 'PowerShell executable token stream changed' }
if (@($tokensAfter | Where-Object Kind -eq Comment).Count) { throw 'PowerShell comments remain' }
$record = [ordered]@{
    language='PowerShell'; comment_count=$comments.Count; docstring_count=0; remaining_comment_count=0
    native_parser='System.Management.Automation.Language.Parser'; parser_version=$PSVersionTable.PSVersion.ToString()
    parser_check='PASS'; noncomment_token_stream_equal=$true; before_sha256=(Get-FileHash -LiteralPath $source).Hash.ToLowerInvariant()
    after_sha256=(Get-FileHash -LiteralPath $candidate).Hash.ToLowerInvariant()
}
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $qa 'strip_powershell_audit.json') -Encoding utf8
$record | ConvertTo-Json -Compress
