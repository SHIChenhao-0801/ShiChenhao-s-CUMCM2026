# A 题新生产入口独立静态审查

审查时间：2026-09-10 15:30–15:35 UTC。对象为 `paper_output/code/modeling/run_modeling.py`、`q1_model.py`—`q4_model.py`、核心 v4 的分块 diagnostics、`export_outputs.py` 正文末时刻调整及主图接口。只读审查，没有修改生产代码，没有启动重复求解，没有执行外来模型代码，没有操作 Git、guard 或 GUI。下文行号和结论对应本次读到的版本；主代理随后修改时须重新核对相关项。

## 一、结论与优先修正

四问模型调用、第二/三问共用同一 Run、原精度阈值判定、正文向上舍入末行和主图产物收集的主要路径一致。不能据此声称新生产已经成功：审查时 `paper_output/results/production` 尚不存在，全局新生产 `run_manifest.json` 尚不存在，两条细网格收敛程序仍在运行。

发现两项确定的实现缺陷，以及一项有实际系统状态支持的高优先级运行风险：

1. **P1：正式合同发布早于最后依赖核对和实际进程退出。** `run_modeling.py:107–115` 在每问完成时即覆盖全局表文件；`:172–174` 发布全局 computed 合同；`:175–176` 才检查依赖是否变化，父进程在 `:223` 才能取得真正 returncode。若随后发生依赖变化、产物哈希读取失败、写盘失败或 worker 异常，已发布文件不会回滚，而已有旧版本全局 PASS 账本也不会失效。`execution_provenance.run_exit_code=0` 在 `:145` 预填，此时尚非已观测的实际进程结果。本次尚未发生该失败路径；缺陷由控制流明确确定。

   建议 worker 只写带版本的目录，完成依赖复核、全部产物记录后写 worker success。父进程取得实际退出码 0，再把版本合同/表发布到全局位置，并最后原子替换全局 manifest；失败时记录实测非零退出码、失败阶段和对应版本，禁止保留新合同与旧 PASS 的混合组合。成功合同中的退出码由父进程最终填入。多个全局文件无法一次原子替换时，可让唯一全局 manifest 指向不可变版本目录，并要求消费者按该入口读取。

2. **P2：指标的证据路径没有所报数值。** `run_modeling.py:76` 调用 `save_run` 写单问 `summary.json`；`:77–83` 后加的 solver warning count、completion、复现采样仅进入内存。`:123` 将增强数据写到 `numerical_summaries.json`，但 `:132、159–161` 的 `evidence_path` 仍指向此前的单问 `summary.json`。因此 `reported_drying_time` 指向的文件不存在该报告时间；`center_C_at_report_time` 也没有对应时间和空间位置的采样证据。核心摘要的 `final_max_C` 属于 `end_s`，不能替代另一个 `reported_time_s` 的中心值。

   建议完成增强后重写版本内单问摘要，记录 `metric_sample={time_s, material_x, T_K, C}`，并在指标中明确采样时间和 JSON 路径；或统一指向包含这些精确字段的 `numerical_summaries.json`。主代理已修的 `sampletime=completion['reported_time_s']` 在本次 `:129–130` 读到的版本中生效，不再报告旧的采样时刻错误。

3. **P1 运行风险：当前提交内存接近上限，分块 diagnostics 未解决 dense Run 常驻内存。** 实测与量级见第三节。不能在当前两个收敛进程之外同时再启动最终生产。新生产依次求解但把 Q1、Q23、Q4 三条完整 dense Run 同时留在 `runs`（`:84`），对计划 N1=3200、N23=3200、N4=6400 仍需解决内存预算。此项是实际风险，尚不声称已发生 OOM。

以上关键发现已及时发送主代理。未在本任务内擅自修生产程序。

## 二、正确路径与验证边界

### 2.1 四问入口及共用轨迹

| 对象 | 本次实际代码 | 审查结论 |
|---|---|---|
| Q1 | `q1_model.py:5–8`，`question='Q1'`，Kirchhoff，rtol=1e-10，T atol=1e-10、C atol=1e-12 | 使用附录2物性，核心 Q1 horizon=1800 s；没有误接附录3。 |
| Q2 | `q2_model.py:5–8`，`question='Q23'`，从 t=0 单独求全程 | 没有把 Q1 末状态拼接到附录3模型。 |
| Q3 | `q3_model.py:6–27`，只调用 `completion(run)` | 无新求解，属于 Q2 同一轨迹的全域阈值泛函。 |
| Q4 | `q4_model.py:5–8`，`question='Q4', shrink=True` | 整组附录4物性与给定 R(t)；主入口显式传 `args.n4`。 |
| 实际共用 | `run_modeling.py:69` 只求 Q1/Q23/Q4 三次；`:98` 将 Q2 和 Q3 指向同一 `runs['Q23']` | 主结果表和主图都来自同一对象，没有分别求解后混版本。 |

`q4_model.solve` 的独立 API 默认 intervals=3200，而 CLI 默认 n4=6400。这不会影响主入口，因为它显式传入 n4；但单独调用 `q4_model.solve()` 会得到不同网格。建议文档/VS入口均打印实际配置，或统一 API 默认值，避免人工复现误用。

### 2.2 阈值及三个终点口径

核心 `drying_core.py:280–282` 事件为所有材料网格节点最大含水率减 0.15，下降穿越且 terminal。它没有将中心低于阈值、平均含水率低于阈值或四舍五入后的 0.1500 当作达标。

核心 `:303–309` 事件后确实继续积分到 `ceil(event_s)+1` 秒；不是对已终止轨迹作域外外推。`q3_model.py:11–20` 先把临界小时数向上到 0.0001 h 网格，再从 live Run 读取该时刻所有 C，若仍不严格小于 0.15 则再增加一个报告刻度。0.0001 h=0.36 s，核心保守尾段足以覆盖正常的第一次向上报告点；若仍超出尾段会报错，不会静默外推。

应始终区分：

- `critical_event_s`：数值连续根，最大值等于阈值。
- `reported_time_s`：向上取四位小时小数后又以原精度实际验证严格阈值的报告时刻。
- `end_s`：`ceil(event_s)+1` 的保守复核尾段终点，代码明确没有声称它是最早达标整数秒。

`export_outputs.py:239–241` 正文 Q3/Q4 表使用 `reported_time_s`，每6h加实际报告末行。`run_modeling.py:129–130` 最终中心指标也已同口径。完整 XLSX 仍按 `end_s` 导出：Q2 逐秒 0..end_s；Q3/Q4 每60秒加临界根和保守尾段终点。正文和完整表的末行时刻不同属于已选口径，交付说明应明写，建议在 export manifest 额外列 `reported_time_s`，避免收件人把最后一行误认作报告烘干时间。

这套判定验证的是离散状态与 BDF 稠密输出中的数值事件，不能自动证明连续时空 PDE 的严格界或真实药材的达标时间；主入口 LIMITATIONS 已保留这一点。

### 2.3 完整输出与 live Run 回读

`export_outputs.py:277–378` 的 XLSX 使用 write_only，并从 live Run 每块 1000 个时刻重新评估；不会从每60秒 NPZ 重构逐秒数据。Q2 包含全程至复核末秒，非仅前三小时。完整逐秒长度超过 Excel 行数时抛错。Q4 在物理固定半径网格上以 `r<=R(t)+1e-12m` 判内域、域外写空值，同时另存实际表面 C 和半径 sheet；不会以固定 2 cm 当收缩后表面。

`validate_exports` 会逐行、逐单元读取 XLSX，对照未舍入 CSV.gz、精确时间安排、物理半径、空域和四位格式；再对 manifest 中抽取的时刻从 live Run 独立重新求值，容差 1e-10。发现任何 accumulated error 最终在 `:503–504` 抛错。因此主入口 `export_validation.json` 汇总硬写 PASS 虽可改为显式聚合，现有实际调用不会把已经返回的 FAIL 静默当 PASS。

验证范围需准确表述：XLSX/raw archive 是全部导出单元的一致性检查，独立 live Run 是抽样重评估，二者都不等于与实测真值相比。正文 CSV 当前仅检查文件 SHA（`:409`），没有逐格重新读取并与声明时刻 live Run 对照。正文生成代码在本次静态审查中与题定时间/位置一致，但若要称“正文表回读通过”，还需实际回读该 CSV。

导出 manifest 的状态保持 `EXPORTED_PENDING_STREAM_READBACK`，export 返回记录中的 `validation_status` 也保持 pending；成功回读另有 `.validation.json` 与统一 export_validation。因此最终消费者应读取后者，不应把 manifest 的 pending 误解为实际没校验。建议最终合同显式关联验证报告路径和状态，保留不可变原始 export manifest。

### 2.4 diagnostics 分块改动

`drying_core.py:238–250` 按每段时间点块256读取 `piece.y` 视图。交错数组正确取 T=`raw[:-1:2]`、C=`raw[1:-1:2]`，最后一行为累计流出。`2*w@C + raw[-1] - C0` 的轴与权重正确；`np.diff(C,axis=0)` 检查径向相邻节点，非时间相邻点。T、C 同样 ravel 的顺序一致，按点求物性未错配。

此改动保持所检查 accepted states 的诊断数学量，避免以前把所有 accepted states 横向拼接和一次生成多套物性；没有改 RHS 或积分解。但 diagnostics 只扫描 accepted states；它不等于对任意稠密输出时刻的全局连续正性证明。当前 exporter 另行检查导出域内数值 finite。

## 三、内存风险的实际证据与估算

约 15:29 UTC 的只读系统快照：

| 进程 | 已核对命令 | WorkingSet | PeakWorkingSet | PrivateMemory |
|---|---|---:|---:|---:|
| PID 48528 | `verify_convergence.py --question Q23 --grids 1600 3200 --full-second-comparison --tag Q23_final_resolution_v4` | 4,961,857,536 B | 4,964,704,256 B | 6,455,857,152 B |
| PID 49416 | `verify_convergence.py --question Q4 --grids 1600 3200 6400 --full-second-comparison --tag Q4_final_resolution_v4` | 5,078,425,600 B | 5,080,633,344 B | 6,596,689,920 B |

系统当时 FreePhysicalMemory=3,866,620 KiB（约3.69 GiB），FreeVirtualMemory=862,376 KiB（约0.82 GiB），TotalVirtualMemorySize=42,962,500 KiB。这是快照，不是正式生产峰值，更不是之后状态；没有终止任何进程。

已保存的 N1600 完整计算分别有 Q23 14,294 和 Q4 16,018 个 accepted time points。按同样点数作量级估算：

- Q23 N3200 单份 `y` 的数据约 `(2*(3200+1)+1)*14294*8`=0.73 GB。
- Q4 N6400 单份 `y` 约 `(2*(6400+1)+1)*16018*8`=1.64 GB。
- BDF dense_output 还为每步保留多个差分系数；若大部分步的阶数在3–5，一般还需4–6份对应状态大小，不能只按 `y` 一份估内存。这里是静态量级估算，没有实测最终 N6400 的实际阶数分布。
- `Run.state` (`drying_core.py:196–205`) 另分配全节点×请求时间阵列并接收 SciPy 返回阵列。`save_run:341–345` 仍两次对全部每60秒采样时刻调用全节点稠密解，第二次完整 `state` 持有至压缩保存完成；Q4 N6400、约3068个时刻时，单个状态数组就约314 MB，稠密求值还有临时数组。
- diagnostics 的256块在 N6400 下每个 T/C 物性数组约13 MB，多套物性和临时变量合计仍为数十至上百 MB，但这一项已受块大小限制。
- 正式 exporter chunk=1000 时，Q4 的单次全状态数组约102 MB，加稠密输出临时阵列；不是“因为只输出21列所以只占21列内存”。
- `drying_core.file_record:323` 用 `read_bytes()` 对单个完整文件哈希，最终 Q2 XLSX/CSV.gz 的大小也会进入额外瞬时内存；exporter/绘图模块已有1 MiB分块哈希，可复用。

建议最终生产按“求一个物理 Run→完成其对应问题全部导出、验证、主图和精确指标→保存小型汇总→释放该 Run”组织；Q23 必须在释放前同时完成 Q2/Q3，以保持同一对象，不需要重复求解。主图可拆为单问调用而不必同时保留三条 Run。`--review` 也可以每条 Run 保存复现样本后立即释放，只保留摘要。若最终必须保留稠密轨迹，可考虑磁盘分段缓存，但这是实现改动，须独立复核且不得冒称原内存实现已验证。

正在运行的 `verify_convergence.py:55–96` 只长期保留上一条 Run，但求下一条和比较时会同时保留 coarse+fine；Q4 从 N3200 进入 N6400 时，内存继续上升。因此应按实际系统容量串行安排重任务，不以“诊断已分块”代替整体内存审查。

## 四、账本真实性、依赖与图表覆盖

父进程通过 `subprocess.Popen` 启动 worker、流式保存 stdout、`process.wait()` 获取实际退出码，成功后才写 `run_manifest`。这比凭空填写测试通过有实质改进。`--review` 注释明确只有在 VS 启动且观察才构成 GUI 证据，脚本自身不自动认证 GUI；human_review 一直 pending，口径正确。

核心、解析 Jacobian、exporter 和 plot module 均有 import 时冻结 SHA，保存/导出时检查变更；输入 CSV 在模型加载时冻结来源字节并复核。新主入口的 `dependencies()` 记录核心、Jacobian、四问 wrapper、exporter、plot、validate_bessel、两份 CSV、route 和本题全部 XLSX，前后进行比较。下面仍需完善或明确限制：

1. `run_modeling.py:25–26` 先 import wrappers，直到 `:65` 才读它们的在盘哈希；主入口和 wrappers 本身没有 import 时冻结哈希。在这个窗口内修改脚本，可使载入旧函数而记录新盘上哈希。正式冻结后不编辑可避免当前执行中的风险；更完整方案是给实际载入模块逐个冻结哈希或由父进程在启动前形成快照并让 worker 核对。父进程 `:228` 又在运行结束读取 SOURCE，应该采用启动时/worker 已验证的源码记录，避免结束后的改动错署。
2. 依赖版本目前仅记录 Python/NumPy/SciPy (`:232–234`)；openpyxl、matplotlib 和实际中文字体也影响完整产物。图 metadata 记录字体名称/路径，但未记录字体 SHA。建议记录 openpyxl/matplotlib 版本和字体文件哈希。`validate_bessel.py` 虽列为依赖，这次生产入口没有执行它，不能据清单声称本次又运行解析验证；解析证据应关联真实的独立验证报告。
3. 每张主图的 PNG/SVG/PDF、`*_data.npz`、metadata JSON 均由 `run_modeling.py:181–183` 收集，未遗漏主图附属文件；主图来自本次 live Run。Q1 题定7个时刻、Q2 前3h六时刻；Q3/Q4 展示全程含水率与中心/干质量加权均值/表面，临界事件用 event_s 标签，与正文 reported_time 区分。
4. 当前 `make_plots` 只产4张主图。已存在的 S3 数据图、收敛图、同物性收缩对照、物理敏感性图不由此入口自动纳入全局 figure_index；主入口会用4张主图覆盖该索引。这不使四张主图无效，但最终若计划正式使用那些验证图，必须分别关联来源报告、实际图及附属产物并合并索引，不能把它们当作本入口已生成。
5. `:211` 只拒绝已写 worker_success/review_result 的版本；失败的版本目录可被同名再次启动，stdout.log 会被覆盖 (`:218`)。这与报错文案“retain failed version”和不可变版本的目标不完全一致。建议主入口拒绝任何非空版本目录，worker 通过父进程专用启动标记进入；至少拒绝覆盖已有 stdout.log 并保存失败 manifest。
6. 正式支撑包20M问题仍需对最终真实压缩包核验。exporter 只报告单个 workbook是否超过20,000,000 B，不会据此自动满足整个支撑包体积；源码已正确标注仍需实际包检查。不能因单个XLSX低于20M就声称支撑包合规。

## 五、审查版本及未执行验证

本次在盘源码 SHA256：

| 文件 | SHA256 |
|---|---|
| run_modeling.py | d2e63f56dd43cf702e5983e8dca1757fee61a441630cc337707c4f932a51357b |
| q1_model.py | 58f0f3d8a3c833a9bf4f60702a3a02ec4cd67ae9ace8d0567cb20f84073cdfa8 |
| q2_model.py | 4ceb89001d2e99270e117d124394213adab1ba678a85395e7e8cf36b0e4d1204 |
| q3_model.py | 43a65b6a1982649503beaeec92d7aa553dd6d8f516703cc50b912a086ba9a137 |
| q4_model.py | ebc9d8aa92471dc1fd2bbe0d3ed67fa7900ccdb59feb86057b7c0aeb4d87bf15 |
| drying_core.py | f113d965ce87a43ba86a95c291ce721120bf9543180bdcbd58e7c43f06eb76de |
| analytic_jacobian.py（已保存摘要引用） | d7dfda75b335e82eb27d39b8e2f12edf5a56254269ff4f273e7a828ed75a8665 |
| export_outputs.py | 7ad751b0d66c9a3956e4717c6d7aeeecf95e37907f126340100317b5a077af62 |
| publication_plots.py | 0c4ef4d8085211be26d64d139d9c91314a977a06e8fb2333e7b113b7a3005b41 |

本任务没有实跑新生产入口或主动触发失败注入；没有重新执行 Bessel、Jacobian 自检或模型对照；没有将当前未完成的细网格报告当作收敛通过；没有检查正式主图的实际渲染，因为这批生产图尚未生成；没有以静态审查替代 VS GUI 和用户人工审查。修正后需检查实际成功账本、各指标精确证据、全部图表及其SHA、全程导出回读与最终包体积，才能冻结正式结果。
