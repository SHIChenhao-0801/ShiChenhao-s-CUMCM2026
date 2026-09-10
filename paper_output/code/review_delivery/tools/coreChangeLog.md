# 核心八模块审查副本变更记录

本记录属于 2026 A 题代码审查交付。来源是 `paper_output/code/modeling/` 下的八个冻结模块，新增文件只位于 `paper_output/code/review_delivery/`。原生产源码、观测数据与 `final_v6a` 结果均未由本子任务修改。

| 原模块 | 审查副本 | 主要职责 |
|---|---|---|
| drying_core.py | dryingCore.py | 有效物性、材料网格、有限体积通量、BDF 积分、密集查询与运行记录 |
| analytic_jacobian.py | analyticJacobian.py | 解析稀疏 Jacobian 与原有导数自检入口 |
| disk_dense.py | diskDense.py | 保持原 BDF 多项式字节的磁盘存储与断点选择 |
| q1_model.py | q1Model.py | Q1 的附录 2 正式参数 |
| q2_model.py | q2Model.py | Q2/Q3 的附录 3 正式参数 |
| q3_model.py | q3Model.py | 从同一个 Q2 Run 计算严格达标报告时刻 |
| q4_model.py | q4Model.py | Q4 的附录 4 与给定半径收缩 |
| export_outputs.py | exportOutputs.py | 官方格式导出、原精度归档与回读核验 |

`buildCamelCopies.py` 根据 AST 绑定识别自有名称，再按词法标记位置替换，保留原始语句排版和运算表达式。共登记 185 个标识符变化，完整映射、源文件与副本 SHA-256 均在同目录 `coreRenameReport.json`。增加了简体中文关键注释，说明单位、材料控制体、物性延拓、Kirchhoff 势差、共享面通量、严格事件、磁盘缓存和导出数据来源。

本次没有改变物理公式、常数、求解容差、默认网格、运算先后、积分器、停止条件或插值。自有函数、局部变量、参数和属性采用 lowerCamelCase；类名保留 PascalCase，常量保留原形式，T、C、D、x 等单字母保留数学意义。

以下接口例外有明确原因：

- SciPy 继承协议 `_call_impl`、`_dense_output_impl` 和 `t_shift`、`t_old` 保持原名。
- `dense_cache` 是通过 `solve_ivp` 注入 `DiskBDF` 的命名参数，保留以匹配外部调用协议。
- NumPy/SciPy/openpyxl 等第三方函数、方法和关键字参数保持原名。
- argparse 的 `args.output_dir`、`args.paper_selfcheck`、`arguments.self_test` 等由原开关生成，保留其外部协议字段。
- 显式 JSON 字典键、CSV 列名、NPZ 数组名均保留原 schema。例如 `Run.eventS` 对应输出字典里的 `event_s`；`fields(materialX=...)` 对应 NPZ 里的 `material_x`。`Settings` 是新 API 的数据类，其 `asdict` 配置键自然使用驼峰字段，不能直接把旧 snake 配置字典传入。历史自检中 `Settings(**settings)` 的配置字典已同步转换。
- 原说明中的历史英文自检叙述和旧 API 示例保留供来源核对；实际审查入口以本轮说明和新模块函数签名为准。

来源路径和独立自检默认输出位置已登记更新为审查副本位置。`getattr(run.model, 'inputRecords', [])` 已同步，防止来源记录因属性改名而变成空列表。原 `Settings` 构造参数字典仅在明确用于配置的上下文改名，未改普通输出字段。

生成脚本把副本 AST 中登记的新名字、路径和配置键反向恢复后，与原模块完整 AST 比较；八模块全部相等。此检查涵盖运算符、常数、分支、循环、调用结构与关键字。哈希报告把该检查记录为 `normalizedAstIdentical: true`，它只证明登记变更范围内的代码结构对应，不单独证明物理模型正确。

`verifyCamelCopies.py` 已实际由 `C:/Python314/python.exe -B` 执行，退出码 0，64 项逐字节一致，警告数 0，实际验证耗时约 3.52 秒。详细环境、时戳、形状和诊断见 `../runtime/coreRenameVerification.json`。验证范围包括：

- Q1、Q23、Q4 三类 N8 模型的初始、非均匀和近等浓度状态；分别比对 RHS、完整小型 Jacobian 和四组物性。
- Q1 的 N8 完整 0–1800 s 求解，在 memory 与 disk 两种存储下分别比较原版和副本的所有接受时刻、所有接受状态。
- 两种存储下查询每个接受断点、其左右 `nextafter` 浮点邻点和 30 s 定时点，密集状态逐字节一致；另对固定物理半径的温湿度查询逐字节比较。

N8 检查验证改名兼容性与存储/调用连接，不能充当正式 N3200/N6400 网格精度验收。此次子任务只做 CLI 运行；没有声称已通过本轮 Visual Studio GUI 复现，也没有声称用户已人工审查。八个核心副本已交主代理开展独立批次求解与正式结果回归。
