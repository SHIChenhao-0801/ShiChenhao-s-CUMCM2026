param([Parameter(Mandatory)][string]$Before,[Parameter(Mandatory)][string]$Current)
$ErrorActionPreference='Stop'
$tokensA=$null; $errorsA=$null; $tokensB=$null; $errorsB=$null
$null=[System.Management.Automation.Language.Parser]::ParseFile($Before,[ref]$tokensA,[ref]$errorsA)
$null=[System.Management.Automation.Language.Parser]::ParseFile($Current,[ref]$tokensB,[ref]$errorsB)
if ($errorsA.Count -or $errorsB.Count) { throw 'PowerShell parse failure' }
$a=@($tokensA | Where-Object Kind -ne Comment | ForEach-Object {[string]$_.Kind+':'+$_.Text})
$b=@($tokensB | Where-Object Kind -ne Comment | ForEach-Object {[string]$_.Kind+':'+$_.Text})
if (($a -join [char]0) -cne ($b -join [char]0)) { throw 'PowerShell noncomment token mismatch' }
if (@($tokensB | Where-Object Kind -eq Comment).Count) { throw 'PowerShell comments remain' }
[ordered]@{parser='System.Management.Automation.Language.Parser';comment_count=0;noncomment_token_equivalent=$true;syntax='PASS'} | ConvertTo-Json -Compress
