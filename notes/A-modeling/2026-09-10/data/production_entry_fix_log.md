# 生产入口修复交接

完成时间：2026-09-10 16:07 UTC（北京时间9月11日00:07）。本任务只修改 `paper_output/code/modeling/run_modeling.py` 并新增 `production_provenance.py`；没有改动 core、disk_dense、export_outputs、publication_plots 或 q1—q4 模块。原模型参数与题设口径保持原配置；主入口默认 N1=3200、N23=3200、N4=6400。

## 已实现

1. **每次只保留一条 Run。** 顺序为 Q1 求解→导出/回读/主图→close；Q23 求解→同一对象完成 Q2、Q3→close；Q4 求解→导出/回读/主图→close。`try/finally` 中调用已存在的 `run.close()`，随后清除 bound method 和 Run 引用并 GC。图接口优先使用公开 `make_question_plot(run,qid,directory)`，保留旧私有接口的存在检查作为兼容后备。
2. **worker 不发布全局结果。** 所有数值摘要、导出、正文表、主图及附属产物只写在本次版本目录。正文表与图不会另外复制到固定全局文件名；全局 table_index/figure_index 指向该版本内真实路径。
3. **真实退出码控制正式发布。** 父进程在启动前记录源码/输入/库/字体，监督真正的子进程并保存 stdout、PID、argv、开始/结束与实测 returncode。只有实际退出码为0、完整 worker success 与前后来源及产物哈希匹配，才进入发布阶段。worker版本合同中退出码为 null，明确等待父进程观察；正式合同由父进程填实际0和 process_result 证据路径。
4. **发布期间先取消旧 PASS 的可用性。** 带排它标记的发布事务先保存旧合同和旧 manifest，在全局 manifest 标 PUBLISHING；逐个发布并实际读取验证合同/图表字节和输入哈希；最后提交 PASS manifest。异常恢复原文件，旧 PASS 在原合同恢复后才恢复；回滚失败会保留 FAILED_PUBLICATION 状态及错误。旧内容保存在版本目录 `publication_previous`。
5. **版本不可重用。** 父进程 `mkdir(exist_ok=False)` 原子认领版本，`launch_claim.json`/`launch.json` 为独占创建；worker 需匹配随机启动标记与参数，并独占写 `worker_started.json`。成功、失败、空但已认领的版本一律不能再次覆盖。失败记录 `worker_failure.json`、`process_result.json`（若有实际子进程）、`parent_failure.json`。启动失败不会虚构 returncode；真实子进程退出失败会保留实测值。
6. **指标证据完整落盘。** 每条增强摘要包含 completion、solver_warning_count、复现采样和按 Q1/Q2/Q3/Q4 区分的 `metric_samples`。它们在构造指标前已实际保存。每项 metric 有 evidence_path 和精确 `evidence_json_pointer`，worker和父进程都读取保存的JSON并检查对应值完全相等。Q3/Q4样本使用 `reported_time_s`；不会用保守尾段 `end_s` 代替。
7. **完整来源快照。** 启动时动态读取 `modeling/*.py` 库存，包括主代理随后发布的 core/disk_dense 版本，不预先锁死旧 core hash。核心/q wrappers等模型模块延迟到 worker 来源预检后才 import，并在 import 后再次核对来源。入口/辅助模块自身有 import 时哈希冻结。库存不等于执行清单；worker另记实际载入的本地模块。记录 Python、NumPy、SciPy、openpyxl、matplotlib 版本及字体文件 SHA。
8. **保留真实旧图索引。** 发布前读取现有 figure_index，逐一验证既有真实图和已登记附属文件。保留不同ID的真实图，对同ID的新主图替换并记录；不将 planned/placeholder 条目提升为真实图。旧索引原件随发布备份保留。新图PNG/SVG/PDF、NPZ、metadata及保留下来的图附属产物均列入正式账本。
9. **VS复现为直接单进程。** `--review` 不起子进程，直接运行同一组 wrappers/core，便于 VS F5 命中核心断点。只保存小型摘要与复现样本，不重复正式 Excel 导出、不发布全局合同。review_result 和 review_evidence_validation 状态为 `COMPUTED_PENDING_GUI_OBSERVATION`，不自报已观察的进程退出0、GUI通过或人工批准；这些证据由主代理在VS实际观察后另行记录。
10. **任务进程内限制BLAS线程。** 新参数 `--blas-threads` 默认1，在导入 NumPy/SciPy 前设置当前进程 OPENBLAS_NUM_THREADS 和 OMP_NUM_THREADS，并传给正式worker、写入运行环境。没有修改Windows全局环境或注册表。

## 实际执行的验证

`C:/Python314/python.exe -B paper_output/code/modeling/production_provenance.py --selfcheck` 已完成10项隔离契约验证。最新报告：

`notes/A-modeling/2026-09-10/data/production_entry_contract_selfcheck/check-qy0teplj/selfcheck.json`

- 来源文件修改被哈希核验拒绝。
- 已存在的排它启动标记拒绝覆盖。
- 指标值与保存证据不相等时拒绝。
- 既有真实产物被保留，planned 条目不被升级。
- 发布中途注入文件写入异常后，旧合同和旧 manifest 被恢复。
- 成功发布时校验实际目标字节，再最后提交 manifest。
- 两个真实微型 Python 子进程的实际退出码0和7均被观察并保存。
- 注入的微型 Run 服务验证每时刻只存活一条 Run，Q2/Q3对象身份相同。
- Q3导出注入异常后仍关闭 Q23，且异常继续上抛。
- 上述 worker 正常与异常调用前后，正式全局合同/图索引哈希完全不变。

另外，两份代码 AST 解析通过，入口 `--help` 通过；微型入口测试实际导入了最终入口，因此也验证当前源码可编译。测试中的 Run、导出和绘图为显式隔离 fixture，**没有求解 PDE，没有生成正式模型数值或可用科学图**。所有 fixture、日志和报告均位于 notes 内，不进入正式全局索引。本任务没有启动实际大生产、没有通过VS GUI；命令行契约检查不等于GUI证据。

## 交给主代理的剩余验证

- 由主代理冻结 core v6/导出器等最终来源，再统一启动正式计算。入口会在运行途中发现任何 modeling/*.py 或输入变更时拒绝发布，故正式过程中不得修改库存目录源码。
- 将两个新增/修改的Python源码纳入VS可视审查清单；review直接运行同一进程，实际退出与断点/变量截图另记。
- 独立导出代理负责正文CSV内容回读等增强；本任务保留 exporter 既有API，实际全程大XLSX生成/读回和最终包20M仍未在本任务运行。
- 发布消费者应读取全局 manifest 的 PASS 状态并检查其中哈希，随后按 table_index/figure_index 路径取文件；不要继续假定 `paper_output/tables/q3_paper_moisture.csv` 等固定复制件存在。
- 本任务的发布事务已测微型写盘成功和中途失败；极端磁盘故障可能让日志或回滚本身无法写入，这种情况会保留异常/非PASS状态，不能保证在硬件不可写时仍能持久化全部证据。

## 交接源码哈希

| 文件 | SHA256 |
|---|---|
| run_modeling.py | 1770dc580f54a932f5854b6e5bb211efbc72f7db162858b6aaccccec6d82683a6 |
| production_provenance.py | 0370979d780ff59487d1616d7c0ff6041c642624d9267c51f9a0925b26453130 |

主代理随后修改任一文件，应以新实测哈希和相应复核结果覆盖本交接版本；不要复用本表宣称新文件已验证。
