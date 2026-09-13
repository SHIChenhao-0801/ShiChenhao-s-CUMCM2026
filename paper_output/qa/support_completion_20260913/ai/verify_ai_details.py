from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import pymupdf
from lxml import etree

root = Path('D:/Document/数学建模/2026CUMCM')
qa = root / 'paper_output/qa/support_completion_20260913/ai'
out = root / '支撑材料/AI工具使用详情.docx'
source = root / '药材热湿耦合模型与干燥时间计算_附录修订版.docx'
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(out) as z:
    assert z.testzip() is None
    xml = etree.fromstring(z.read('word/document.xml'))
    styles = etree.fromstring(z.read('word/styles.xml'))
    text = '\n'.join(xml.xpath('//w:t/text()', namespaces=ns))
    assert len(xml.xpath('//w:tbl', namespaces=ns)) == 7
    assert len(xml.xpath('//w:pBdr', namespaces=ns)) == 0
    assert len(styles.xpath('//w:pBdr', namespaces=ns)) == 0
    assert not any(s in text for s in ['福州大学', '厦门大学', 'Shi Chenhao', 'D:/', 'D:\\', '☑', '☒'])
    assert all(s in text for s in ['赛题理解', '模型假设', '建模设计', '代码求解', '结果检验', '论文撰写', '辅助工作', '真实性声明'])
    assert 'word/comments.xml' not in z.namelist()
    assert len(xml.xpath('//w:ins|//w:del', namespaces=ns)) == 0

pdf = pymupdf.open(qa / 'rendered/AI工具使用详情.pdf')
assert len(pdf) == 6
assert len(list((qa / 'rendered').glob('page-*.png'))) == 6
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
assert source_hash == 'b6fbac8fefd87c10497a7c63f3638a7ead1f7e82c9bb0af7e773031a51f6960c'

audit = json.loads((qa / 'build_audit.json').read_text(encoding='utf-8'))
audit.update({
    'sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
    'output_size': out.stat().st_size,
    'render_status': 'PASS',
    'rendered_pages': 6,
    'page_images_visually_reviewed': [1, 2, 3, 4, 5, 6],
    'layout_findings': 'No clipped text, broken tables, title border, overlap or missing visible glyphs in final six page images.',
    'ooxml_crc_valid': True,
    'all_seven_stages_present': True,
    'human_checkboxes_not_preselected': True,
    'metadata_and_anonymity_checked': True,
    'comments_and_tracked_changes': False,
    'source_unchanged': True,
    'delivery_format': 'DOCX only; rendered PDF and PNGs retained only in internal QA.',
    'ready_for_human_completion': True,
    'ready_for_submission': False,
    'render_runtime': 'Codex bundled Python 3.12 and documents render_docx.py; user-configured local LibreOffice D:/Document/数学建模/tools/libreoffice/app/program/soffice.exe; bundled Poppler.',
})
(qa / 'build_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(qa / '交付核查.txt').write_text(
    'AI工具使用详情 DOCX 交付核查\n'
    '正式交付：支撑材料/AI工具使用详情.docx\n'
    f'字节数：{out.stat().st_size}\nSHA256：{audit["sha256"]}\n'
    '最终渲染为 6 页，7 张可编辑表格；六页 PNG 已逐页打开核查。\n'
    '覆盖工具版本、7环节、3份真实交互填写表、采纳修改、本队主导确认及真实性声明。\n'
    '保留末尾9.3所述用途，未添加新的既往使用事实。未编造提示词、AI回复或人工通过记录。\n'
    '待本队填写：两个客户端具体版本及使用时段、模型假设/设计是否使用AI、对应文件/章节位置、三份真实交互及采纳修改细节、人工核验和声明确认。\n'
    '正式支撑只新增DOCX；内部PDF/PNG用于排版核查，不能替代本队补齐后的最终AI详情PDF。\n'
    '源论文SHA256保持 b6fbac8fefd87c10497a7c63f3638a7ead1f7e82c9bb0af7e773031a51f6960c，未修改。\n'
    '状态：可编辑参考文档完成；尚未完成真实记录填写与团队确认，不标记可直接提交。\n',
    encoding='utf-8'
)
print(json.dumps(audit, ensure_ascii=False, indent=2))
