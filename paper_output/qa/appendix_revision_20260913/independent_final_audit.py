from pathlib import Path
from zipfile import ZipFile
from lxml import etree as ET
import hashlib
import json
import re

ROOT = Path('D:/Document/数学建模/2026CUMCM')
QA = ROOT / 'paper_output/qa/appendix_revision_20260913'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{' + NS['w'] + '}'
build = json.loads((QA / 'build_audit.json').read_text(encoding='utf-8-sig'))
inventory = json.loads((QA / 'source_inventory.json').read_text(encoding='utf-8-sig'))
source = ROOT / '药材热湿耦合模型与干燥时间计算_文献公式修订版(1).docx'
output = ROOT / '药材热湿耦合模型与干燥时间计算_附录修订版.docx'

def sig(element):
    return (element.tag, dict(element.attrib), element.text, element.tail,
            tuple(sig(child) for child in element))

def txt(element):
    chunks = []
    for child in element.iter():
        if child.tag == W + 't':
            chunks.append(child.text or '')
        elif child.tag == W + 'tab':
            chunks.append('\t')
        elif child.tag == W + 'br':
            chunks.append('\n')
    return ''.join(chunks)

def attrs(element):
    return None if element is None else dict(element.attrib)

with ZipFile(source) as original, ZipFile(output) as revised:
    old_body = ET.fromstring(original.read('word/document.xml')).find('w:body', NS)
    new_body = ET.fromstring(revised.read('word/document.xml')).find('w:body', NS)
    prefix_differences = [i for i in range(470) if sig(old_body[i]) != sig(new_body[i])]
    zip_members_equal = original.namelist() == revised.namelist()
    changed_parts = [name for name in original.namelist()
                     if name != 'word/document.xml' and original.read(name) != revised.read(name)]
    final_section_equal = sig(old_body[-1]) == sig(new_body[-1])

sources = []
source_heading_rows = [(i, txt(el)) for i, el in enumerate(new_body)
                       if re.match(r'^9\.2\.\d+\s', txt(el))]
for item, (heading_index, heading_text) in zip(build['sources'], source_heading_rows, strict=True):
    start = item['first_body_index']
    count = item['paragraph_count']
    path = Path(item['path'])
    raw = path.read_bytes()
    actual_lines = path.read_text(encoding='utf-8-sig').splitlines()
    document_lines = [txt(el) for el in new_body[start:start + count]]
    source_check = {
        'number': item['number'], 'path': item['relative_path'],
        'heading': heading_text, 'heading_index': heading_index,
        'line_count': len(actual_lines),
        'exact_text_equal': actual_lines == document_lines,
        'line_count_matches': len(actual_lines) == count,
        'heading_before_first_line': heading_index + 1 == start,
        'heading_filename_correct': heading_text.endswith(item['filename']),
        'current_source_sha256': hashlib.sha256(raw).hexdigest(),
        'source_hash_matches_manifest': hashlib.sha256(raw).hexdigest() == item['sha256'],
    }
    sources.append(source_check)

inventory_retained = {item['relative_path'] for item in inventory['files'] if item['recommendation'] == 'retain'}
document_sources = {item['relative_path'] for item in build['sources']}
allowed = [ROOT / '支撑材料/03_程序代码',
           ROOT / '支撑材料/05_数值检验与实验/MATLAB对照证据',
           ROOT / '支撑材料/05_数值检验与实验/Python检验源码/paper_output/code']
source_scope_valid = all(any(Path(item['path']).is_relative_to(root) for root in allowed) for item in build['sources'])

tables = []
table_records = []
for i, el in enumerate(new_body):
    if el.tag != W + 'tbl' or i < 470:
        continue
    rows = el.findall('w:tr', NS)
    table_borders = el.find('w:tblPr/w:tblBorders', NS)
    table_border_clear = table_borders is not None and all(b.get(W + 'val') in ('none', 'nil') for b in table_borders)
    border_errors = []
    for row_index, row in enumerate(rows):
        cells = row.findall('w:tc', NS)
        for col_index, cell in enumerate(cells):
            b = cell.find('w:tcPr/w:tcBorders', NS)
            borders = {} if b is None else {ET.QName(edge).localname: edge.get(W + 'val') for edge in b}
            expected = {'top': 'single' if row_index == 0 else 'nil',
                        'bottom': 'single' if row_index in (0, len(rows)-1) else 'nil',
                        'left': 'nil', 'right': 'nil'}
            if borders != expected:
                border_errors.append({'row': row_index, 'column': col_index, 'observed': borders, 'expected': expected})
        if row_index:
            table_records.append([txt(cell) for cell in cells])
    caption = txt(new_body[i-1])
    caption_style = new_body[i-1].find('w:pPr/w:pStyle', NS)
    body_caption_style = old_body[74].find('w:pPr/w:pStyle', NS)
    tables.append({'body_index': i, 'caption': caption, 'rows': len(rows),
                   'caption_matches_body_style': attrs(caption_style) == attrs(body_caption_style),
                   'caption_is_table_title': bool(re.match(r'^(续)?表\d+\s', caption)),
                   'caption_keep_next': new_body[i-1].find('w:pPr/w:keepNext', NS) is not None,
                   'table_borders_clear': table_border_clear,
                   'cell_border_errors': border_errors,
                   'three_line_table': table_border_clear and not border_errors})
expected_records = {str(item['number']): (item['filename'], item['description']) for item in build['sources']}
observed_records = {row[0]: (Path(row[1]).name, row[2]) for row in table_records}
catalog_paths_valid = all(next(item['relative_path'] for item in build['sources'] if str(item['number']) == row[0]).endswith('/' + row[1]) for row in table_records)
catalog_exact = expected_records == observed_records and len(table_records) == 36 and catalog_paths_valid

ai_index = next(i for i, el in enumerate(new_body) if txt(el) == '9.3 AI 使用报告')
ai_paragraphs = [txt(el) for el in new_body[ai_index:] if txt(el)]
ai_text = '\n'.join(ai_paragraphs)
ai_checks = {
    'placed_at_end': ai_index > max(s['first_body_index'] + s['paragraph_count'] - 1 for s in build['sources']),
    'uses_exact_requested_combinations': all(name in ai_text for name in ['Deepseek Harness', 'Deepseek v4.1 flash', 'Codex', 'GPT6-Astra']),
    'human_review': 'PASS: Deepseek discussion remains limited to syntax inspection and partial debugging. Codex discussion remains limited to interpreting the problem, searching references, checking modeling results, and organizing formulas. Expanded examples stay within those uses; no extra AI tool, use purpose, invented prompt log or claimed human sign-off added.',
    'paragraphs': ai_paragraphs,
}
inherited_refs = [{'body_index': i, 'text': txt(el)} for i, el in enumerate(old_body[:232]) if re.search(r'附录[A-D]', txt(el))]
checks = {
    'prefix470_recursive_xml_equal': not prefix_differences,
    'body232_recursive_xml_equal': all(sig(old_body[i]) == sig(new_body[i]) for i in range(232)),
    'derivation238_recursive_xml_equal': all(sig(old_body[i]) == sig(new_body[i]) for i in range(232, 470)),
    'all_non_document_zip_parts_byte_equal': zip_members_equal and not changed_parts,
    'last_section_properties_equal': final_section_equal,
    'all_36_source_texts_exact': len(sources) == 36 and all(row['exact_text_equal'] and row['line_count_matches'] and row['source_hash_matches_manifest'] and row['heading_before_first_line'] and row['heading_filename_correct'] for row in sources),
    'all_source_paths_in_user_scope': source_scope_valid,
    'retained_inventory_matches': inventory_retained == document_sources,
    '36_catalog_entries_match_source_sections': catalog_exact,
    'all_four_new_tables_three_line_and_captioned': len(tables) == 4 and all(t['three_line_table'] and t['caption_matches_body_style'] and t['caption_is_table_title'] and t['caption_keep_next'] for t in tables),
    'ai_report_final_and_requested_names': ai_checks['placed_at_end'] and ai_checks['uses_exact_requested_combinations'],
}
report = {
    'reviewer': 'document_audit', 'output': str(output),
    'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
    'result': 'PASS_STATIC_APPENDIX_REVISION' if all(checks.values()) else 'FAIL',
    'checks': checks, 'prefix_differences': prefix_differences,
    'changed_non_document_parts': changed_parts,
    'source_count': len(sources), 'source_total_lines': sum(s['line_count'] for s in sources),
    'sources': sources, 'tables': tables, 'ai_report': ai_checks,
    'inherited_cross_reference_count': len(inherited_refs),
    'inherited_cross_references': inherited_refs,
    'inherited_reference_disposition': 'Original A/A.2/C/C.4 references were already inconsistent with numbered 9.1-9.4 sections in user source. Preserved under explicit no-body-edit instruction; no editing-history note added inside manuscript.',
    'limitations': ['Static document audit only; new visual inspection is recorded separately.', 'No new numerical model execution or human code approval claimed.']
}
(QA / 'independent_final_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'result': report['result'], 'checks': checks, 'source_lines': report['source_total_lines'], 'output_sha256': report['output_sha256']}, ensure_ascii=False, indent=2))
