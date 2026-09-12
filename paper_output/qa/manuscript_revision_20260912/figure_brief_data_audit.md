# 六项绘图说明数据核查

结果：PASS_DATA_AND_BRIEF_AUDIT。只写绘图清单及本 QA，不绘图、不运行模型、不改 DOCX 或构建器、不写 Git。

- 当前用户 DOCX 的六处绘图原文与 user_edits_review.json 完全一致，逐项章节及位置已提取。
- 页码已根据 revision_v5 的实际渲染核实为9、11、12、15、18、19；插入图片后页码可能变化，须再核对。
- 核验正式 Q1/Q23=N3200、Q4=N6400；首图121个径向点、Q23保存3452×21、Q4保存3069×21，区分生产网格与输出抽样。
- 图4 max_C 来自全体生产节点；根与报告点分别从 Q23 completion 取值。报告时刻不在 sampled_solution.npz 中，但有真实 summary 点；206902秒是后验终点，不是报告时刻。0–60小时仅为轴范围，末段留空。
- 环境 CSV 241点至4小时，末点50.165°C、0.04986；t>4小时才切50°C、0.05，明确观测与延拓跳变。
- 半径 CSV 145点至72小时；Q4材料坐标21个输出点按本时刻R映射，六个建议时刻均精确存在且含真实表面。
- 图6六个情景全部 intervals=800、latentFraction=0、eventReached=true、computed_event_only。统一使用 scenarios 顶层 event_h；不混入 frozenBaselineForComparison 或正式生产值。六行全精度值见 JSON。
- 情景 JSON 的旧吸附闭合/基线下界叙述不采纳；仅作未标定经验边界阻力情景。
- 用户最新参考文献选择只作约束记录，正文 [3]–[6] 不由本任务更改。

全部17个主要数据文件的存在性、SHA-256及NPZ形状已记录。正文原件只读SHA和六段原文也已记录。
