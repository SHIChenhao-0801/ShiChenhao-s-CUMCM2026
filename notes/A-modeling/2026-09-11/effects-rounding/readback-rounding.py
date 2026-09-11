"""Read frozen evidence and selected XLSX rows; no PDE or production imports."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal,ROUND_HALF_EVEN,ROUND_HALF_UP
import hashlib,json,zipfile,xml.etree.ElementTree as ET,math,os,csv
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import numpy as np
ROOT=Path.cwd().resolve();OUT=Path(__file__).resolve().parent
assert ROOT.name=='2026CUMCM' and OUT.is_relative_to(ROOT)
OLD=ROOT/'paper_output/results/production/final_v6a'
NEW=ROOT/'paper_output/results/code_delivery/camel_final_v2'
GUI=ROOT/'paper_output/results/code_delivery/gui_camel_final_v2'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def rec(p):
 p=Path(p);return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def load(p):
 with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def workbook_rows(path, mode):
 ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
 rows=[];styleids=set();count=0
 with zipfile.ZipFile(path) as z:
  styles=ET.fromstring(z.read('xl/styles.xml'))
  custom={int(e.attrib['numFmtId']):e.attrib['formatCode'] for e in styles.findall('m:numFmts/m:numFmt',ns)}
  xfs=styles.find('m:cellXfs',ns)
  fmt={i:custom.get(int(e.attrib['numFmtId']),f'builtin:{e.attrib["numFmtId"]}') for i,e in enumerate(xfs)}
  with z.open('xl/worksheets/sheet1.xml') as source:
   for _,element in ET.iterparse(source,events=['end']):
    if element.tag!='{'+ns['m']+'}row':continue
    count+=1;row=[]
    for c in element.findall('m:c',ns):
     value=c.find('m:v',ns);s=int(c.attrib.get('s',0));styleids.add(s)
     text=c.find('m:is/m:t',ns)
     row.append({'cell':c.attrib['r'],'value':None if value is None else float(value.text),
                 'text':None if text is None else text.text,'format':fmt[s]})
    if count<=3:rows.append(row)
    if mode=='Q2' and count==5402:rows.append(row)
    if mode in ['Q3','Q4']:
     if count>=4:rows.append(row)
     if len(rows)>7:rows.pop(3)
    element.clear()
    if mode=='Q1' and count==3:break
    if mode=='Q2' and count==5402:break
 return {'path':path.relative_to(ROOT).as_posix(),'actual_rows_read':count,'selected_rows':rows,
         'styles_observed':{i:fmt[i] for i in sorted(styleids)}}

report={'generated_at':datetime.now(timezone.utc).isoformat(),'status':'READBACK_COMPLETE_PENDING_INTERPRETATION',
 'scope':'Read sources, selected workbook rows and archived NPZ; no new PDE, no GUI or workbook edits.',
 'new_PDE_solves':0,'sources':[],'events':{},'workbooks':{},'rounding_examples':[],
 'round_doc':round.__doc__}
for p in ['problem_files/CUMCM2026Problems/A题/A题.pdf','paper_output/step1/A题_原文抽取.txt',
 'paper_output/code/modeling/q3_model.py','paper_output/code/modeling/export_outputs.py',
 'paper_output/code/review_delivery/q3Model.py','paper_output/code/review_delivery/exportOutputs.py',
 'paper_output/qa/recheck_20260910_1828/numerical_recheck.json']:
 report['sources'].append(rec(ROOT/p))
for q in ['Q23','Q4']:
 old=read(OLD/q/'summary.json');new=read(NEW/q/'summary.json');gui=read(GUI/q/'summary.json')
 done=new['completion'];event=done['critical_event_s'];nearest=round(event/3600.,4)
 s=load(NEW/q/'sampled_solution.npz');i=int(np.argmin(np.abs(s['times_s']-event)))
 before=np.flatnonzero(s['times_s']<event)[-1]
 after=np.flatnonzero(s['times_s']>event)[0]
 archives=[rec(root/q/'sampled_solution.npz') for root in [OLD,NEW,GUI]]
 assert len({a['sha256'] for a in archives})==1
 assert old['diagnostics']['event_s']==event==gui['completion']['critical_event_s']
 assert done==gui['completion']
 report['events'][q]={'completion':done,'nearest_4dp_h':nearest,'nearest_time_s':nearest*3600.,
  'nearest_time_minus_event_s':nearest*3600.-event,'archive_sources':archives,
  'new_gui_completion_equal':True,'new_old_gui_sampled_NPZ_byte_equal':True,
  'saved_root':{'time_s':float(s['times_s'][i]),'max_of_21_material_C':float(np.max(s['C'][i]))},
  'previous_saved':{'time_s':float(s['times_s'][before]),'max_C':float(np.max(s['C'][before]))},
  'next_saved':{'time_s':float(s['times_s'][after]),'max_C':float(np.max(s['C'][after]))},
  'exact_nearest_rounded_time_saved':bool(np.any(s['times_s']==nearest*3600.)),
  'strict_at_reported_record':done['max_C_at_reported_time']<.15}
for q in ['Q1','Q2','Q3','Q4']:
 name='result'+q[-1]
 rows=[workbook_rows(root/'outputs'/f'{name}.xlsx',q) for root in [OLD,NEW]]
 assert rows[0]['selected_rows']==rows[1]['selected_rows']
 report['workbooks'][q]={'old':rows[0],'latest':rows[1],'selected_values_and_styles_equal':True,
  'export_manifest':rec(NEW/'outputs'/f'{name}.export.json')}
 if q in ['Q3','Q4']:
  d=read(NEW/'outputs'/f'{name}.export.json')
  report['workbooks'][q]['paper_table_time_contract']=d['paper_table_time_contract']
  csvs=[]
  for root in [OLD,NEW]:
   p=root/'outputs'/f'{q.lower()}_paper_moisture.csv'
   with p.open(encoding='utf-8-sig',newline='') as f: table=list(csv.reader(f))
   csvs.append({'source':rec(p),'last_row':table[-1]})
  assert csvs[0]['last_row']==csvs[1]['last_row']
  report['workbooks'][q]['paper_CSV_last_rows']=csvs
for value in ['0.03125','-0.03125','1.23445','57.47230195056044','51.09057478683054']:
 x=Decimal(value)
 report['rounding_examples'].append({'decimal_string':value,'python_float_round_4':round(float(x),4),
  'decimal_half_even_4':str(x.quantize(Decimal('.0001'),rounding=ROUND_HALF_EVEN)),
  'decimal_half_up_4':str(x.quantize(Decimal('.0001'),rounding=ROUND_HALF_UP))})
report['script']=rec(__file__)
(OUT/'rounding-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'events':report['events'],'rounding_examples':report['rounding_examples'],
                 'workbook_selection_matches':list(report['workbooks'])},ensure_ascii=False,indent=2))
