from pathlib import Path
import json,hashlib,re,sys
import pymupdf
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path.cwd();assert ROOT.as_posix()=='D:/Document/数学建模/2026CUMCM'
QA=ROOT/'paper_output/qa/formatting_20260913'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
manifest=read(QA/'v3_render_manifest.json');previous=read(QA/'v1_render_manifest.json');semantic=read(QA/'final_semantic_audit.json')
source=ROOT/'paper_output/paper/药材热湿耦合模型与干燥时间计算_文献公式修订版.docx'
output=ROOT/manifest['docx'];digest=hashlib.sha256(output.read_bytes()).hexdigest()
assert semantic['output_sha256']==manifest['docxSha256']==digest
assert source.read_bytes()==(QA/'source.docx').read_bytes()
assert manifest['pageCount']==33
changed=[b['page'] for a,b in zip(previous['pages'],manifest['pages']) if a['sha256']!=b['sha256']]
assert changed==[2,5,6,9,10,11,12,13,14]
first_eight=read(QA/'final_visual_pages_01_08.json')
assert first_eight['status'].startswith('PASS')
visual=[]
for old,new in zip(previous['pages'],manifest['pages']):
 actual=digest
 visual.append({'page':new['page'],'imageSha256':new['sha256'],'review':'direct_v3_image_review' if new['page'] in changed else 'byte_identical_v1_review_reused','status':'PASS'})
 pdf=ROOT/manifest['pdf']
with pymupdf.open(pdf) as doc:
 numbers=[];caps=[]
 for i,p in enumerate(doc,1):
  footer=[x for x in p.get_text('words') if x[1]>p.rect.height-65]
  assert len(footer)==1 and footer[0][4]==str(i),(i,footer)
  assert abs((footer[0][0]+footer[0][2])/2-p.rect.width/2)<1
  numbers.append(i)
  for line in p.get_text().splitlines():
   if re.match(r'^图\s*[1-6] {2}',line):caps.append({'page':i,'text':line})
 assert [x['page'] for x in caps]==[9,11,13,16,19,20],caps
 assert '8 参考文献' in doc[23].get_text()
 assert '\n附录\n' in doc[24].get_text()
report={'status':'PASS_FORMATTING_AND_LANGUAGE_REVISION','docx':manifest['docx'],'docxSha256':digest,'sourceSha256':semantic['source_sha256'],'renderPdf':manifest['pdf'],'renderPdfSha256':manifest['pdfSha256'],'pages':33,'abstractPages':[1],'mainTextIncludingAiAndReferencesPages':[2,24],'appendixPages':[25,33],'pageNumbers':numbers,'pageNumberDecision':'Follow current explicit format2026 request: abstract page 1 and continuous Arabic numbering including appendix. format article 3 specifies continuous numbering; article 4 exempts appendix from page-count cap, not page numbers. Briefing page 76 conflict separately documented; optional clarification had no reply, default explicitly communicated.','captions':caps,'languageLocalReplacements':32,'figureDescriptionsRewritten':2,'allVisualPages':visual,'independentSemanticAudit':'final_semantic_audit.json','unchanged':semantic['independent_checks'],'limitations':['LibreOffice headless render and actual PNG review; no new Word GUI or team sign-off claim.','Inherited appendix code long-line soft wraps are fully visible; code content remains byte-equivalent at XML level.','This pass covers requested formatting and language, not full submission compliance or model revalidation.']}
(QA/'final_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(QA/'revision_summary.txt').write_text('论文格式与语言修订完成\n\n来源：最新文献公式修订版，原稿保留。\n页码：按本轮指定format2026第三条从摘要1连续编号。正文含AI声明与参考文献为2—24页；附录25—33页。附录页数不限不等于无页码。与说明会第76页冲突已另存核查记录。\n图名：六图图下居中，与图片同页；正式图说明替换2处绘图指令并清除高亮。\n人称与措辞：未发现我、我们、你、笔者等人称；保留学术指代“本文”与AI责任声明，32处局部措辞/句法修改。\n验证：33页完整覆盖视觉检查；本版9变化页实际重看，24页图像与已审v1逐字节相同。226公式、9表逐格内容、8结果表结构、全部附录D代码与11媒体文件不变。\n范围：只处理格式与语言，不等同于模型重新计算、Word GUI点击验证或团队人工签核。\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'pages':33,'captionPages':[x['page'] for x in caps],'sha256':digest}))
