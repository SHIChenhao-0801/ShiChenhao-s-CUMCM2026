from pathlib import Path
from zipfile import ZipFile
from lxml import etree as ET
from docx import Document
import csv, hashlib, io, json, re, datetime, sys, difflib
import pymupdf

ROOT = Path.cwd()
assert ROOT.as_posix() == 'D:/Document/数学建模/2026CUMCM'
sys.stdout.reconfigure(encoding='utf-8')
QA = ROOT/'paper_output/qa/final_accuracy_20260913/numerical'
QA.mkdir(parents=True, exist_ok=True)
SUPPORT = ROOT/'支撑材料'
FROZEN = ROOT/'paper_output/results/production/final_v6a'
DOCX = ROOT/'药材热湿耦合模型与干燥时间计算_附录修订版.docx'
PDF = ROOT/'论文.pdf'
NS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{'+NS['w']+'}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def txt(el):
    out=[]
    for c in el.iter():
        if c.tag in (W+'t',M+'t'): out.append(c.text or '')
        elif c.tag == W+'tab': out.append('\t')
        elif c.tag == W+'br': out.append('\n')
    return ''.join(out)
inputs=[{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size,'mtime':datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat()} for p in [DOCX,PDF]]
doc=Document(DOCX)
with ZipFile(DOCX) as z:
    body=ET.fromstring(z.read('word/document.xml')).find('w:body',NS)
tables=[[[c.text for c in row.cells] for row in t.rows] for t in doc.tables]
pdf=pymupdf.open(PDF)
pages=[p.get_text(sort=True) for p in pdf]
(QA/'pdf_text.txt').write_text('\n'.join(f'\n--- PDF物理页 {i+1} ---\n{t}' for i,t in enumerate(pages)),encoding='utf-8')
headings=[(i,txt(el)) for i,el in enumerate(body) if re.match(r'^9\.2\.\d+\s',txt(el))]
first_source=headings[0][0]
(QA/'docx_main_and_derivations.txt').write_text('\n'.join(txt(el) for el in body[:first_source]),encoding='utf-8')
table_checks=[]
for p in sorted((SUPPORT/'04_结果表格/Referrence Table Files').glob('q*_paper_*.csv')):
    rows=list(csv.reader(io.StringIO(p.read_text(encoding='utf-8-sig'))))
    matches=[i for i,t in enumerate(tables) if t[1:]==rows[1:]]
    numeric_pdf_rows=[]
    for row in rows[1:]:
        # Match complete numeric rows after removing PDF whitespace; preserves minus and digit values.
        needle=''.join(row)
        where=[i+1 for i,t in enumerate(pages[:30]) if needle in re.sub(r'\s+','',t)]
        numeric_pdf_rows.append({'row':row,'pdf_pages':where})
    frozen=FROZEN/'outputs'/p.name
    table_checks.append({'csv':str(p.relative_to(ROOT)),'sha256':sha(p),'frozen_sha256':sha(frozen),
        'frozen_equal':p.read_bytes()==frozen.read_bytes(),'data_cells':sum(len(r) for r in rows[1:]),
        'docx_table_indices':matches,'pdf_numeric_rows':numeric_pdf_rows})
build=json.loads((ROOT/'paper_output/qa/appendix_revision_20260913/build_audit.json').read_text(encoding='utf-8-sig'))
source_checks=[]
for old,(i,heading) in zip(build['sources'],headings,strict=True):
    p=ROOT/old['relative_path']; lines=p.read_text(encoding='utf-8-sig').splitlines()
    extracted=[txt(el) for el in body[i+1:i+1+len(lines)]]
    diffs=[{'line':j+1,'current_source':a,'docx':b} for j,(a,b) in enumerate(zip(lines,extracted)) if a!=b]
    source_checks.append({'source':str(p.relative_to(ROOT)),'heading':heading,'source_lines':len(lines),'sha256':sha(p),
        'exact_lines_equal':lines==extracted,'differences':diffs})
    if '主要部分' in heading:
        stop=next(j for j in range(i+1,len(body)) if txt(body[j])=='9.3 AI 使用报告')
        excerpt=[txt(el) for el in body[i+1:stop]]
        while excerpt and not excerpt[-1]:excerpt.pop()
        omission=[{'type':tag,'source_line_start':a+1,'source_line_stop_inclusive':b,
                   'docx_line_start':c+1,'docx_line_stop_inclusive':d}
                  for tag,a,b,c,d in difflib.SequenceMatcher(None,lines,excerpt).get_opcodes() if tag!='equal']
        source_checks[-1].update({'declared_excerpt':True,'excerpt_lines':len(excerpt),
            'differences':omission,'matches_full_source_except_markdown_formatter':excerpt==lines[:154]+lines[162:],
            'note':'标题明确注明主要部分；省略源码155–162行的markdown报告格式化函数，数值比较主体未变。此节选不能被视为完整可独立运行源码。'})
books=[]
for p in sorted((SUPPORT/'04_结果表格').glob('result*.xlsx')):
    frozen=FROZEN/'outputs'/p.name
    books.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'frozen_equal':sha(p)==sha(frozen),'frozen_sha256':sha(frozen)})
old=json.loads((ROOT/'paper_output/qa/comment_sandbox_20260913/final_delivery_audit.json').read_text(encoding='utf-8-sig'))
bindings=[]
for r in old['evidenceBindings']:
    p=ROOT/r['path']; bindings.append({'path':r['path'],'recorded_sha256':r['sha256'],'current_sha256':sha(p),'equal':sha(p)==r['sha256']})
core_files=[]
for r in old['formalFiles']:
    if r['path'].startswith(('03_程序代码/','04_结果表格/')):
        p=SUPPORT/r['path']; core_files.append({'path':str(p.relative_to(ROOT)),'recorded_sha256':r['sha256'],'current_sha256':sha(p),'equal':sha(p)==r['sha256']})
current_assertions={}
for key,pat in {'drying_times':'57.472|51.090|6.3818','numerical_errors':'10⁻|10−|10-|1.80|0.011|1600|6400',
    'independent_comparisons':'129.8452|60.65|59.6239|65.4447|79.4187|43.0796|70.4059|38.3160',
    'method_root':'ROOT = Path','assumptions':'平台|映射|干骨架|干物质|潜热|材料坐标'}.items():
    current_assertions[key]=[{'page':i+1,'text':t} for i,t in enumerate(pages[:43]) if re.search(pat,t)]
report={'audit_time_local':datetime.datetime.now().isoformat(),'inputs':inputs,'pdf_pages':len(pdf),
    'seven_result_tables':table_checks,'all_297_docx_cells_equal':len(table_checks)==7 and sum(x['data_cells'] for x in table_checks)==297 and all(len(x['docx_table_indices'])==1 for x in table_checks),
    'all_seven_csv_equal_frozen':all(x['frozen_equal'] for x in table_checks),
    'all_pdf_table_rows_found':all(x['pdf_pages'] for t in table_checks for x in t['pdf_numeric_rows']),
    'four_workbooks':books,'appendix_sources':source_checks,'source_total_lines':sum(x['source_lines'] for x in source_checks),
    'all_36_sources_exact':len(source_checks)==36 and all(x['exact_lines_equal'] for x in source_checks),
    'sandbox_evidence_binding_checks':bindings,'sandbox_current_03_04_file_checks':core_files,
    'recorded_full_run':{k:old[k] for k in ['core','workbookCells','paperCells','savedArraysExactlyEqual','q3','q4']},
    'assertion_pdf_pages':current_assertions,'source_and_pdf_unchanged_during_audit':all(sha(ROOT/x['path'])==x['sha256'] for x in inputs),
    'scope':'Read-only comparison; no new PDE calculation; CLI metadata inspection is not VS GUI or human review.'}
(QA/'numerical_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k in ['inputs','pdf_pages','all_297_docx_cells_equal','all_seven_csv_equal_frozen','all_pdf_table_rows_found','source_total_lines','all_36_sources_exact','source_and_pdf_unchanged_during_audit']},ensure_ascii=False,indent=2))
print('source_differences',json.dumps([s for s in source_checks if not s['exact_lines_equal']],ensure_ascii=False))
print('unmatched_pdf_rows',json.dumps([{'csv':t['csv'],'rows':[r for r in t['pdf_numeric_rows'] if not r['pdf_pages']]} for t in table_checks if any(not r['pdf_pages'] for r in t['pdf_numeric_rows'])],ensure_ascii=False))
print('core_binding_mismatches',json.dumps([r for r in core_files+bindings if not r['equal']],ensure_ascii=False))
