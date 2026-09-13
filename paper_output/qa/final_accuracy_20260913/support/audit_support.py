from pathlib import Path
import io, json, hashlib, zipfile, re, csv, collections, difflib, datetime, ast
import xml.etree.ElementTree as ET
import fitz
from PIL import Image
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table

ROOT = Path('D:/Document/数学建模/2026CUMCM')
SUP = ROOT/'支撑材料'
QA = ROOT/'paper_output/qa/final_accuracy_20260913/support'
QA.mkdir(parents=True, exist_ok=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def dump(n,d): (QA/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def docx_text(p):
    with zipfile.ZipFile(p) as z:
        root=ET.fromstring(z.read('word/document.xml'))
        ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        paras=[''.join(e.itertext()) for e in []]
        paras=[''.join(e.text or '' for e in par.findall('.//w:t',ns)) for par in root.findall('.//w:p',ns)]
        text='\n'.join(paras)
        metadata=ET.tostring(ET.fromstring(z.read('docProps/core.xml')),encoding='unicode') if 'docProps/core.xml' in z.namelist() else ''
        return text, {'tables':len(root.findall('.//w:tbl',ns)), 'images':len([s for s in z.namelist() if s.startswith('word/media/')]), 'tracked_changes':len(root.findall('.//w:ins',ns))+len(root.findall('.//w:del',ns)), 'comments':'word/comments.xml' in z.namelist(), 'metadata':metadata}

files=sorted([p for p in SUP.rglob('*') if p.is_file()], key=lambda p:p.relative_to(SUP).as_posix())
records=[{'path':p.relative_to(SUP).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'md5':hashlib.md5(p.read_bytes()).hexdigest(),'mtime':datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat(),'windows_attributes':p.stat().st_file_attributes} for p in files]
actual={r['path']:r for r in records}
old=load('paper_output/qa/support_completion_20260913/final_delivery_audit.json')
oldfiles={r['path']:r for r in old['files']}
diff={'added':sorted(actual.keys()-oldfiles.keys()),'removed':sorted(oldfiles.keys()-actual.keys()),'modified':[k for k in actual.keys()&oldfiles.keys() if actual[k]['sha256']!=oldfiles[k]['sha256']]}
counts=dict(collections.Counter(p.relative_to(SUP).parts[0] if len(p.relative_to(SUP).parts)>1 else 'ROOT' for p in files))
checks={'archive_crc':[],'pdf_open':[],'image_verify':[],'python_parse':[]}
texts={}
docxs={}
for p in files:
    rel=p.relative_to(SUP).as_posix()
    if p.suffix.lower() in ('.docx','.xlsx','.npz','.zip'):
        try:
            with zipfile.ZipFile(p) as z: bad=z.testzip()
            checks['archive_crc'].append({'path':rel,'pass':bad is None,'bad_entry':bad})
        except Exception as e: checks['archive_crc'].append({'path':rel,'pass':False,'error':str(e)})
    if p.suffix.lower()=='.pdf':
        try:
            d=fitz.open(p); texts[rel]='\n'.join(page.get_text() for page in d)
            checks['pdf_open'].append({'path':rel,'pass':not d.is_encrypted,'pages':len(d),'metadata':d.metadata,'page_sizes':sorted(set((round(pg.rect.width,2),round(pg.rect.height,2)) for pg in d))})
            d.close()
        except Exception as e: checks['pdf_open'].append({'path':rel,'pass':False,'error':str(e)})
    if p.suffix.lower()=='.png':
        try:
            with Image.open(p) as im: dim=im.size; im.verify()
            checks['image_verify'].append({'path':rel,'pass':True,'dimensions':dim})
        except Exception as e: checks['image_verify'].append({'path':rel,'pass':False,'error':str(e)})
    if p.suffix.lower()=='.docx': texts[rel],docxs[rel]=docx_text(p)
    if p.suffix.lower() in ('.txt','.csv','.py','.m','.mjs','.ps1','.r','.html','.sln','.pyproj'):
        try: texts[rel]=p.read_text(encoding='utf-8-sig')
        except UnicodeError: texts[rel]=p.read_text(encoding='gb18030',errors='replace')
    if p.suffix.lower()=='.py':
        try: ast.parse(texts[rel],filename=rel); checks['python_parse'].append({'path':rel,'pass':True})
        except Exception as e: checks['python_parse'].append({'path':rel,'pass':False,'error':str(e)})

listing={}
for name in ['00_文件清单.txt','00_可用于论文附录的支撑清单.txt']:
    listing[name]={'missing_paths':[k for k in actual if k not in texts[name]],'claims_137':'137' in texts[name]}
inv_text, inv_meta=docx_text(ROOT/'支撑材料文件列表_附录用.docx')
inv_doc=Document(ROOT/'支撑材料文件列表_附录用.docx'); inv_group=None; inv_paths=[]
for el in inv_doc.element.body:
    if el.tag.endswith('}p'):
        m=re.match(r'^表(\d+)\s+(.+)$',Paragraph(el,inv_doc).text)
        if m: inv_group=m[2]
    elif el.tag.endswith('}tbl'):
        rows=[[c.text for c in r.cells] for r in Table(el,inv_doc).rows]
        if rows[0]==['序号','文件名','用途']:
            for number,name,purpose in rows[1:]: inv_paths.append(name if inv_group=='根目录' else inv_group+'/'+name)
listing['支撑材料文件列表_附录用.docx']={'entry_count':len(inv_paths),'missing_paths':sorted(actual.keys()-set(inv_paths)),'extra_paths':sorted(set(inv_paths)-actual.keys()),'duplicates':[k for k,v in collections.Counter(inv_paths).items() if v>1]}

privacy=[]
patterns={'identity':r'福州大学|厦门大学|Shi\s*Chenhao|SHIChenhao|施陈灏','local_path':r'[A-Za-z]:[\\/](?:Users|Document|Runtime|Work|Control)|/Users/|/home/','credential':r'(?i)(?:sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)'}
metadata_hits=[]
for p in files:
    if p.suffix.lower() in ('.docx','.xlsx'):
        with zipfile.ZipFile(p) as z:
            for n in z.namelist():
                if n.startswith('docProps/') and n.endswith('.xml'):
                    t=z.read(n).decode('utf-8')
                    if re.search(patterns['identity'],t): metadata_hits.append({'path':p.relative_to(SUP).as_posix(),'part':n,'category':'team_identity'})
for rel,t in texts.items():
    for category,pattern in patterns.items():
        hits=[]
        for n,line in enumerate(t.splitlines(),1):
            if re.search(pattern,line): hits.append({'line':n,'excerpt':line[:300] if category!='credential' else '[REDACTED]'})
        if hits: privacy.append({'path':rel,'category':category,'hits':hits})

core=load('paper_output/qa/comment_sandbox_20260913/final_delivery_audit.json')
core_files=[r for r in core['formalFiles'] if r['path'].startswith('03_程序代码/')]
core_binding={'files_checked':len(core_files),'mismatches':[r['path'] for r in core_files if r['path'] not in actual or actual[r['path']]['sha256']!=r['sha256']], 'evidence_bindings':[{'path':r['path'],'exists':(ROOT/r['path']).exists(),'hash_matches':(ROOT/r['path']).exists() and sha(ROOT/r['path'])==r['sha256']} for r in core['evidenceBindings']], 'actual_historical_run':core['core'],'workbook_cells':core['workbookCells'],'paper_cells':core['paperCells']}
inp=[]
for r in csv.DictReader(io.StringIO(texts['03_程序代码/input_manifest.csv'])):
    p=SUP/'03_程序代码'/r['path']; inp.append({'path':r['path'],'pass':p.exists() and sha(p)==r['sha256'] and p.stat().st_size==int(r['bytes'])})
ver=load('paper_output/qa/support_completion_20260913/verification/audit.json')
ver_binding={'files_checked':len(ver['files']),'mismatches':[r['path'] for r in ver['files'] if '05_数值检验与实验/'+r['path'] not in actual or actual['05_数值检验与实验/'+r['path']]['sha256']!=r['sha256']], 'runs':ver['runs'],'fine_grid_rerun':False, 'matplotlib_requirement':texts['05_数值检验与实验/Python检验源码/requirements.txt']}
for key in ('grid','time','method'):
    runroot=ROOT/f'paper_output/qa/support_completion_20260913/verification/isolated_{key}'
    if runroot.exists():
        run_files=[p for p in runroot.rglob('*.py')]
        ver_binding[f'{key}_source_matches']=[{'path':str(p.relative_to(runroot)).replace('\\','/'),'pass':(SUP/'05_数值检验与实验/Python检验源码'/p.relative_to(runroot)).exists() and sha(SUP/'05_数值检验与实验/Python检验源码'/p.relative_to(runroot))==sha(p)} for p in run_files]

figure_binding=[]
for r in csv.DictReader(io.StringIO(texts['06_绘图程序与数据/数据来源与校验.csv'])):
    p=SUP/'06_绘图程序与数据'/r['文件']
    with p.open(encoding='utf-8-sig',newline='') as f: nr=sum(1 for _ in csv.reader(f))-1
    figure_binding.append({'path':r['文件'],'pass':sha(p).lower()==r['SHA256'].lower(),'rows':nr,'row_count_matches':nr==int(r['数据行数_不含表头'])})
figure_pngs=[]
for r in csv.DictReader(io.StringIO(texts['06_绘图程序与数据/图像校验.csv'])):
    p=SUP/'06_绘图程序与数据'/r['文件']; figure_pngs.append({'path':r['文件'],'pass':sha(p).lower()==r['SHA256'].lower()})
r_current=SUP/'06_绘图程序与数据/draw_figures.R'
r_executed=ROOT/'paper_output/qa/support_completion_20260913/figures/isolated_support/draw_figures.R'
r_binding={'sha256':sha(r_current),'executed_copy_exists':r_executed.exists(),'executed_copy_matches':r_executed.exists() and sha(r_executed)==sha(r_current),'run_status_path':'paper_output/qa/support_completion_20260913/figures/run_status.csv','log_sha256':sha(ROOT/'paper_output/qa/support_completion_20260913/figures/R_reproduction.log')}

buf=io.BytesIO()
with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in files: z.writestr(p.relative_to(SUP).as_posix(),p.read_bytes())
estimate={'method':'In-memory ZIP DEFLATE level 9; UTF-8 file names; no root directory entries; no archive saved','bytes':buf.tell(),'decimal_20MB_limit':20000000,'binary_20MiB_limit':20971520,'fits_decimal_20MB':buf.tell()<=20000000,'fits_binary_20MiB':buf.tell()<=20971520}
with zipfile.ZipFile(buf) as z: estimate['largest_compressed_members']=[{'path':i.filename,'compressed_bytes':i.compress_size,'source_bytes':i.file_size} for i in sorted(z.infolist(),key=lambda i:-i.compress_size)[:12]]
oldzip=ROOT/'支撑材料临时.zip'
with zipfile.ZipFile(oldzip) as z:
    old_crc=z.testzip(); names=[n for n in z.namelist() if not n.endswith('/')]
    zmap={}
    for n in names:
        key=n.replace('\\','/')
        if key.startswith('支撑材料/'): key=key[len('支撑材料/'):]
        zmap[key]={'archive_path':n,'sha256':hashlib.sha256(z.read(n)).hexdigest()}
zipcomp={'bytes':oldzip.stat().st_size,'sha256':sha(oldzip),'crc_bad_entry':old_crc,'files':len(zmap),'sample_paths':names[:8], 'missing_current_files':sorted(actual.keys()-zmap.keys()),'extra_files':sorted(zmap.keys()-actual.keys()),'different_common_files':[k for k in actual.keys()&zmap.keys() if actual[k]['sha256']!=zmap[k]['sha256']],'can_submit_as_current':False}

ai_pdf=texts.get('AI工具使用详情.pdf',''); ai_docx=texts.get('AI工具使用详情.docx','')
for name,t in [('AI_PDF_提取文本.txt',ai_pdf),('AI_DOCX_提取文本.txt',ai_docx)]: (QA/name).write_text(t,encoding='utf-8')
old_ai=(ROOT/'paper_output/qa/support_completion_20260913/ai/filled_text.txt').read_text(encoding='utf-8-sig')
(QA/'AI_新旧文本差异.txt').write_text('\n'.join(difflib.unified_diff(old_ai.splitlines(),ai_docx.splitlines(),fromfile='15时实填版本',tofile='当前用户DOCX',lineterm='')),encoding='utf-8')
norm=lambda x:re.sub(r'\s+','',x)
ai_cmp={'docx_sha256':actual.get('AI工具使用详情.docx',{}).get('sha256'),'pdf_sha256':actual.get('AI工具使用详情.pdf',{}).get('sha256'),'docx_metadata':docxs.get('AI工具使用详情.docx'),'normalized_text_exact':norm(ai_docx)==norm(ai_pdf),'normalized_similarity':difflib.SequenceMatcher(None,norm(ai_docx),norm(ai_pdf),autojunk=False).ratio(),'old_filled_docx_hash_matches':actual.get('AI工具使用详情.docx',{}).get('sha256')==load('paper_output/qa/support_completion_20260913/ai/filled_records_audit.json')['output_sha256']}
ai_cmp['body_text_matches_after_removing_pdf_page_footers']=norm(ai_docx)==re.sub(r'第[1-5]页共5页','',norm(ai_pdf))
report={'audited_at':datetime.datetime.now().astimezone().isoformat(),'status':'REVIEW_IN_PROGRESS','scope':'Read-only submission support accuracy audit; no compressed artifact created, no PDE run, no GUI or human review claim','file_count':len(files),'support_bytes':sum(r['bytes'] for r in records),'directory_counts':counts,'files':records,'changes_since_1540_audit':diff,'integrity':checks,'forbidden_files':[r['path'] for r in records if Path(r['path']).suffix.lower() in ('.json','.md','.zip','.rar','.7z')],'hidden_ide_files':[r['path'] for r in records if r['windows_attributes'] & 2 or any(part in ('.vs','__pycache__','.venv') for part in Path(r['path']).parts) or Path(r['path']).name=='UpgradeLog.htm'],'empty_files':[r['path'] for r in records if r['bytes']==0],'listings':listing,'privacy_path_scan':privacy,'core_provenance':core_binding,'core_input_manifest':inp,'verification_provenance':ver_binding,'figures_csv':figure_binding,'zip_memory_estimate':estimate,'old_zip_comparison':zipcomp,'ai_details':ai_cmp}
dump('support_audit.json',report)
report['metadata_identity_hits']=metadata_hits
report['figures_png']=figure_pngs
report['R_execution_binding']=r_binding
dump('support_audit.json',report)
summary={k:report[k] for k in ['file_count','support_bytes','directory_counts','changes_since_1540_audit','forbidden_files','hidden_ide_files','empty_files','listings','zip_memory_estimate','ai_details']}
summary['integrity_counts']={k:{'checked':len(v),'failures':[i for i in v if not i['pass']]} for k,v in checks.items()}
summary['core_files']=core_binding['files_checked']; summary['core_mismatches']=core_binding['mismatches']; summary['verification_mismatches']=ver_binding['mismatches']; summary['old_zip_diff_counts']={k:len(zipcomp[k]) for k in ['missing_current_files','extra_files','different_common_files']}
print(json.dumps(summary,ensure_ascii=False,indent=2))
