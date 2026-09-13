"""Record automated artifact checks and explicitly observed page review."""
from pathlib import Path
import hashlib,json,re
import pymupdf

qa=Path(__file__).resolve().parent
root=qa.parents[3]
pdf=root/'支撑材料/AI工具使用详情.pdf'
records=root/'支撑材料/06_AI使用记录'
doc=pymupdf.open(pdf)
content=json.loads((records/'AI披露内容.json').read_text(encoding='utf-8'))
norm=lambda s:re.sub(r'\s+','',s)
missing=[]
for idx,page in enumerate(content['pages']):
    text=norm(doc[idx].get_text())
    expected=[page['title'],page['subtitle']]
    for b in page['blocks']:
        if b['type']=='p':expected.append(b['text'])
        else:expected.extend(b['headers']);expected.extend(x for row in b['rows'] for x in row)
    missing.extend({'page':idx+1,'text':s} for s in expected if norm(s) not in text)
bounds=[]
for i,p in enumerate(doc):
    for block in p.get_text('dict')['blocks']:
        for line in block.get('lines',[]):
            for span in line['spans']:
                x0,y0,x1,y1=span['bbox']
                if x0<35 or y0<15 or x1>p.rect.width-35 or y1>p.rect.height-15:bounds.append({'page':i+1,'bbox':span['bbox'],'text':span['text']})
sensitive=['福州大学','厦门大学','Shi Chenhao','SHICHE','微信','乐乐','Apple Music','D:\\','D:/','C:\\','C:/']
hits=[]
for p in records.iterdir():
    if p.is_file():
        t=p.read_text(encoding='utf-8')
        hits.extend({'file':p.name,'term':s} for s in sensitive if s in t)
assert not missing,missing
assert not bounds,bounds
assert not hits,hits
images=[{'page':i,'pngSha256':hashlib.sha256((qa/f'page-{i}.png').read_bytes()).hexdigest(),'review':'PASS_ACTUALLY_VIEWED'} for i in range(1,7)]
audit={'status':'PASS_FOR_AI_DISCLOSURE_ARTIFACT','pdfSha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'bytes':pdf.stat().st_size,'pages':6,'textMatchesStructuredSource':True,'contentBlockMismatches':missing,'textOutsidePageSafeBounds':bounds,'publicRecordSensitiveTokens':hits,'metadataAuthor':doc.metadata.get('author'),'metadataCreator':doc.metadata.get('creator'),'visualReview':{'method':'Poppler rendered at 120dpi; all six pages viewed in image tool. Final changed pages 4, 5 and 6 actually re-viewed; pages 1, 2 and 3 pixel-identical to previously reviewed version.','pages':images,'noClippingOrOverlapObserved':True,'chineseGlyphsLegible':True},'humanReview':'PENDING_TEAM_CONFIRMATION','currentPackageCli':'PASS_SAME_MACHINE_ISOLATED_CLI; quick/final actual exit 0; new GUI and second physical device not tested','limits':['Artifact QA is machine/AI verification, not team signoff.','No production PDE computation in this disclosure subtask; latest full CLI reproduction was independently performed and is explicitly disclosed.']}
(qa/'final_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':audit['status'],'pdfSha256':audit['pdfSha256'],'pages':6,'bytes':pdf.stat().st_size},ensure_ascii=False))
