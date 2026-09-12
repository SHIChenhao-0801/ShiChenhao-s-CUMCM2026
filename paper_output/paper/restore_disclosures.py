# -*- coding: utf-8 -*-
"""从 v2 源稿精确恢复被压缩过程删除的三处"严谨性披露"。

背景：第 8–11 章压到 59.77% 时，为达标删除了三段内容。这三段不是冗余，
而是与评分点（不确定性披露、主动披露不完美）直接相关：
  1. 10.11 节 四位小数显示末位披露（v2 第 1736 行附近）
  2. 8.4 节 "逐时 argmax 是否恒为圆心"的浮点舍入说明（v2 第 1125 行附近）
  3. 10.5 节 符号错误被质量守恒守卫抓住的实例（v2 第 1448 行附近）
  4. 11.2 节 潜热核对的 kJ 绝对值（v2 第 1793 行附近）

用法：python restore_disclosures.py           # 试运行，只打印
      python restore_disclosures.py --apply   # 写回 _part3.md
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "paper_output" / "drafts" / "A题正文"
SRC = D / "A题_论文正文_v2.md"
TGT = D / "_part3.md"

#: (锚点正则, 恢复用锚点正则, 取多少行上下文, 说明)
BLOCKS = [
    (r"数值解的显示末位在个别网格点上可能随求解器容差设置变化",
     r"数值解的显示末位在个别网格点上", 3, "四位小数显示末位披露"),
    (r"关于.逐时 argmax 是否恒为圆心.的严谨表述",
     r"逐时 argmax 是否恒为圆心", 10, "argmax 浮点舍入说明"),
    (r"一个被质量守恒守卫抓住的真实错误",
     r"一个被质量守恒守卫抓住的真实错误", 6, "符号错误实例披露"),
    (r"497\.705 kJ",
     r"\| 问题二、三 \| 497", 5, "潜热核对 kJ 绝对值"),
]


def grab(src: str, anchor: str, nlines: int) -> str:
    lines = src.splitlines()
    for i, ln in enumerate(lines):
        if re.search(anchor, ln):
            return "\n".join(lines[i:i + nlines]).strip()
    return ""


def main() -> int:
    apply = "--apply" in sys.argv
    src = SRC.read_text(encoding="utf-8")
    tgt = TGT.read_text(encoding="utf-8")

    plan = []
    for probe, anchor, n, label in BLOCKS:
        block = grab(src, anchor, n)
        already = bool(re.search(probe, tgt))
        plan.append((label, len(block), already, block))

    print("%-24s %8s %s" % ("待恢复项", "字符", "当前状态"))
    for label, ln, already, _ in plan:
        print("%-24s %8d %s" % (label, ln, "已在分片内" if already else "【缺失，需恢复】"))

    todo = [p for p in plan if not p[2] and p[1] > 0]
    if not todo:
        print("\n无需恢复：全部内容已在分片中。")
        return 0
    if not apply:
        print("\n试运行。加 --apply 写回 %s" % TGT.name)
        for label, ln, _, block in todo:
            print("\n----- %s -----\n%s" % (label, block[:400]))
        return 0

    # 写回：把缺失块追加到对应章节末尾（保守做法，不破坏现有结构）
    out = tgt.rstrip()
    marker = "\n\n<!-- 以下为恢复的严谨性披露，请排版时并入对应小节 -->\n\n"
    body = "\n\n".join(b for _, _, _, b in todo)
    out = out + marker + body + "\n"
    TGT.write_text(out, encoding="utf-8")
    print("\n已写回 %s（新增 %d 字符）" % (TGT.name, len(out) - len(tgt)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
