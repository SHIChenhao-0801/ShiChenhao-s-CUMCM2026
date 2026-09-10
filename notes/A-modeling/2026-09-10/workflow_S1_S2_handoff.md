# S1/S2契约交接及独立Bessel验证设计

2026-09-10，北京时间。子代理workflow_contracts负责本文件；主记忆和Git由主代理统一更新。

已完成的事实：从本届根目录实际运行S1入口guard，PASS；逐一核对A题7份资产SHA256并重新抽取4页PDF文字；写入`paper_output/step1/problem_analysis.json`和A/B/C/D四项；实际运行S2入口guard，PASS；写入`paper_output/plan/model_route.json`、`rubric_alignment.json`及`scoring_strategy.md`。最后实际运行`workflow_guard.py --status`返回`current=S2 next=S3`。已通知data_history_audit接续S3，之后本代理不并发改写guard。

构建脚本为`paper_output/code/contracts/build_a_contracts.py`，两个阶段分别运行。脚本只生成契约和题面抽取，不调用物理求解器。无生产数值、无S5/S6通过、无VS正式源码复现、无用户人工审查完成。主代理需按context-memory-keeper统一更新memoryskill及workflow_memory，避免子代理并发覆盖。

核心路线记录：Q1固定骨架短时热传导及非线性扩散；Q2从同一初值起全程采用附录3双向物性耦合；Q3在Q2同一模型上作全域max(C)阈值事件；Q4采用附录4和实测半径的同比材料收缩。有效体积热容量rho(C)cp(C)与守恒干骨架rho_d分清。Ceq等于附件空气值、4h后50°C/0.05平台、h/beta沿用、固定长度和一维径向均显式记录为假设。Q4必须同附录4物性下固定/收缩对照，不能将跨问物性差异全部归于收缩。

后续独立校核方案（此时只为数学设计）：对于常系数圆柱Robin热方程，令g(t)=T∞(t)，θ=T−g。温差θ满足齐次Robin边界，方程θ_t=αLθ−g'(t)。特征根满足μ_n J1(μ_n)=Bi J0(μ_n)，Bi=hR/k，λ_n=αμ_n²/R²，常函数展开系数A_n=2J1(μ_n)/[μ_n(J0²(μ_n)+J1²(μ_n))]。

因此T(r,t)=g(t)+Σ_n A_n J0(μ_n r/R){[T0−g(0)]exp(−λ_n t)−∫_0^t exp[−λ_n(t−s)]g'(s)ds}。在g的每个线性段[a,b]上，斜率m恒定，积分为m exp[−λ_n(t−b)]{−expm1[−λ_n(b−a)]}/λ_n；b不超过当前求值时刻。这样不另引入边界时间积分步长误差。

有限体积比较时应使用环形单元体积平均解析解。归一化半径单元[a,b]上的J0均值为2[bJ1(μb)−aJ1(μa)]/[μ(b²−a²)]。中心和表面点值另给；不能把单元平均值当作节点值后误报离散误差。

Bessel级数只为常系数线性方程提供解析基准。第一问的常系数热方程可以使用实际附件的分段线性温度边界；第一问D依赖C，不能称其含水率非线性解有同一Bessel精确解。冻结D的水分基准需单独标注为算法验证情景。实施单文件拟为`paper_output/code/modeling/validate_bessel.py`，待S3实际通过后按model-code-and-result-generator入口要求实施，核心solver由主代理拥有。

## 后续实际完成记录

已读取本轮2026-09-10 22:13:13（北京时间）的`workflow_guard_report.json`，其mode为skill、skill为model-code-and-result-generator、required_step=S3、status=PASS。S3入口与主代理接续已完成；本代理没有并发重写guard。

已完成并实际运行`C:/Python314/python.exe -B paper_output/code/modeling/validate_bessel.py`，退出码0。脚本独立于核心求解器，不写主run_manifest。主接口为`bessel_temperature(times_s,radii_m,env_t,env_T,...)`，返回时间×空间的Kelvin数组；可传`cell_edges_m`取得环形体积平均。`bessel_moisture`仅处理调用者指定的常量D。边界不自动延拓，超过最后给定边界时刻会报错，要求调用方明确提供延拓数据。

实际自检记录：`paper_output/results/bessel_validation/bessel_selfcheck.json`，包含代码和输入CSV哈希、运行命令、Python版本、输出文件哈希及未完成GUI/人工审查状态。8项自检全部通过：特征方程相对残差5.0162e-12；分段卷积对独立自适应积分误差8.8818e-16K；环形均值对独立积分误差4.4409e-16；常边界阶跃热量平衡残差1.7694e-16K/s；实际附件温度边界的120/240项差1.5247e-7K、240/480项差1.8995e-8K；均匀平衡和绝热特例误差0。

实际基准表：`q1_exact_heat_paper_points.csv`（Q1热方程解析级数240项，7个题定时刻×5个题定半径）和`frozen_D_moisture_benchmark_points.csv`（固定初始D的算法验证情景，不是非线性Q1含水率答案）。上述“差”是抽查时空点的截断敏感性，未证明所有时空点统一误差上界；也尚未对主FVM求解器形成比较结果。Visual Studio GUI复现与用户人工核验仍待进行。
