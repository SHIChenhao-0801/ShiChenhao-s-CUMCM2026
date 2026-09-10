"""Read-only checks of corrected prose; assemble the physics audit JSON."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re
q=Path('paper_output/qa/recheck_20260910_1828')
s=json.loads((q/'physics_small_checks.json').read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
docs=[]
for name in ['A题_完整建模与公式推导.md','A题_建模浓缩交接.md']:
    old=q/'documents_before'/name
    new=Path('notes/A-modeling/2026-09-10')/name
    a,b=old.read_text(encoding='utf8'),new.read_text(encoding='utf8')
    ma,mb=re.findall(r'\\\[(.*?)\\\]',a,re.S),re.findall(r'\\\[(.*?)\\\]',b,re.S)
    checks={'effective_capacity_explicit':('有效容量约定' in b or '这一容量约定' in b),
            'rounding_limit_explicit':'2.03μm' in b and '5μm' in b}
    if '完整' in name:checks['separable_step_limit_explicit']='联合阶跃响应作Duhamel卷积' in b
    docs.append({'name':name,'before_sha256':sha(old),'after_sha256':sha(new),
        'before_display_formula_blocks':len(ma),'after_display_formula_blocks':len(mb),
        'display_formula_blocks_identical':ma==mb,'wording_checks':checks})
unchanged=[]
for rec in s['sources']:
    if '完整建模' in rec['path']:continue
    unchanged.append({'path':rec['path'],'sha256_now':sha(Path(rec['path'])),
                      'matches_fresh_check_source':sha(Path(rec['path']))==rec['sha256']})
findings=[
('PH01','conditional_energy_structure_and_missing_capacity_validation','M09 218-225; M21 332-342; J02 999; drying_core.py 181','Effective capacity is an additional constitutive approximation; no mandatory TB_C C_t term is missing.','Resolved wording at M09 and condensed draft; physical validation remains absent.'),
('PH02','literal_density_incompatibility','M23-M27 354-412; drying_core.py 80-85,120,123','True wet density, fixed length, given R and conserved dry mass cannot all be imposed literally.','Retain explicit effective-density convention; data gap remains.'),
('PH03','overprecise_measurement_interpretation','M26 398','19.5 h is first printed sample below necessary bound, not certified real onset; margin 2.03 micrometers.','Corrected and re-read.'),
('PH04','conditional_derivation_valid','M11-M13 235-259; M28-M32 416-468; drying_core.py 161-183','Uniform dry skeleton and homologous radial motion are necessary assumptions for cancellations.','No new algebra defect found.'),
('PH05','units_valid_but_gas_solid_closure_missing','M15-M18 273-312; drying_core.py 95-107,172','Air kg/kg and material dry-basis kg/kg are different bases; need sorption isotherm, pressure and beta calibration.','Already disclosed; physical closure unresolved.'),
('PH06','conditional_physical_direction_conflict','M19; latent paragraph 800-805; drying_core.py 174-179','At standard pressure and air humidity-ratio interpretation, saved surface-latent states imply condensation while effective Robin predicts evaporation.','Keep algebraic stress-test label; not a closed alternative prediction.'),
('PH07','kirchhoff_algebra_valid_conditionally','K01-K03 812-857; drying_core.py 145-159','Phi derivative and separate temperature prefactor correct; cylindrical geometry and variable T remain approximated.','No new algebra defect found.'),
('PH08','local_jacobian_checks_pass','analytic_jacobian.py 76-171','Seven fresh small-state five-point differences, mass left null and passive column checks pass.','No global all-state proof claimed.'),
('PH09','separability_condition_missing_in_old_wording','M53 732','Product of radial/axial responses requires the homogeneous separable step problem; arbitrary ambient needs Duhamel.','Corrected and re-read.'),
('PH10','dimension_reduction_limit','M53 and axisymmetric results 725-798','Area ratio is not an end-effect error bound; Q23 two-grid comparison does not certify all questions.','Physical and discretization scope limits remain.'),
('PH11','assumption_start_disclosure','Data table 59-80; M04 177','Effective capacity, Ceq, homologous motion start at t=0; ambient extension starts after 4 h; h/beta reused by convention.','Already accurately disclosed.'),
('PH12','numerical_vs_physical_error_separation','M48/M50/M55; final accuracy chapters','Adjacent grid differences, tighter tolerances, conservation and report rounding are not true material prediction error bounds.','Independent numerical review handles full reductions; retain scope statement.')]
report={'status':'PHYSICS_RECHECK_COMPLETE_WITH_EXPLICIT_PHYSICAL_LIMITATIONS',
  'created_at_utc':datetime.now(timezone.utc).isoformat(),
  'not_formal_S7':True,'new_PDE_solves':0,'GUI_operation':False,'human_approval':False,
  'small_check_process_observed':{'tool_exit_code':0,'tool_wall_seconds':1.8005414,'warning_count':0,
       'command':'C:/Python314/python.exe -B paper_output/qa/recheck_20260910_1828/physics_small_checks.py'},
  'independent_small_check_results':s,
  'new_confirmed_core_algebra_defects':[],
  'findings':[dict(zip(['id','classification','snapshot_location','finding','resolution'],f)) for f in findings],
  'primary_external_sources':[
    {'url':'https://handbook.ashrae.org/Handbooks/F25/SI/F25_Ch01/F25_Ch01_si.aspx','role':'Humidity ratio definition and ideal gas basis; not medicinal material parameters.'},
    {'url':'https://www.nist.gov/document/nistir5078-tab1pdf','role':'Saturation pressure at 11/15 C and latent heat near 50 C, table 1 first page; pressure converted from MPa to Pa.'},
    {'url':'https://www.comsol.com/blogs/how-to-model-heat-and-moisture-transport-in-porous-media-with-comsol','role':'Primary software-author discussion of phase/moisture energy coupling; not empirical fit for this plant.'}],
  'corrected_document_recheck':docs,
  'all_checked_display_formulas_unchanged':all(d['display_formula_blocks_identical'] for d in docs),
  'all_corrected_wording_checks_pass':all(all(d['wording_checks'].values()) for d in docs),
  'read_source_unchanged_after_review':unchanged,
  'report_md_sha256':sha(q/'physics_recheck.md')}
(q/'physics_recheck.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':report['status'],'documents':docs,
    'all_read_inputs_unchanged':all(x['matches_fresh_check_source'] for x in unchanged),
    'report_md_sha256':report['report_md_sha256'],'report_json_sha256':sha(q/'physics_recheck.json')},ensure_ascii=False,indent=2))
assert report['all_checked_display_formulas_unchanged'] and report['all_corrected_wording_checks_pass']
assert all(x['matches_fresh_check_source'] for x in unchanged)
