from pathlib import Path
from zipfile import ZipFile
import json,hashlib,datetime,sys
import pymupdf
from docx import Document
from docx.oxml.ns import qn
sys.stdout.reconfigure(encoding='utf-8')
root=Path.cwd();assert root.as_posix()=='D:/Document/数学建模/2026CUMCM'
qa=root/'paper_output/qa/figure_guide_20260912'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v1=read(qa/'guide_v1_manifest.json');v2=read(qa/'guide_v2_manifest.json');build=read(qa/'build_manifest.json')
assert v2['pageCount']==7 and build['sha256']==v2['docxSha256']==sha(root/v2['docx'])
assert v2['pdfSha256']==sha(root/v2['pdf'])
with ZipFile(root/v2['docx']) as z:assert z.testzip() is None
d=Document(root/v2['docx']);assert len([p for p in d.paragraphs if p.style.name=='Heading 1'])==6
assert not list(d.styles.element.iter(qn('w:pBdr')))
for f in build['sources']:assert sha(root/f['path'])==f['sha256']
pages=[]
for old,p in zip(v1['pages'],v2['pages']):
    assert sha(root/p['image'])==p['sha256']
    changed=old['sha256']!=p['sha256']
    assert changed==(p['page'] in [1,5,6])
    pages.append({'page':p['page'],'sha256':p['sha256'],'actuallyViewedVersion':'guide_v2' if changed else 'guide_v1',
                  'unchangedFromViewedV1':not changed,'status':'PASS_VISUAL'})
outside=[]
for pi,p in enumerate(pymupdf.open(root/v2['pdf']),1):
    for b in p.get_text('dict')['blocks']:
        for line in b.get('lines',[]):
            for s in line['spans']:
                x0,y0,x1,y1=s['bbox']
                if min(x0,y0)<0 or x1>p.rect.width+.5 or y1>p.rect.height+.5:outside.append((pi,s['text']))
assert not outside
record={'status':'PASS','scope':'Standalone six-figure requirements and source-data Word guide',
 'docx':v2['docx'],'docxSha256':v2['docxSha256'],'pdfSha256':v2['pdfSha256'],'pages':pages,'pageCount':7,
 'layout':'One overview page and one page per figure; no clipping, overlap, missing text or split figure sections.',
 'sourceFilesInWord':len(build['sources']),'dataRecheck':'paper_output/qa/figure_guide_20260912/data_recheck.json',
 'figure2GuidePage':3,'newModelRuns':0,'paperModified':False,
 'imageReview':'Root actually viewed every guide_v1 page and re-viewed all changed guide_v2 pages1/5/6; four others have identical PNG hashes.'}
(qa/'final_audit.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
(qa/'final_audit.md').write_text('独立六图Word手册审查PASS。共7页，总览1页，每图1页。已实际查看初版全部7页，复看最终变化的1/5/6页，其余4页PNG哈希一致。14个文中数据文件当前哈希匹配；独立复核20个相关文件，无数值错误。图2明确241条记录和表头、4h实测末点及t>4h假设平台；图4补齐completion具体键名；图5写全核对路径；图6列六个全精度情景点。无新模型计算，不修改原论文。最终DOCX SHA256：'+v2['docxSha256']+'。',encoding='utf-8')
memory=root/'memoryskill.md';text=memory.read_text(encoding='utf-8')
section='''## 独立六图绘图手册（2026-09-12）

- 用户要求Word逐图说明要求和所需数据，已交付 `paper_output/paper/A题六张图绘制要求与数据说明.docx`，共7页（总览1页、每图1页）；每图完整路径、字段/形状、单位、时刻、图注和边界限制齐全，图2在手册第3页。QA `paper_output/qa/figure_guide_20260912/final_audit.json`。
- 图2CSV是241条观测+表头，末点4h=50.165°C/0.04986；t>4h平台50°C/0.05另画为假设。图4报告点从summary.completion取，图5域外留空，图6六点全为N800。未改论文/模型，未生成实际图像。
- 上轮Apple Music已点击播放并显示暂停按钮，但验证进度时用户按物理Esc终止；该音乐操作已停止，本轮独立手册不恢复桌面播放操作。

'''
if '## 独立六图绘图手册（2026-09-12）' not in text:
    text=text.replace('## 用户修改稿公式排版与精简附录（2026-09-12，最新）',section+'## 用户修改稿公式排版与精简附录（2026-09-12，最新）')
memory.write_text(text,encoding='utf-8')
wm=root/'paper_output/context/workflow_memory.json';w=read(wm)
w['six_figure_word_guide']={k:record[k] for k in ['status','docx','docxSha256','pageCount','figure2GuidePage','paperModified']}
w['six_figure_word_guide']['audit']='paper_output/qa/figure_guide_20260912/final_audit.json'
wm.write_text(json.dumps(w,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':'PASS','pages':7,'docx':record['docx'],'sha256':record['docxSha256']},ensure_ascii=False))
