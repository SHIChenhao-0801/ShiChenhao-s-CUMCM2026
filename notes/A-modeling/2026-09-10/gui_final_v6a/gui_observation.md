# Visual Studio 独立完整复现的实际观察

结论：**核心建模程序已通过 Computer Use 在 Visual Studio 中独立完整求解、导出并观察变量；60 项产物一致性检查通过。** GUI 调试输出窗口未显示该次进程退出码，记为 `null`，不宣称 GUI 退出码已观察为 0。用户/团队人工审查仍待完成。

本记录是主代理对实际 GUI 操作的外部观察；不修改求解程序生成的 `COMPUTED_PENDING_GUI_OBSERVATION` 原始记录，不让程序自证已接受人工或 GUI 检查。

## 环境、参数与源码

- Visual Studio Community 2026，18.10.0；打开项目 `A_Drying.pyproj`，解释器 `C:\Python314\python.exe`，Python 3.14.7。
- 启动参数：`--review --review-exports --version gui_final_v6a --n1 3200 --n23 3200 --n4 6400 --blas-threads 1`；解释器参数 `-B`。
- 根代理于 2026-09-10 16:58:25 UTC 通过 GUI 启动；程序记录开始于 16:58:30.437395 UTC。Q1、Q23、Q4 顺序求解，Q2 与 Q3 共用一条完整 Q23 轨迹；GUI 运行包含人为断点暂停，不用其耗时作性能比较。
- 正式生产版本为 `final_v6a`，本轮 GUI 产物在 `paper_output/results/gui_reproduction/gui_final_v6a/`。独立检查已确认全部 28 项输入/源码哈希与正式生产一致。
- 初次 GUI 尝试因项目采用无效的 `ScriptArguments` 属性而缺少 `--version`，在 argparse 处退出 2，未进入模型求解。修改启动元数据为 PTVS 实际使用的 `CommandLineArguments`，并加入 `InterpreterArguments=-B`，经项目重新加载和属性页可见参数确认后重新启动。该修复只改项目启动元数据，没有修改冻结的模型 Python 源码。原始配置另存为 `../data/A_Drying_before_launch_fix.pyproj.txt`，失败不改写成成功。

## 实际断点、变量与完成证据

| 证据 | 实际观察 |
|---|---|
| `01_launch_settings.png` | 属性页显示完整脚本参数及 `-B` |
| `02_q1_entry_breakpoint.png`、`02_q1_entry_locals.txt` | Q1 入口断点，N=3200，实际参数完整 |
| `03_settings_expanded.png`、`03_settings_locals.txt` | 展开 Settings，检查问题、网格和求解设置 |
| `04_rhs_single_step.png`、`04_rhs_locals.txt` | 实际单步进入 RHS；t=0，T=301.15 K，C=2.55，数组 3201 点；D≈4.93765509×10⁻⁹ m²/s，ρ=820 kg/m³，cp=2600 J/(kg·K)，k=0.36 W/(m·K)，R=0.02 m；Ceq=0.01963，表面水通量和 C 导数为负、累计失水导数为正 |
| `05_q23_entry_breakpoint.png`、`05_q23_entry_locals.txt` | Q1 已完成并释放，进入 Q2/Q3 共用的 N=3200 轨迹 |
| `06_q4_entry_breakpoint.png` | Q23 全量计算/导出完成后进入 Q4 |
| `07_q4_model_6400.png`、`07_q4_model_locals.txt` | Q4 实际调用中 intervals=6400、shrink=True |
| `08_gui_all_solves_exports_complete.png` | 控制台实际可见 `REPRODUCTION_SOLVES_COMPLETED`、`ALL_SOLVES_AND_REQUESTED_VALIDATIONS_COMPLETED` 及 `REVIEW_FUNCTION_COMPLETED; GUI_OBSERVATION_AND_ACTUAL_EXIT_NOT_SELF_CERTIFIED` |
| `09_debug_session_closed.png` | 计算完成后的启动器等待已通过 VS 停止调试关闭；启动按钮启用、停止调试禁用 |

在控制台出现全部完成标记及“Press any key to continue”后，操作系统查询已没有原模型 Python 进程 PID 49336。VS 调试器仍在等待启动器关闭。2026-09-10 17:53 UTC 左右，通过 VS 的停止调试按钮结束这一后置等待；未向控制台输入命令。VS 输出窗口为空，**没有得到“退出码为 0”的 GUI 文本证据**。退出码未观察与计算结果未完成是两件事；此处仅按已存在的完整产物和实际完成标记记录计算/导出完成。

本机安装的 debugpy 启动器源码 `launcher/debuggee.py` 的 `wait_for_exit()` 显示：它先等待模型进程，发送携带真实 `exitCode` 的 `exited` 事件，再可能进入按键等待；这解释了启动器等待可晚于模型进程结束。但源码解释不代替本次实际退出码证据，本记录仍保留 `null`。正式命令行生产进程的实际退出 0 以其 `process_result.json` 为准，不移植为本次 GUI 退出码。

## 独立产物核对

另一个代理在完整 `review_result.json` 已落盘后，于 17:41:50—17:41:53 UTC 独立检查，**60 项全部通过**：

- 三条轨迹参数、临界事件、复现采样和 NPZ 数值完全一致；NPZ 容器也一致。
- 四份原精度 gzip 共 150,667,700 字节的解压内容完全一致。
- 七个工作表 XML 共 398,111,196 字节完全一致；四个 XLSX 容器内容的差别仅为 `docProps/core.xml` 创建/修改日期。
- 七份正文 CSV 和四张正式主图的数据数组逐值一致，NaN 位置一致。
- 28 项冻结输入和源码当前哈希仍与生产相同。

详见同目录 `independent_comparison.md` 与 `independent_comparison.json`，不以文件大小或完成标记代替逐值核对。原始 GUI `review_result.json` 继续保留其生成期状态，由本记录补充实际观察。

## 明确保留的界限

本轮证据覆盖实际执行的核心求解、导出、主图和校验调用链，不声称所有历史实验脚本及新增文档/审计/补充绘图工具都已在 VS 中分别运行。三张补充证据图的新驱动只做了命令行生成、数据回读和视觉检查；其单独 GUI 与人工审查仍待完成。本次 GUI 复现不等于用户人工代码审查，也不验证缺失的药材内部实测真值、平衡含水率映射或潜热闭合假设。
