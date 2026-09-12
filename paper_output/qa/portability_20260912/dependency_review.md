# 提交包依赖可重建性独立审查（2026-09-12）

结论：**核心 Python 的已声明依赖可以从官方 PyPI 在新建、隔离的 Windows 虚拟环境重建；整份提交包的依赖声明仍不完整，不能据此宣称全部代码已可在另一台设备独立运行。** 本项没有执行 PDE，也没有把同机新虚拟环境称为真实异机或跨平台验收。

## 实际执行与证据

- 源码依赖入口：`paper_output/code/review_delivery/requirements.txt`，固定 `numpy==2.5.2`、`scipy==1.18.1`、`openpyxl==3.1.5`。
- 本次新环境：`tmp/cache/portability_20260912/dependency_probe/venv`；解释器为其中的 `Scripts/python.exe`。
- `pyvenv.cfg` 实际显示 `include-system-site-packages = false`。解释器是本机 CPython 3.14.7，Windows AMD64；虚拟环境仍共用本机基础 Python，不等于携带独立 Python 运行时。
- 清除了子进程的 `PIP_*`、`PYTHONPATH`、`PYTHONHOME` 与 `VIRTUAL_ENV`，设置 `PIP_CONFIG_FILE=nul`、`PYTHONNOUSERSITE=1`；使用 `pip --isolated --no-cache-dir --index-url https://pypi.org/simple --only-binary=:all:`，未读取本地 site-packages 作为依赖来源，也未使用本地缓存轮子。
- 新环境创建退出 0；官方安装退出 0，耗时 92.43 秒；`pip check` 退出 0，报告无依赖破损。
- 三个直接依赖均实际导入，`__file__` 全部位于新虚拟环境内。SciPy 内部 `BDF`、`BdfDenseOutput`、`DenseOutput` 均实际导入成功。接口可导入不等于磁盘密集输出算法已在此环境重新数值核验。
- 安装清单：NumPy 2.5.2、SciPy 1.18.1、openpyxl 3.1.5、传递依赖 et_xmlfile 2.0.0；安装工具 pip 26.2.1。前三项与冻结生产声明相同。`et_xmlfile` 由 openpyxl 自动解析，目前没有在提交依赖文件固定版本。
- pip 下载来源实际为 `files.pythonhosted.org` 官方分发地址；机器报告保留精确 wheel URL、SHA256、安装元数据。NumPy/SciPy 的已安装 wheel 为 `cp314-cp314-win_amd64`，元数据要求 Python >=3.12；其他 Python 版本/操作系统的可用轮子与执行效果没有在本项检验。

完整命令实现及可复核证据：

| 文件 | 内容 |
|---|---|
| `run_dependency_probe.py` | 本轮探测源码；拒绝重用已存在的虚拟环境作为“全新”环境 |
| `dependency_review.json` | 时间、源码/ZIP哈希、环境、每步退出码、导入结果及ZIP静态依赖清单 |
| `dependency_venv_create.log` | venv 创建实际日志（成功时无标准输出） |
| `dependency_pypi_install.log` | 真实下载、安装和版本日志 |
| `dependency_pip_report.json` | 下载 URL、轮子 SHA256、包元数据与运行平台 |
| `dependency_pip_check.log` | 已安装依赖一致性检查 |
| `dependency_pip_freeze.log` | 已安装精确版本 |
| `dependency_import_probe.log` | 真实解释器、库路径、版本、SciPy内部接口导入结果 |

## ZIP 中其他代码的依赖缺口

对当前 `paper_output/submission/支撑材料/A题_支撑材料.zip` 内全部 **55 个 `.py` 文件**进行了 AST 解析，未发现语法错误。按标准库与包内模块过滤，发现外部模块 `numpy`、`scipy`、`openpyxl`、`matplotlib`、`pymupdf`；这里只是静态依赖扫描，不是运行全覆盖，字符串动态导入和外部文件还需结合主审查结果。

| ZIP 内代码 | 未在唯一 requirements.txt 声明的依赖 | 影响 |
|---|---|---|
| `code/data/prepare_a_data.py` | matplotlib | 重做输入整理/绘图时需要 |
| `code/modeling/publication_plots.py` | matplotlib | 重绘正式图件时需要 |
| `code/modeling/compare_analytic.py` | matplotlib | 解析比较绘图分支需要 |
| `code/verification/crossvalidate_series.py` | matplotlib | 验证图件生成时需要 |
| `code/verification/latent_heat_scenarios.py` | matplotlib | 潜热情景绘图时需要 |
| `evidence/recheck_20260910_1828/data_scale_recheck_helper.py` | pymupdf | 历史PDF数据复核需要 |
| `evidence/recheck_20260910_1828/physics_small_checks.py` | pymupdf | 历史题面/PDF复核需要 |

本次仅按原 requirements 安装的干净环境中，`importlib.util.find_spec` 已实际确认 `matplotlib`、`pymupdf` 均不存在。没有为了让审计看起来通过而额外安装后声称原依赖清单齐全。

此外，`code/modeling/publication_plots.py:32–34` 固定字体路径 `C:/Windows/Fonts/msyh.ttc`，不存在立即抛出 `RuntimeError`。这会阻止没有该字体/路径的设备重绘图件，须提供可配置字体或确定性后备方案。`prepare_a_data.py` 的同类字体选择有存在性分支，风险不同，不能一并视为强制失败。

`code/verification/crossvalidate_series.py:39`、`code/verification/latent_heat_scenarios.py:36` 等还保留原机器项目根目录；这是额外的文件布局问题，不会因为 pip 安装成功自动解决。主审查负责端到端打包、输入闭包和路径验证。

## 判定边界与后续验收

1. 本项可以证明：在本机 Windows AMD64 / Python 3.14.7 下，核心声明的依赖能从官方来源重建并导入，且没有借用现有全局科学计算包。
2. 本项尚不能证明：当前 ZIP 解压即可运行、全部文件路径闭合、所有模型与导出在新环境成功、Linux/macOS 支持、离线设备可安装，以及 VS GUI 或用户人工审查已经完成。
3. 若交付范围包括绘图及历史复核脚本，应补相应依赖说明及可移植入口；若它们仅作历史证据，应在提交说明中明确用途，避免把它们宣称为已经验证的独立运行入口。
4. 对核心交付，下一步应使用这里的新解释器从实际候选提交包的解压目录进行隔离启动、小网格完整导出，再按资源预算执行正式网格复现。模型核心发生改变需重做相应数值与 GUI 证据；本轮依赖检查没有改变模型或冻结结果。
