# Workflow Guard Report

- Target step: `S8`
- Status: `INCOMPLETE`
- Generated at: `2026-09-12T18:22:34`
- Current step: `S7`
- Next step: `S8`
- Recommended skill: `paper-formal-writer`
- Next action: 运行 check_paper_format.py 并修复格式门禁失败项。

## Steps
- S0 准入预检: `PASS`
- S1 审题分析: `PASS`
- S2 模型路线: `PASS`
- S3 数据与图表计划: `PASS`
- S4 建模代码: `PASS`
- S5 结果证据: `PASS`
- S6 证据门禁: `PASS`
- S7 正式稿: `PASS`
- S8 格式门禁: `FAIL`
  - format_check_report.json status 不是 PASS。
  - missing delivery scope; rerun prepare_authoring.py
  - 格式门禁报告已过期，输入发生变化：paper_output/final_paper_source.md
  - 格式门禁报告已过期，输入发生变化：paper_output/final_paper.docx
  - 格式门禁报告已过期，输入发生变化：paper_output/context/authoring_state.json
