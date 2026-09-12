# 已采纳检验的完整源码补充清单说明

本补充列出 31 份完整源文件，共 6440 行；与原生产清单 11 份源码无字节重复。清单每项提供 path、sha256、lineCount、name、role、适用范围、原运行槽位、依赖及证据 JSON 指针。应按文件完整嵌入，不删函数或摘录算法片段。

现版源码不是全部历史运行的同一版本。Q1 空间证据匹配 v3 核心及 verify_convergence_v1；Q23/Q4 空间证据匹配 v5 核心、disk_dense_v5 和 verify_convergence_v5。正式生产仍使用原清单 v6。这些历史文件须在隔离副本按 originalRuntimeSlot 装配，不能直接将归档文件名当模块入口。早期调和反例与同物性 N200 收缩对照已被数值过程附录引用，故补入其必要 v1/v2 快照；未引用的其他历史试验未收录。

MATLAB N40 支线包括 runCrossCheck.m、compareMatlab.mjs、runLogged.ps1，以及 runDelivery.py 和其实际调用的七个驼峰模块。MATLAB/比较器及八个 Python 文件均有当前字节匹配证据；PowerShell 监督器自身未保存历史哈希。runDelivery 的 legacy 分支引用原11份生产模块，无需重印。其启动还核验107个冻结输入/输出并盘点原模板；比较器需要20项既存输入，因此源码收齐不能表述为当前ZIP独立可运行。

文件前必须附采纳范围勘误：sensitivity_analysis.py 只采纳修复后的 dscale/kscale 路径，保留完整 Morris/Sobol 源码但不采用旧无效结果；isotherm_activity_closure.py 只采纳经验 Kp 缩放的 p=1/2/4 事件情景，不采用原注释的“材料平衡点由数据强制”“awRef约束已证明”“真实时长下界”；energy_balance_check.py 只采用实际 sum(2wBR²*Tdot) 的瞬时恒等式，原 d/dt sum(2wBTR²) 及变容量累计守恒说明已被否定。threshold 文件的二分和尺度积分均共享数值轨迹信息，不是另一份物理验证。

历史入口未保存运行时源码SHA的条目，hashStatus记为 CURRENT_BYTES_ONLY_NO_RUN_TIME_SOURCE_LOCK；本轮哈希不能倒填为历史源码认证。后续生产清单、回顾盘点或本轮QA登记能证明文件被登记，不能证明它是早期试验启动时的同一字节。

本轮只读取、计算指纹、分析静态依赖，并生成清单和本说明。没有重新积分PDE、没有运行MATLAB或Node比较、没有修改原源码/正文/旧清单、没有新增GUI或人工签核、没有操作Git。

|序号|文件|行数|采用用途|
|---|---|---:|---|
|1|paper_output/code/modeling/validate_bessel.py|345|Robin–Bessel解析热场、级数截断自检|
|2|paper_output/code/modeling/compare_analytic.py|242|早期解析对照及常D特例筛选入口|
|3|paper_output/code/modeling/verify_convergence.py|127|当前投影/场差归约模块|
|4|paper_output/code/modeling/verify_time_accuracy.py|251|同N容差和步长收紧的监督运行入口|
|5|paper_output/code/modeling/verify_dense_storage.py|69|内存/磁盘稠密输出等价性入口|
|6|paper_output/code/modeling/run_experiments.py|74|Kirchhoff网格与同物性收缩对照批次入口|
|7|paper_output/code/verification/crossvalidate_solver.py|206|BDF/Radau与面格式对照入口|
|8|paper_output/code/verification/method_comparison.py|197|Kirchhoff与另一守恒面格式比较|
|9|paper_output/code/verification/threshold_and_scaling_checks.py|175|N800阈值二分及R平方时标归约|
|10|paper_output/code/verification/energy_balance_check.py|245|有效热方程瞬时加权通量检验|
|11|paper_output/code/verification/sensitivity_analysis.py|292|修复后的D/k单参数扫描入口|
|12|paper_output/code/verification/isotherm_activity_closure.py|494|经验边界阻力p情景入口|
|13|paper_output/code/versions/verify_convergence_v1.py|106|Q1空间检查的原驱动快照|
|14|paper_output/code/versions/verify_convergence_v5.py|123|Q23/Q4最终空间检查的原驱动快照|
|15|paper_output/code/versions/drying_core_v2_kirchhoff.py|326|采用Kirchhoff的早期实际核心快照|
|16|paper_output/code/versions/drying_core_v3_analytic_jacobian.py|338|Q1空间检查实际核心快照|
|17|paper_output/code/versions/drying_core_v5_disk_dense.py|395|Q23/Q4空间检查实际核心快照|
|18|paper_output/code/versions/disk_dense_v5.py|99|历史空间检查磁盘轨迹依赖|
|19|paper_output/code/versions/run_experiments_v1.py|73|附录粗网格反例的原批次入口|
|20|paper_output/code/versions/drying_core_v1_harmonic.py|296|附录粗网格反例的原核心快照|
|21|paper_output/code/review_delivery/matlab/runCrossCheck.m|495|MATLAB独立N40求解入口|
|22|paper_output/code/review_delivery/tools/compareMatlab.mjs|200|MATLAB/Python共点比较及Node进程监督|
|23|paper_output/code/review_delivery/runLogged.ps1|50|N40 Python实际进程监督入口|
|24|paper_output/code/review_delivery/runDelivery.py|281|MATLAB对照所用Python N40生成入口|
|25|paper_output/code/review_delivery/dryingCore.py|420|N40驼峰有限体积求解器|
|26|paper_output/code/review_delivery/analyticJacobian.py|333|N40驼峰解析Jacobian|
|27|paper_output/code/review_delivery/diskDense.py|128|N40驼峰磁盘轨迹存储|
|28|paper_output/code/review_delivery/q1Model.py|10|N40问题一入口|
|29|paper_output/code/review_delivery/q2Model.py|10|N40问题二三入口|
|30|paper_output/code/review_delivery/q3Model.py|30|N40严格报告与采样时刻|
|31|paper_output/code/review_delivery/q4Model.py|10|N40问题四入口|
