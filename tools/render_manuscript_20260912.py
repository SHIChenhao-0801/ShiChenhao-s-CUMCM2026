"""Run the packaged Word renderer with isolated contest-local caches."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
sys.stdout.reconfigure(encoding='utf-8')

root=Path(__file__).resolve().parents[1]
assert Path.cwd().resolve()==root
qa=root/'paper_output/qa/manuscript_20260912'
version=sys.argv[1] if len(sys.argv)>1 else 'v1'
cache=root/'tmp/cache/manuscript_20260912'
render=cache/('render_'+version)
temp=cache/'render_temp'
render.mkdir(parents=True,exist_ok=True);temp.mkdir(parents=True,exist_ok=True)
runtime=Path(sys.executable).parent.parent
script=Path('C:/Users/Shi Chenhao/.codex/plugins/cache/openai-primary-runtime/documents/26.905.11957/skills/documents/render_docx.py')
lo=root.parent/'tools/libreoffice/app/program'
poppler=runtime/'native/poppler/Library/bin'
env=os.environ.copy()
env['PATH']=str(lo)+os.pathsep+str(poppler)+os.pathsep+env['PATH']
for key in ('TEMP','TMP','TMPDIR'):env[key]=str(temp)
env['PYTHONIOENCODING']='utf-8'
source=root/'paper_output/final_paper.docx'
command=[sys.executable,'-B',str(script),str(source),'--output_dir',str(render),'--emit_pdf','--dpi','150','--verbose']
with (qa/('render_'+version+'.log')).open('w',encoding='utf-8') as log:
    proc=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
assert proc.returncode==0,f'Render failed: {proc.returncode}; inspect log.'
pdf=render/'final_paper.pdf'
assert pdf.is_file()
retained=qa/'rendered';retained.mkdir(exist_ok=True)
pdfout=retained/'final_paper.pdf';shutil.copyfile(pdf,pdfout)
pages=sorted(render.glob('page-*.png'),key=lambda p:int(p.stem.split('-')[-1]))
assert pages,'No packaged renderer page images.'
import fitz
doc=fitz.open(pdfout)
assert len(doc)==len(pages)
texts=[p.get_text() for p in doc]
page_records=[]
for i,(p,t) in enumerate(zip(pages,texts),1):
    page_records.append({'page':i,'path':p.relative_to(root).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'textChars':len(t),'start':t[:110]})
(qa/'render_page_texts.json').write_text(json.dumps(texts,ensure_ascii=False,indent=2),encoding='utf-8')
manifest={'renderedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':command,'returncode':proc.returncode,'docx':source.relative_to(root).as_posix(),'docxSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'pdf':pdfout.relative_to(root).as_posix(),'pdfSha256':hashlib.sha256(pdfout.read_bytes()).hexdigest(),'libreoffice':str(lo/'soffice.exe'),'pageCount':len(pages),'pages':page_records,'cachePolicy':'PDF, manifest and review evidence are retained; per-page PNG images are rebuildable contest-local cache.'}
(qa/'render_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pageCount':len(pages),'pdfBytes':pdfout.stat().st_size,'pageStarts':[{k:r[k] for k in ('page','start')} for r in page_records[:45]]},ensure_ascii=False),flush=True)
