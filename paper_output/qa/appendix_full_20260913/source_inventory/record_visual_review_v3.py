from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path('D:/Document/数学建模/2026CUMCM')
QA = ROOT / 'paper_output/qa/appendix_full_20260913'
OUT = QA / 'source_inventory'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
manifest_path = QA / 'v3_render_manifest.json'
comparison_path = QA / 'v2_v3_page_comparison.json'
previous_path = OUT / 'visual_source_81_165_v2.json'
manifest = read(manifest_path)
comparison = read(comparison_path)
previous = read(previous_path)
assert manifest['docxSha256'] == comparison['v3_docx_sha256']
assert previous['docx_sha256'] == comparison['v2_docx_sha256']
v3 = {p['page']: p for p in manifest['pages']}
v2_review = {p['page']: p for p in previous['pages']}
actual_viewed = {66, 67, 118, 119}
pages = []
for n in [66, 67] + list(range(81, 166)):
    page = v3[n]
    digest = sha(ROOT / page['image'])
    assert digest == page['sha256'], n
    notes = []
    if n in actual_viewed:
        method = 'Actual visual inspection of the individual full 120 dpi original v3 PNG with view_image'
        notes.append('实际查看本页完整 120 dpi 原始 PNG；未见裁切、乱码、重叠或页脚碰撞。')
        if n in {67, 119}:
            notes.append('完整末函数的 def、if 与赋值现在同在本页；原先只有最后赋值占下一页的问题已解决。')
            notes.append('末函数之外的留白由完整源文件分页产生；源码不压缩、不删减。')
        else:
            notes.append('上一函数及类方法在本页完整结束；末尾 align 函数整体移到下一页，未在 def 或 if 之间断裂。')
        directly_observed = True
        inherited = None
    else:
        previous_page = v2_review[n]
        assert digest == previous_page['sha256'], n
        assert n in comparison['unchanged_pages'], n
        assert previous_page['observed'] and not previous_page['issues'], n
        method = 'Reused actual v2 full-page visual review after independently verifying byte-identical v3 PNG SHA256'
        notes.append('本页 v3 PNG 与已实际逐页观察的 v2 PNG 字节一致；本次独立重算 SHA 后继承该页观察结果。')
        directly_observed = False
        inherited = {'audit': str(previous_path.relative_to(ROOT)).replace('\\', '/'), 'page': n, 'sha256': digest}
    pages.append({
        'page': n, 'image': page['image'], 'sha256': digest,
        'matches_v3_render_manifest': True,
        'directly_observed_v3': directly_observed,
        'review_method': method,
        'inherited_byte_identical_review': inherited,
        'observations': notes,
        'issues': [],
    })
assert len(pages) == 87
report = {
    'version': 'v3', 'reviewer': '/root/comment_cleanup',
    'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
    'docx': manifest['docx'], 'docx_sha256': manifest['docxSha256'],
    'pdf': manifest['pdf'], 'pdf_sha256': manifest['pdfSha256'],
    'render_manifest': str(manifest_path.relative_to(ROOT)).replace('\\', '/'),
    'render_manifest_sha256': sha(manifest_path),
    'comparison_evidence': str(comparison_path.relative_to(ROOT)).replace('\\', '/'),
    'comparison_evidence_sha256': sha(comparison_path),
    'assigned_range': [81, 165], 'assigned_pages_covered': 85,
    'directly_observed_v3_pages': sorted(actual_viewed),
    'assigned_v3_pages_reusing_byte_identical_v2_review': 83,
    'extra_pages_directly_observed': [66, 67],
    'resolved_finding': 'D.17 第 119 页末赋值孤行已改为完整 align_bdf_segments 函数同页；相应生产版本第 67 页亦同。',
    'status': 'PASS', 'issues_remaining': 0,
    'source_integrity_final_docx_check': 'Waiting for final PAGEREF-cache update and root handoff; this record certifies v3 images only.',
    'pages': pages,
}
target = OUT / 'visual_source_81_165_v3.json'
target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'output': str(target), 'status': report['status'], 'assigned_covered': 85, 'directly_viewed_v3': 4, 'byte_identical_reused': 83}, ensure_ascii=False))
