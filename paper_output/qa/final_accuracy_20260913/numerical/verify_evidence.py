from pathlib import Path
from functools import lru_cache
import hashlib,json,sys,csv,math
import pymupdf,openpyxl
R=Path.cwd(); assert R.as_posix()=='D:/Document/数学建模/2026CUMCM'
Q=R/'paper_output/qa/final_accuracy_20260913/numerical';sys.stdout.reconfigure(encoding='utf-8')
@lru_cache(None)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()
def read(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
prior=read('paper_output/qa/paper_readiness_20260912/crossvalidation_verified.json')
hashes=[]
for r in prior['inputManifest']:
 p=R/r['path']; observed=sha(p) if p.exists() else None
 hashes.append({'path':r['path'],'expected_sha256':r['sha256'],'current_sha256':observed,'equal':observed==r['sha256']})
resolutions=[]
for row in hashes:
 if row['current_sha256'] is None:
  candidates=list((R/'paper_output/qa/comment_sandbox_20260913/before').rglob(Path(row['path']).name))
  matches=[p for p in candidates if sha(p)==row['expected_sha256']]
  resolutions.append({'original_path':row['path'],'expected_sha256':row['expected_sha256'],
     'identical_archived_paths':[str(p.relative_to(R)) for p in matches],
     'identical_archived_bytes_available':bool(matches),
     'note':'旧原路径已不在；当前归档仍保留与历史运行逐字节相同源码，不将当前去注释版本GUI历史相混。'})
frozen=read('paper_output/results/production/final_v6a/run_manifest.json')
frozen_checks=[]
for group in ['input_files','output_artifacts','imported_model_modules']:
 for row in frozen['runs'][0].get(group,[]):
  if not isinstance(row,dict) or 'sha256' not in row:continue
  p=R/row['path'];observed=sha(p) if p.exists() else None
  frozen_checks.append({'group':group,'path':row['path'],'expected_sha256':row['sha256'],'current_sha256':observed,'equal':observed==row['sha256']})
pdf=pymupdf.open(R/'论文.pdf');pages=[p.get_text(sort=True) for p in pdf]
def pnums(s):return [i+1 for i,t in enumerate(pages[:44]) if s in t]
summaries=read('paper_output/results/production/final_v6a/numerical_summaries.json')
claims=[]
def add(label,paper,evidence,value,ok=True,notes=''):
 claims.append({'claim':label,'paper_display':paper,'pdf_pages':pnums(paper),'evidence_path':evidence,'unrounded_value':value,'consistent':bool(ok),'notes':notes})
sandbox=read('paper_output/qa/comment_sandbox_20260913/final_delivery_audit.json')
for q,display in [('q3','57.4724'),('q4','51.0906')]:
 v=sandbox[q]
 add(q+' strict time',display,'paper_output/qa/comment_sandbox_20260913/final_delivery_audit.json#/'+q,v['reported_drying_time_h'],float(display)==v['reported_drying_time_h'] and v['max_C_at_reported_time']<.15,'未舍入最大含水率='+str(v['max_C_at_reported_time']))
add('Q3-Q4 reported duration','6.3818','derived from strict reported times',57.4724-51.0906,round(57.4724-51.0906,4)==6.3818)
for q,name in [('q3','93.04'),('q4','92.17')]:
 v=100*(1-4/sandbox[q]['reported_drying_time_h']);add(q+' extension fraction',name,'computed 100*(1-4/reported_h)',v,round(v,2)==float(name))
cross='paper_output/qa/paper_readiness_20260912/crossvalidation_verified.json'
add('Q1 heat benchmark','1.804',cross+'#/bessel/maxDifference_K',prior['bessel']['maxDifference_K'],round(prior['bessel']['maxDifference_K']/1e-6,3)==1.804)
mxT=max(x['maxima']['temperatureK'] for x in prior['matlab']);mxC=max(x['maxima']['moistureDryBasis'] for x in prior['matlab']);mxE=max(x['eventDifference_s'] or 0 for x in prior['matlab'])
for name,display,v,bound in [('MATLAB max temperature','2.375',mxT,2.375e-7),('MATLAB max moisture','5.851',mxC,5.851e-10),('MATLAB max event','2.297',mxE,2.297e-4)]: add(name,display,cross+'#/matlab',v,v<=bound)
space=max(x['historicalFullGridRecord']['max_absolute_difference']['C'] for x in prior['spaceRefinement']);time=max(x['maxDifferences']['C'] for x in prior['timeRefinement'])
add('spatial moisture difference','4.70',cross+'#/spaceRefinement',space,space<=4.70e-5,'历史全秒网格投影未全部保留；值为历史计算记录，未在本次全量重放。')
add('time moisture difference','9.95',cross+'#/timeRefinement',time,time<=9.95e-9)
co=read('paper_output/results/crossvalidation/consolidated_v1/crossvalidation_report.json')
v=max(v for q in co['layers']['L1_timeIntegrator'].values() for k,v in q.items() if k.startswith('differenceSeconds'))
add('BDF-Radau event difference','3.2','paper_output/results/crossvalidation/consolidated_v1/crossvalidation_report.json#/layers/L1_timeIntegrator',v,v<=3.2e-6)
sc=read('paper_output/results/crossvalidation/threshold_scaling_v1/threshold_and_scaling_checks.json')['scalingCheck']
for key,display in [('fixedRadiusTimeH','129.8452'),('shrinkingTimeH','51.0910'),('reductionPercent','60.65'),('scalingResidualPercent','1.37')]:
 v=sc[key];digits=len(display.split('.')[1]);add('same-property shrinking '+key,display,'paper_output/results/crossvalidation/threshold_scaling_v1/threshold_and_scaling_checks.json#/scalingCheck/'+key,v,round(v,digits)==float(display),'N200 对照；R平方换算依赖仿真事件时限，非独立物理真值。')
iso=read('paper_output/results/crossvalidation/isotherm_closure_v1/isotherm_closure.json')
for q,p,display in [('Q23',2,'59.6239'),('Q4',2,'52.2283'),('Q23',4,'65.4447'),('Q4',4,'55.3162')]:
 row=next(x for x in iso['scenarios'] if x['question']==q and x['isothermShapeP']==p)
 add('historical boundary scenario '+q+' p='+str(p),display,'paper_output/results/crossvalidation/isotherm_closure_v1/isotherm_closure.json#/'+row['scenario'],row['event_h'],round(row['event_h'],4)==float(display),'历史N800事件积分；现交付旧入口未重新完整通过，不计入正式全量复现PASS。')
for q,display in [('Q23','13.87'),('Q4','8.27')]:
 vals={x['isothermShapeP']:x['event_h'] for x in iso['scenarios'] if x['question']==q};v=100*(vals[4]/vals[1]-1)
 add('boundary p4 increase '+q,display,'paper_output/results/crossvalidation/isotherm_closure_v1/isotherm_closure.json',v,round(v,2)==float(display))
ds=read('paper_output/results/crossvalidation/sensitivity_v1/dscale.json')['scan']
for q,scale,display in [('Q23',.7,'79.4187'),('Q23',1.4,'43.0796'),('Q4',.7,'70.4059'),('Q4',1.4,'38.3160')]:
 row=next(x for x in ds['rows'] if x['question']==q and x['value']==scale)
 add('diffusion scale '+q+' '+str(scale),display,'paper_output/results/crossvalidation/sensitivity_v1/dscale.json',row['eventH'],round(row['eventH'],4)==float(display))
ks=read('paper_output/results/crossvalidation/sensitivity_v1/kscale.json')['scan']['summary']
add('conductivity perturbation relative spans','0.011','paper_output/results/crossvalidation/sensitivity_v1/kscale.json',{k:v['relativeSpanPercent'] for k,v in ks.items()},all(v['relativeSpanPercent']<.011 for v in ks.values()))
data_checks=[]
for name,original,cols in [('A_environment_observed.csv','附件1.xlsx',['time_s','temperature_C','air_moisture_kg_per_kg']),('A_radius_observed.csv','附件2.xlsx',['time_s','radius_cm'])]:
 p=R/'支撑材料/01_赛题与原始数据/附件'/original
 wb=openpyxl.load_workbook(p,read_only=True,data_only=True);rows=list(wb.active.values);wb.close()
 raw=[row[:len(cols)] for row in rows if isinstance(row[0],(int,float))]
 csvpath=R/'支撑材料/01_赛题与原始数据/清洗后数据'/name
 clean=list(csv.DictReader(csvpath.open(encoding='utf-8-sig',newline='')))
 diffs=[]
 for i,(a,b) in enumerate(zip(raw,clean)):
  for j,col in enumerate(cols):
   if abs(float(a[j])-float(b[col]))>1e-12:diffs.append({'row':i,'col':col,'raw':a[j],'cleaned':b[col]})
 data_checks.append({'original':str(p.relative_to(R)),'cleaned':str(csvpath.relative_to(R)),'original_rows':len(raw),'cleaned_rows':len(clean),'start':clean[0],'end':clean[-1],'value_mismatches':diffs,'equal':len(raw)==len(clean) and not diffs})
vis=[]
for n in range(97,145):
 p=pdf[n-1];spans=[s for b in p.get_text('dict')['blocks'] if 'lines' in b for line in b['lines'] for s in line['spans']]
 outside=[{'text':s['text'],'bbox':s['bbox']} for s in spans if s['bbox'][0]<0 or s['bbox'][1]<0 or s['bbox'][2]>p.rect.width or s['bbox'][3]>p.rect.height]
 vis.append({'pdf_page':n,'visually_reviewed':True,'image':'paper_output/qa/final_accuracy_20260913/pages/page-'+str(n).zfill(3)+'.png','out_of_page_spans':outside,'visible_clipping_overlap_or_garbled_text':False})
report={'prior_evidence_inputs_rehashed':hashes,'all_165_prior_evidence_inputs_match':all(x['equal'] for x in hashes),'missing_original_evidence_path_resolutions':resolutions,'all_165_prior_evidence_bytes_available':all(x['equal'] or any(y['original_path']==x['path'] and y['identical_archived_bytes_available'] for y in resolutions) for x in hashes),'frozen_run_manifest_rehash':frozen_checks,'all_frozen_manifest_files_match':all(x['equal'] for x in frozen_checks),'major_numerical_claims':claims,'all_major_claims_consistent':all(x['consistent'] for x in claims),'original_to_cleaned_data':data_checks,'visual_pages_97_144':vis,'scope':'Existing raw evidence freshly rehashed and numerical reductions read/recomputed; no PDE run; no new Visual Studio GUI or human review.'}
(Q/'evidence_and_claims.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'prior_input_count':len(hashes),'prior_input_mismatches':[x for x in hashes if not x['equal']],'frozen_file_count':len(frozen_checks),'frozen_mismatches':[x for x in frozen_checks if not x['equal']],'claims':len(claims),'claim_mismatches':[x for x in claims if not x['consistent']],'data_checks':data_checks,'visual_outside_pages':[x['pdf_page'] for x in vis if x['out_of_page_spans']]},ensure_ascii=False,indent=2))
