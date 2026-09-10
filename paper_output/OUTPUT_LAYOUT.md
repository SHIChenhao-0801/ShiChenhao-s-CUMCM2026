# 本届正式输出布局

所有路径相对于 `D:/Document/数学建模/2026CUMCM/`。本文件说明预期用途，目录或文件名出现不表示成果已完成。当前状态以 `paper_output/qa/workflow_guard_report.json` 为准。

| 路径 | 用途 |
| --- | --- |
| paper_output/preflight_report.json、input_manifest.json | 自动库存/可读性/哈希预检，覆盖保留的原始题包 |
| paper_output/context/active_problem_scope.json | A题活动输入范围；B–E、原题包仅库存保留，不能自动加载为A数据 |
| paper_output/step1/ | 结构化审题与歧义 |
| paper_output/plan/ | 模型路线、评分对齐、数据/图表/写作计划 |
| paper_output/data_cleaned/ | 主流程正式读取报告与清洗产物，原始数据不覆写 |
| paper_output/code/ | 正式模型、清洗、导出与验证源码 |
| paper_output/results/ | 实际计算、指标、结论和run_manifest |
| paper_output/figures/、tables/、figure_index.json | 可追溯图表和索引 |
| paper_output/code-review/、logs/ | 软件复现、用户人工审查状态与运行证据 |
| paper_output/drafts/ | 主流程章节、审计和组装稿 |
| paper_output/final_paper_source.md、final_paper.docx | 主流程唯一正式源稿与Word产物；尚未生成 |
| paper_output/paper/ | 论文同学交接/历史稿和导出证据，指定唯一主稿后记录来源，避免双主稿 |
| paper_output/qa/、context/ | 当前门禁、恢复记忆、选择和状态 |
| paper_output/submission/ | 最终匿名PDF、result1–result4、支撑包、哈希清单和提交凭证 |
| notes/A-plan/ | 本轮计划与Skills调度，属于工作安排，不是冻结模型契约 |
| notes/ | 来源、AI参与、交接、规则与日常记录 |
| tmp/cache/ | 可重建缓存 |

预检脚本当前不会自动按选题过滤库存。S1/S3须结合活动范围读取，只采用A题两份原始数据；result*.xlsx始终是提交模板。原题包format2026.doc的规则转换/核验列为后续待办，S0文件准入PASS不代表该旧DOC已被完整解析。
