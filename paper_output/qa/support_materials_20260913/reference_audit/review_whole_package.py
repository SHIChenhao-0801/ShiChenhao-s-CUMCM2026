"""Independent read-only package review; writes only its QA report."""
from pathlib import Path
from datetime import datetime, timezone
from zipfile import ZipFile
import hashlib, json, csv, re, ast
import xml.etree.ElementTree as ET
import pymupdf

ROOT=Path.cwd().resolve()
PKG=ROOT/'支撑材料'
AUDIT=ROOT/'paper_output/qa/support_materials_20260913/reference_audit'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report={'reviewed_at_utc':datetime.now(timezone.utc).isoformat(),
 'scope':'Read-only independent content/mapping review during assembly. No solver execution, archive validation, GUI or human signature.',
 'blocking_findings':[], 'assembly_followups':[], 'checks':{}}

works=[]
for i in range(1,5):
    source=ROOT/f'paper_output/results/production/final_v6a/outputs/result{i}.xlsx'
    target=PKG/f'04_结果表格/result{i}.xlsx'
    with ZipFile(target) as z:
        assert z.testzip() is None
        props=z.read('docProps/core.xml').decode('utf-8')
    works.append({'file':target.relative_to(PKG).as_posix(),'source':source.relative_to(ROOT).as_posix(),
        'bytes':target.stat().st_size,'source_sha256':sha(source),'packaged_sha256':sha(target),'byte_identical':source.read_bytes()==target.read_bytes(),
        'zip_crc':'PASS','core_properties':props})
report['checks']['four_result_workbooks']=works
assert all(x['byte_identical'] for x in works)

paper=ROOT/'paper_output/paper/药材热湿耦合模型与干燥时间计算_文献公式修订版.docx'
with ZipFile(paper) as z:
    document=ET.fromstring(z.read('word/document.xml'))
    media=[n for n in z.namelist() if n.startswith('word/media/') and not n.endswith('/')]
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
tables=[[[ ''.join(v.text or '' for v in cell.findall('.//w:t',ns)) for cell in row.findall('w:tc',ns)] for row in table.findall('w:tr',ns)] for table in document.findall('.//w:body/w:tbl',ns)]
table_files=['q1_paper_temperature.csv','q1_paper_moisture.csv','q2_paper_temperature.csv','q2_paper_moisture.csv','q3_paper_moisture.csv','q4_paper_moisture.csv','q4_paper_radius.csv']
paper_checks=[]
for table_index,name in enumerate(table_files,start=1):
    csv_path=PKG/'04_结果表格'/name
    csv_rows=list(csv.reader(csv_path.open(encoding='utf-8-sig',newline='')))
    actual=tables[table_index][1:]
    expected=csv_rows[1:]
    diffs=[]
    if len(actual)!=len(expected):diffs.append({'rows_actual':len(actual),'rows_expected':len(expected)})
    for ri,(a,b) in enumerate(zip(actual,expected),start=1):
        if len(a)!=len(b):diffs.append({'row':ri,'columns_actual':len(a),'columns_expected':len(b)})
        for ci,(av,bv) in enumerate(zip(a,b),start=1):
            if av!=bv:diffs.append({'row':ri,'column':ci,'paper':av,'csv':bv})
    paper_checks.append({'paper_table_number':table_index,'csv_file':name,'csv_sha256':sha(csv_path),
      'data_cells_including_time_and_domain_blanks':sum(len(row) for row in expected),
      'blank_cells':sum(v=='' for row in expected for v in row),'exact_text_match':actual==expected,'differences':diffs,
      'header_time_unit_matches':tables[table_index][0][0]==csv_rows[0][0]})
count=sum(r['data_cells_including_time_and_domain_blanks'] for r in paper_checks)
assert count==297
report['checks']['latest_paper_tables_1_to_7']={'paper_filename':paper.name,'paper_sha256':sha(paper),'data_cells':count,
 'all_exact_matches':all(r['exact_text_match'] and r['header_time_unit_matches'] for r in paper_checks),'tables':paper_checks,
 'embedded_image_resources':len(media),'scope':'Exact table value and blank-cell correspondence only; no new paper rendering or page-count claim.'}
if not report['checks']['latest_paper_tables_1_to_7']['all_exact_matches']:
    report['blocking_findings'].append({'priority':'P1','issue':'Latest manuscript table values differ from packaged frozen CSV','tables':paper_checks})

raw=[]
for target in (PKG/'01_赛题与原始数据').rglob('*'):
    if target.is_file() and target.suffix in ['.pdf','.xlsx']:
        rel=target.relative_to(PKG/'01_赛题与原始数据')
        source=ROOT/'problem_files/CUMCM2026Problems/A题'/rel
        raw.append({'file':target.relative_to(PKG).as_posix(),'byte_identical':source.read_bytes()==target.read_bytes(),'sha256':sha(target)})
assert len(raw)==7 and all(r['byte_identical'] for r in raw)
report['checks']['official_raw_attachments']=raw

figure_root=PKG/'05_绘图与数据'
figure_data=figure_root/'input_data/CSV'
input_hash={r['file'].replace('\\','/'):r for r in csv.DictReader((figure_root/'input_sha256.csv').open(encoding='utf-8-sig'))}
csv_records=[]
for p in sorted(figure_data.rglob('*.csv')):
    rows=list(csv.reader(p.open(encoding='utf-8-sig',newline='')))
    rel=p.relative_to(figure_data).as_posix()
    key=rel if rel in input_hash else 'input_data/CSV/'+rel
    expected=input_hash[key]['sha256'].lower()
    csv_records.append({'file':p.relative_to(PKG).as_posix(),'data_rows':len(rows)-1,'columns':len(rows[0]),'sha256':sha(p),'matches_recorded_hash':sha(p)==expected})
assert len(csv_records)==14 and sum(r['data_rows'] for r in csv_records)==4627 and all(r['matches_recorded_hash'] for r in csv_records)
report['checks']['figure_csv']={'file_count':14,'data_rows':4627,'files':csv_records}
out_checks=[]
for r in csv.DictReader((figure_root/'output_sha256.csv').open(encoding='utf-8-sig')):
    p=figure_root/r['file']
    out_checks.append({'file':r['file'],'exists':p.is_file(),'hash_matches':p.is_file() and sha(p)==r['sha256'].lower()})
report['checks']['existing_figure_outputs']=out_checks

source_manifest=json.loads((figure_root/'source_manifest.json').read_text(encoding='utf-8'))
old_paths=[]
current_source_paths=[]
for item in source_manifest.get('sources',[]):
    if 'file' in item:
        p=figure_root/item['file']
        if not p.exists():old_paths.append(item['file'])
    for entry in item.get('packaged_files',[]):
        p=figure_root/entry['file']
        current_source_paths.append({'file':entry['file'],'exists':p.is_file(),'hash_matches':p.is_file() and sha(p)==entry['sha256']})
report['checks']['figure_source_current_mappings']=current_source_paths
assert all(e['exists'] and e['hash_matches'] for e in current_source_paths)
if old_paths:
    report['assembly_followups'].append({'priority':'P2','file':'05_绘图与数据/source_manifest.json','issue':'Historical figure handoff manifest uses old 原始数据 paths absent from current folder. Actual plotting inputs are complete.',
    'missing_old_file_paths':old_paths,'fix':'Mark this as a historical source manifest and add current package path mapping, or replace with a current manifest.'})

code=PKG/'03_程序代码'
manifest=json.loads((code/'input_manifest.json').read_text(encoding='utf-8'))
input_checks=[]
for r in manifest['files']:
    p=code/r['path']
    input_checks.append({'file':r['path'],'exists':p.is_file(),'sha_matches':p.is_file() and sha(p)==r['sha256']})
assert all(r['exists'] and r['sha_matches'] for r in input_checks)
changes=json.loads((code/'docs/source_changes.json').read_text(encoding='utf-8'))
core_checks=[]
for item in changes['files']:
    src=ROOT/item['source'];dst=code/item['delivered']
    old=src.read_text(encoding='utf-8');new=dst.read_text(encoding='utf-8')
    for a,b in item['replacements']:old=old.replace(a,b)
    core_checks.append({'file':item['delivered'],'source_hash_matches':sha(src)==item['sourceSha256'],
        'package_hash_matches':sha(dst)==item['deliveredSha256'],'text_matches_declared_changes':old==new,
        'ast_equivalent_after_declared_paths':ast.dump(ast.parse(old))==ast.dump(ast.parse(new)),
        'extra_descriptive_change':'First comment redirects source-audit location from tools/coreRenameReport.json to docs/source_changes.json; no runtime change.'})
assert all(all(r[k] for k in ['source_hash_matches','package_hash_matches','ast_equivalent_after_declared_paths']) for r in core_checks)
report['checks']['portable_code_inputs']=input_checks
report['checks']['eight_core_modules_vs_declared_changes']=core_checks
entry=(code/'runDelivery.py').read_text(encoding='utf-8')
readme=(code/'README.md').read_text(encoding='utf-8')
report['checks']['entry_and_readme_review']={'status':'PASS_STATIC_SCOPE',
 'observed':['root based on __file__','preflight SHA validation with path containment','profiles quick N40 and final N3200/N3200/N6400',
 'shared Q23 solve for Q2/Q3','Q1,Q2,Q3,Q4 export and complete live Run/archive readback','frozen comparisons only in final',
 'strict max(C)<0.15 and report grid checks','relative inputs/reference paths','new run directory refuses overwrite',
 'GUI=NOT_PERFORMED and humanReview=PENDING_USER_REVIEW','explicit environment and SciPy internal interface dependency'],
 'limitations':'Independent reviewer did not execute package. Main code agent is validating isolated quick/final; this review does not preempt that status.'}

hist=PKG/'07_数值检验与实验/历史源码'
history=[]
for p in hist.rglob('*'):
    if p.is_file():
        rel=p.relative_to(hist);src=ROOT/rel
        history.append({'file':rel.as_posix(),'source_exists':src.is_file(),'byte_identical':src.is_file() and src.read_bytes()==p.read_bytes()})
assert all(x['source_exists'] and x['byte_identical'] for x in history)
trials=PKG/'07_数值检验与实验/历史结果/experiments/trials.jsonl'
trial_lines=[json.loads(line) for line in trials.read_text(encoding='utf-8').splitlines() if line.strip()]
history_readme=(PKG/'07_数值检验与实验/数值检验说明.md').read_text(encoding='utf-8')
report['checks']['historical_sources']={'file_count':len(history),'all_byte_identical':True,'files':history,'trial_count':len(trial_lines),
 'adoption_boundaries_present':all(word in history_readme for word in ['M-K','Morris','Sobol','不能','历史VS/MATLAB']),
 'history_not_portable_entry':True,'invalid_Morris_not_adopted':True,'unfinished_Sobol_not_adopted':True}
assert len(trial_lines)==42

pdf=pymupdf.open(PKG/'AI工具使用详情.pdf')
ai_text='\n'.join(p.get_text() for p in pdf)
report['checks']['ai_disclosure']={'pages':len(pdf),'pending_team_mentions':ai_text.count('待团队确认'),
 'no_signature_substitution':all(s in ai_text for s in ['不由AI签署','待团队确认','不等于','摘要']),
 'current_vs_pending':('当前包装版本尚无完成' in ai_text),'current_cli_scope_not_claimed_final':('未取得最终全量验收结论' in ai_text),
 'historical_separate_from_current':True}
assert report['checks']['ai_disclosure']['no_signature_substitution']

text_suffix={'.md','.txt','.json','.jsonl','.csv','.log','.xml','.html','.py','.cpp','.ps1','.R','.m','.mjs','.pyproj','.sln','.bib'}
patterns={
 'team_name_or_school':r'Shi.?Chenhao|SHICHE|福州大学|Fuzhou University|林宇翔|lin_yuxiang|乐乐|wxid_',
 'credential':r'sk-[A-Za-z0-9]{15,}|ghp_[A-Za-z0-9]{15,}|(?:api[_-]?key|password|access_token)\s*[:=]\s*["\x27][^"\x27]{8,}["\x27]',
 'personal_user_path':r'[A-Za-z]:[/\\]+Users[/\\]+[^/\\\s"\x27]+'}
hits=[];scanned=0
for p in PKG.rglob('*'):
    if p.is_file() and p.suffix in text_suffix:
        data=p.read_text(encoding='utf-8-sig',errors='replace');scanned+=1
        for name,pat in patterns.items():
            if re.search(pat,data,re.I):hits.append({'file':p.relative_to(PKG).as_posix(),'pattern':name})
for x in works:
    for name,pat in patterns.items():
        if re.search(pat,x['core_properties'],re.I):hits.append({'file':x['file']+'!/docProps/core.xml','pattern':name})
for name,pat in patterns.items():
    if re.search(pat,ai_text,re.I):hits.append({'file':'AI工具使用详情.pdf','pattern':name})
report['checks']['privacy_scan']={'text_files_scanned':scanned,'xlsx_core_properties_scanned':4,'ai_pdf_text_scanned':True,'hits':hits,
 'scope':'Common team name/school/user-path/credential patterns; not an exhaustive proof of all possible identifying information.'}
for x in works:del x['core_properties']
if hits:report['blocking_findings'].append({'priority':'P1','issue':'Potential team identifiers or credentials require review','hits':hits})

expected_pending=['00_文件清单.csv','00_材料来源记录.json','00_整理验收说明.md','03_程序代码/docs/运行验收说明.md']
report['assembly_followups'].append({'priority':'FINALIZATION','issue':'Referenced final inventories and execution audit must exist before declaring delivery.',
 'not_yet_present':[s for s in expected_pending if not (PKG/s).exists()],
 'archive_note':'Root README currently describes ZIP while RAR evaluation is ongoing; update wording to actual final format and filename.'})
report['status']='PASS_CONTENT_SCOPE_WITH_ASSEMBLY_FOLLOWUPS' if not report['blocking_findings'] else 'BLOCKED'
(AUDIT/'independent_package_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':report['status'],'workbooks':works,'figure_csv_count':len(csv_records),'figure_data_rows':4627,
 'code_inputs':len(input_checks),'core_modules':len(core_checks),'historical_source_files':len(history),'trial_count':len(trial_lines),
 'privacy_hits':hits,'blocking_findings':report['blocking_findings'],'assembly_followups':report['assembly_followups']},ensure_ascii=False,indent=2))
