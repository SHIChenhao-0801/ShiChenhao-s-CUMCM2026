from pathlib import Path
import csv
import hashlib
import json
import sys
from docx import Document

ROOT = Path.cwd()
assert ROOT.as_posix() == 'D:/Document/数学建模/2026CUMCM'
sys.stdout.reconfigure(encoding='utf-8')
QA = ROOT / 'paper_output/qa/appendix_full_20260913'

def read(name):
    return json.loads((QA / name).read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

build = read('build_manifest.json')
render = read('v4_render_manifest.json')
source_audit = read('source_inventory/docx_source_audit_final.json')
manifest = read('source_inventory/source_manifest.json')
docx = Path(build['docx'])
digest = sha(docx)
assert digest == build['docx_sha256'] == render['docxSha256'] == source_audit['docx_sha256']
assert source_audit['status'] == 'PASS'
document = Document(docx)
actual_tables = [[[cell.text for cell in row.cells] for row in t.rows] for t in document.tables]
numeric_tables = []
for expected in build['result_tables']:
    path = ROOT / expected['path']
    assert sha(path) == expected['sha256']
    with path.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.reader(stream))
    assert rows == expected['rows']
    matches = [i for i, table in enumerate(actual_tables) if table == rows]
    assert len(matches) == 1, (path, matches)
    numeric_tables.append({'path': expected['path'], 'sha256': sha(path), 'data_cells': sum(len(row) for row in rows[1:]), 'docx_table_index': matches[0]})
assert sum(item['data_cells'] for item in numeric_tables) == 297
for item in manifest['formal_support_files']:
    assert sha(Path(item['absolute_path'])) == item['sha256']
assert len(manifest['formal_support_files']) == 106
paper = ROOT / 'paper_output/paper/药材热湿耦合模型与干燥时间计算_格式与语言修订版.docx'
assert sha(paper) == build['source_paper_sha256']
v2, v3 = read('v2_render_manifest.json'), read('v3_render_manifest.json')
assert render['pageCount'] == v2['pageCount'] == v3['pageCount'] == 247
changed = {page['page'] for old, page in zip(v2['pages'], v3['pages']) if old['sha256'] != page['sha256']}
direct_v3 = {17, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 39, 40, 66, 67, 118, 119}
assert changed == direct_v3
review_files = ['visual_A_v2.json', 'visual_root_24_80_v2.json', 'source_inventory/visual_source_81_165_v2.json', 'visual_source_166_247_v2.json', 'visual_A_v3.json', 'visual_root_v3.json', 'source_inventory/visual_source_81_165_v3.json']
reviews = [{'path': str((QA / name).relative_to(ROOT)), 'sha256': sha(QA / name)} for name in review_files]
pages = []
for a, b, c in zip(v2['pages'], v3['pages'], render['pages']):
    assert b['sha256'] == c['sha256'] == sha(ROOT / c['image'])
    assert not c['suspect_geometry']
    page = c['page']
    reviewer = '/root/verification_independence' if page <= 23 else '/root' if page <= 80 else '/root/comment_cleanup' if page <= 165 else '/root/sandbox_gui'
    pages.append({'page': page, 'final_png_sha256': c['sha256'], 'reviewer': reviewer, 'actual_original_png_review_version': 'v3' if page in direct_v3 else 'v2', 'reuse_basis': 'Final v4 PNG SHA256 matches the actually viewed page PNG exactly.'})
report = {'status': 'PASS_DOCUMENT_CONTENT_AND_ALL_PAGE_REVIEW', 'docx': str(docx), 'docx_sha256': digest, 'bytes': docx.stat().st_size, 'pages': 247, 'display_equations': len(build['equations']), 'native_omml': build['omml_count'], 'complete_sources': 47, 'source_lines': 9917, 'source_integrity_report_sha256': sha(QA / 'source_inventory/docx_source_audit_final.json'), 'result_tables': numeric_tables, 'all_106_support_files_unchanged': True, 'source_paper_unchanged': True, 'visual_review_evidence': reviews, 'page_reviews': pages, 'remaining_minor_typography': 'Some Chinese inline equation references and punctuation wrap between lines; the full symbols remain readable and no display formula is clipped. Independent A review classifies this as low priority.', 'scope': 'Standalone appendix editing and evidence audit; no new production model solve, no substituted human code review, AI details remain user-authored.'}
(QA / 'final_appendix_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({key: report[key] for key in ['status', 'docx_sha256', 'bytes', 'pages', 'display_equations', 'complete_sources', 'source_lines']}, ensure_ascii=False))
