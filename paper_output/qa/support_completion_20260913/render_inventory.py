from pathlib import Path
import os,sys,json,hashlib,subprocess
import pymupdf

ROOT=Path(__file__).resolve().parents[3]
QA=Path(__file__).resolve().parent
version=sys.argv[1] if len(sys.argv)>1 else 'v1'
source=ROOT/'支撑材料文件列表_附录用.docx'
render=ROOT/'tmp/cache/support_completion_20260913/inventory'/version
render.mkdir(parents=True,exist_ok=True)
temp=render.parent/'temp';temp.mkdir(exist_ok=True)
env=os.environ.copy()
lo=ROOT.parent/'tools/libreoffice/app/program'
runtime=Path(sys.executable).parent.parent
env['PATH']=str(lo)+os.pathsep+str(runtime/'native/poppler/Library/bin')+os.pathsep+env['PATH']
env['LIBREOFFICE_PATH']=str(lo/'soffice.com')
for key in ('TEMP','TMP','TMPDIR'):env[key]=str(temp)
env['PYTHONIOENCODING']='utf-8'
renderer='C:/Users/Shi Chenhao/.codex/plugins/cache/openai-primary-runtime/documents/26.905.11957/skills/documents/render_docx.py'
with (QA/(version+'_inventory_render.log')).open('w',encoding='utf-8') as log:
    result=subprocess.run([sys.executable,'-B',renderer,str(source),'--output_dir',str(render),'--emit_pdf','--dpi','110','--verbose'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
assert result.returncode==0,result.returncode
pdf=render/(source.stem+'.pdf');doc=pymupdf.open(pdf)
pages=[]
for i,p in enumerate(doc,1):
    image=render/f'page-{i}.png';assert image.is_file()
    spans=[s for b in p.get_text('dict')['blocks'] if 'lines' in b for line in b['lines'] for s in line['spans']]
    clipped=[s['text'] for s in spans if s['bbox'][0]<40 or s['bbox'][2]>p.rect.width-35 or s['bbox'][1]<30 or s['bbox'][3]>p.rect.height-20]
    pages.append({'page':i,'png':str(image),'png_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'text':p.get_text(),'geometry_suspects':clipped})
report={'version':version,'docx_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'page_count':len(doc),'pdf':str(pdf),'pages':pages,'render_exit':result.returncode}
(QA/(version+'_inventory_render.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pages':len(doc),'geometry_suspect_pages':[p['page'] for p in pages if p['geometry_suspects']]},ensure_ascii=False))
