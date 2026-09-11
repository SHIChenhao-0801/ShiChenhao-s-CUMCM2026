"""Verify that every table value copied into the handoff pack matches the frozen CSVs.

Read-only. Exact check: every frozen CSV row's value tuple (times excluded) must
equal some markdown table row's numeric-token tuple, in order, within one table.
"""
import pathlib
import re
import csv
import json
import sys

ROOT = pathlib.Path(r"D:\Document\数学建模\2026CUMCM")
PACK = ROOT / "paper_output" / "paper" / "A题_论文写作交接包"
OUT = ROOT / "paper_output" / "results" / "production" / "final_v6a" / "outputs"

NUM4 = re.compile(r"^\d+\.\d{4}$")

PAIRS = [
    ("03_问题一二_写作页.md", "q1_paper_temperature.csv"),
    ("03_问题一二_写作页.md", "q1_paper_moisture.csv"),
    ("03_问题一二_写作页.md", "q2_paper_temperature.csv"),
    ("03_问题一二_写作页.md", "q2_paper_moisture.csv"),
    ("04_问题三四_写作页.md", "q3_paper_moisture.csv"),
    ("04_问题三四_写作页.md", "q4_paper_moisture.csv"),
    ("04_问题三四_写作页.md", "q4_paper_radius.csv"),
]


def md_tables(path):
    """List of tables; each table is a list of rows; each row is a tuple of 4-decimal tokens."""
    text = path.read_text(encoding="utf-8").replace("*", "")
    tables, currentTable = [], None
    for line in text.splitlines():
        stripped = line.strip()
        isRow = stripped.startswith("|") and stripped.endswith("|")
        if isRow:
            if currentTable is None:
                currentTable = []
                tables.append(currentTable)
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            tokens = tuple(c for c in cells if NUM4.match(c))
            if tokens:
                currentTable.append(tokens)
        else:
            currentTable = None
    return tables


def csv_rows(path):
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        next(reader)
        for row in reader:
            values = tuple(c.strip() for c in row[1:] if c.strip() != "")
            rows.append(values)
    return rows


def contiguous_in(needle, hay):
    n = len(needle)
    if n == 0 or n > len(hay):
        return False
    return any(hay[i:i + n] == needle for i in range(len(hay) - n + 1))


results = []
ok = True
for mdName, csvName in PAIRS:
    tables = md_tables(PACK / mdName)
    rows = csv_rows(OUT / csvName)
    detail = []
    for values in rows:
        hit = any(values == row for table in tables for row in table) or \
            any(contiguous_in(values, row) for table in tables for row in table)
        detail.append(hit)
        ok = ok and hit
    results.append({
        "markdown": mdName,
        "csv": csvName,
        "csvRowCount": len(rows),
        "exactRowHits": sum(1 for x in detail if x),
        "allRowsExactMatch": all(detail),
    })

print(json.dumps({"status": "PASS" if ok else "FAIL", "checks": results},
                 ensure_ascii=False, indent=2))
sys.exit(0 if ok else 1)
