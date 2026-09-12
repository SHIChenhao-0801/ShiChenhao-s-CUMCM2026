# 最终正文保留独立审计

审查时间（UTC）：2026-09-12T14:09:47.007372+00:00。

唯一正文权威：`paper_output/qa/manuscript_revision_20260912/user_edited_source.docx`，SHA256 `0c8bb744b568fd751dc0ad0d883f69b5f895a74b9f8fcb3666b99975db7b05ee`。

当前最终稿：`paper_output/paper/A题_论文_公式规范与精简附录版.docx`，SHA256 `bbc16aae9a8aa2efb3c20662d8ac91d809a464096700b81d80fb3b3fb2a0518e`。

结论：正文完整保留，仅发生已授权的一个符号格笔误修复和6个绘图标记前缀替换。原文192段与9表顺序一致，19个原生公式内容及结构一致。读取前后两输入哈希未变。

按用户最新决定，正文 [3]–[6] 标号及引文句全部保留；文末仍只有用户保留的两条参考文献，四处未对应引用仅增加批注。此规则覆盖早先“删除引用”的临时安排。

| 核对项 | 实际结果 |
|---|---|
| 正文段落 | 192段一一对应；186段可见文字完全一致，6段仅改绘图位置前缀，绘图说明全文不变。 |
| 正文表格 | 9表的行列顺序和文本一致，仅第1表第16行第1列 B=ρeff··cp 改为 B=ρeff·cp。 |
| 原生公式 | 式(1)–(19)逐一比对文字、分式、上下标和表达式树，全部一致；字体、nor等显示属性允许变化。 |
| 正文引用 | 段落索引43、48、57、61的全文与用户稿完全相同；[5]、[3]、[4]、[6]均保留。 |
| 引用批注 | 新增4条“当前参考文献表没有对应条目”批注，分别锚定上述4段。 |
| 旧批注 | 删除已解决的长度、文献[2]作者省略2条；更新骨架限定、BDF拼写2条；另4条原批注全文不变。 |
| 当前批注结构 | 共10条，每条ID唯一，各有1个起点/终点/引用，正文锚点有效。 |

用户保存Word后批注编号曾重排；被移除的原ID7在新增批注时被复用。因此本审计以批注全文与锚点核对删除和新增，不误把数字ID复用视为旧批注未删除。

## 绑定正文指纹

| 指纹 | SHA256 |
|---|---|
| sourceCanonicalBodySha256 | `8a31e2d9703a8c2b20b77c369a96a530f2ca012a3602ada79d1d3274bada5476` |
| expectedAuthorizedFinalBodySha256 | `c34bc6a2be709f6e74bb81f536c2df90d0c16bae9621a2110de0a43a53a0d8d1` |
| actualFinalBodySha256 | `c34bc6a2be709f6e74bb81f536c2df90d0c16bae9621a2110de0a43a53a0d8d1` |

期待授权后正文指纹与当前正文指纹完全一致。JSON 保留逐段、逐表、逐公式结果、全部当前批注及锚点。

## 限定检查结果

| 检查 | 结果 |
|---|---|
| source_is_frozen_user_authority | 符合预期 |
| final_is_requested_v5 | 符合预期 |
| source_and_final_zip_crc_ok | 符合预期 |
| same_192_paragraphs_and_order | 符合预期 |
| only_six_marker_prefixes_differ_in_paragraphs | 符合预期 |
| six_figure_descriptions_exactly_retained | 符合预期 |
| nine_tables_same_except_one_permitted_cell | 符合预期 |
| nineteen_math_expressions_semantically_identical | 符合预期 |
| expected_body_blocks_exact_match | 符合预期 |
| references_3_to_6_body_text_retained | 符合预期 |
| four_new_comments_correctly_anchored | 符合预期 |
| two_resolved_old_comments_removed_by_content | 符合预期 |
| two_partial_comments_updated_at_same_anchor | 符合预期 |
| four_remaining_old_comments_unchanged | 符合预期 |
| ten_current_comments_all_have_valid_ranges | 符合预期 |
| bibliography_remains_two_entries_exact_user_text | 符合预期 |

本报告不替代科学模型终审、团队人工批准或附录审查；视觉分页检查另行保存。

## revision_v5 重新核验

表头时间/h和式(19)的字体修订后，对新DOCX重新读取ZIP/XML，并重建了全部正文块、19个公式和10条批注的文本/范围/锚点。201个正文块与从用户快照独立施加允许改动得到的预期结果完全一致；正文指纹仍为 `c34bc6a2be709f6e74bb81f536c2df90d0c16bae9621a2110de0a43a53a0d8d1`。新一轮读取前后输入哈希一致。此前v4记录单独保留在JSON的 priorVersionReview，不用旧文件哈希指代当前成品。
