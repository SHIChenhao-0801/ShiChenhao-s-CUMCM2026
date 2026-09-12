from pathlib import Path
import os, sys, json, hashlib, subprocess, shutil
import pymupdf
sys.stdout.reconfigure(encoding='utf-8')
root=Path.cwd(); assert root.as_posix()=='D:/Document/数学建模/2026CUMCM'
qa=root/'paper_output/qa/figure_package_20260912';qa.mkdir(parents=True,exist_ok=True)
source=root/'paper_output/handoff/six_figures_20260912/六图绘图说明.docx'
version=sys.argv[1] if len(sys.argv)>1 else 'guide_v1'
cache=root/'tmp/cache/figure_package_20260912';render=cache/version;render.mkdir(parents=True,exist_ok=True)
temp=cache/'render_temp';temp.mkdir(exist_ok=True)
env=os.environ.copy();runtime=Path(sys.executable).parent.parent
env['PATH']=str(root.parent/'tools/libreoffice/app/program')+os.pathsep+str(runtime/'native/poppler/Library/bin')+os.pathsep+env['PATH']
for key in ('TEMP','TMP','TMPDIR'):env[key]=str(temp)
env['PYTHONIOENCODING']='utf-8'
renderer='C:/Users/Shi Chenhao/.codex/plugins/cache/openai-primary-runtime/documents/26.905.11957/skills/documents/render_docx.py'
with (qa/(version+'.log')).open('w',encoding='utf-8') as log:
    proc=subprocess.run([sys.executable,'-B',renderer,str(source),'--output_dir',str(render),'--emit_pdf','--dpi','150','--verbose'],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
assert proc.returncode==0
pdf=render/(source.stem+'.pdf');pdfout=qa/(version+'.pdf');shutil.copy2(pdf,pdfout)
doc=pymupdf.open(pdfout);pages=[]
for i,p in enumerate(doc,1):
    image=render/f'page-{i}.png';assert image.exists()
    pages.append({'page':i,'image':image.relative_to(root).as_posix(),'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'text':p.get_text()})
manifest={'version':version,'docx':source.relative_to(root).as_posix(),'docxSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'pdf':pdfout.relative_to(root).as_posix(),'pageCount':len(doc),'pages':pages,'renderExitCode':proc.returncode}
(qa/(version+'_manifest.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pages':len(doc),'pageStarts':[{'page':p['page'],'text':p['text'][:60]} for p in pages]},ensure_ascii=False))
