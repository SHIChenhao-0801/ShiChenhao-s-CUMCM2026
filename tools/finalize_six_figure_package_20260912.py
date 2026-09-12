"""Archive and independently reopen the portable plotting handoff."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import csv, hashlib, json, math, re, sys, zipfile
from openpyxl import load_workbook
from lxml import etree
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path.cwd(); assert ROOT.as_posix()=='D:/Document/数学建模/2026CUMCM'
PKG = ROOT/'paper_output/handoff/six_figures_20260912'
QA = ROOT/'paper_output/qa/figure_package_20260912'
ARCHIVE = ROOT/'paper_output/handoff/A题六图绘图资料包_含全部数据.zip'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
review = json.loads((QA/'agent_audit.json').read_text(encoding='utf-8'))
assert review['status']=='PASS'
doc_render = json.loads((QA/'guide_v1_manifest.json').read_text(encoding='utf-8'))
assert doc_render['pageCount']==7 and doc_render['docxSha256']==sha(PKG/'六图绘图说明.docx')
for page in doc_render['pages']: assert sha(ROOT/page['image'])==page['sha256']
assert sha(PKG/'六图绘图数据.xlsx')=='ef23e4b4bcc96bcc3ccbaf2e17e6ff2e291e059e51befe1c5baae371ee1848e9'
manifest = json.loads((PKG/'数据清单.json').read_text(encoding='utf-8'))
expected = {t['csv'] for t in manifest['tables']} | {s['file'] for s in manifest['sources']} | {
    '六图绘图数据.xlsx','六图绘图说明.docx','请先阅读.txt','数据清单.json'}
actual = {p.relative_to(PKG).as_posix() for p in PKG.rglob('*') if p.is_file() and p.name!='文件校验SHA256.txt'}
assert actual==expected, (actual-expected, expected-actual)
checksums = {name:sha(PKG/name) for name in sorted(expected)}
(PKG/'文件校验SHA256.txt').write_text('\n'.join(f'{v}  {k}' for k,v in checksums.items())+'\n',encoding='utf-8-sig')
expected.add('文件校验SHA256.txt')
with zipfile.ZipFile(ARCHIVE,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for name in sorted(expected): z.write(PKG/name, 'A题六图绘图资料包/'+name)

extract = ROOT/'tmp/cache/figure_package_20260912'/('relocated_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
extract.mkdir(parents=True)
with zipfile.ZipFile(ARCHIVE) as z:
    assert z.testzip() is None
    for name in z.namelist():
        q=PurePosixPath(name); assert not q.is_absolute() and '..' not in q.parts
    assert len(z.namelist())==len(expected)
    z.extractall(extract)
relocated=extract/'A题六图绘图资料包'
for name in expected: assert sha(relocated/name)==sha(PKG/name)
for s in manifest['sources']:
    path=relocated/s['file'];assert sha(path)==s['sha256']
    if path.suffix=='.npz':
        with np.load(path,allow_pickle=False) as arrays:
            for key in arrays.files: assert np.isfinite(arrays[key]).all()
    if path.suffix=='.json': json.loads(path.read_text(encoding='utf-8'))

wb=load_workbook(relocated/'六图绘图数据.xlsx',read_only=True,data_only=False)
assert wb.sheetnames==[t['name'] for t in manifest['tables']]
cells=0;rows=0;max_abs_error=0.
for t in manifest['tables']:
    with (relocated/t['csv']).open(encoding='utf-8-sig',newline='') as f: records=list(csv.reader(f))
    assert records[0]==t['columns'] and len(records)-1==t['data_rows']
    ws=wb[t['name']]
    got=list(ws.iter_rows(min_row=6,max_row=6+t['data_rows'],max_col=len(t['columns']),values_only=True))
    assert list(got[0])==records[0]
    for observed,wanted in zip(got[1:],records[1:]):
        assert len(observed)==len(wanted)
        for v,w in zip(observed,wanted):
            try: number=float(w)
            except ValueError: assert v==w
            else:
                assert isinstance(v,(int,float)) and math.isclose(v,number,rel_tol=2e-14,abs_tol=1e-16),(t['name'],v,w)
                max_abs_error=max(max_abs_error,abs(v-number))
            cells+=1
    rows+=len(records)-1
wb.close()
for filename in ['六图绘图数据.xlsx','六图绘图说明.docx']:
    with zipfile.ZipFile(relocated/filename) as z:
        assert z.testzip() is None
        assert not any(n.startswith('xl/externalLinks/') for n in z.namelist())
        for name in z.namelist():
            if name.endswith('.rels'):
                x=etree.fromstring(z.read(name))
                assert not any(e.get('TargetMode')=='External' for e in x), (filename,name)
with zipfile.ZipFile(relocated/'六图绘图说明.docx') as z:
    x=etree.fromstring(z.read('word/document.xml'))
text='\n'.join(x.xpath('//w:t/text()',namespaces={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}))
assert not re.search(r'[A-Za-z]:[/\\]',text)
audit={'status':'PASS','zip':ARCHIVE.relative_to(ROOT).as_posix(),'zipSha256':sha(ARCHIVE),
       'zipBytes':ARCHIVE.stat().st_size,'fileCount':len(expected),'dataTables':14,
       'dataRows':rows,'dataCells':cells,'copiedOriginalFiles':15,
       'archiveCRC':'PASS','relocatedReadback':'PASS','relocatedPath':relocated.relative_to(ROOT).as_posix(),
       'allFileHashesMatch':True,'allWorkbookCSVCellsCompared':True,'maximumWorkbookAbsoluteError':max_abs_error,
       'externalWorkbookOrWordLinks':0,'docxPages':7,'docxSha256':sha(PKG/'六图绘图说明.docx'),
       'wordVisualReview':'Root actually viewed all seven final guide_v1 page images; all legible, no clipping or overflow.',
       'workbookSha256':sha(PKG/'六图绘图数据.xlsx'),'workbookVisualReview':'All 14 sheets reviewed by workbook agent; see workbook_final_audit.md.',
       'newModelRuns':0,'originalPaperModified':False}
(QA/'final_package_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
(QA/'final_package_audit.md').write_text(
    f"# 六图绘图资料包核验\n\n状态：PASS。{len(expected)}个文件，14张作图数据表，{rows}行、{cells}个数据格。\n\n"
    'CSV逐值对原始冻结数据通过；15份源文件SHA一致。ZIP CRC通过，实际解压到另一个目录后重读所有文件、14张Excel表与CSV，数值全部一致（容差2e-14）。Word与Excel无外部文件链接，Word无本机绝对路径。\n\n'
    '7页Word全部实际视觉检查；14张Excel工作表由独立代理检查。未重算模型，未改论文。\n\n'
    f"ZIP SHA256：{audit['zipSha256']}\n",encoding='utf-8')

memory_path=ROOT/'memoryskill.md';memory=memory_path.read_text(encoding='utf-8')
section='## 六图数据实际打包交付（2026-09-12，替代仅路径手册）\n\n'
section+='- 用户纠正：绘图同学没有本地工作区，交接必须实际包含所有六图数据。已生成 `paper_output/handoff/A题六图绘图资料包_含全部数据.zip`，可直接转发。内含7页便携Word、14表Excel、14CSV、15原始文件以及说明/清单/校验。\n'
section+='- 已将NPZ直接导出可绘图列，共4627行；图2观测与假设平台独立，图4中心样点/全节点最大值/严格事件独立，图5六组各自XY，图6统一N800。Word使用包内路径，无需对方自行转换NPZ。\n'
section+=f"- ZIP {audit['zipBytes']}字节，SHA256 `{audit['zipSha256']}`；实际异目录解压回读与CSV/Excel全部逐值比对通过。QA `paper_output/qa/figure_package_20260912/final_package_audit.json`。无新模型计算或论文修改。\n\n"
if '## 六图数据实际打包交付' not in memory:
    memory=memory.replace('## 独立六图绘图手册',section+'## 独立六图绘图手册',1)
    memory_path.write_text(memory,encoding='utf-8')
state_path=ROOT/'paper_output/context/workflow_memory.json'
state=json.loads(state_path.read_text(encoding='utf-8'))
state['six_figure_data_package']={'path':audit['zip'],'sha256':audit['zipSha256'],
    'status':'PORTABLE_DATA_PACKAGE_VERIFIED','tables':14,'dataRows':rows,'originalFiles':15,
    'qa':'paper_output/qa/figure_package_20260912/final_package_audit.json',
    'scope':'Six plotting figures only; supersedes path-only handoff. Does not change modeling/submission review status.'}
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:audit[k] for k in ['status','zip','zipBytes','zipSha256','fileCount','dataRows','dataCells']},ensure_ascii=False))
