# Convert a DOCX to PDF using Microsoft Word COM automation (authoritative OMML rendering).
# Non-destructive: renders to <OutDir>, never touches other directories.
# Usage: powershell -File tools/docx2pdf-word.ps1 -Src <docx> [-OutDir <dir>] [-Log <file>]
param(
  [Parameter(Mandatory=$true)][string]$Src,
  [string]$OutDir = '',
  [string]$Log = ''
)
$ErrorActionPreference = 'Continue'
function Say($m) {
  $line = (Get-Date -Format 'HH:mm:ss') + ' ' + $m
  Write-Output $line
  if ($Log) { Add-Content -Path $Log -Value $line -Encoding UTF8 }
}
$Src = (Resolve-Path $Src).Path
if (-not $OutDir) { $OutDir = Join-Path (Split-Path $Src -Parent) 'pdf-preview' }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$pdf = Join-Path $OutDir ([IO.Path]::GetFileNameWithoutExtension($Src) + '.pdf')

Say "creating Word COM"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.AutomationSecurity = 3
Say ("word version " + $word.Version)
$doc = $null
try {
  Say "opening $Src"
  $doc = $word.Documents.Open($Src, $false, $true, $false)
  $doc.Repaginate()
  Say ("opened; pages=" + $doc.ComputeStatistics(2) + " words=" + $doc.ComputeStatistics(0))
  Say "exporting to $pdf"
  $doc.ExportAsFixedFormat($pdf, 17)
  Say ("exported bytes=" + (Get-Item $pdf).Length)
} catch {
  Say ("ERROR: " + $_.Exception.Message)
} finally {
  if ($doc) { try { $doc.Close($false) } catch {} }
  try { $word.Quit() } catch {}
}
if (Test-Path $pdf) { Say "DONE" } else { Say 'PDF NOT CREATED' }
