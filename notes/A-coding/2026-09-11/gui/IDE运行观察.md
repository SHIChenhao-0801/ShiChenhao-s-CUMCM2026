# 本轮 IDE 实际操作观察

工作区为 `D:/Document/数学建模/2026CUMCM`。本记录由主代理在 Computer Use 读取原生窗口、点击或按键后整理；数值程序自己的 `guiObserved=false`、`actualProcessExitCode=null` 保留原值，由本外部观察记录补充。用户人工审查仍为 **pending**。

## MATLAB

应用：MATLAB R2026a Update 5，程序日志记录版本 `26.1.0.3346908`。通过原生命令窗口执行：

```matlab
cd('D:/Document/数学建模/2026CUMCM');
addpath('D:/Document/数学建模/2026CUMCM/paper_output/code/review_delivery/matlab');
crossCheckResult = runCrossCheck('D:/Document/数学建模/2026CUMCM/paper_output/qa/matlab_crosscheck_20260911');
```

首次定位落在当前文件夹栏，已清除该未执行内容；随后重新观察并点击命令窗口执行以上代码。实际日志从 UTC `2026-09-10T19:32:42.731Z` 至 `19:33:27.745Z`，Q1/Q23/Q4 三案例均完成，命令窗口返回 `>>`。之后执行 `edit(.../runCrossCheck.m); disp(crossCheckResult.status);`，编辑器实际打开对应源码，命令窗口打印 `COMPLETED_NUMERICAL_CHECKS`。MATLAB 为交互会话，未退出整个应用，不把函数返回状态写成 MATLAB 进程退出码。

截图：[启动](matlab_launch.jpg)、[三案例完成并返回提示符](matlab_completed.jpg)、[已运行源码与完成状态](matlab_source_and_completed_status.jpg)。数值日志与跨语言比较在 `paper_output/qa/matlab_crosscheck_20260911`。MATLAB 默认 N40 是交叉实现检查，未声称其执行 N3200/N6400 正式生产或新的空间收敛研究。

## Visual Studio

打开 `paper_output/code/review_delivery/A_CodeReview.sln`，解释器为 `C:/Python314/python.exe`，启动 `runDelivery.py`，工作目录为本届根目录，解释器参数 `-B`。使用 F5 启动/继续，当前键位 F8 为逐语句。源码由主代理和分工代理在工作区创建；Computer Use 负责在 IDE 打开、调试与实际复现。

1. `gui_camel_final_v1` 启动后在 `runDelivery.py:139` 首次 `solve` 前暂停。此时发现并修复 CLI v1 已触发的导出来源路径问题，为重载修复版本点击停止调试。该 GUI v1 未执行完整求解，保留目录及[暂停截图](vs_v1_paused_before_solve.jpg)，不能算通过。
2. 工程参数更新为 `--profile final --run-id gui_camel_final_v2`，接受 Visual Studio 的重新加载项目对话框后 F5 启动。程序打印启动 UTC `19:47:23.822978+00:00`。
3. 在 `runDelivery.py:139` 首次命中，Locals 显示 `intervalCount=3200`、`questionKey='Q1'`、`moduleName='q1Model'`、`profile='final'`。按 F8 进入 `q1Model.solve`，观察正式容差与步长。截图：[Q1参数](vs_v2_q1_parameters.jpg)、[单步进入](vs_v2_q1_step_into.jpg)。
4. 在 `dryingCore.py:197` 设置 RHS 返回断点并继续，命中后 Locals 实际显示：`t=0`、`radius=0.02`、`T` 为 3201 个 301.15 K、`C` 为 3201 个 2.55、`ceq=0.01963`、`cp=2600`、`k=0.36`、`rho=820`、状态长度 6403，及 D、heatG、waterG、derivative 数组。保存[初始变量截图](vs_v2_rhs_initial_variables.jpg)，随后移除高频 RHS 断点。
5. Q1 GUI 求解和导出完成，进入 Q23 前再次命中 `runDelivery.py:139`，Locals 显示 `questionKey='Q23'`、`moduleName='q2Model'`、N3200；保存[Q23参数截图](vs_v2_q23_parameters.jpg)。在此暂停等待独立 CLI 正式复现退出，避免并发高网格求解。UTC 19:58 后继续 Q23。

GUI v2 全量完成状态尚待最终追加。含人工断点暂停的墙钟耗时不能当作纯算法性能；CLI 监督器的独立计时单列。所有截图包含的是代理操作证据，不能代替用户亲自审查。
