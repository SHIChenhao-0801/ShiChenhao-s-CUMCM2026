# 05 数值检验源码独立运行审阅

范围为 31 个 Python、1 个 MATLAB 和 1 个 Node.js 源文件。删除注释不等同于修复可移植性或复现历史实验；下列条目分别记录原入口、函数级小规模执行和不可执行的原因。原支撑目录和正式模型算法不在本子任务中修改。

## 共用依赖

`Python检验源码` 是原 modeling 文件按 `parents[3]` 推导的根。所有 PDE 至少需要该根下 `paper_output/data_cleaned/A_environment_observed.csv` 和 `A_radius_observed.csv`，当前 05 没有二者。两者可从 03 的 inputs 副本逐字节复制进隔离实验目录，不需要读取原生产工作区。

基本 Python 依赖是 NumPy、SciPy；原导出和 provenance.runtime_record 需要 openpyxl；后者即使不绘图也需要 Matplotlib 的已安装元数据。四个绘图入口需要 Matplotlib。publication_plots/run_modeling 明确读取 C:/Windows/Fonts/msyh.ttc；这是外部系统字体依赖，不是数据自包含。

13 个 verification 文件均含原 D 盘绝对 ROOT（以及 validate_bessel.main 内的 cwd 检查）。未适配时它们会访问原工作区，不能仅改变 cwd 后声称隔离。适配副本可统一改为自身文件 parents[3]；所有原数组运算、模型参数和积分设置应保持不变。先保留未适配失败证据，再把适配执行和原件执行分别记账。

输出默认写到推导根下 paper_output/results。disk_dense 私有缓存位于根/tmp/cache/solver_runs，必须允许写入并核实 close 后清理。run_modeling 会向其根下发布全局 JSON 合同，只有在隔离副本里才可运行。

## 逐源码入口与最小实算

| 源文件 | 入口或调用方式 | 独立输入与实际验证范围 |
|---|---|---|
| drying_core.py | 库，solve_case(Settings(...)) | 两 CSV；由全部 PDE 检查覆盖，不把直接执行空模块算 PASS |
| analytic_jacobian.py | --self-test | 两 CSV；完整 84 状态/336 方向及 4 个短 BDF 测试，可实际完整运行 |
| disk_dense.py | 库 | 由 verify_dense_storage 的磁盘/内存实跑覆盖 |
| q1_model.py | solve(N) | Q1 1800 s 实际轨迹；通过时间误差检查调用 |
| q2_model.py | solve(N) | Q23 完整事件轨迹；由库函数检查调用 |
| q3_model.py | completion(run) | Q23 同一轨迹严格报告值；不独立重求解 |
| q4_model.py | solve(N) | Q4 完整收缩事件轨迹；由库函数检查调用 |
| validate_bessel.py | 默认 main / selfcheck(env_t, env_T) | 原绝对 cwd 门禁须区分；8 个解析自检，无新 PDE |
| compare_analytic.py | 默认 main | 完整 6 个 Q1 N100/200/400/800 计算，通常数十秒；需要 Matplotlib |
| verify_convergence.py | --question Q1 --grids 20 40 --tag sandbox | 两条实际 Q1 轨迹、1801 秒×21 半径；是小网格功能与收敛检查 |
| verify_time_accuracy.py | --question Q1 --n 20 --tag sandbox | 原监督父/子进程，基准/紧容差各一条实算；provenance 还要 4 个依赖包元数据 |
| verify_dense_storage.py | 默认 main | 原完整 N40 三条轨迹×两种存储，逐位比较 accepted 状态与全部内部结点左右浮点邻点 |
| run_experiments.py | --batch baseline --n 20 --tag sandbox --face-scheme kirchhoff | 三条实算；默认 harmonic 不能偷换成生产 Kirchhoff而不记录参数 |
| production_provenance.py | --selfcheck | 真实小文件故障注入、真实 exit0/7 子进程、入口生命周期 fixture；不是 PDE 结果 |
| run_modeling.py | --version sandbox --n1 20 --n23 20 --n4 20 --review | 原完整入口额外强制 model_route.json、4 个原 XLSX 模板、系统字体；当前 05 未附，必须报告缺失，不能弱化清单后称原入口 PASS |
| export_outputs.py | --selfcheck | 两 CSV 与 result1.xlsx 模板；实际 Q1 N40 导出与所有单元格回读 |
| publication_plots.py | --selfcheck | 三条 N40 实算和4图；四个额外历史对比可选；需要系统微软雅黑 |
| axisymmetric_check.py | --nr 6 --nz 4 --end-faces off --budget-s 120 --tag sandbox | 完整2D小网格+同径向1D事件轨迹；验证关闭端面时的退化一致性，不是原30×30精度 |
| crossvalidate_series.py | 默认 main | 两CSV及 Q23/sampled_solution.npz；NPZ必须是显式附带或本轮生成，不允许隐式读取final_v6a；旧顺序M-K缺陷不因程序exit0而恢复结论 |
| crossvalidate_solver.py | runCase(name,Settings(Q1,N20,...))，BDF/Radau各一次 | 真实相同PDE不同积分器；默认block1是8条N800/1600长轨迹，block2另12条，block3另10条，应单独标明未全跑 |
| threshold_and_scaling_checks.py | 默认 main；solver_checks(N) | 默认标度入口及Q23/Q4 N20阈值函数已在HOST与Windows Sandbox实际完成；早期静态推测的二分越域分支未触发，不列为实际失败 |
| method_comparison.py | --quick | 完整8条Q1 N100/200、常数/变量D、两种面通量；自带通量调用路径护栏 |
| latent_heat_scenarios.py | scenario(Q23,False,.25,20) | 一条完整事件轨迹及真实热湿/潜热采样；原默认8条N800，函数覆盖不等同全入口 |
| sensitivity_analysis.py | control_check；evaluate | control默认两条N200；Morris默认362条N200，Sobol默认由子集决定，需预算。dScale实际缩放Kirchhoff面通量已读到，不能仅properties缩放 |
| isotherm_activity_closure.py | --identity-only；ActivityModel/rhs；_extract | 恒等式可执行；_extract误把时间×空间当空间×时间，索引会越界；不修改或恢复原错误物理解释 |
| isotherm_diagnose.py | 默认 main | ActivityModel(...,B=4.2)与当前p接口不相容；waterActivity(C,T)也把T当p，不能擅自把B映射p |
| isotherm_jacobian_probe.py | probe(1e-7,intervals=8,horizon_h=...) | 调用SciPy内部common.num_jac，需实际核实numJacCalls与状态；exit0但calls=0不构成注入成功 |
| energy_balance_diagnose.py | 默认 main | N50、1h真实诊断；打印旧错误率关系不应冒充守恒证书 |
| energy_balance_diagnose2.py | 默认 main | Q23/Q4 N100、1h；200001时点形成约200×200001状态矩阵，内存约320MB，另有循环开销 |
| energy_balance_check.py | runCase(Q1,20,False) | Q1真实热通量望远镜恒等式与累计残差；Q23/Q4旧累计能量定义不成立，不以exit0当cumulativePassed |
| runCrossCheck.m | MATLAB GUI runCrossCheck(outputDirectory) | 源所在处上四层已不再是Python检验根，当前缺CSV；保留MATLAB独立实现，不能用Python翻译替代其实际运行 |
| compareMatlab.mjs | node compareMatlab.mjs --worker | 当前上四层root不对，且需已删除历史MATLAB/Python JSON；严格来源哈希按原文件绑定，不能改写旧声明冒称当前无注释源码所跑 |

## 确定接口问题

1. `Run.fields` 的真实接口返回 `(len(times), len(points))`。`isotherm_activity_closure._extract` 中 `C[1,i]` 在第三时点便越界，异常被 solveScenario 捕获后又进入另一次积分，因此默认入口可能隐藏采样接口错误并浪费第二次积分。
2. `isotherm_diagnose` 调用不存在的 `B=` 参数。当前 `waterActivity` 第二位置参数为 p，也不是温度。没有充分依据把旧 B=4.2 解释为 p=4.2，留为历史接口失败。
3. 早期静态阅读曾注意到 `threshold_and_scaling_checks.solver_checks` 的二分端点为 `[event-3600,event+3600]`，推测特定浮点分支可能访问已求解区间以外。本轮HOST与Windows Sandbox的原Q23/Q4 N20函数实测均通过，二分时间与事件根差分别为8.73e-11、5.82e-11秒，没有触发所推测的越域；不得将静态可能性写成已经复现的错误。未拉长原积分或外推状态。
4. `crossvalidate_series.sequential_mk` 的forward以符号和更新 sk，却减去了基于正计数的期望；常数序列会伪越界。仅运行成功不能恢复已明确弃用的旧M-K结论。
5. `analytic_metric_check` 写入的静态 interpretation 声称细化差值不减；应与本轮rows对照，不把历史解释当计算证据。
6. 许多实验main捕获单case失败后仍return0，必须检查内部status/failed/warnings/断言和场值，不能只看外层进程exit0。

适配与测试结果待实际执行日志绑定。独立sandbox仅能说明本机干净依赖与受限文件访问环境；不扩大为第二物理设备、MATLAB/VS GUI复现或团队人工代码审查。
