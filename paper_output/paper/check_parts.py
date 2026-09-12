# -*- coding: utf-8 -*-
"""检查各压缩分片是否完整保留了公式。"""
from pathlib import Path
import re

D = Path(r"D:\Document\数学建模\2026CUMCM\paper_output\drafts\A题正文")
DOLLAR = chr(36)

for name in ["_part1.md", "_part2.md", "_part3.md", "_part3b.md", "_part3c.md", "_part4.md"]:
    f = D / name
    if not f.exists():
        print("%-14s 缺失" % name)
        continue
    t = f.read_text(encoding="utf-8")
    n_block = t.count(DOLLAR + DOLLAR)
    n_tag = len(re.findall(r"\\tag\{", t))
    n_inline = len(re.findall(r"(?<!" + re.escape(DOLLAR) + r")"
                              + re.escape(DOLLAR) + r"[^" + re.escape(DOLLAR) + r"]+"
                              + re.escape(DOLLAR) + r"(?!" + re.escape(DOLLAR) + r")", t))
    n_frac = t.count("\\frac")
    n_part = t.count("\\partial")
    heads = re.findall(r"(?m)^#{1,3} .+", t)
    print("%-14s 字符%7d | $$块%3d | \\tag%3d | 行内公式%4d | \\frac%3d | \\partial%3d | 标题%3d"
          % (name, len(t), n_block, n_tag, n_inline, n_frac, n_part, len(heads)))
