from pathlib import Path
from zipfile import ZipFile
from lxml import etree
import hashlib
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
root = Path.cwd()
assert root.as_posix() == 'D:/Document/数学建模/2026CUMCM'
qa = root / 'paper_output/qa/formatting_20260913'
source = qa / 'source.docx'
final = root / 'paper_output/paper/药材热湿耦合模型与干燥时间计算_格式与语言修订版.docx'
ns = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
}

def text(el):
    return ''.join(el.xpath('.//w:t/text() | .//m:t/text()', namespaces=ns))

def canon_list(doc, xpath):
    return [etree.tostring(x, method='c14n') for x in doc.xpath(xpath, namespaces=ns)]

with ZipFile(source) as zs, ZipFile(final) as zf:
    sd = etree.fromstring(zs.read('word/document.xml'))
    fd = etree.fromstring(zf.read('word/document.xml'))
    sb = list(sd.find('w:body', ns))
    fb = list(fd.find('w:body', ns))
    recommendations = json.loads((qa / 'language_recommendations.json').read_text(encoding='utf-8'))
    expected = [text(x) for x in sb]
    for rec in recommendations['replacements']:
        i = rec['block_index']
        assert expected[i].count(rec['old']) == 1
        expected[i] = expected[i].replace(rec['old'], rec['new'], 1)
    supplemental_old = '计算出药材内部水分浓度每隔60s、到药材中心距离每隔0.1cm的药材水分浓度以及烘干结束时间'
    supplemental_new = '以60 s为时间间隔、0.1 cm为径向距离间隔输出水分浓度，并确定烘干结束时间'
    assert expected[16].count(supplemental_old) == 1
    expected[16] = expected[16].replace(supplemental_old, supplemental_new, 1)
    expected[93] = '图2展示烘房温度与空气水分指标在0—4 h内的观测及分段线性插值，并区分4 h之后的假设平台延拓；平台值分别为50°C和0.05 kg/kg。'
    expected[110] = '图3分别展示中心与表面在前4 h内的温度响应及从初始状态至达标时刻的干基含水率变化，以不同时间尺度呈现传热与脱水过程。'
    expected_retained = [s for i, s in enumerate(expected) if i not in (76, 94)]
    final_texts = [text(x) for x in fb]
    caption_re = re.compile(r'^图([1-6])\s{2}\S')
    actual_retained = [s for s in final_texts if not caption_re.match(s)]
    assert expected_retained == actual_retained, 'Unexpected text change, omission, insertion, or incomplete replacement'
    all_text = '\n'.join(final_texts)
    assert not re.search(r'我们|你们|笔者|本人|咱|我|你|【绘图位置|Step [1-5]：|不能把延拓段画成实测点', all_text)
    assert not fd.xpath('//w:highlight[not(@w:val="none")]', namespaces=ns), 'Highlight remains'
    assert canon_list(sd, '//m:oMath') == canon_list(fd, '//m:oMath'), 'Equation XML changed'
    source_tables = sd.xpath('//w:tbl', namespaces=ns)
    final_tables = fd.xpath('//w:tbl', namespaces=ns)
    assert len(source_tables) == len(final_tables) == 9
    assert [[text(c) for c in t.xpath('.//w:tc', namespaces=ns)] for t in source_tables] == [[text(c) for c in t.xpath('.//w:tc', namespaces=ns)] for t in final_tables], 'Table cell contents changed'
    assert canon_list(sd, '//w:tbl')[1:] == canon_list(fd, '//w:tbl')[1:], 'Result table XML changed'
    source_symbol_cells = source_tables[0].xpath('.//w:tc', namespaces=ns)
    final_symbol_cells = final_tables[0].xpath('.//w:tc', namespaces=ns)
    changed_symbol_cells = [(i, text(b)) for i, (a, b) in enumerate(zip(source_symbol_cells, final_symbol_cells)) if etree.tostring(a, method='c14n') != etree.tostring(b, method='c14n')]
    assert len(changed_symbol_cells) == 1 and changed_symbol_cells[0][1] == '全域含水率阈值的临界时刻', 'Unexpected symbol table change'
    appendix_title = '附录 D 必要算法片段'
    sa = [text(x) for x in sb].index(appendix_title)
    fa = final_texts.index(appendix_title)
    assert [etree.tostring(x, method='c14n') for x in sb[sa:-1]] == [etree.tostring(x, method='c14n') for x in fb[fa:-1]], 'Code appendix XML changed'
    field_xpath = '//w:instrText/text() | //w:fldSimple/@w:instr'
    assert sd.xpath(field_xpath, namespaces=ns) == fd.xpath(field_xpath, namespaces=ns), 'Field instructions changed'
    for kind in ('bookmarkStart', 'bookmarkEnd'):
        assert canon_list(sd, '//w:' + kind) == canon_list(fd, '//w:' + kind), kind + ' changed'
    media_names = [n for n in zs.namelist() if n.startswith('word/media/') and not n.endswith('/')]
    assert media_names == [n for n in zf.namelist() if n.startswith('word/media/') and not n.endswith('/')]
    assert all(zs.read(n) == zf.read(n) for n in media_names), 'Image file bytes changed'
    caption_texts = [s for s in final_texts if caption_re.match(s)]
    assert len(caption_texts) == 6
    assert [int(caption_re.match(s).group(1)) for s in caption_texts] == list(range(1, 7))
    relationships = etree.fromstring(zf.read('word/_rels/document.xml.rels'))
    relmap = {x.get('Id'): x.get('Target') for x in relationships}
    visual_observations = [
        '两幅子图分别展示100、300、600、900、1200、1500、1800 s的径向温度和干基含水率，标题与实际内容一致。',
        '四幅子图展示0—4 h温度、空气水分指标及至60 h的50°C与0.05 kg/kg假设平台，标题及新增说明准确。',
        '左图为前4 h中心/表面温度，右图为全过程中心/表面干基含水率，标题及新增说明与时间尺度一致。',
        '左图为中心、表面、全域最大含水率的达标过程，右图放大临界时刻并区分临界根与严格达标取值，标题准确。',
        '左图为半径随时间收缩，右图为多个时刻以各自真实表面为终点的域内干基含水率分布，标题准确。',
        '图示经验边界阻力参数p=1、2、4与两组临界时长的关系，图中明确N=800，标题准确。',
    ]
    figures = []
    for i, node in enumerate(fb):
        if not node.xpath('.//w:drawing', namespaces=ns):
            continue
        number = len(figures) + 1
        caption = final_texts[i + 1]
        assert caption.startswith(f'图{number}  '), 'Caption is not directly after corresponding figure'
        embed = node.xpath('.//a:blip/@r:embed', namespaces=ns)[0]
        media_path = 'word/' + relmap[embed]
        local_media = qa / 'source_media' / Path(media_path).name
        assert zf.read(media_path) == local_media.read_bytes(), 'Viewed image does not match embedded image'
        figures.append({
            'number': number,
            'caption': caption,
            'embedded_media': media_path,
            'sha256': hashlib.sha256(zf.read(media_path)).hexdigest(),
            'caption_directly_after_image': True,
            'visual_content_check': visual_observations[number - 1],
        })
    assert len(figures) == 6
    audited = {
        'status': 'PASS_STATIC_SEMANTIC_AND_PRESERVATION',
        'source': str(source),
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'output': str(final),
        'output_sha256': hashlib.sha256(final.read_bytes()).hexdigest(),
        'independent_checks': {
            'all_32_local_replacements_complete': True,
            'changed_paragraph_count': len(set(x['block_index'] for x in recommendations['replacements'])),
            'two_figure_descriptions_complete': True,
            'full_body_text_matches_only_expected_changes_and_six_captions': True,
            'no_run_boundary_omissions_or_duplicate_phrases': True,
            'no_first_or_second_person': True,
            'formal_self_references_retained': {'本文': all_text.count('本文'), '本参赛队': all_text.count('本参赛队')},
            'no_figure_work_instructions_or_highlight': True,
            'six_caption_numbers_ordered_and_adjacent': True,
            'math_xml_identical_count': len(fd.xpath('//m:oMath', namespaces=ns)),
            'table_cell_contents_identical_count': len(final_tables),
            'result_table_xml_identical_count': 8,
            'symbol_table_only_expected_style_change': changed_symbol_cells,
            'entire_code_appendix_xml_identical': True,
            'field_instructions_identical': True,
            'bookmarks_identical': True,
            'media_files_byte_identical_count': len(media_names),
        },
        'figures': figures,
        'language_assessment': '逐段核对局部替换后的完整句子，未发现新病句、词语重复或替换残留。保留既有模型局限、结果适用条件及人工审查声明。',
        'limitations': '本审计只确认DOCX静态文本/结构及六张嵌入图与图名的对应；最终PDF分页、页面视觉排版由主代理独立渲染核验，不视为团队人工签核。',
    }
(qa / 'final_semantic_audit.json').write_text(json.dumps(audited, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(audited, ensure_ascii=False))
