# 论文 CSV 独立逐格校验交接

2026-09-10 UTC，状态：实现与四问真实小网格导出自检 PASS。所有自检 Run 已依次 close；这是导出保真检验，不能替代正式细网格精度验收、Visual Studio GUI 复现或用户人工审查。

当前 `paper_output/code/modeling/export_outputs.py` SHA256：`7111606498554e18e2e007a58e0d5161b5fd209cde98b949a245981eb403c21b`。

修改前归档 `paper_output/code/versions/export_outputs_v2.py` SHA256：`7ad751b0d66c9a3956e4717c6d7aeeecf95e37907f126340100317b5a077af62`。

本次只修改 exporter 源码，未修改核心求解器、主生产入口、图模块、索引、门禁或主记忆。自检使用冻结的 core v6，Python 3.14，单进程，OPENBLAS_NUM_THREADS=1、OMP_NUM_THREADS=1，N=40，各问结束后释放 Run。

新增 `_validate_paper_tables` 独立重建题目时间网格，读取 CSV 表头并验证物理半径列，直接重新调用 live `Run.fields`。它不调用生成器 `_paper_tables`，不复用生成期数组，也不从 60 秒归档插值。Q4 的表面独立查询 `material_x=1`，半径独立调用 `run.model.radius`；固定物理半径大于实际半径的单元格必须为空。

Q3/Q4 的最终论文行独立重新调用 `q3_model.completion` 得到向上报告时刻，并用真实报告秒数查询原精度解。manifest 的 `paper_table_time_contract` 记录 `reported_time_s`、`reported_time_h`、`reported_drying_time_h`、`critical_event_s`、`conservative_post_verification_s` 等字段。论文末行采用报告时刻；工作簿保留整个求解区间至事后严格核验终点，两者含义明确区分。

四位小数既作为 CSV 格式契约，也作为数值回读舍入契约；回读值必须与独立求解查询值舍入后的结果一致。误差报告另记未舍入原值到保存值的差，最大值均小于 5e-5。它不保证四位小数的物理预测精度，也不能发现没有改变四位小数显示结果的微小源值扰动。

| 自检问 | XLSX 每表数据行 | XLSX 回读单元格 | 论文 CSV 独立检查单元格 | XLSX 字节 | 结果 |
|---|---:|---:|---:|---:|---|
| Q1 | 1801 | 79244 | 84 | 391166 | PASS |
| Q2，加速导出验证 | 16103 | 708532 | 72 | 3605431 | PASS |
| Q3 | 3451 | 75922 | 60 | 339128 | PASS |
| Q4，两表 | 3069 | 76725 | 81 | 278102 | PASS |

Q2 仅为控制自检成本设 `constant_D=2e-8`、`beta=8e-6`，其实际事件发生于 16100.416298198237 s，完整逐秒导出覆盖 0..16102 s。它涵盖前三小时及实际事件之后的核验区间，无静默裁段；这些数值不是正式 Q2 物理结论。其他问采用各自名义物理设定，但 N=40 仍仅作为导出检验。

负例测试只修改自检 CSV 的独立副本，且同步更新副本的记录哈希，保证拒绝原因来自逐格值或契约而不是简单哈希不匹配。以下六类均正确拒绝：Q1 温度值增加 0.01、Q2 水分值增加 0.01、Q3 末行时间减少 0.001 h、Q4 域外空白填成 0.0000、Q4 实际表面值删为空白、Q4 半径增加 0.01 cm。具体错误定位、故障副本路径和哈希均在报告内。

完整报告 `paper_csv_selfcheck_report.json` SHA256：`7263543e03037a21f1906858e0a3c1f60952c4fa09b9a775663d920da5013076`。各问目录另存独立 `.validation.json` 与 `.export.json`。

后续由主生产持有正式 live Run 调用同一 `export_question` 和 `validate_exports`；正式 Q2 全程逐秒文件与支撑包体积必须实际测量，不可用本自检体积推定通过。正式源码的 Visual Studio GUI 复现及人工审查仍待主代理执行和用户核实。
