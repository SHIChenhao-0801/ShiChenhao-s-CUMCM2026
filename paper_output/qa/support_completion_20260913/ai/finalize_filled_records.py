from pathlib import Path
from zipfile import ZipFile
import hashlib, json, datetime
from docx import Document

root = Path.cwd()
qa = root / 'paper_output/qa/support_completion_20260913'
support = root / '支撑材料'
replacements = {
    '00_支撑材料总说明.txt': [('已根据论文末尾AI报告填写已知工具和用途；真实交互、精确客户端版本及人工确认等字段须由团队据实补齐。', '已依据论文末尾AI报告及本次真实交互填写工具、七环节用途、三项交互节选和采纳情况，末尾保留团队签名与日期。')],
    '00_整理验收说明.txt': [('AI真实交互及团队确认仍待据实填写，论文PDF尚未定稿。', 'AI三项真实交互节选已实填，团队签名与日期保留空白；论文PDF尚未定稿。')],
}
for name, changes in replacements.items():
    p = support / name
    text = p.read_text(encoding='utf-8-sig')
    for before, after in changes:
        assert before in text
        text = text.replace(before, after)
    p.write_text(text, encoding='utf-8')

docx = support / 'AI工具使用详情.docx'
document = Document(docx)
text = '\n'.join(p.text for p in document.paragraphs) + '\n'.join(c.text for t in document.tables for r in t.rows for c in r.cells)
assert not any(s in text for s in ['待填写', '待本队确认', '待粘贴', '已人工审核通过', '本队已对采用'])
with ZipFile(docx) as z:
    assert z.testzip() is None
    assert 'word/comments.xml' not in z.namelist()
render = json.loads((qa / 'filled_ai_filled_render.json').read_text(encoding='utf-8-sig'))
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert render['docx_sha256'] == digest(docx)
assert render['page_count'] == 6
assert all(not p['geometry_suspects'] for p in render['pages'])
assert not document.core_properties.author
paper = root / '药材热湿耦合模型与干燥时间计算_附录修订版.docx'
assert digest(paper) == 'b6fbac8fefd87c10497a7c63f3638a7ead1f7e82c9bb0af7e773031a51f6960c'
files = [{'path': p.relative_to(support).as_posix(), 'bytes': p.stat().st_size, 'sha256': digest(p)} for p in sorted(support.rglob('*')) if p.is_file()]
assert len(files) == 137
audit = json.loads((qa / 'ai/filled_records_audit.json').read_text(encoding='utf-8'))
audit.update({'status': 'FILLED_AND_VISUALLY_CHECKED', 'pages': 6, 'visually_reviewed_pages': [1,2,3,4,5,6], 'table_count':len(document.tables), 'remaining_signature_only': True, 'file_count':137, 'model_versions_follow_manuscript_9_3':True, 'historical_template_audit_superseded':True})
(qa / 'ai/filled_records_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
final = json.loads((qa / 'final_delivery_audit.json').read_text(encoding='utf-8'))
final.update({'updated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'files':files, 'support_bytes':sum(f['bytes'] for f in files)})
final['ai_docx'].update({'sha256':digest(docx), 'actual_topic_excerpts':3, 'remaining':'Team signature and date only; final PDF not created.'})
(qa / 'final_delivery_audit.json').write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding='utf-8')
inventory = json.loads((qa / 'inventory_audit.json').read_text(encoding='utf-8'))
inventory.update({'final_file_manifest':files, 'support_bytes':final['support_bytes'], 'content_update':'AI document now has three actual topic excerpts; inventory membership and appendix DOCX unchanged.'})
(qa / 'inventory_audit.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding='utf-8')
(qa / 'ai/交付核查.txt').write_text('AI工具使用详情实填修订\n已填七环节、三项真实对话主题节选及处理/核验结果，删除原重复填写提示。\n三例为同一交互按主题节选，未虚构三次独立对话或Deepseek历史提示词。\n人工责任以末尾签认落实，未代签或写成人工已通过。\n最新版6页，7张表，已逐页检查；文件名及支撑137项清单成员不变。\nSHA256：'+digest(docx)+'\n', encoding='utf-8')
with (root / 'memoryskill.md').open('a', encoding='utf-8') as f:
    f.write('\n- 2026-09-13用户催促实填AI详情：已以本线程真实提示和回复按绘图、数值检验、附录清单三主题填完，七环节与采用位置已实填；删重复待核实，仅末尾团队签名/日期空白。6页逐页检查通过，文件名及137文件清单不变。最新审计ai/filled_records_audit.json覆盖前次空白模板状态。\n')
print('PASS: 6 pages, 3 actual topic excerpts, 7 tables, 137 files; source paper unchanged.')
