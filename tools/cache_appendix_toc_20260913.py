from pathlib import Path
import hashlib
import json
import re
import sys
import zipfile
import pymupdf
from lxml import etree

ROOT = Path.cwd()
assert ROOT.as_posix() == 'D:/Document/数学建模/2026CUMCM'
sys.stdout.reconfigure(encoding='utf-8')
QA = ROOT / 'paper_output/qa/appendix_full_20260913'
build = json.loads((QA / 'build_manifest.json').read_text(encoding='utf-8'))
docx = Path(build['docx'])
before = hashlib.sha256(docx.read_bytes()).hexdigest()
assert before == build['docx_sha256']
pdf = pymupdf.open(QA / 'v3.pdf')
outline = {title: page for level, title, page in pdf.get_toc()}
mapping = {h['bookmark']: outline[h['text']] for h in build['toc']}
assert len(mapping) == 35
(QA / 'toc_page_map.json').write_text(json.dumps(mapping, indent=2), encoding='utf-8')
with zipfile.ZipFile(docx) as archive:
    members = [(z, archive.read(z.filename)) for z in archive.infolist()]
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
root = etree.fromstring(dict((z.filename, raw) for z, raw in members)['word/document.xml'])
fields = []
for f in root.xpath('//w:fldSimple', namespaces=ns):
    match = re.fullmatch(r'\s*PAGEREF\s+(HEAD_\d+)\s+\\h\s*', f.get('{'+ns['w']+'}instr', ''))
    if match:
        key = match.group(1)
        text = f.xpath('./w:r/w:t', namespaces=ns)
        assert len(text) == 1
        text[0].text = str(mapping[key])
        fields.append(key)
assert set(fields) == set(mapping)
xml = etree.tostring(root, encoding='UTF-8', xml_declaration=True, standalone=True)
temporary = QA / 'toc_cached.docx'
with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for z, raw in members:
        archive.writestr(z, xml if z.filename == 'word/document.xml' else raw)
temporary.replace(docx)
after = hashlib.sha256(docx.read_bytes()).hexdigest()
for h in build['toc']:
    h['cached_page'] = mapping[h['bookmark']]
build['docx_sha256'] = after
(QA / 'build_manifest.json').write_text(json.dumps(build, ensure_ascii=False, indent=2), encoding='utf-8')
index = json.loads((QA / 'code_index.json').read_text(encoding='utf-8'))
assert index['docx_sha256'] == before
index['docx_sha256'] = after
(QA / 'code_index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')
(QA / 'toc_cache_update.json').write_text(json.dumps({'before_sha256': before, 'after_sha256': after, 'fields': mapping, 'scope': 'Only 35 PAGEREF field cached text nodes changed; all source paragraphs and formulas unchanged.'}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'docx_sha256': after, 'bytes': docx.stat().st_size, 'cached_fields': len(fields)}))
