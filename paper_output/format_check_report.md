# Formal Paper Format Check Report

- Status: `FAIL`
- Acceptance scope: `NOT_ACCEPTED`
- Generated at: `2026-09-12T18:16:52`
- Source: `paper_output/final_paper_source.md`
- DOCX: `paper_output/final_paper.docx`
- Effective chars: `41013`
- CJK chars: `17600`
- Figures in index: `6`
- Tables in index: `7`
- Tables marked for paper: `7`
- Source formulas: `767`
- Native Word equations: `744`
- Body citations: `3`
- Render QA: `FAIL`

## Failures
- S7 写作门禁未通过：authoring state schema_version is not 2.2
- S7 写作门禁未通过：missing delivery scope; rerun prepare_authoring.py
- S7 写作门禁未通过：writing plan envelope is not Standard 2.2 PASS
- 正文引用了参考文献表中不存在的编号：[0]
- 参考文献表存在未在正文引用的条目：[2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
- missing delivery scope; rerun prepare_authoring.py
- 缺少正式论文结构：3 模型假设
- 缺少正式论文结构：5 模型的建立与求解
- 缺少正式论文结构：6 模型检验
- 缺少正式论文结构：7 模型评价
- 缺少正式论文结构：8 参考文献
- 缺少 5.1.1 建模思路
- 缺少 5.1.2 变量定义与公式推导
- 缺少 5.1.3 求解算法
- 缺少 5.1.4 结果分析
- 缺少 5.1.5 模型检验或灵敏度分析
- 5.1 缺少 Step 1/Step 2 形式的算法步骤
- 缺少 5.2.1 建模思路
- 缺少 5.2.2 变量定义与公式推导
- 缺少 5.2.3 求解算法
- 缺少 5.2.4 结果分析
- 缺少 5.2.5 模型检验或灵敏度分析
- 5.2 缺少 Step 1/Step 2 形式的算法步骤
- 缺少 5.3.1 建模思路
- 缺少 5.3.2 变量定义与公式推导
- 缺少 5.3.3 求解算法
- 缺少 5.3.4 结果分析
- 缺少 5.3.5 模型检验或灵敏度分析
- 5.3 缺少 Step 1/Step 2 形式的算法步骤
- 缺少 5.4.1 建模思路
- 缺少 5.4.2 变量定义与公式推导
- 缺少 5.4.3 求解算法
- 缺少 5.4.4 结果分析
- 缺少 5.4.5 模型检验或灵敏度分析
- 5.4 缺少 Step 1/Step 2 形式的算法步骤
- figure_index.json 中的图片未在正文引用：fig_A_environment
- figure_index.json 中的图片未在正文引用：fig_A_radius
- figure_index.json 中的图片未在正文引用：fig_q1_profiles
- figure_index.json 中的图片未在正文引用：fig_q2_profiles
- figure_index.json 中的图片未在正文引用：fig_q3_drying
- figure_index.json 中的图片未在正文引用：fig_q4_drying
- table_index.json 中的表格未在正文引用：q1_paper_temperature
- table_index.json 中的表格未在正文引用：q1_paper_moisture
- table_index.json 中的表格未在正文引用：q2_paper_temperature
- table_index.json 中的表格未在正文引用：q2_paper_moisture
- table_index.json 中的表格未在正文引用：q3_paper_moisture
- table_index.json 中的表格未在正文引用：q4_paper_moisture
- table_index.json 中的表格未在正文引用：q4_paper_radius
- Word 中没有可识别标题样式，标题结构可能未正确写入。
- No Word heading styles were detected while markdown headings exist
- DOCX contains empty tables: 3
- Word 原生公式数量不足：744 < 767。禁止用普通文本冒充公式。
- 渲染 PDF 无法读取：ValueError: missing delivery scope; rerun prepare_authoring.py
- missing delivery scope; rerun prepare_authoring.py

## Warnings
- 正文有效字数超过建议上限：41013 > 22000

## Question Coverage
- Q1: `FAIL`
  - 缺少 5.1.1 建模思路
  - 缺少 5.1.2 变量定义与公式推导
  - 缺少 5.1.3 求解算法
  - 缺少 5.1.4 结果分析
  - 缺少 5.1.5 模型检验或灵敏度分析
  - 5.1 缺少 Step 1/Step 2 形式的算法步骤
- Q2: `FAIL`
  - 缺少 5.2.1 建模思路
  - 缺少 5.2.2 变量定义与公式推导
  - 缺少 5.2.3 求解算法
  - 缺少 5.2.4 结果分析
  - 缺少 5.2.5 模型检验或灵敏度分析
  - 5.2 缺少 Step 1/Step 2 形式的算法步骤
- Q3: `FAIL`
  - 缺少 5.3.1 建模思路
  - 缺少 5.3.2 变量定义与公式推导
  - 缺少 5.3.3 求解算法
  - 缺少 5.3.4 结果分析
  - 缺少 5.3.5 模型检验或灵敏度分析
  - 5.3 缺少 Step 1/Step 2 形式的算法步骤
- Q4: `FAIL`
  - 缺少 5.4.1 建模思路
  - 缺少 5.4.2 变量定义与公式推导
  - 缺少 5.4.3 求解算法
  - 缺少 5.4.4 结果分析
  - 缺少 5.4.5 模型检验或灵敏度分析
  - 5.4 缺少 Step 1/Step 2 形式的算法步骤

## DOCX Structure
- exists: `True`
- package_ok: `True`
- paragraph_count: `496`
- table_count: `111`
- table_cell_count: `1827`
- empty_table_count: `3`
- image_count: `11`
- inline_shape_count: `11`
- heading_count: `0`
- sample_headings: `[]`
- nonspace_text_chars: `29203`
- native_omml_count: `744`
- display_omml_count: `0`
- math_text_chars: `6749`
- text_preview: `2026 年高教社杯全国大学生数学建模竞赛
A 题　药材的烘干问题
摘要
本文针对长 25 cm、半径 2 cm 的圆柱形药材,建立轴对称一维径向热湿耦合偏微分方程模型:傅里叶导热定律描述热量传递,干基菲克扩散本构描述水分迁移,由质量守恒导出含水率演化方程;第四问的收缩几何用材料坐标变换映射为固定计算域。空间离散用守恒型节点对偶有限体积与 Kirchhoff 浓度势(精确积分强非线性含水率),时间推进用变阶变步长隐式 BDF/NDF 与解析稀疏 Jacobian,达标时刻由空`

## Visual QA
- status: `FAIL`
- source_heading_count: `135`
- failure: Word 中没有可识别标题样式，标题结构可能未正确写入。
- failure: No Word heading styles were detected while markdown headings exist
- failure: DOCX contains empty tables: 3

## Formula QA
- status: `FAIL`
- source_formula_count: `767`
- source_display_formula_count: `78`
- native_omml_count: `744`
- native_display_omml_count: `0`
- failures: `['Word 原生公式数量不足：744 < 767。禁止用普通文本冒充公式。']`
- warnings: `[]`

## Citation QA
- bibliography_entry_count: `14`
- body_citation_count: `3`
- body_citation_ids: `[0, 1]`
- uncited_bibliography_ids: `[2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]`
- unknown_body_citation_ids: `[0]`

## Render QA
- mode: `required`
- status: `FAIL`
- libreoffice: `D:\Document\数学建模\tools\libreoffice\app\program\soffice.com`
- pdf: `paper_output/qa/rendered/final_paper.pdf`
- page_count: `38`
- extracted_text_chars: `40741`
- returncode: `0`
- stdout: `Could not find platform independent libraries <prefix>
convert D:\Document\��ѧ��ģ\2026CUMCM\paper_output\final_paper.docx as a Writer document -> D:\Document\��ѧ��ģ\2026CUMCM\paper_output\qa\rendered\final_paper.pdf using filter : writer_pdf_Export
`
- pdf_sha256: `3fc1a19ead1b5d8ea6117020264ee3976c4c31adb59d170cf893cf97441c1ebe`
- pdf_bytes: `2810089`
- text_preview: `1
2026 年高教社杯全国大学生数学建模竞赛
A 题　药材的烘干问题
摘要
本文针对长 25 cm、半径 2 cm 的圆柱形药材,建立轴对称一维径向热湿耦合偏微分方程模型:傅里
叶导热定律描述热量传递,干基菲克扩散本构描述水分迁移,由质量守恒导出含水率演化方程;第四问的收
缩几何用材料坐标变换映射为固定计算域。空间离散用守恒型节点对偶有限体积与 Kirchhoff 浓度势
(精确积分强非线性含水率),时间推进用变阶变步长隐式 BDF/NDF 与解析稀疏 Jacobian,达`
