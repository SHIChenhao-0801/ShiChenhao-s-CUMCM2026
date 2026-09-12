# -*- coding: utf-8 -*-
"""修复 _part3.md：用 _part3c.md 的第 11 章替换受损的第 11 章，并校验表 27/28/29/32 与式 (62)—(71)。

背景：第 10、11 章的压缩由不同子代理并行进行，其中一次就地改写使 _part3.md
的第 11 章丢失了表 28（等温线 p 族）并出现标题粘连。本脚本以 _part3c.md
（第 11 章专用版本）为准修复，并逐项校验受保护内容是否齐备。
"""
from pathlib import Path
import re
import sys

D = Path(r"D:\Document\数学建模\2026CUMCM\paper_output\drafts\A题正文")
SRC = D / "_part3.md"
FIX = D / "_part3c.md"
OUT = D / "_part3_fixed.md"

#: 第 11 章必须存在的受保护内容
MUST_TABLES = ["表 27", "表 28", "表 29", "表 32"]  # 表 26 在第 9 章，不在本章
MUST_NUMBERS = [
    "1.2112029565", "97.83", "2.1683", "2.03 μm", "21.59", "21.73",
    "+1.24%", "+2.54%", "+5.26%", "+2.60%", "+5.23%", "+10.56%",
    "60.497191", "56.484445", "1.09", "1.99907", "129.8452", "51.0910",
    "60.65%", "131.6198", "1.37%", "0.6073", "0.600",
    "+1.69%", "+3.74%", "+8.51%", "+13.87%",
    "+1.02%", "+2.23%", "+5.04%", "+8.27%",
]
MUST_TAGS_11 = [str(i) for i in range(62, 72)]


def tags(text: str) -> list[str]:
    return re.findall(r"\\tag\{([^}]+)\}", text)


def main() -> int:
    src = SRC.read_text(encoding="utf-8")
    fix = FIX.read_text(encoding="utf-8")

    i11 = src.find("# 11　模型的修正与创新")
    i12 = src.find("# 12　多方法交叉验证")
    if i11 < 0:
        print("无法定位第 11 章起点")
        return 1
    if i12 < 0:
        # 该分片当前只到第 11 章末，用文件末尾作边界
        i12 = len(src)
        print("注意：本分片不含第 12 章，第 11 章边界取文件末尾")
    old11 = src[i11:i12]
    print("原第 11 章: %d 字符, \\tag %d, 表 28 %s"
          % (len(old11), len(tags(old11)), "有" if "表 28" in old11 else "【缺失】"))

    # 修复拼接：把 _part3c.md 的第 11 章接回第 10 章之后。
    # 注意：必须保留原文件的分隔符（拼接处原本是 "\n---\n"），
    # 不能补 \n\n，否则会插入空行、并且把标题行从换行后挤开。
    tail = src[i12:] if i12 < len(src) else ""
    merged = src[:i11].rstrip("\n") + "\n" + fix.lstrip("\n") + tail
    if not merged.endswith("\n"):
        merged += "\n"
    OUT.write_text(merged, encoding="utf-8")

    # 校验
    j11 = merged.find("# 11　模型的修正与创新")
    j12 = merged.find("# 12　多方法交叉验证")
    ch11 = merged[j11:j12 if j12 > 0 else len(merged)]
    ok = True
    print("\n--- 修复后校验 ---")
    print("第 11 章: %d 字符, \\tag %d" % (len(ch11), len(tags(ch11))))
    miss_t = [t for t in MUST_TABLES if t not in ch11]
    print("受保护表: %s" % ("全部在" if not miss_t else "缺失 " + ", ".join(miss_t)))
    ok &= not miss_t
    miss_n = [n for n in MUST_NUMBERS if n not in ch11]
    print("关键数值: %s" % ("全部在" if not miss_n else "缺失 " + ", ".join(miss_n)))
    ok &= not miss_n
    miss_g = [t for t in MUST_TAGS_11 if t not in tags(ch11)]
    print("式 (62)—(71): %s" % ("全部在" if not miss_g else "缺失 " + ", ".join(miss_g)))
    ok &= not miss_g

    glued = re.findall(r"[^\n]## \d", merged)
    print("标题粘连: %s" % ("无" if not glued else "%d 处" % len(glued)))
    ok &= not glued

    total = tags(merged)
    print("\n本分片 \\tag 合计: %d" % len(total))
    print("结果: %s -> %s" % ("PASS" if ok else "FAIL", OUT.name))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
