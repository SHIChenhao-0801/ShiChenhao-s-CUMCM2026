# DOCX 内嵌源码逐行复原核查

状态：PASS_SOURCE_LINES。共 42 份源码、9434 行。

DOCX SHA256：`3c0edfdf5946019ac8129afee637880954c86561a6440adc6dc0553483185013`。

逐段重建 OOXML 中带指定 rsidR 的代码文字，与两份 manifest 顺序、源码原始 SHA256、文件标题及所印 SHA256 核对；空白行、缩进、TAB 均逐行比较。只规范化文本编码 BOM 与物理换行约定，未删除任何代码行。Word 段落本身不保存源文件 BOM 和 CRLF/LF 字节约定，因此此 PASS 是全文逐行一致，不宣称单靠 DOCX 可恢复原始文件字节格式。

| 次序 | 文件 | 行数 | 源码哈希 | 逐行内容 |
|---:|---|---:|---|---|
| 1 | run_modeling.py | 448 | 匹配 | 全部一致 |
| 2 | q1_model.py | 8 | 匹配 | 全部一致 |
| 3 | q2_model.py | 8 | 匹配 | 全部一致 |
| 4 | q3_model.py | 27 | 匹配 | 全部一致 |
| 5 | q4_model.py | 8 | 匹配 | 全部一致 |
| 6 | drying_core.py | 402 | 匹配 | 全部一致 |
| 7 | analytic_jacobian.py | 325 | 匹配 | 全部一致 |
| 8 | disk_dense.py | 121 | 匹配 | 全部一致 |
| 9 | export_outputs.py | 748 | 匹配 | 全部一致 |
| 10 | publication_plots.py | 402 | 匹配 | 全部一致 |
| 11 | production_provenance.py | 497 | 匹配 | 全部一致 |
| 12 | validate_bessel.py | 345 | 匹配 | 全部一致 |
| 13 | compare_analytic.py | 242 | 匹配 | 全部一致 |
| 14 | verify_convergence.py | 127 | 匹配 | 全部一致 |
| 15 | verify_time_accuracy.py | 251 | 匹配 | 全部一致 |
| 16 | verify_dense_storage.py | 69 | 匹配 | 全部一致 |
| 17 | run_experiments.py | 74 | 匹配 | 全部一致 |
| 18 | crossvalidate_solver.py | 206 | 匹配 | 全部一致 |
| 19 | method_comparison.py | 197 | 匹配 | 全部一致 |
| 20 | threshold_and_scaling_checks.py | 175 | 匹配 | 全部一致 |
| 21 | energy_balance_check.py | 245 | 匹配 | 全部一致 |
| 22 | sensitivity_analysis.py | 292 | 匹配 | 全部一致 |
| 23 | isotherm_activity_closure.py | 494 | 匹配 | 全部一致 |
| 24 | verify_convergence_v1.py | 106 | 匹配 | 全部一致 |
| 25 | verify_convergence_v5.py | 123 | 匹配 | 全部一致 |
| 26 | drying_core_v2_kirchhoff.py | 326 | 匹配 | 全部一致 |
| 27 | drying_core_v3_analytic_jacobian.py | 338 | 匹配 | 全部一致 |
| 28 | drying_core_v5_disk_dense.py | 395 | 匹配 | 全部一致 |
| 29 | disk_dense_v5.py | 99 | 匹配 | 全部一致 |
| 30 | run_experiments_v1.py | 73 | 匹配 | 全部一致 |
| 31 | drying_core_v1_harmonic.py | 296 | 匹配 | 全部一致 |
| 32 | runCrossCheck.m | 495 | 匹配 | 全部一致 |
| 33 | compareMatlab.mjs | 200 | 匹配 | 全部一致 |
| 34 | runLogged.ps1 | 50 | 匹配 | 全部一致 |
| 35 | runDelivery.py | 281 | 匹配 | 全部一致 |
| 36 | dryingCore.py | 420 | 匹配 | 全部一致 |
| 37 | analyticJacobian.py | 333 | 匹配 | 全部一致 |
| 38 | diskDense.py | 128 | 匹配 | 全部一致 |
| 39 | q1Model.py | 10 | 匹配 | 全部一致 |
| 40 | q2Model.py | 10 | 匹配 | 全部一致 |
| 41 | q3Model.py | 30 | 匹配 | 全部一致 |
| 42 | q4Model.py | 10 | 匹配 | 全部一致 |

本次未运行 PDE、未编辑 DOCX 或源码；本报告不替代逐页视觉检查和团队人工审查。
