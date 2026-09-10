[CmdletBinding()]
param(
    [string]$Message = ('backup: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')),
    [switch]$Preview
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$expectedRemote = 'https://github.com/SHIChenhao-0801/ShiChenhao-s-CUMCM2026.git'

function Invoke-GitChecked {
    param([string[]]$GitArgs)
    & git @GitArgs
    if ($LASTEXITCODE -ne 0) {
        throw ('Git failed: git ' + ($GitArgs -join ' '))
    }
}

$originalConsoleEncoding = [Console]::OutputEncoding
Push-Location -LiteralPath $repoRoot
try {
    # Decode Git's UTF-8 paths consistently, including in Windows PowerShell 5.1.
    [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
    $actualRoot = (Invoke-GitChecked -GitArgs @('rev-parse', '--show-toplevel')).Trim()
    if ([IO.Path]::GetFullPath($actualRoot) -ne [IO.Path]::GetFullPath($repoRoot)) {
        throw 'Run this script only from its own contest repository.'
    }
    $remote = (Invoke-GitChecked -GitArgs @('remote', 'get-url', '--push', 'origin')).Trim()
    if ($remote -ne $expectedRemote) { throw 'Unexpected origin URL. Review the remote before syncing.' }
    $branch = (Invoke-GitChecked -GitArgs @('branch', '--show-current')).Trim()
    if ($branch -ne 'main') { throw 'This helper expects branch main. Review the current branch first.' }

    if ($Preview) {
        Invoke-GitChecked -GitArgs @('status', '--short', '--branch')
        Write-Host 'Preview only: no files staged, no commit created, no network push.'
        return
    }

    Invoke-GitChecked -GitArgs @('fetch', 'origin')
    $behind = [int](Invoke-GitChecked -GitArgs @('rev-list', '--count', 'HEAD..origin/main'))
    if ($behind -gt 0) {
        throw 'GitHub has commits missing locally. Preserve local edits and review/integrate those commits before retrying. No commit or push was made.'
    }

    # Check candidate sizes before staging. Large project artifacts need an explicit LFS decision.
    $candidateOutput = Invoke-GitChecked -GitArgs @('ls-files', '--cached', '--others', '--exclude-standard', '-z')
    $candidatePaths = (($candidateOutput -join "`n") -split "`0") | Where-Object { $_ }
    foreach ($relativePath in $candidatePaths) {
        $candidate = Join-Path -Path $repoRoot -ChildPath $relativePath
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            $candidateInfo = Get-Item -LiteralPath $candidate
            if ($candidateInfo.Length -ge 100MB) {
                throw ('File is at least 100 MiB; configure Git LFS or document an external backup before syncing: ' + $relativePath)
            }
        }
    }

    Invoke-GitChecked -GitArgs @('add', '--all')
    & git diff --cached --quiet
    $diffStatus = $LASTEXITCODE
    if ($diffStatus -eq 1) {
        Invoke-GitChecked -GitArgs @('diff', '--cached', '--stat')
        Invoke-GitChecked -GitArgs @('commit', '-m', $Message)
    } elseif ($diffStatus -ne 0) {
        throw 'Could not inspect staged changes.'
    } else {
        Write-Host 'No new file changes to commit.'
    }

    Invoke-GitChecked -GitArgs @('push', '-u', 'origin', 'main')
    $localHead = (Invoke-GitChecked -GitArgs @('rev-parse', 'HEAD')).Trim()
    $remoteLine = Invoke-GitChecked -GitArgs @('ls-remote', '--exit-code', 'origin', 'refs/heads/main')
    $remoteHead = ($remoteLine -split '\s+')[0]
    if ($localHead -ne $remoteHead) { throw 'Remote main does not match local HEAD. Recheck before reporting a successful backup.' }
    $remainingChanges = Invoke-GitChecked -GitArgs @('status', '--porcelain')
    Write-Host ('Verified GitHub commit: ' + $localHead)
    if ($remainingChanges) {
        Write-Warning 'Files changed during sync and are not in this snapshot. Run the helper again when those files are ready.'
        $remainingChanges
    } else {
        Write-Host 'Working tree is clean; all non-ignored files match the uploaded snapshot.'
    }
} finally {
    [Console]::OutputEncoding = $originalConsoleEncoding
    Pop-Location
}
