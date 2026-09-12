# 可提交代码源码与设备迁移独立审查

审查日期：2026-09-12（北京时间）。对象是实际 `paper_output/submission/支撑材料/A题_支撑材料.zip`，不是仅看本机源码目录。该包审查时 SHA256 为 `6460f3299e012c2728385b1f78212386ba98b30a1acad926b9c446cc890c5b91`，178 个条目。本文是原包快照的审查，后续修复候选须另行验证。

**结论：此版本代码有完整的核心数值实现和本机运行历史，但当前提交包不能按所附说明在另一台设备独立运行。阻断主要发生在打包路径、必需输入与历史回归依赖；不能以既有本机 CLI/GUI 成功、ZIP CRC、文件清单齐全替代迁移验收。** 本审查没有重跑正式 PDE，没有修改源码、冻结结果或提交包，没有操作 Git，没有代替用户人工签核。

## 实际检查范围

- 直接读取 ZIP 内 55 个 Python 文件，全部通过当前 Python 3.14 的 AST 语法解析；这是静态语法检查，不是所有脚本执行通过。
- 根级 9 个 Python 文件、PowerShell 监督器、MATLAB 实现与 `paper_output/code/review_delivery/` 当前副本逐字节相同，故本报告对应源码行号适用于包内同名文件。
- 实际包已经追加原实现：`code/modeling/` 19 个 Python 文件，以及 `code/data/`、`code/verification/`；不能照打包器默认选项误说原实现未打包。
- 对冻结账本 107 个唯一文件，包内原路径匹配 0 个；即使按内容 SHA256 重映射，只有 59 个内容已包含，48 个内容仍缺失。缺失清单见 `source_review.json`。
- 监督器只做语法解析，没有启动模型。PowerShell 7.6.5 解析错误 0；Windows PowerShell 5.1.26100.9444 解析错误 1（第 9 行附近），且该版 .NET Process 不具有 `Kill(bool)` 重载。

## 确定的迁移阻断

| 严重性 | 事实与代码位置 | 实际影响 | 最小修复方向 |
|---|---|---|---|
| P1 | `runDelivery.py:29,230`、`dryingCore.py:27,36`、`exportOutputs.py:40,43` 仍按源码上三级确定比赛根目录并读取原层级；ZIP 却把源码放 `code/`、输入放 `figures/` | 解压目录不是推定根目录；主入口先拒绝 cwd，绕过后仍找不到所需数据；导入入口还会向推定根目录创建临时目录 | 给提交包独立的根目录定义和统一路径配置；按这一配置打包数据/模板，不依赖原比赛目录层级 |
| P1 | `runDelivery.py:108–121,253` 两种 profile 都无条件核验完整 `final_v6a` 账本；`159–178` 还读取冻结 NPZ、事件、原精度 CSV.GZ、正文 CSV | 只重排目录不能解决；48 个账本文件内容不存在，四个原精度 GZ 合计约 44.64 MB，本身不能全部塞入目前限制的提交包 | 独立提交运行负责真实求解、导出与回读；本地历史逐字节回归作为明确独立的可选模式。提供包内可验证的轻量基准，不伪造历史全量回归 PASS |
| P1 | `exportOutputs.py:104–113,436` 实际读取原 `result1–4.xlsx` 模板；ZIP 内没有模板，根目录四个 XLSX 是最终结果 | 求解后导出仍失败；不能把最终结果默认为原模板 | 纳入四份原始小模板，记录原始哈希并令导出器读取包内模板目录 |
| P1 | `runDelivery.py:199` 的 `audit` 读取 `paper_output/code/modeling`；原实现虽在 ZIP 中，却位于 `code/modeling` | N40 audit 旧版对照不能正常加载 | 统一本包与审查副本的原实现路径，或者使用仅依赖提交包的有限网格烟测入口；不要把 audit 当全量导出测试 |
| P1 | `code/verification/` 全部 14 个脚本都将 ROOT 硬编码为 `D:\Document\数学建模\2026CUMCM`；例如 `crossvalidate_solver.py:28`、`sensitivity_analysis.py:45`；`code/modeling/validate_bessel.py:291` 强制同一绝对 cwd | 换盘符/用户名/目录或非 Windows 即失败；在原机测试副本时更可能意外读取原项目，形成假的独立运行 | 统一解析包根目录，明确每个实验所需输入、依赖及输出；隔离验收要拦截原工作区读取 |
| P1 | `code/modeling/publication_plots.py:25,32–34` 依赖 matplotlib，导入时硬性要求 `C:/Windows/Fonts/msyh.ttc`；`requirements.txt` 只有 numpy/scipy/openpyxl | 按说明安装三依赖不足以运行已提交绘图/数据脚本；其他系统通常无该字体路径 | 补充绘图依赖声明，支持指定字体或发现可用中文字体；把核心求解、可选绘图、历史审计依赖分别说明 |
| P2 | `runLogged.ps1:4,7–8` 默认 `C:\Python314\python.exe` 并取父三级；原文件 UTF-8 无 BOM 在 PS5.1 实际解析失败；`:30` 使用 PS5.1 不支持的 `Kill($true)` | 默认 Windows PowerShell 不能执行文档中的监督入口，换 Python 安装路径也失败 | Python 主入口应可直接使用；监督器明确 PS7 要求或兼容 PS5.1，默认发现当前 Python 并保留显式覆盖 |
| P2 | `matlab/runCrossCheck.m:9–11,64–67` 按固定父四层取根并读原 `paper_output/data_cleaned`；当前 ZIP 层级是 `code/matlab` | MATLAB 脚本同样不是解压可运行；仅改变示例绝对路径不够 | 让 MATLAB 读取统一的包内数据目录；保留 JVM 要求及 N40 独立核验用途 |
| P2 | `code/README.md` 要求打开同目录 `A_CodeReview.sln`，ZIP 实际没有 `.sln/.pyproj`；本机工程又硬编码 WorkingDirectory、Python、MSBuild targets 安装位置 | 随包 GUI 说明不可执行，不能移植原工程后直接声称 VS 可用 | 给提交包新的可迁移工程或准确的 VS 创建/选择解释器说明，另在目标环境完成 GUI 复现 |

## 复现标准和剩余工程问题

`diskDense.py:14–15,101–116,120–130` 使用 SciPy `_ivp` 私有接口及 BDF 内部多项式字段。固定 `scipy==1.18.1` 是必要的版本说明，但不能自动证明不同操作系统/CPU/BLAS、不同 Python 小版本都兼容。本机实际版本是 Python 3.14.7、NumPy 2.5.2、SciPy 1.18.1、openpyxl 3.1.5；其他组合没有从源码审查获得实测保证。异常清理使用 `BaseException.add_note`，通用版本说明至少应考虑 Python 3.11 的此 API；依赖本身可能要求更高版本，最终以实际安装及测试矩阵为准。

`runDelivery.py:85,162,164,177` 要求数组、浮点事件、整份 completion 字典、原精度 CSV 逐值/逐字节完全一致。这适合原环境代码重构回归。另一台机器发生浮点末位差异时，程序可能得到足够精确且约束合格的数值结果仍被判失败；这属于复现验收定义过窄，不能直接推定不同设备算错。跨设备验收需要预先明确字段、单位、采样和数值容差，并独立重查严格阈值；四位小数正好处于舍入边界的格子也不能随意以宽容差隐去。保留原字节比较作为更强的附加指标。

`runDelivery.py:236–244` 通过 glob 收集数据/模板，缺失目录会得到空列表，并未立即报告输入数量错误；依赖版本查询和 launch 信息建立在主要异常留痕 try 之前。建议提交入口先验证 Python/库版本、两份 CSV 字段/时间/有限值、四份模板、输出写权限和可用磁盘，再计算，失败时产生明确的可诊断报告。核心 `dryingCore.loadInputs` 本身只读入和哈希，MATLAB 有更完整输入验证；独立入口不应完全依赖原项目上游审计状态。

`exportOutputs.py:735–750` 的独立 `--selfcheck` 分支没有用 finally 关闭 Run 缓存；主要 `runDelivery.runQuestion` 已有 finally 释放。若把这个分支作为提交包推荐测试入口，应补齐缓存清理。三个 `code/tools/` 脚本是内部重命名/修复历史工具，额外依赖没打包的 `tools/exportPathFixBefore/` 和旧失败运行记录（`verifyExportPathFix.py:32,40,66–67`）；应注明“历史维护工具，非迁移复现入口”，或补齐所需资产。

全包静态 import 清单还发现 `evidence/recheck_20260910_1828/data_scale_recheck_helper.py:14`、`physics_small_checks.py:8` 依赖 PyMuPDF。该依赖只影响所附历史审计源码，不属于四问核心求解的最小依赖。随包 README 应明确哪些文件是可重复执行入口、哪些仅为历史证据，不能笼统宣称 55 个脚本装三项依赖后均能运行。

已有 README 记录 Q4 密集多项式缓存约 8.33 GB，串行求解后释放。现有程序没有磁盘容量预检，通用的“另一台设备”必须说明 64 位 Python、足够 RAM 与临时磁盘空间；32 GB 是本机环境而非已证明的最低内存要求。此处不推定 GPU、MATLAB 或 Visual Studio 是纯 Python CLI 求解的必需软件。

## 可保留的既有证据及结论边界

核心有完整的 Q1/Q23/Q4 参数入口、共享 Q2/Q3 轨迹、连续阈值与严格达标检查、解析稀疏 Jacobian、磁盘密集输出、四工作簿及原精度/正文表回读、源输入哈希、异常重抛与主要缓存清理。当前缺陷不能据此改写为“数学算法不存在”。原 `camel_final_v2` 与 `gui_camel_final_v2` 的实际全量通过、MATLAB N40 对照是原项目环境的既有证据；本报告没有重新核实其中每一个数值，也没有把它们算作迁移运行。

主代理独立沙箱实跑、后续修复和当前新哈希验收另行记录。只有在从提交包本身解压、安装声明依赖、禁止读取原项目的条件下，完成预检、有限网格三轨迹和四题真实导出/回读，才能证明包的基本独立性；完整正式网格还应实际通过并记录。没有实际第二台机器/第二系统测试时，最终措辞应是“同机隔离环境迁移测试通过”，不能宣称所有设备或 Linux/macOS 均已验证。Visual Studio GUI 当前源码复现和用户人工审查也继续单独记账。
