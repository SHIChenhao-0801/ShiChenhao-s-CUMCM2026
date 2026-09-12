# Formal Paper Format Check Report

- Status: `PASS`
- Acceptance scope: `STANDARD_COMPETITION_CHECKS`
- Generated at: `2026-09-12T20:48:03`
- Source: `paper_output/final_paper_source.md`
- DOCX: `paper_output/final_paper.docx`
- Effective chars: `17061`
- CJK chars: `11205`
- Figures in index: `0`
- Tables in index: `7`
- Tables marked for paper: `7`
- Source formulas: `203`
- Native Word equations: `203`
- Body citations: `6`
- Render QA: `PASS`

## Warnings
- 图数量少于展示样例建议值：0 < 5
- Word 标题数量明显少于 Markdown 标题：106 < 293

## Question Coverage
- Q1: `PASS`
- Q2: `PASS`
- Q3: `PASS`
- Q4: `PASS`

## DOCX Structure
- exists: `True`
- package_ok: `True`
- paragraph_count: `9897`
- table_count: `12`
- table_cell_count: `527`
- empty_table_count: `0`
- image_count: `0`
- inline_shape_count: `0`
- heading_count: `106`
- sample_headings: `['摘要', '1 问题重述', '1.1问题背景', '1.2问题提出', '2 问题分析', '2.1问题一分析', '2.2问题二分析', '2.3问题三分析', '2.4问题四分析', '3 模型假设', '4 符号说明', '5 模型的建立与求解']`
- nonspace_text_chars: `406639`
- native_omml_count: `203`
- display_omml_count: `0`
- math_text_chars: `3445`
- text_preview: `考虑物性变化与径向收缩的药材热湿耦合模型及数值验证
摘要
药材热风烘干同时涉及温度传递、水分迁移及尺寸变化，表面状态难以直接代表内部干燥程度。针对圆柱形药材的四个问题，本文基于题给环境观测和物性关系，建立一维径向有效热湿耦合模型，并以全域最大干基含水率确定烘干结束时间。模型区分有效显热容量与守恒干物质密度，将气固含水率映射、观测窗后环境平台和同比径向收缩作为明确闭合；在环形控制体上采用Kirchhoff浓度势处理非线性扩散，配合解析稀疏Jacobian与隐式BDF求解。
针对`

## Visual QA
- status: `PASS`
- source_heading_count: `293`
- warning: Word 标题数量明显少于 Markdown 标题：106 < 293

## Formula QA
- status: `PASS`
- source_formula_count: `203`
- source_display_formula_count: `68`
- native_omml_count: `203`
- native_display_omml_count: `0`
- failures: `[]`
- warnings: `[]`

## Citation QA
- bibliography_entry_count: `6`
- body_citation_count: `6`
- body_citation_ids: `[1, 2, 3, 4, 5, 6]`
- uncited_bibliography_ids: `[]`
- unknown_body_citation_ids: `[]`

## Render QA
- mode: `required`
- status: `PASS`
- libreoffice: `D:\Document\数学建模\tools\libreoffice\app\program\soffice.exe`
- returncode: `0`
- pdf: `paper_output/qa/manuscript_20260912/rendered/final_paper.pdf`
- pdf_sha256: `93cfe62b5db0ec8627be6b7d51170acd916b2b5613e4f3182663f13830539cd4`
- pdf_bytes: `4716057`
- page_count: `218`
- extracted_text_chars: `411350`
- paper_scope: `{'counted_main_pages': 22, 'total_pages': 218, 'delivery_mode': 'competition', 'boundaryMethod': 'exact standalone manuscript appendix heading; numbered task attachments are body references', 'abstract_pages': 1, 'body_including_AI_references_pages': 21, 'abstract_to_references_pages': 22, 'appendix_start_page': 23, 'seminar_body_max': 30}`
- renderer: `packaged documents/render_docx.py; SHA-bound reuse`
- manifest: `paper_output\qa\manuscript_20260912\render_manifest.json`
