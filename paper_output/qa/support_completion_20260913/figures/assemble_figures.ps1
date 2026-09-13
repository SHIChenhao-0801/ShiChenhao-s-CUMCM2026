$ErrorActionPreference = 'Stop'
$projectRoot = 'D:/Document/数学建模/2026CUMCM'
$sourceRoot = Join-Path $projectRoot 'paper_output/figures/review_20260913'
$destRoot = Join-Path $projectRoot '支撑材料/06_绘图程序与数据'
$qaRoot = Join-Path $projectRoot 'paper_output/qa/support_completion_20260913/figures'
$utf8 = New-Object System.Text.UTF8Encoding($false)
New-Item -ItemType Directory -Path $destRoot -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $destRoot 'PNG') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $sourceRoot 'input_data/CSV') -Destination (Join-Path $destRoot 'CSV') -Recurse
$pngNames = @('图1_径向温度与含水率.png','图2_环境观测与平台延拓.png','图3_中心与表面热湿响应.png','图4_全域达标与临界放大.png','图5_收缩半径与域内含水率.png','图6_经验边界阻力情景.png')
foreach ($name in $pngNames) { Copy-Item -LiteralPath (Join-Path $sourceRoot $name) -Destination (Join-Path $destRoot "PNG/$name") }
$raw = [IO.File]::ReadAllText((Join-Path $sourceRoot 'draw_figures.R')) -replace "`r`n", "`n"
$pathOld = @'
root <- normalizePath("paper_output/figures/review_20260913", winslash = "/", mustWork = TRUE)
input <- file.path(root, "input_data", "CSV")
'@
$pathNew = @'
args_all <- commandArgs(trailingOnly = FALSE)
script_arg <- args_all[startsWith(args_all, "--file=")]
if (length(script_arg) != 1L) stop("Run this file with Rscript --vanilla.")
root <- dirname(normalizePath(sub("^--file=", "", script_arg), winslash = "/", mustWork = TRUE))
input <- file.path(root, "CSV")
args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 0L) {
  output <- file.path(root, "PNG")
} else if (length(args) == 2L && args[1] == "--output-dir") {
  output <- args[2]
} else {
  stop("Usage: Rscript --vanilla draw_figures.R [--output-dir DIRECTORY]")
}
dir.create(output, recursive = TRUE, showWarnings = FALSE)
output <- normalizePath(output, winslash = "/", mustWork = TRUE)
'@
if (-not $raw.Contains($pathOld)) { throw 'Original path block not found' }
$adapted = $raw.Replace($pathOld, $pathNew)
$emitOld = @'
emit <- function(name, draw, width = 7.2, height = 4.6) {
  png(file.path(root, paste0(name, ".png")), width = width, height = height, units = "in", res = 300, type = "cairo", bg = "white", family = font_cn, pointsize = 10)
  draw(); dev.off()
  cairo_pdf(file.path(root, paste0(name, ".pdf")), width = width, height = height, family = font_cn, pointsize = 10, bg = "white", onefile = TRUE)
  draw(); dev.off()
  svg(file.path(root, paste0(name, ".svg")), width = width, height = height, family = font_cn, pointsize = 10, bg = "white", onefile = TRUE)
  draw(); dev.off()
  cat("WROTE", name, "PNG 300 dpi / PDF / SVG\n")
}
'@
$emitNew = @'
emit <- function(name, draw, width = 7.2, height = 4.6) {
  png(file.path(output, paste0(name, ".png")), width = width, height = height, units = "in", res = 300, type = "cairo", bg = "white", family = font_cn, pointsize = 10)
  draw(); dev.off()
  cat("WROTE", name, "PNG 300 dpi\n")
}
'@
if (-not $adapted.Contains($emitOld)) { throw 'Original device block not found' }
$adapted = $adapted.Replace($emitOld, $emitNew)
$pdfOld = @'
cairo_pdf(file.path(root,"六图合并核查.pdf"),width=7.2,height=5.9,family=font_cn,pointsize=10,bg="white",onefile=TRUE)
draw1(); draw2(); draw3(); draw4(); draw5(); draw6(); dev.off()
'@
if (-not $adapted.Contains($pdfOld)) { throw 'Original combined PDF block not found' }
$adapted = $adapted.Replace($pdfOld, '')
$adapted = $adapted.Replace('write.csv(bounds,file.path(root,"axis_range_checks.csv"),row.names=FALSE,fileEncoding="UTF-8")','print(bounds, row.names = FALSE)')
$adapted = $adapted.Replace('write.csv(data.frame(metric=', 'print(data.frame(metric=')
$adapted = $adapted.Replace('  file.path(root,"plot_checks.csv"),row.names=FALSE,fileEncoding="UTF-8")', '  row.names=FALSE)')
$adapted = $adapted.Replace('capture.output(sessionInfo(),file=file.path(root,"R_session_info.txt"))', 'print(sessionInfo())')
$adapted = $adapted.Replace('cat("DONE. Plot data remain unchanged. No PDE integration or DOCX modification performed.\n")', 'cat("DONE. Six PNG figures generated from the supplied CSV data.\n")')
[IO.File]::WriteAllText((Join-Path $qaRoot 'adapted_before_comment_removal.R'), $adapted, $utf8)
$noComments = (($adapted -split "`n" | Where-Object { $_ -notmatch '^\s*#' }) -join "`n")
[IO.File]::WriteAllText((Join-Path $destRoot 'draw_figures.R'), $noComments, $utf8)
$manifest = Get-Content -LiteralPath (Join-Path $sourceRoot 'source_manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$tables = foreach ($table in $manifest.tables) {
  $src = Join-Path (Join-Path $sourceRoot 'input_data') $table.csv
  $dst = Join-Path $destRoot $table.csv
  $srcHash = (Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash
  $dstHash = (Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash
  $rows = @(Import-Csv -LiteralPath $dst -Encoding UTF8).Count
  if ($srcHash -ne $dstHash -or $rows -ne $table.data_rows) { throw "CSV mismatch: $($table.csv)" }
  [PSCustomObject]@{ '文件'=$table.csv; '图号'=$table.figure; '数据行数_不含表头'=$rows; '用途'=$table.title; '数据来源追踪'=$table.source; '字段'=$table.columns -join ' | '; '口径说明'=$table.note; 'SHA256'=$dstHash; '与冻结绘图CSV字节一致'='是' }
}
$tables | Export-Csv -LiteralPath (Join-Path $destRoot '数据来源与校验.csv') -NoTypeInformation -Encoding UTF8
if (($tables | Measure-Object -Property '数据行数_不含表头' -Sum).Sum -ne 4627) { throw 'Unexpected total row count' }
$pngHashes = foreach ($name in $pngNames) {
  $srcHash = (Get-FileHash -LiteralPath (Join-Path $sourceRoot $name) -Algorithm SHA256).Hash
  $dstHash = (Get-FileHash -LiteralPath (Join-Path $destRoot "PNG/$name") -Algorithm SHA256).Hash
  if ($srcHash -ne $dstHash) { throw "PNG mismatch: $name" }
  [PSCustomObject]@{ '文件'="PNG/$name"; 'SHA256'=$dstHash; '与已审绘图原件字节一致'='是' }
}
$pngHashes | Export-Csv -LiteralPath (Join-Path $destRoot '图像校验.csv') -NoTypeInformation -Encoding UTF8
$readme = @'
六幅论文图的绘图程序与数据

一、目录
draw_figures.R：论文六图实际 R 绘图源码，使用随目录提供的 14 份 CSV。
CSV/图1～图6/：共 14 份 CSV，数据行共 4627 行（不含表头），与冻结绘图输入逐字节一致。
PNG/：六张论文图，300 dpi；只保留 PNG 格式。
数据来源与校验.csv：逐表字段、单位/科学口径、来源追踪、行数、SHA256。
图像校验.csv：六图 SHA256，与原已检查图像的对应关系。

二、环境和依赖
已实际验证的 R 版本：4.6.1（2026-06-24 ucrt），Windows 11 x64。
仅使用 R 自带 base、graphics、grDevices、utils 等基础功能，无需安装额外 R 包。
PNG 使用 Cairo 图形设备；中文字体为 Microsoft YaHei，数学标签为 Times New Roman。
为获得逐字节相同的图像，需使用相同 R 版本、图形设备、字体及系统字体环境；不同平台可能出现字形差异。

三、运行
在本目录打开 PowerShell，使用已安装 R 的 Rscript：
& 'D:/R-4.6.1/bin/Rscript.exe' --vanilla './draw_figures.R'
如 R 安装位置不同，仅修改上面的 Rscript 可执行文件路径。
可从任意工作目录运行脚本的绝对路径；输入始终相对于脚本自身目录查找，不依赖原工程路径。
默认将六图写入本目录 PNG/，同名图会被重绘覆盖。
也可指定独立输出目录：
& 'D:/R-4.6.1/bin/Rscript.exe' --vanilla './draw_figures.R' --output-dir './复现输出'
参数中的相对输出路径相对于命令的当前工作目录。终端输出数据不变量、11组坐标范围、关键数值与 R sessionInfo；可按需重定向保存运行日志。

四、数据口径
所有曲线直接使用已冻结数据；本脚本只绘图，不重新求解模型。
图1、图3、图4使用 N=3200；图5使用 N=6400；图6的六个情景点统一使用 N=800、零潜热负荷。
图2的0～4h是观测；4h后的50°C/0.05 kg/kg是左端开放的假设平台。
图4严格达标点与临界等号根分别保留；图5各剖面止于相应时刻真实表面；图6不混入高网格生产结果。
数据来源与校验.csv 中“原始数据/…”沿用原冻结来源清单的标签，仅供来源追踪；运行时只读取本目录 CSV/，不要求另建这些来源路径。
CSV/图4/centre_near_event.csv 保留原绘图数据集合中的中心核查样点，程序读取它；实际图4的全域放大曲线使用 maximum_near_event.csv，不能混同两者。

五、本次调整与验收范围
源码只调整脚本/输入/输出路径、只保留 PNG 设备输出、将核查表与环境信息输出到终端，以及删除注释；绘图表达式、视觉参数和数值检查保留。
14份CSV和随附六张PNG均与原冻结文件逐字节一致；在独立拷贝目录、不同当前工作目录下，用上述 R 版本实际重绘六图，退出码为0。
重绘六图与本轮原R源码对照运行的六图逐字节一致；相对9月12日保存的历史PNG存在少量栅格像素差（最大RGB通道差为17/255），并非本次路径、设备输出或去注释调整所致。六图已逐张视觉检查，图中文字、曲线、标记和版式保留。导致历史像素差的具体字体/栅格化环境因素未进一步确定；未将这种差异称为字节完全复现。随附PNG仍为原冻结文件。
此处程序复现与图像检查不代替团队对模型结论和论文图像的人工核实。
'@
[IO.File]::WriteAllText((Join-Path $destRoot '绘图复现说明.txt'), $readme, $utf8)
Write-Output "Assembled: $destRoot"
Write-Output "CSV count: $($tables.Count); data rows: 4627; PNG count: $($pngNames.Count)"
