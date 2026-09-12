# 当前最终 v5 DOCX 独立静态审查

审查时间（UTC）：2026-09-12T12:58:46.991934+00:00。

文件：`paper_output/final_paper.docx`，311,035 字节。SHA256：`3c0edfdf5946019ac8129afee637880954c86561a6440adc6dc0553483185013`。

结论：本次直接重新读取当前 v5 的 DOCX ZIP/XML，不继承旧 v3 报告；全部 17 项限定范围静态检查符合预期。该结论不代表团队人工批准或科学结论终审。

## 核查结果

| 项目 | 这次实际检查结果 |
|---|---|
| ZIP 完整性 | 18 个成员，CRC 未发现损坏。 |
| 用户前文保留 | 原件 87 个正文段落，41 个非空；31 段原内容/子标题逐字保留；10 个原章标题按明确映射重新编号或改名。无缺失。 |
| 用户原符号表 | 原 22 行、66 个单元格与成品第 1 张表逐格文字及顺序完全一致。 |
| 两条原参考文献 | 原条目全文逐字存在；原有作者/期页错误保留并用 Word 批注提示。 |
| 批注 | 8 条，ID 唯一，每条各有 1 个起点、终点和引用；作者均为“审阅”，首字母为空。 |
| 原生公式 | 203 个 OMML 数学对象，其中 68 个显示公式编号按 (1)–(68) 顺序唯一连续。两个数字统计口径不同。 |
| 章节顺序 | 第 1–7 章 → AI 工具使用声明 → 第 8 章参考文献 → 附录；附录包含 A–E 的推导、计算过程与完整程序。 |
| 表与图主题 | 共 12 张表；6 段图像主题文字；无嵌入图片，符合用户自制图的安排。 |
| 完整源码 | 42 个源文件、9,434 行逐行与对应原始文件完全相同，全部来源 SHA256 与代码附录清单一致。 |
| 纸张和页边距 | 1 节，A4（11906×16838 twip），四边 1417 twip，即 2.5 cm 取整。 |
| 匿名字段与链接 | 创建者/最后修改者/主题/说明为空；8 个批注使用通用作者；全包 XML 未命中已知学校、账号或个人目录；无外部关系。 |
| 修订与隐藏 | document.xml 未发现插入/删除修订节点或隐藏文字标记。 |

## 保留方式及边界

“原文保留”指非空内容和原符号表均有明确对应，不等于保留原空白段落和原版式。原件 153 个 XML 段落包含表格单元格；正文非空段落只有 41 个，统计口径不可混用。原件没有 OMML 公式，成品的 203 个原生数学对象来自后续写作。

10 个改名或重新编号标题如下：

| 原标题 | 当前标题 |
|---|---|
| 问题重述 | 1 问题重述 |
| 问题分析 | 2 问题分析 |
| 模型假设 | 3 模型假设 |
| 符号说明 | 4 符号说明 |
| 模型的建立与求解 | 5 模型的建立与求解 |
| 模型的评价 | 7 模型评价与推广 |
| 6.1模型的优点 | 7.1 模型优点 |
| 6.2模型的不足 | 7.2 模型不足 |
| 6.3模型的推广 | 7.3 改进方向与适用范围 |
| 参考文献 | 8 参考文献 |

原文的科学或书目问题没有静默替换：8 条批注分别提示 BD/BDF 与“精确”措辞、长度 2/25 cm、Q1 扩散系数温度项、材料坐标变化项、附录 4 扩散系数比较条件、干物质骨架迁移、参考文献 [1]、参考文献 [2]。批注全文、正文锚点和计数保存在同名 JSON。

完整代码仍有 8 处通用 D 盘工作区路径。这些文字没有学校或个人身份，但可能影响另一设备运行；本次没有执行代码，不给出可移植性通过结论。

继承的 app.xml 仍保存 Pages=1、Words=0 和 WPS 产品标识，这些属于旧统计/应用信息，不是实际页数或本轮运行版本。实际 PDF 总页数 218 以 render_manifest.json 和分页审查为准；本报告只核查 DOCX 静态结构。

## 自动检查明细

| 检查 | 结果 |
|---|---|
| docx_hash_matches_requested_v5 | 符合预期 |
| zip_crc_ok | 符合预期 |
| all_source_nonempty_paragraphs_preserved_or_heading_mapped | 符合预期 |
| source_31_verbatim_content_or_subheadings_preserved | 符合预期 |
| source_22_row_table_exact_text_and_order_preserved | 符合预期 |
| eight_comments_have_unique_valid_range_and_reference | 符合预期 |
| comment_authors_generic_and_initials_empty | 符合预期 |
| numbered_display_equations_1_through_68_once | 符合预期 |
| native_omml_count_203 | 符合预期 |
| main_chapter_order_and_ai_before_references | 符合预期 |
| six_figure_textual_briefs_and_no_embedded_images | 符合预期 |
| a4_and_2_5cm_margins | 符合预期 |
| anonymous_core_person_fields_empty | 符合预期 |
| no_known_identity_literal_in_all_package_xml | 符合预期 |
| no_external_relationships | 符合预期 |
| complete_42_source_files_9434_lines_equal_embedded_text | 符合预期 |
| no_tracked_insert_delete_or_hidden_body_runs | 符合预期 |
