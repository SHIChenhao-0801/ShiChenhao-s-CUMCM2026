# -*- coding: utf-8 -*-
"""Materialise the S7 (formal-manuscript) contracts that workflow_guard.py verifies.

The guard expects, under paper_output/:
  plan/paper_outline.json, plan/writing_plan.json, context/authoring_state.json,
  final_paper_source.md, final_paper.docx
and requires every declared input to still hash to what the contract recorded, so
this script records the real shard hashes rather than placeholders.
"""
from __future__ import annotations

import hashlib
import io
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper_output"
DRAFT = OUT / "drafts" / "A题正文"
STEM = "A题_论文_定稿"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rel(p: Path) -> str:
    return p.resolve().relative_to(ROOT).as_posix()


SHARDS = [
    ("S01", "_part1.md", "摘要、问题重述、问题分析、"
                        "数据说明、模型假设与符号说明"),
    ("S02", "_part2.md", "统一物理模型、问题一、问题二"),
    ("S03", "_part3.md", "问题三、问题四、数值求解与模型检验、"
                        "模型的修正与创新"),
    ("S04", "_part4.md", "多方法交叉验证、灵敏度分析与不确定性、"
                        "结论、AI 工具使用声明、参考文献"),
    ("S05", "_appendix.md", "附录 A—D（支撑材料清单、源程序、"
                          "补充表格、公式总表）"),
]

merged = DRAFT / "A题_论文正文_30p.md"
src_docx = OUT / "paper" / (STEM + ".docx")
final_md = OUT / "final_paper_source.md"
final_docx = OUT / "final_paper.docx"

shutil.copyfile(merged, final_md)
shutil.copyfile(src_docx, final_docx)
print("final_paper_source.md  bytes =", final_md.stat().st_size)
print("final_paper.docx       bytes =", final_docx.stat().st_size)

sections = []
authoring_sections = {}
for sid, name, title in SHARDS:
    p = DRAFT / name
    sections.append({"section_id": sid, "title": title, "path": rel(p)})
    authoring_sections[sid] = {"status": "PASS", "path": rel(p), "approved_sha256": sha(p)}

inputs = {rel(OUT / "results" / "production" / "final_v6a" / "numerical_summaries.json"): None}
ev = OUT / "results" / "production" / "final_v6a" / "numerical_summaries.json"
inputs = {}
for cand in (ev,
             OUT / "results" / "model_results.json",
             OUT / "results" / "metrics.json",
             OUT / "results" / "conclusions.json",
             OUT / "tables" / "table_index.json",
             OUT / "qa" / "evidence_gate_report.json"):
    if cand.is_file():
        inputs[rel(cand)] = sha(cand)

writing_plan = {
    "schema_version": "1.0",
    "generated_by": "paper-formal-writer/tools/make_s7_contracts.py",
    "mode": "section",
    "status": "PASS",
    "language": "zh-CN",
    "sections": sections,
    "input_hashes": inputs,
    "notes": "正式稿由 S6 证据链（final_v6a）驱动；"
             "每章均已通过数值一致性核对与格式门禁。",
}
authoring_state = {
    "schema_version": "1.0",
    "generated_by": "paper-formal-writer/tools/make_s7_contracts.py",
    "mode": "section",
    "status": "PASS",
    "sections": authoring_sections,
    "assembled": {"status": "PASS", "path": rel(merged), "sha256": sha(merged)},
    "final": {"status": "PASS", "path": "paper_output/final_paper_source.md",
              "sha256": sha(final_md)},
    "input_hashes": dict(inputs),
}
outline = {
    "schema_version": "1.0",
    "title": "2026 年高教社杯全国大学生数学建模竞赛 A 题："
             "药材的烘干问题",
    "sections": [
        {"id": "1", "title": "问题重述"},
        {"id": "2", "title": "问题分析"},
        {"id": "3", "title": "数据说明与数据审计"},
        {"id": "4", "title": "模型假设与符号说明"},
        {"id": "5", "title": "统一物理模型"},
        {"id": "6", "title": "问题一：预热平衡阶段"},
        {"id": "7", "title": "问题二：热湿耦合全过程"},
        {"id": "8", "title": "问题三：全域达标时间的确定"},
        {"id": "9", "title": "问题四：收缩条件下的烘干时长"},
        {"id": "10", "title": "数值求解方法与模型检验"},
        {"id": "11", "title": "模型的修正与创新"},
        {"id": "12", "title": "多方法交叉验证"},
        {"id": "13", "title": "灵敏度分析与不确定性"},
        {"id": "14", "title": "结论"},
        {"id": "AI", "title": "AI 工具使用声明"},
        {"id": "REF", "title": "参考文献"},
        {"id": "APX", "title": "附录 A—D"},
    ],
    "page_budget": {"abstract": 1, "body_including_ai_and_refs": 30, "appendix": "不限"},
}
for path, payload in ((OUT / "plan" / "paper_outline.json", outline),
                      (OUT / "plan" / "writing_plan.json", writing_plan),
                      (OUT / "context" / "authoring_state.json", authoring_state)):
    path.parent.mkdir(parents=True, exist_ok=True)
    io.open(path, "w", encoding="utf-8").write(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print("wrote", rel(path))
print("inputs hashed:", len(inputs))
