from pathlib import Path
import os,sys,json,hashlib,subprocess,shutil
import pymupdf
ROOT=Path.cwd();assert ROOT.as_posix()=='D:/Document/数学建模/2026CUMCM'
sys.stdout.reconfigure(encoding='utf-8')
QA=ROOT/'paper_output/qa/appendix_full_20260913'
version=sys.argv[1]
source=ROOT/'paper_output/paper/药材热湿耦合模型与干燥时间计算_完整附录.docx'
cache=ROOT/'tmp/cache/appendix_full_20260913';render=cache/version
render.mkdir(parents=True,exist_ok=True);temp=cache/'temp';temp.mkdir(exist_ok=True)
env=os.environ.copy();runtime=Path(sys.executable).parent.parent
lo=ROOT.parent/'tools/libreoffice/app/program'
assert (lo/'soffice.exe').exists()
env['PATH']=str(lo)+os.pathsep+str(runtime/'native/poppler/Library/bin')+os.pathsep+env['PATH']
for key in ('TEMP','TMP','TMPDIR'):env[key]=str(temp)
env['PYTHONIOENCODING']='utf-8'
renderer='C:/Users/Shi Chenhao/.codex/plugins/cache/openai-primary-runtime/documents/26.905.11957/skills/documents/render_docx.py'
cmd=[sys.executable,'-B',renderer,str(source),'--output_dir',str(render),'--emit_pdf','--dpi','120','--verbose']
with (QA/(version+'_render.log')).open('w',encoding='utf-8') as log:
 proc=subprocess.run(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
assert proc.returncode==0,proc.returncode
pdf=render/(source.stem+'.pdf');pdfout=QA/(version+'.pdf');shutil.copy2(pdf,pdfout)
doc=pymupdf.open(pdfout);pages=[]
for i,p in enumerate(doc,1):
 image=render/f'page-{i}.png';assert image.exists()
 spans=[s for b in p.get_text('dict')['blocks'] if 'lines' in b for line in b['lines'] for s in line['spans']]
 clipped=[{'text':s['text'],'bbox':s['bbox']} for s in spans if s['bbox'][0]<40 or s['bbox'][2]>p.rect.width-35 or s['bbox'][1]<30 or s['bbox'][3]>p.rect.height-15]
 pages.append({'page':i,'image':image.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'text':p.get_text(),'suspect_geometry':clipped,'footer':[w for w in p.get_text('words') if w[1]>p.rect.height-65]})
manifest={'version':version,'docx':source.relative_to(ROOT).as_posix(),'docxSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'pdf':pdfout.relative_to(ROOT).as_posix(),'pdfSha256':hashlib.sha256(pdfout.read_bytes()).hexdigest(),'pageCount':len(doc),'pages':pages,'renderExitCode':proc.returncode,'libreoffice':str(lo/'soffice.exe')}
(QA/(version+'_render_manifest.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'version':version,'pages':len(doc),'geometry_suspects':[p['page'] for p in pages if p['suspect_geometry']]},ensure_ascii=False))
