"""Inspect actual PDF geometry, equation numbering and full code text binding."""
from pathlib import Path
import hashlib
import json
import re
import sys
import pymupdf
from docx import Document
from docx.oxml.ns import qn

sys.stdout.reconfigure(encoding='utf-8')
root=Path(__file__).resolve().parents[1]
assert Path.cwd().resolve()==root
qa=root/'paper_output/qa/manuscript_20260912'
m=json.loads((qa/'render_manifest.json').read_text(encoding='utf-8'))
pdf=root/m['pdf'];doc=pymupdf.open(pdf)
outside=[];margins=[];strange=[]
for i,page in enumerate(doc,1):
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines',[]):
            text=''.join(s['text'] for s in line['spans'])
            x0,y0,x1,y1=line['bbox']
            if x0<0 or x1>page.rect.width+.1 or y0<0 or y1>page.rect.height+.1:
                outside.append({'page':i,'bbox':[x0,y0,x1,y1],'text':text[:160]})
            if x0<68 or x1>page.rect.width-68:
                margins.append({'page':i,'bbox':[x0,y0,x1,y1],'text':text[:160]})
            if i<38 and ('¿' in text or '\ufffd' in text):strange.append({'page':i,'text':text})
d=Document(root/'paper_output/final_paper.docx')
numbers=[]
for p in d.paragraphs:
    if p._p.find(qn('m:oMath')) is not None and re.search(r'\t\(\d+\)$',p.text):
        numbers.append(int(re.search(r'\((\d+)\)$',p.text).group(1)))
assert numbers==list(range(1,69)),numbers
report={'docxSha256':m['docxSha256'],'pdfSha256':m['pdfSha256'],'pages':len(doc),'numberedEquations':numbers,'outsidePage':outside,'marginCandidates':margins,'unexpectedMathGlyphs':strange,'scope':'Automatic geometry is supplementary; each rendered page must also be visually inspected.'}
(qa/'layout_geometry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('numberedEquations','scope')},ensure_ascii=False,indent=1))
