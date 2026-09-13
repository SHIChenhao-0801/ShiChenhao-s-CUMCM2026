from pathlib import Path
from datetime import datetime
import collections
import hashlib
import json
import re
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
import pymupdf

ROOT = Path(__file__).resolve().parents[3]
QA = ROOT / 'paper_output/qa/appendix_full_20260913'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
EXPECTED_DOCX = '2fd451eb2c2492438e324c44ddc3ecd6dc5e514a963ed507ff23ea91582400b9'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def wt(element):
    return ''.join(x.text or '' for x in element.iter(W + 't'))

def normalized(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text))

v3 = read_json(QA / 'v3_render_manifest.json')
v4 = read_json(QA / 'v4_render_manifest.json')
toc_map = read_json(QA / 'toc_page_map.json')
cache_update = read_json(QA / 'toc_cache_update.json')
build = read_json(QA / 'build_manifest.json')
docx = ROOT / v4['docx']
pdf_path = ROOT / v4['pdf']
failures = []

def check(condition, message):
    if not condition:
        failures.append(message)

check(sha(docx) == EXPECTED_DOCX == v4['docxSha256'] == cache_update['after_sha256'], 'Final DOCX hash binding mismatch')
check(sha(pdf_path) == v4['pdfSha256'], 'v4 PDF hash binding mismatch')
with zipfile.ZipFile(docx) as z:
    tree = ET.fromstring(z.read('word/document.xml'))
elements = list(tree.iter())
parents = {child: parent for parent in elements for child in parent}
positions = {element: i for i, element in enumerate(elements)}
starts = [x for x in elements if x.tag == W + 'bookmarkStart']
ends = [x for x in elements if x.tag == W + 'bookmarkEnd']
start_ids = [x.get(W + 'id') for x in starts]
end_ids = [x.get(W + 'id') for x in ends]
names = [x.get(W + 'name') for x in starts]
check(len(start_ids) == len(set(start_ids)), 'Duplicate bookmark start ID')
check(len(end_ids) == len(set(end_ids)), 'Duplicate bookmark end ID')
check(len(names) == len(set(names)), 'Duplicate bookmark name')
check(set(start_ids) == set(end_ids), 'Unpaired bookmark ID')
end_by_id = {x.get(W + 'id'): x for x in ends}
bookmarks = {}
for start in starts:
    name = start.get(W + 'name')
    end = end_by_id.get(start.get(W + 'id'))
    if end is None:
        continue
    left, right = positions[start], positions[end]
    check(left < right, f'Bookmark range reversed: {name}')
    paragraph = start
    while paragraph is not None and paragraph.tag != W + 'p':
        paragraph = parents.get(paragraph)
    bookmarks[name] = {
        'name': name,
        'id': start.get(W + 'id'),
        'text': ''.join(x.text or '' for x in elements[left + 1:right] if x.tag == W + 't'),
        'paragraph_text': wt(paragraph) if paragraph is not None else '',
        'range_fields': [x.get(W + 'instr', '').strip() for x in elements[left + 1:right] if x.tag == W + 'fldSimple'],
    }

fields = []
for field in tree.iter(W + 'fldSimple'):
    instruction = field.get(W + 'instr', '').strip()
    tokens = instruction.split()
    fields.append({'kind': tokens[0] if tokens else '', 'instruction': instruction, 'cache': wt(field), 'tokens': tokens})
check(not list(tree.iter(W + 'fldChar')), 'Unexpected complex fields need separate audit')
seq = [x for x in fields if x['kind'] == 'SEQ']
refs = [x for x in fields if x['kind'] == 'REF']
pagerefs = [x for x in fields if x['kind'] == 'PAGEREF']
check(len(seq) == 78, 'SEQ count is not 78')
check(len(refs) == 38, 'REF count is not 38')
check(len(pagerefs) == 35, 'PAGEREF count is not 35')
equations = []
for n, field in enumerate(seq, 1):
    match = re.fullmatch(r'SEQ\s+AppendixA\s+\\r\s+(\d+)', field['instruction'])
    check(bool(match) and int(match.group(1)) == n, f'SEQ instruction gap/repeat at {n}')
    check(field['cache'] == str(n), f'SEQ cache mismatch at {n}')
expected_equations = {x['key']: x['number'] for x in build['equations']}
equation_names = {name for name in bookmarks if name.startswith('EQ_A_')}
check(equation_names == set(expected_equations), 'Equation bookmark inventory differs from 78 formula source labels')
for name, number in expected_equations.items():
    bm = bookmarks.get(name)
    if bm is None:
        continue
    expected = f'（{number}）'
    check(bm['text'] == expected, f'Equation bookmark cached label mismatch: {name}')
    check(len(bm['range_fields']) == 1 and bm['range_fields'][0].startswith('SEQ AppendixA '), f'Equation bookmark missing its unique SEQ field: {name}')
    equations.append({'bookmark': name, 'number': number, 'cache': bm['text'], 'seq_instruction': bm['range_fields'][0] if bm['range_fields'] else None})
reference_checks = []
for i, field in enumerate(refs, 1):
    target = field['tokens'][1]
    bm = bookmarks.get(target)
    check(bm is not None, f'REF dead bookmark: {target}')
    check(bm is not None and field['cache'] == bm['text'], f'REF cache mismatch: {target}')
    check(target in expected_equations, f'Unexpected REF target: {target}')
    reference_checks.append({'index': i, 'target': target, 'cache': field['cache'], 'matches_bookmarked_label': bm is not None and field['cache'] == bm['text']})

hyperlinks = list(tree.iter(W + 'hyperlink'))
anchor_links = [x for x in hyperlinks if x.get(W + 'anchor')]
check(len(anchor_links) == 35, 'Expected 35 TOC title hyperlinks')
anchor_counts = collections.Counter(x.get(W + 'anchor') for x in anchor_links)
page_targets = [x['tokens'][1] for x in pagerefs]
check(set(page_targets) == set(toc_map) and len(set(page_targets)) == 35, 'PAGEREF target set differs from 35 TOC entries')
check(set(anchor_counts) == set(toc_map) and all(v == 1 for v in anchor_counts.values()), 'TOC title hyperlink targets missing or duplicated')
pdf = pymupdf.open(pdf_path)
outline = pdf.get_toc()
check(pdf.page_count == 247 == v4['pageCount'], 'v4 page count mismatch')
check(len(outline) == 82, 'Unexpected PDF outline count')
outline_by_title = collections.defaultdict(list)
for level, title, page in outline:
    outline_by_title[normalized(title)].append((level, page))
toc_checks = []
for field in pagerefs:
    target = field['tokens'][1]
    bm = bookmarks.get(target)
    check(bm is not None, f'PAGEREF dead bookmark: {target}')
    if bm is None:
        continue
    title = bm['paragraph_text']
    matches = outline_by_title.get(normalized(title), [])
    check(len(matches) == 1, f'TOC heading ambiguous/missing in actual PDF outline: {target}')
    actual_page = matches[0][1] if len(matches) == 1 else None
    check(str(actual_page) == field['cache'] == str(toc_map[target]), f'TOC page cache/map/actual outline mismatch: {target}')
    check(cache_update['fields'][target] == actual_page, f'TOC cache update record differs from actual outline: {target}')
    link = [x for x in anchor_links if x.get(W + 'anchor') == target][0]
    check(normalized(wt(link)) == normalized(title), f'TOC title differs from bookmarked heading: {target}')
    toc_checks.append({'bookmark': target, 'heading': title, 'cached_page': int(field['cache']), 'map_page': toc_map[target], 'actual_pdf_outline_page': actual_page, 'title_link_exists': True})
pdf_toc_links = []
for page_index in (0, 1):
    for link in pdf[page_index].get_links():
        destination = link.get('page')
        check(link.get('kind') == pymupdf.LINK_GOTO and destination is not None and 0 <= destination < pdf.page_count, f'Invalid PDF TOC destination on page {page_index + 1}')
        pdf_toc_links.append({'toc_page': page_index + 1, 'destination_page': destination + 1 if destination is not None else None, 'kind': link.get('kind')})
check(len(pdf_toc_links) == 70, 'Expected 70 PDF TOC links: 35 titles + 35 page fields')
check(collections.Counter(x['destination_page'] for x in pdf_toc_links) == collections.Counter([v for v in toc_map.values() for _ in range(2)]), 'PDF TOC destinations do not match title/page link pairs')

png_checks = []
for a, b in zip(v3['pages'], v4['pages'], strict=True):
    old_sha, new_sha = sha(ROOT / a['image']), sha(ROOT / b['image'])
    check(a['page'] == b['page'], 'v3/v4 PNG page mapping order changed')
    check(old_sha == a['sha256'] and new_sha == b['sha256'], f'PNG/manifest hash mismatch at page {b["page"]}')
    check(old_sha == new_sha, f'Unexpected v3/v4 visual page change at {b["page"]}')
    png_checks.append({'page': b['page'], 'sha256': new_sha, 'v3_v4_png_bytes_identical': old_sha == new_sha})
check(len(png_checks) == 247, 'PNG cache mapping does not cover 247 pages')

result = {
    'schema': 'appendix_independent_field_and_page_audit_v1',
    'reviewer': '/root/verification_independence',
    'time': datetime.now().astimezone().isoformat(),
    'status': 'PASS' if not failures else 'FAIL',
    'docx': str(docx.relative_to(ROOT)),
    'docx_sha256': sha(docx),
    'pdf': str(pdf_path.relative_to(ROOT)),
    'pdf_sha256': sha(pdf_path),
    'method': 'Independently parsed current DOCX XML and actual v4 PDF outline/link destinations; rehashed every v3/v4 PNG. Did not rely solely on root summary/cache map.',
    'counts': {'bookmarks': len(starts), 'paired_bookmarks': len(ends), 'simple_fields': len(fields), 'formula_seq': len(seq), 'formula_ref': len(refs), 'toc_pageref': len(pagerefs), 'toc_title_hyperlinks': len(anchor_links), 'actual_pdf_outline_entries': len(outline), 'actual_pdf_toc_links': len(pdf_toc_links), 'png_pages_compared': len(png_checks)},
    'sequence_gap_or_duplicate': False if not failures else 'see failures',
    'dead_internal_bookmark_link': False if not failures else 'see failures',
    'equations': equations,
    'formula_refs': reference_checks,
    'toc_entries': toc_checks,
    'actual_pdf_toc_links': pdf_toc_links,
    'v3_v4_png_page_mapping': png_checks,
    'failures': failures,
    'visual_review_transfer': 'All v4 PNG bytes equal v3; A visual acceptance inherits visual_A_v3.json, including resolved ceiling and retained low-priority inline line breaks. Other agent visual scopes remain separate.',
    'limits': ['This is a static field and rendered page mapping audit, not a new PDE run or Word GUI click test.', 'Existing SEQ instructions explicitly reset each current number; numbering correctness is confirmed for this frozen document, not promised for arbitrary future insertions.', 'No changes made to DOCX/PDF/source or renderer.'],
}
out = QA / 'independent_final_fields_and_pages.json'
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': result['status'], 'counts': result['counts'], 'failures': failures, 'audit_sha256': sha(out)}, ensure_ascii=True))
raise SystemExit(bool(failures))
