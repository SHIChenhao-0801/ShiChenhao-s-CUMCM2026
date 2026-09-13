from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path('D:/Document/数学建模/2026CUMCM')
QA = ROOT / 'paper_output/qa/appendix_full_20260913'
OUT = QA / 'source_inventory'
manifest_path = QA / 'v2_render_manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
entries = []
metadata_pages = {82, 86, 87, 92, 101, 107, 112, 117, 120, 127, 141, 150, 158, 159, 160, 161, 162, 164}
for p in manifest['pages']:
    n = p['page']
    if not 81 <= n <= 165:
        continue
    path = ROOT / p['image']
    digest = sha(path)
    assert digest == p['sha256'], (n, 'image differs from v2 manifest')
    notes = [
        '已实际查看本页完整 120 dpi 原始 PNG；未使用缩略拼图代替逐页观察。',
        '页内代码可读；未见裁切、文字重叠、乱码或页脚碰撞；页码与图像页号一致。',
        '长行采用显示折行；完整逻辑行、空行及缩进另由 v2 DOCX 源码逐行一致性检查确认。',
    ]
    if n in metadata_pages:
        notes.append('源码标题、路径及用途文字可读；语言与 SHA 已独立分段、左对齐，未见 v1 的两端对齐字间距问题。')
    if 82 <= n <= 85:
        notes.append('该组深层数据字典保留原始缩进，较多左侧留白和显示折行不构成源码缺失。')
    if n == 118:
        notes.append('页末 align_bdf_segments 函数与 if 条件之后的赋值跨到第 119 页；该小块的分页问题记录在第 119 页。')
    issues = []
    if n == 119:
        issues.append({
            'severity': 'minor_layout',
            'source': 'D.17 disk_dense.py',
            'finding': '文件末尾 result.sol = OdeSolution(...) 单独占一页；上一页已列 align_bdf_segments 函数及 if 条件。代码完整，但单行孤页影响阅读。',
            'recommended_action': '仅保持该函数末尾约 3–4 行同页，不修改源文字、缩进或字号。',
            'parent_notified': True,
            'v2_status': 'open_pending_v3_local_pagination_fix',
        })
    if n in {158, 159, 161}:
        notes.append('此页对应仅 7 行的完整独立封装文件；标题后保留整页文件边界造成的留白合理，不是断裂后的孤行。')
    entries.append({
        'page': n,
        'image': p['image'],
        'sha256': digest,
        'matches_render_manifest': True,
        'observed': True,
        'review_method': 'Actual visual inspection of the individual full 120 dpi original PNG with view_image',
        'observations': notes,
        'issues': issues,
    })
assert [e['page'] for e in entries] == list(range(81, 166))
report = {
    'version': 'v2',
    'reviewer': '/root/comment_cleanup',
    'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
    'docx': manifest['docx'],
    'docx_sha256': manifest['docxSha256'],
    'pdf': manifest['pdf'],
    'pdf_sha256': manifest['pdfSha256'],
    'render_manifest': str(manifest_path.relative_to(ROOT)).replace('\\', '/'),
    'render_manifest_sha256': sha(manifest_path),
    'reviewed_page_range': [81, 165],
    'expected_pages': 85,
    'actually_viewed_pages': len(entries),
    'coverage_complete': True,
    'source_static_audit': 'paper_output/qa/appendix_full_20260913/source_inventory/docx_source_audit_v2.json',
    'status': 'COMPLETE_WITH_ONE_MINOR_PAGINATION_FINDING_PENDING_V3',
    'material_clipping_overlap_or_missing_glyph_findings': 0,
    'minor_pagination_findings': 1,
    'pages': entries,
}
target = OUT / 'visual_source_81_165_v2.json'
target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'output': str(target), 'pages': len(entries), 'status': report['status']}, ensure_ascii=False))
