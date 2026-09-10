# A题 Q1–Q4 代码审查入口

这是基于最终有效模型与 `final_v6a` 冻结生产结果整理的独立代码版本。Python 负责正式全量数据，MATLAB 负责同空间离散的独立数值交叉核验。公式、物性、初边值及生产网格不因代码整理而更换。新增变量与自有函数使用驼峰命名；数学单字母、常量、第三方库接口、SciPy重载方法和既有结果文件字段保留各自约定。

先阅读 [公式与算法说明](docs/公式与算法说明.md)，再按 [人工审查清单](docs/人工审查清单.md) 打开代码。实际执行与GUI记录以 [本轮交付记录](../../results/code_delivery/交付与运行记录.md) 为入口。用户人工审查没有由代理代签。

## 文件和阅读顺序

| 文件 | 用途 |
|---|---|
| `runDelivery.py` | 一次运行三条轨迹，覆盖四题；保留运行记录并核验新结果 |
| `q1Model.py` | Q1附录2、0–1800秒、正式N3200参数 |
| `q2Model.py` | Q2/Q3附录3从t=0开始，正式N3200参数 |
| `q3Model.py` | 从Q23全域最大水分求严格达标的报告时间 |
| `q4Model.py` | 附录4、同比径向材料收缩、正式N6400参数 |
| `dryingCore.py` | 输入、物性、径向控制体、热/水通量、BDF求解、查询与守恒检查 |
| `analyticJacobian.py` | 按同一通量推导的解析稀疏Jacobian |
| `diskDense.py` | 原精度BDF密集多项式磁盘缓存和断点选段 |
| `exportOutputs.py` | 4个题目工作簿、原精度CSV、正文CSV及完整回读核验 |
| `runLogged.ps1` | 命令行监督器，记录真实进程退出码、耗时和观察到的内存占用 |
| `matlab/runCrossCheck.m` | MATLAB独立有限体积+ode15s交叉实现，N40核验用途 |
| `tools/coreRenameReport.json` | 旧/新标识符映射、源码哈希与反向归一化AST一致性证据；不替代实际路径和导出检查 |
| `runtime/exportPathFix_v2/verification.json` | Q3来源路径修复后的N40 Q3/Q4实际求解、完整导出/回读及来源哈希核验 |

## Visual Studio 中运行

在 **Visual Studio Community 2026** 打开同目录 `A_CodeReview.sln`。工程已选择 `C:\Python314\python.exe`，工作目录为 `D:\Document\数学建模\2026CUMCM`，启动文件为 `runDelivery.py`，解释器参数 `-B`。检查工程“调试”属性的脚本参数后启动；“逐语句”的快捷键以当前VS菜单显示为准。

正式参数为 `--profile final`；可加 `--run-id 自定义编号`。省略编号时自动生成UTC时间戳。相同编号的目录存在时拒绝覆盖，请使用新编号。

第一次人工阅读可以设置断点于 `runQuestion` 调用逐问 `solve` 的位置，再进入 `dryingCore.RadialModel.rhs`，观察温度、水分、物性、面通量和时间导数。不要在每一次RHS调用都停留；正式一条轨迹有上万次计算。全部参数和输入文件SHA256自动写入输出目录 `launch.json`。

## 命令行复现

在 PowerShell 中，先切换到本届比赛根目录。以下第一条是正式全量，第二条是N40等价性试验；两种用途必须区分。

```powershell
Set-Location -LiteralPath 'D:\Document\数学建模\2026CUMCM'
.\paper_output\code\review_delivery\runLogged.ps1 -Profile final
.\paper_output\code\review_delivery\runLogged.ps1 -Profile audit
```

也可以直接运行 `python -B paper_output/code/review_delivery/runDelivery.py --profile final`；模型日志仍会生成，但真实外部进程退出码需要调用方记录。`runResult.json` 内的 `actualProcessExitCode=null` 是有意保留的：模型运行到最后并不能自己证明它已退出。监督器输出位于 `driver_<runId>/processResult.json`。

实际使用环境为 Python 3.14.7、NumPy 2.5.2、SciPy 1.18.1、openpyxl 3.1.5，见本次 `launch.json`。`requirements.txt` 固定了直接依赖；磁盘BDF适配调用SciPy内部接口，更换SciPy版本后必须重新核验密集输出和断点选段。源码无需改动系统环境；线程与缓存路径设置只影响当前进程。

## 输出内容

结果写入比赛根目录的 `paper_output/results/code_delivery/<runId>/`。下表的四工作簿、原精度CSV和正文CSV属于 `final` 全量模式；`audit` 只产生N40轨迹、诊断、旧版对照和运行记录，不执行四题导出。某版本存在部分文件不等于整次运行成功，应同时核对其 `runResult.json` 与监督退出记录。

| 输出 | 数据含义 |
|---|---|
| `outputs/result1.xlsx` | Q1逐秒、0–2cm每0.1cm，温度和水分两个表 |
| `outputs/result2.xlsx` | Q2完整逐秒温度/水分场，至干燥后的核验秒 |
| `outputs/result3.xlsx` | Q3每60秒水分场并补事件、核验终点 |
| `outputs/result4.xlsx` | Q4每60秒水分场、真实移动表面水分及半径表；域外留空 |
| `outputs/result*_unrounded.csv.gz` | 17位有效数字的原精度值；不是由每60秒NPZ补插逐秒数据 |
| `outputs/q*_paper_*.csv` | 7份题目指定的正文采样表 |
| `Q1/Q23/Q4/sampled_solution.npz` | 密集轨迹的材料坐标采样，便于回归检验和再次画图 |
| `Q1/Q23/Q4/summary.json` | 实际设置、事件、守恒、物性范围、采样和源码哈希 |
| `Q1/Q23/Q4/comparison.json` | 与冻结结果的NPZ、事件、原精度CSV和正文CSV比较 |
| `stdout.log`、`launch.json`、`runResult.json` | 开始结束、运行步骤、异常/警告、参数、版本和实际完成状态 |
| `artifactManifest.json` | 成功或失败收尾时生成的现有文件大小与SHA256清单；保留相应状态 |

正式计算按Q1→Q23→Q4串行执行，完成一个轨迹的导出和校验后关闭其私有缓存。Q4历史生产单条轨迹密集多项式曾约8.33GB，运行时需要足够可重建临时磁盘空间。内存并非严格O(N)：`solve_ivp`仍暂存当前分段接受状态，说明文档给出准确复杂度。不要同时启动多个正式大网格复现。

Q1水分未降到0.15不是失败，Q1只计算预热半小时；Q3/Q4必须检查未四舍五入的 `max_C_at_reported_time < 0.15`，显示值0.1500不能单独证明严格达标。四位小数是题目储存/展示口径，不保证所有末位对容差设置都稳定。

## 证据边界

本轮保留了真实失败历史：`camel_final_v1` 在Q3正文表复核记录来源文件时，仍查找旧名 `q3_model.py`，触发 `FileNotFoundError`，监督器实际退出码为1。修复将该来源路径改为 `q3Model.py`，没有更改热水方程、物性、网格或原冻结结果。此前N40 audit不执行导出，初次AI静态审查也未发现这条字符串路径错误，因此不能把那些通过记录扩张为首版全部调用路径已通过。

修复后 [N40定向验证](runtime/exportPathFix_v2/verification.json) 已实际完成Q3/Q4完整工作簿/原精度回读、全部正文表与来源记录核验，且有[外部退出0证据](runtime/exportPathFix_v2/process-exit.json)。它只验证该修复覆盖范围，不代替 `camel_final_v2` 全量复现、GUI完整运行或人工审查。版本失败、修复及最终状态在[独立代码审查](docs/独立代码审查.md)与总日志分别保留；不能因GUI停在断点或已有 `launch.json` 就填“GUI已完成”。

N40试验检查代码重命名前后的等价性，不能替代正式空间网格检验。全量复现检查本轮输出与冻结结果的一致性，也不能弥补缺少内部实测温度/含水率、气固平衡映射和潜热联合闭合的物理信息。原模型限定、历史网格/时间验证和最新解释勘误见比赛根目录 `notes/A-modeling/2026-09-10/A题_成果与重新核验报告.md`。

本轮不新增经验预测精度或真实干燥时间置信区间。MATLAB的独立误差属于跨实现数值核验；最终是否接受模型和代码仍由你及团队审查。
