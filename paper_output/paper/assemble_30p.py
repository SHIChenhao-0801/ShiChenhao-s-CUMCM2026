# -*- coding: utf-8 -*-
"""
拼装压缩后的正文分片，生成 Word 稿，并用 LibreOffice 渲染 PDF 统计页数。

用法：
  python assemble_30p.py            # 拼装 + 生成 docx + 渲染 + 报页数
  python assemble_30p.py --no-pdf   # 只生成 docx

分片约定（由压缩子代理产出）：
  _part1.md   摘要 + 第 1–4 章
  _part2.md   第 5–7 章
  _part3.md   第 8–11 章
  _part4.md   第 12–14 章 + 参考文献 + AI 使用声明
  _appendix.md 附录（不计入 30 页上限）
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # 2026CUMCM
DRAFT = ROOT / "paper_output" / "drafts" / "A题正文"
OUT = ROOT / "paper_output" / "paper"
PY = r"C:\Python314\python.exe"
SOFFICE = r"D:\Document\数学建模\tools\libreoffice\app\program\soffice.com"

PARTS = ["_part1.md", "_part2.md", "_part3.md", "_part4.md", "_appendix.md"]

#: 弃用分片及原因（记录在案，避免再次误用）
REJECTED = {
    "_part2b.md": "第5章单独重压版：与 _part2.md 范围重叠且表格只剩 2 张",
    "_part3b.md": "第10章重压版：公式正文被删空（\\frac / \\partial 计数均为 0），不可用",
    "_part3c.md": "第11章重压版：与 _part3.md 范围重叠，仅作参考",
}

#: 如果分片把论文标题删掉了，拼装时在摘要页之前补回。
#: 格式规范第三条要求"摘要专用页"含标题，故标题必须与摘要同页。
TITLE_BLOCK = ("# 2026 年高教社杯全国大学生数学建模竞赛\n\n"
               "# A 题　药材的烘干问题\n")


def ensure_title(chunks: list[str]) -> list[str]:
    if not chunks:
        return chunks
    head = chunks[0].lstrip()
    if head.startswith("# 2026 年高教社杯"):
        return chunks
    chunks[0] = TITLE_BLOCK + "\n" + chunks[0]
    print("  [补回] 论文标题（摘要页需含标题）")
    return chunks


def merge() -> Path:
    chunks: list[str] = []
    for name in PARTS:
        p = DRAFT / name
        if not p.exists():
            print("  [缺失] %s" % name)
            continue
        body = p.read_text(encoding="utf-8").strip()
        chunks.append(body)
        print("  [并入] %-14s %6d 字符" % (name, len(body)))
    chunks = ensure_title(chunks)
    merged = DRAFT / "A题_论文正文_30p.md"
    merged.write_text("\n\n---\n\n".join(chunks) + "\n", encoding="utf-8")
    print("  [合并] %s  (%d 字符)" % (merged.name, len(merged.read_text(encoding="utf-8"))))
    return merged


def build(md: Path) -> Path:
    docx = OUT / "A题_论文正文_30p.docx"
    r = subprocess.run(
        [PY, "-B", str(OUT / "build_docx.py"), str(md), str(docx)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(ROOT),
        env={**__import__("os").environ,
             "PYTHONPYCACHEPREFIX": str(ROOT / "tmp" / "cache" / "python"),
             "PYTHONIOENCODING": "utf-8"},
    )
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr[-2000:])
    return docx


def pdf(docx: Path) -> Path:
    outdir = OUT / "pdf-preview"
    outdir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [SOFFICE, "--headless", "--norestore",
         "-env:UserInstallation=file:///D:/Document/数学建模/2026CUMCM/tmp/cache/lo30",
         "--convert-to", "pdf", "--outdir", str(outdir), str(docx)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    return outdir / (docx.stem + ".pdf")


def pages(p: Path) -> int:
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf  # type: ignore
    d = pymupdf.open(str(p))
    n = d.page_count
    d.close()
    return n


def main() -> int:
    print("== 1/3 拼装分片 ==")
    md = merge()
    print("== 2/3 生成 DOCX ==")
    docx = build(md)
    if "--no-pdf" in sys.argv:
        return 0
    print("== 3/3 渲染 PDF 并统计页数 ==")
    p = pdf(docx)
    if not p.exists():
        print("  PDF 未生成：%s" % p)
        return 1
    n = pages(p)
    print("  正文总页数（含摘要页、参考文献、AI 声明）：%d" % n)
    print("  目标 ≤30 页：%s" % ("达标" if n <= 30 else "超出 %d 页" % (n - 30)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
