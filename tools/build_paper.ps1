# Build the A-problem paper: markdown -> DOCX (OMML) -> PDF (LibreOffice) and report the page count.
# Usage: powershell -File tools/build_paper.ps1 [-Stem <name>] [-NoPdf]
param(
  [string]$Stem = 'A题_论文_定稿',
  [switch]$NoPdf
)
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONPYCACHEPREFIX = Join-Path $root 'tmp\cache\python'

$md    = Join-Path $root 'paper_output\drafts\A题正文\A题_论文正文_30p.md'
$docx  = Join-Path $root ('paper_output\paper\' + $Stem + '.docx')
$outdir= Join-Path $root 'tmp\cache\paperpdf'
New-Item -ItemType Directory -Force -Path $outdir | Out-Null

Write-Output '== build docx =='
& python -B (Join-Path $root 'paper_output\paper\build_docx.py') $md $docx
if (-not (Test-Path $docx)) { Write-Output 'DOCX FAILED'; exit 1 }
Write-Output ('docx bytes=' + (Get-Item $docx).Length)
if ($NoPdf) { exit 0 }

Write-Output '== render pdf =='
$soffice = 'D:\Document\数学建模\tools\libreoffice\app\program\soffice.com'
& $soffice --headless --norestore ('-env:UserInstallation=file:///' + ($root -replace '\\','/') + '/tmp/cache/lo30') --convert-to pdf --outdir $outdir $docx | Out-Null
$pdf = Join-Path $outdir ($Stem + '.pdf')
if (-not (Test-Path $pdf)) { Write-Output 'PDF FAILED'; exit 1 }
Write-Output ('pdf bytes=' + (Get-Item $pdf).Length)
& python -B (Join-Path $root 'tools\page_stats.py') $pdf
