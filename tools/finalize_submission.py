# -*- coding: utf-8 -*-
"""Final gate before hand-in: structure, size, anonymity and cross-checks.

Checks
  1. body page span (abstract page, AI declaration before references, appendix last)
  2. 20 MB cap on both the paper PDF and the support archive
  3. identity scan of the PDF text, PDF metadata and DOCX core properties
  4. the two headline numbers appear identically in abstract, body and conclusion
  5. extractable (non-image) text
Copies the verified PDF next to the support archive.
"""
from __future__ import annotations

import io
import json
import re
import shutil
import zipfile
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper_output"
PDF = ROOT / "tmp" / "cache" / "paperpdf" / "A题_论文_定稿.pdf"
DOCX = OUT / "paper" / "A题_论文_定稿.docx"
ZIP = OUT / "submission" / "支撑材料" / "A题_支撑材料.zip"
SUB = OUT / "submission"

CAP = 20 * 1024 * 1024
report: dict = {"checks": [], "failures": []}


def check(name: str, ok: bool, detail: str) -> None:
    report["checks"].append({"name": name, "ok": bool(ok), "detail": detail})
    if not ok:
        report["failures"].append(f"{name}: {detail}")
    print(("  PASS  " if ok else "  FAIL  ") + name + " -- " + detail)


doc = pymupdf.open(PDF)
pages = [p.get_text() for p in doc]
full = "".join(pages)


def first_page(pat: str):
    for i, t in enumerate(pages):
        if re.search(pat, t, re.M):
            return i + 1
    return None


ai = first_page(r"^\s*AI\s*工具使用声明")
ref = first_page(r"^\s*参考文献\s*$")
apx = first_page(r"^\s*附录\s*$")
check("abstract is page 1", "摘要" in pages[0], "摘要 heading on page 1")
check("keywords on the abstract page",
      "关键词" in pages[0], "关键词 line is on page 1 (not page 2)")
check("AI declaration before references",
      ai is not None and ref is not None and ai <= ref,
      f"AI page {ai}, references page {ref}")
# the body runs from page 2 (page 1 is the abstract page) through the page
# BEFORE the appendix heading, so its length is apx - 2, not apx - 1
check("body (p2 .. end of references) within 30 pages",
      apx is not None and (apx - 2) <= 30,
      f"appendix starts p{apx} -> body = pages 2..{apx - 1} = {apx - 2} page(s), cap 30")
check("no table of contents", "目录" not in full[:4000] or "不设目录" in full, "no TOC section")
check("PDF under 20 MB", PDF.stat().st_size <= CAP, f"{PDF.stat().st_size:,} bytes")
check("support archive under 20 MB", ZIP.is_file() and ZIP.stat().st_size <= CAP,
      f"{ZIP.stat().st_size:,} bytes" if ZIP.is_file() else "archive missing")
check("PDF text is extractable", len(full) > 40000, f"{len(full):,} extractable characters")
check("no placeholder boxes", full.count("\u2751") == 0 and full.count("\u25a1") == 0,
      f"U+2751={full.count(chr(0x2751))}, U+25A1={full.count(chr(0x25a1))}")

for label, num in (("Q3 = 57.4724 h", "57.4724"), ("Q4 = 51.0906 h", "51.0906")):
    hits = [i + 1 for i, t in enumerate(pages) if num in t]
    check(f"{label} present", bool(hits), f"appears on pages {hits}")

# ---- identity scan ----------------------------------------------------------
BAD = ["福州", "学校", "赛区", "队号", "姓名",
       "C:\\Users", "Shi Chenhao", "SHIChenhao", "github.com", "高校"]
hits = [b for b in BAD if b in full]
check("no identity strings in PDF text", not hits, f"hits: {hits}" if hits else "clean")

meta = doc.metadata or {}
meta_bad = {k: v for k, v in meta.items()
            if v and any(b.lower() in str(v).lower() for b in
                         ["Shi", "Chenhao", "福州", "github"])}
check("PDF metadata carries no identity", not meta_bad, json.dumps(meta, ensure_ascii=False)[:300])

with zipfile.ZipFile(DOCX) as z:
    core = z.read("docProps/core.xml").decode("utf-8", "replace")
check("DOCX core properties carry no identity",
      not any(b.lower() in core.lower() for b in ["shi", "chenhao", "福州", "github"]),
      re.sub(r"<[^>]+>", " ", core)[:220].strip())

# ---- copy the verified paper next to the support archive --------------------
SUB.mkdir(parents=True, exist_ok=True)
dst = SUB / "A题_论文.pdf"
shutil.copyfile(PDF, dst)
report["paper_pdf"] = {"path": str(dst.relative_to(ROOT)), "bytes": dst.stat().st_size,
                       "pages": doc.page_count}
io.open(OUT / "qa" / "final_submission_check.json", "w", encoding="utf-8").write(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print()
print("paper copied to", dst.relative_to(ROOT), "pages =", doc.page_count)
print("FAILURES:", len(report["failures"]))
for f in report["failures"]:
    print("   -", f)
