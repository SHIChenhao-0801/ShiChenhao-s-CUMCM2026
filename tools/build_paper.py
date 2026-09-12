# -*- coding: utf-8 -*-
"""Build the A-problem paper: markdown -> DOCX (native OMML) -> PDF, then report structure.

Usage:
    python -B tools/build_paper.py [--stem NAME] [--no-pdf]

LibreOffice is used for rendering because it is the only renderer available in
this environment besides Word; the DOCX itself carries real OMML so both
renderers show the same mathematics.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "paper_output" / "drafts" / "A题正文" / "A题_论文正文_30p.md"
BUILDER = ROOT / "paper_output" / "paper" / "build_docx.py"
STATS = ROOT / "tools" / "page_stats.py"
SOFFICE = Path(r"D:\Document\数学建模\tools\libreoffice\app\program\soffice.com")
PDFDIR = ROOT / "tmp" / "cache" / "paperpdf"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stem", default="A题_论文_定稿")
    ap.add_argument("--no-pdf", action="store_true")
    args = ap.parse_args()

    env = {**os.environ,
           "PYTHONPYCACHEPREFIX": str(ROOT / "tmp" / "cache" / "python"),
           "PYTHONIOENCODING": "utf-8"}
    docx = ROOT / "paper_output" / "paper" / (args.stem + ".docx")

    print("== 0/2 merge shards ==", flush=True)
    sys.path.insert(0, str(ROOT / "paper_output" / "paper"))
    import assemble_30p  # noqa: E402
    assemble_30p.merge()

    print("== 1/2 build docx ==", flush=True)
    r = subprocess.run([sys.executable, "-B", str(BUILDER), str(MD), str(docx)],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(ROOT), env=env)
    print(r.stdout.strip())
    if r.returncode != 0 or not docx.exists():
        print(r.stderr[-3000:])
        print("DOCX FAILED")
        return 1
    print("docx bytes =", docx.stat().st_size)

    if args.no_pdf:
        return 0

    print("== 2/2 render pdf ==", flush=True)
    PDFDIR.mkdir(parents=True, exist_ok=True)
    # LibreOffice silently keeps a stale output when the target already exists
    stale = PDFDIR / (args.stem + ".pdf")
    if stale.exists():
        stale.unlink()
    subprocess.run([str(SOFFICE), "--headless", "--norestore",
                    "-env:UserInstallation=file:///" + str(ROOT / "tmp" / "cache" / "lo30").replace("\\", "/"),
                    "--convert-to", "pdf", "--outdir", str(PDFDIR), str(docx)],
                   capture_output=True, text=True, cwd=str(ROOT))
    pdf = PDFDIR / (args.stem + ".pdf")
    if not pdf.exists():
        print("PDF FAILED")
        return 1
    print("pdf bytes =", pdf.stat().st_size)
    subprocess.run([sys.executable, "-B", str(STATS), str(pdf)], cwd=str(ROOT), env=env)
    return 0


if __name__ == "__main__":
    sys.exit(main())
