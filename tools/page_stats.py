# -*- coding: utf-8 -*-
"""Report page structure of the rendered paper PDF: total pages, where the
abstract, the AI declaration, the references and the appendix start, plus the
count of missing-glyph boxes (a symptom of broken OMML)."""
import sys, re
import pymupdf

pdf = sys.argv[1]
d = pymupdf.open(pdf)
pages = [p.get_text() for p in d]
full = "".join(pages)

def first_page(pat):
    for i, t in enumerate(pages):
        if re.search(pat, t, re.M):
            return i + 1
    return None

ai = first_page(r"^\s*AI\s*工具使用声明")
ref = first_page(r"^\s*参考文献\s*$")
apx = first_page(r"^\s*附录\s*$")

print("TOTAL PAGES      :", d.page_count)
print("abstract page    : 1")
print("AI declaration   :", ai)
print("references       :", ref)
print("appendix starts  :", apx)
# body = every page from page 2 through the last page that carries body/reference text
if apx:
    print("BODY (p2..p%d)   : %d pages   [cap 30]" % (apx, apx - 1))
print("missing-glyph boxes U+2751:", full.count("\u2751"), " U+25A1:", full.count("\u25a1"))
print("figures/tables referenced:", len(set(re.findall(r"图\s?(\d+)", full))), "figs,",
      len(set(re.findall(r"表\s?(\d+)", full))), "tables")
