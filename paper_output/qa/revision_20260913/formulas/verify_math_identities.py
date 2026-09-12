"""Read-only independent formula checks; no PDE integration or production edits."""
from pathlib import Path
import json, re, math, hashlib, csv

OUT=Path(__file__).parent
ROOT=OUT.parents[3]
d=json.loads((OUT/'extracted_blocks.json').read_text(encoding='utf-8'))
numbered=[]
for b in d['blocks']:
    m=re.fullmatch(r'\((\d+)\)',b['text'].strip())
    if m and b['formulas']:
        numbered.append({'block':b['index'],'old_number':int(m.group(1)),'correct_number':len(numbered)+1,'math':b['formulas']})
refs=[{'block':b['index'],'text':b['text']} for b in d['blocks'] if re.search(r'式[（(]',b['text'])]
def read_csv(name):
    with (OUT/name).open(newline='',encoding='utf-8-sig') as f:
        return [{k:float(v) for k,v in row.items()} for row in csv.DictReader(f)]
records=read_csv('kirchhoff_checks.csv')
roots=read_csv('bessel_checks.csv')
time_records=[]
for q in ('Q23','Q4'):
    p=ROOT/'paper_output/results/production/final_v6a'/q/'summary.json'
    summary=json.loads(p.read_text(encoding='utf-8'))
    c=summary['completion']; tc=c['critical_event_s']; dt=.36
    successor=dt*(math.floor(tc/dt)+1)
    time_records.append({'question':q,'critical_s':tc,'successor_s':successor,'frozen_reported_s':c['reported_time_s'],'difference_s':successor-c['reported_time_s'],'frozen_unrounded_max':c['max_C_at_reported_time'],'strictly_feasible_in_stored_query':c['max_C_at_reported_time']<.15,'seconds_margin':successor-tc})
radius=.02*math.sqrt(((760+90*2.55)/(1+2.55))/760)*100
report={
  'source_docx':d['source'],'source_sha256':d['sha256'],
  'scope':'OOXML formula structure, derivation and independent scalar identity checks; no production PDE rerun, no GUI or human review claimed',
  'display_equation_count':len(numbered),'number_mapping':numbered,'textual_equation_references':refs,
  'kirchhoff_quadrature_checks':records,'bessel_projection_checks':roots,
  'diffusivity_ratio_crossing_C':.15/math.log(1/.175),
  'D4_over_D23_at_equal_T_C':[{'C':c,'ratio':.175*math.exp(.15/c)} for c in (.05,.08606000818,.15,2.55)],
  'density_bound_radius_cm':radius,'time_formula_checks':time_records,
  'exact_grid_root_edge_case':{'critical_s':3600,'delta_s':.36,'ceiling_candidate_s':.36*math.ceil(3600/.36),'strict_successor_s':.36*(math.floor(3600/.36)+1),'conclusion':'Ceiling alone can equal root; a strict threshold still needs a feasibility check or a successor grid index.'},
  'all_scalar_identity_checks_pass':max(r['abs_difference'] for r in records)<1e-12 and max(r['abs_difference'] for r in roots)<1e-12 and all(r['strictly_feasible_in_stored_query'] and abs(r['difference_s'])<1e-8 for r in time_records),
  'source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'paper_output/code/modeling/drying_core.py',ROOT/'paper_output/code/modeling/analytic_jacobian.py',ROOT/'paper_output/code/modeling/q3_model.py',ROOT/'paper_output/step1/A题_原文抽取.txt']}
}
(OUT/'formula_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ('display_equation_count','diffusivity_ratio_crossing_C','density_bound_radius_cm','all_scalar_identity_checks_pass')},ensure_ascii=False))
print('equation mapping:', [(r['block'],r['old_number'],r['correct_number']) for r in numbered])
print('time checks:', time_records)
