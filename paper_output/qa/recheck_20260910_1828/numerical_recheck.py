"""Independent saved-evidence recheck. No PDE or production-module imports."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json
import math
import os
import sys
import time

os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import numpy as np
from scipy.optimize import brentq
from scipy.special import j0, j1, jn_zeros

ROOT=Path.cwd().resolve()
OUT=Path(__file__).resolve().parent
assert ROOT.name=='2026CUMCM' and OUT.is_relative_to(ROOT)
START=time.perf_counter()

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as stream:
        for b in iter(lambda:stream.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def rec(p):
    p=Path(p)
    return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}

def check_records(records):
    checked=[]
    for r in records:
        p=ROOT/r['path'];actual=rec(p)
        ok=actual['sha256']==r['sha256'] and ('bytes' not in r or actual['bytes']==r['bytes'])
        checked.append({'path':r['path'],'expected_sha256':r['sha256'],'actual':actual,'matches':ok})
    return checked

def load_npz(p):
    with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}

def independent_error(a,b,ts,rs):
    maxima={};locations={};rounded={}
    for key in ['T_K','C']:
        difference=np.abs(a[key]-b[key]);mask=np.isfinite(difference)
        ix=np.unravel_index(np.nanargmax(difference),difference.shape)
        maxima[key]=float(difference[ix]);locations[key]={'time_s':float(ts[ix[0]]),'radius_m':float(rs[ix[1]])}
        # Integer decimal bins avoid formatted-string allocation for millions of points.
        aa=a[key][mask]-(273.15 if key=='T_K' else 0.)
        bb=b[key][mask]-(273.15 if key=='T_K' else 0.)
        numpy_different=np.round(aa,4)!=np.round(bb,4)
        near_half=(np.abs(np.mod(aa*10000,1)-.5)<2e-6)|(np.abs(np.mod(bb*10000,1)-.5)<2e-6)
        candidates=np.flatnonzero(numpy_different|near_half)
        physical_indices=np.flatnonzero(mask)
        exact=[]
        for candidate in candidates:
            av,bv=round(float(aa[candidate]),4),round(float(bb[candidate]),4)
            if av!=bv:
                position=np.unravel_index(physical_indices[candidate],mask.shape)
                exact.append({'time_s':float(ts[position[0]]),'radius_m':float(rs[position[1]]),
                    'baseline':float(aa[candidate]),'tight':float(bb[candidate]),
                    'baseline_export_4dp':f'{av:.4f}','tight_export_4dp':f'{bv:.4f}'})
        rounded[key]={'finite_pairs':int(mask.sum()),
                      'different_4dp_rounded_values':len(exact),
                      'numpy_round_candidates_different':int(np.count_nonzero(numpy_different)),
                      'actual_Python_round_candidates_verified':len(candidates),
                      'exact_export_round_difference_samples':exact,
                      'rounding_convention':'Python round(float(value),4) then 0.0000; T converted K to Celsius first.'}
    return {'max_absolute_difference':maxima,'locations':locations,'rounded_4dp_comparison':rounded}

def independently_recurrence_bessel(g, diffusivity, biot, nterms):
    """One-second exact recurrence for linear boundary ramps; no FVM code.

    Roots are bracketed between successive J0 zeros, unlike the production
    benchmark's J1-to-J0 brackets. Each ramp integral is integrated exactly.
    """
    upper=jn_zeros(0,nterms); lower=np.r_[0.,upper[:-1]]
    mu=np.array([brentq(lambda z:z*j1(z)-biot*j0(z),a,b,xtol=1e-13,rtol=1e-14)
                 for a,b in zip(lower,upper)])
    A=2*j1(mu)/(mu*(j0(mu)**2+j1(mu)**2))
    lam=diffusivity*mu*mu/.02**2
    decay=np.exp(-lam);ramp=-np.expm1(-lam)/lam
    z=np.zeros((len(g),nterms));z[0]=INITIAL_FOR_BESSEL-g[0]
    for i in range(1,len(g)):z[i]=decay*z[i-1]-(g[i]-g[i-1])*ramp
    modes=j0(mu[:,None]*np.linspace(0,1,21)[None,:])
    result=g[:,None]+(z*A)@modes
    result[0]=INITIAL_FOR_BESSEL
    residual=np.max(np.abs(mu*j1(mu)-biot*j0(mu))/(1+np.abs(mu*j1(mu))+np.abs(biot*j0(mu))))
    return result,float(residual)

production=ROOT/'paper_output/results/production/final_v6a'
manifest=read(production/'run_manifest.json'); runmeta=manifest['runs'][0]
hash_checks=check_records(runmeta['input_files']+runmeta['output_artifacts'])
assert len(hash_checks)==107 and all(x['matches'] for x in hash_checks)
process=read(production/'process_result.json')
summary=read(production/'numerical_summaries.json')
report={'status':'COMPUTED_PENDING_INTERPRETIVE_REVIEW','created_at':datetime.now(timezone.utc).isoformat(),
        'operation':'Read sources and frozen records; independently reduce saved arrays; no new PDE solve.',
        'production_manifest':rec(production/'run_manifest.json'),'production_process':process,
        'production_current_hash_checks':hash_checks,'production':{},'time_reductions':[],
        'space_reports':[],'richardson':{},'Bessel':{},'new_PDE_solves':0,
        'human_approval':False,'GUI_operation':False}

for q in ['Q1','Q23','Q4']:
    path=production/q/'sampled_solution.npz';s=load_npz(path)
    mass=s['mean_C']+s['cumulative_loss']-2.55
    sparse_mean=2*np.trapezoid(s['C']*s['material_x'][None,:],s['material_x'],axis=1)
    entry={'archive':rec(path),'saved_time_count':len(s['times_s']),'saved_material_point_count':len(s['material_x']),
           'saved_mean_plus_loss_max_abs_residual':float(np.max(np.abs(mass))),
           'all_node_accepted_step_mass_residual_recorded':summary[q]['diagnostics']['max_mass_balance_abs_kg_per_kg'],
           '21_point_quadrature_vs_saved_full_node_mean_max_difference':float(np.max(np.abs(sparse_mean-s['mean_C']))),
           'saved_C_range':[float(s['C'].min()),float(s['C'].max())],
           'max_radial_C_increase_saved':float(np.max(np.diff(s['C'],axis=1))),
           'full_accepted_states_available_for_replay':False}
    if q!='Q1':
        c=summary[q]['completion'];event=c['critical_event_s'];idx=np.flatnonzero(s['times_s']==event)
        assert len(idx)==1
        saved_root_max=float(s['C'][idx[0]].max())
        assert abs(saved_root_max-.15)<1e-12
        assert c['max_C_at_reported_time']<.15
        assert c['reported_time_s']<=s['times_s'][-1]
        n=math.ceil(event/3600*10000)
        samples=summary[q]['metric_samples']['Q3' if q=='Q23' else 'Q4']
        assert samples['C'][0][0]==c['max_C_at_reported_time']
        entry.update({'completion':c,'recomputed_initial_reporting_integer':n,
          'recomputed_report_h':n/10000,'report_delay_s':c['reported_time_s']-event,
          'saved_root_max_C_21_material_points':saved_root_max,
          'report_threshold_margin':.15-c['max_C_at_reported_time'],
          'report_sample_reproduces_recorded_center_max':True,
          'all_node_report_max_replay_available':False})
    report['production'][q]=entry

for q,tag in [('Q1','final_v6'),('Q23','final_v6_Q23'),('Q4','final_v6_Q4')]:
    folder=ROOT/'paper_output/results/time_accuracy'/tag;original=read(folder/'time_accuracy_report.json')
    records=original['input_files'][:]
    for r in original['runs']:records+=r['output_artifacts']
    checks=check_records(records);assert all(r['matches'] for r in checks)
    baseline=load_npz(folder/'baseline/comparison_projection.npz')
    tight=load_npz(folder/'tight/comparison_projection.npz')
    ts=baseline['times_s'];rs=baseline['radii_m']
    assert np.array_equal(ts,np.arange(len(ts))) and np.array_equal(ts,tight['times_s'])
    assert np.array_equal(rs,tight['radii_m']) and len(rs)==21
    independent=independent_error(baseline,tight,ts,rs)
    assert independent['max_absolute_difference']==original['comparison']['max_absolute_difference']
    assert independent['locations']==original['comparison']['locations']
    bs=read(folder/'baseline/summary.json');tt=read(folder/'tight/summary.json')
    delta=None if q=='Q1' else tt['diagnostics']['event_s']-bs['diagnostics']['event_s']
    assert delta==original['comparison']['event_difference_s']
    changed={k:[bs['settings'][k],tt['settings'][k]] for k in bs['settings'] if bs['settings'][k]!=tt['settings'][k]}
    independent.update({'question':q,'report':rec(folder/'time_accuracy_report.json'),'hash_checks':checks,
      'sample_shape':[len(ts),len(rs)],'event_tight_minus_baseline_s':delta,'changed_settings':changed,
      'baseline_saved_NPZ_equals_formal':sha(folder/'baseline/sampled_solution.npz')==sha(production/q/'sampled_solution.npz'),
      'worker_returncodes':[r['process']['returncode'] for r in original['runs']],
      'same_N_not_a_pure_fixed_step_order_test':True,'source_report_exactly_reproduced':True})
    report['time_reductions'].append(independent)
    if q=='Q1':Q1_BASELINE=baseline
    del baseline,tight

version_map={sha(p):p for p in (ROOT/'paper_output/code/versions').glob('*.py')}
version_map.update({sha(p):p for p in (ROOT/'paper_output/code/modeling').glob('*.py')})
space_tags=['Q1_K_analytic_J_v3','Q23_K_analytic_J_v3','Q23_final_resolution_v5','Q4_final_resolution_v5','Q1_frozenD_analytic_J_v3']
spaces={}
for tag in space_tags:
    folder=ROOT/'paper_output/results/convergence'/tag;d=read(folder/'convergence_report.json');spaces[tag]=d
    source_records=[d['driver_code']]
    for r in d['runs']:
        source_records += [r[k] for k in ['code','jacobian_code','dense_storage_code'] if k in r]
    provenance=[]
    for r in source_records:
        hit=version_map.get(r['sha256'])
        provenance.append({'original_record':r,'matching_saved_source':None if hit is None else rec(hit)})
    sparse=[]
    for c in d['comparisons']:
        a=load_npz(folder/f"N{c['coarse_N']}"/'sampled_solution.npz')
        b=load_npz(folder/f"N{c['fine_N']}"/'sampled_solution.npz')
        common,ia,ib=np.intersect1d(a['times_s'],b['times_s'],return_indices=True)
        # R is input-only, so common times share R and equal material x also
        # represent equal physical positions. These are sparse stored samples.
        assert np.array_equal(a['material_x'],b['material_x'])
        assert np.array_equal(a['radius_m'][ia],b['radius_m'][ib])
        differences={k:float(np.max(np.abs(a[k][ia]-b[k][ib]))) for k in ['T_K','C']}
        ev=[r['diagnostics']['event_s'] for r in d['runs'] if r['settings']['intervals'] in [c['coarse_N'],c['fine_N']]]
        actual_event=None if ev[0] is None else ev[1]-ev[0]
        assert actual_event==c['event_difference_s']
        sparse.append({'coarse_N':c['coarse_N'],'fine_N':c['fine_N'],
          'source_archives':[rec(folder/f"N{n}"/'sampled_solution.npz') for n in [c['coarse_N'],c['fine_N']]],
          'actual_saved_common_times':len(common),'material_radii':len(a['material_x']),
          'max_difference_sparse_material_samples':differences,
          'event_difference_recomputed':actual_event,
          'recorded_full_second_physical_comparison':c,
          'same_sampling_grid_as_original_full_seconds':False})
    report['space_reports'].append({'tag':tag,'report':rec(folder/'convergence_report.json'),
       'source_provenance':provenance,'saved_sparse_reductions':sparse,
       'full_second_coarse_projection_persisted':False,
       'full_second_field_maxima_independently_recomputed_this_turn':False})

pairs={
 'Q1':spaces['Q1_K_analytic_J_v3']['comparisons'][-2:],
 'Q23':[spaces['Q23_K_analytic_J_v3']['comparisons'][-1],spaces['Q23_final_resolution_v5']['comparisons'][-1]],
 'Q4':spaces['Q4_final_resolution_v5']['comparisons'][-2:]}
for q,cc in pairs.items():
    old,new=[x['max_absolute_difference']['C'] for x in cc]
    p=math.log2(old/new);estimate=new/(2**p-1)
    value={'successive_max_C_differences':[old,new],'p':p,'fine_remaining_indicator':estimate,
           'max_C_error_locations':[x['locations']['C'] for x in cc],
           'same_point_scalar_asymptotic_expansion_proven':False,'strict_error_bound':False}
    if q!='Q1':
        d0,d1=[abs(x['event_difference_s']) for x in cc];pt=math.log2(d0/d1)
        value.update({'event_abs_differences_s':[d0,d1],'event_p':pt,'event_remaining_indicator_s':d1/(2**pt-1)})
    report['richardson'][q]=value

env=np.genfromtxt(ROOT/'paper_output/data_cleaned/A_environment_observed.csv',delimiter=',',names=True,encoding='utf-8-sig')
gt=np.interp(np.arange(1801.),env['time_s'],env['temperature_K'])
INITIAL_FOR_BESSEL=301.15
heat240,r240=independently_recurrence_bessel(gt,.36/(820*2600),25*.02/.36,240)
heat480,r480=independently_recurrence_bessel(gt,.36/(820*2600),25*.02/.36,480)
heatdiff=np.abs(Q1_BASELINE['T_K']-heat480);at=np.unravel_index(heatdiff.argmax(),heatdiff.shape)
report['Bessel']['independent_heat_recurrence']={'max_difference_to_final_N3200_time_baseline_K':float(heatdiff.max()),
    'location':{'time_s':int(at[0]),'radius_m':float(Q1_BASELINE['radii_m'][at[1]])},
    '240_to_480_full_integer_seconds_21_radii_max_difference_K':float(np.max(np.abs(heat480-heat240))),
    'root_relative_residual_240':r240,'root_relative_residual_480':r480,
    'max_difference_to_prior_240_term_comparison_K':float(np.max(np.abs(Q1_BASELINE['T_K']-heat240))),
    'method':'Independent per-second exact ramp recurrence and consecutive J0-zero root brackets; no model or prior benchmark imported.'}
gc=np.interp(np.arange(1801.),env['time_s'],env['air_moisture_kg_per_kg'])
INITIAL_FOR_BESSEL=2.55
water480,wr=independently_recurrence_bessel(gc,4.938e-9,8e-7*.02/4.938e-9,480)
frozen=load_npz(ROOT/'paper_output/results/convergence/Q1_frozenD_analytic_J_v3/N3200/sampled_solution.npz')
ix=frozen['times_s'].astype(int); assert np.array_equal(ix,frozen['times_s'])
report['Bessel']['fixed_D_saved_samples']={'D':4.938e-9,'N':3200,'time_count':len(ix),'material_radius_count':21,
    'max_C_difference':float(np.max(np.abs(water480[ix]-frozen['C']))),
    'scope':'Saved sparse times only; historical t=1 full-second maximum cannot be re-reduced from this archive.',
    'not_nonlinear_Q1_solution':True}
selfcheck_path=ROOT/'paper_output/results/bessel_validation/bessel_selfcheck.json'
selfcheck=read(selfcheck_path)
b_records=selfcheck['execution_provenance']['input_artifacts']+selfcheck['execution_provenance']['output_artifacts']
report['Bessel']['previous_selfcheck_read']={'report':rec(selfcheck_path),'checks':selfcheck['checks'],
    'hash_checks':check_records(b_records),'prior_PASS_not_used_as_new_execution':True}

# Verify invariant weights and telescoping directly without calling RHS.
invariants=[]
for n,R in [(3200,.02),(6400,.012)]:
    x=np.arange(n+1,dtype=float)/n;faces=np.r_[0.,(x[:-1]+x[1:])/2,1.];w=np.diff(faces*faces)/2
    flux=np.sin(np.arange(n+2,dtype=float));flux[0]=0.;flux[-1]=-8e-7*R*(.15-.05)
    derivative=np.diff(flux)/(R*R*w);loss=2*8e-7/R*(.15-.05)
    invariants.append({'N':n,'R':R,'weight_sum':float(w.sum()),
      'arbitrary_flux_telescoping_derivative_residual':float(2*w@derivative+loss),
      'scope':'Discrete algebra identity; arbitrary test flux, not a solved physical trajectory.'})
report['mass_implementation_recheck']={'independent_discrete_telescoping':invariants,
    'definition':'2*sum(w_i*C_i)+ell=C0; ell derivative uses the same surface flux as C RHS.',
    'production_implementation_scope':'All N+1 state nodes at all accepted times. Reported-time completion also all N+1 nodes.',
    'independence_limit':'This invariant checks self-consistency of assembled numerical conservation. It is not an external water-mass experiment or independent constitutive/energy validation.',
    'accepted_all_node_state_cache_retained':False}
report['source_read_checks']={'core':rec(ROOT/'paper_output/code/modeling/drying_core.py'),
    'completion':rec(ROOT/'paper_output/code/modeling/q3_model.py'),
    'projection_driver':rec(ROOT/'paper_output/code/modeling/verify_convergence.py'),
    'time_driver':rec(ROOT/'paper_output/code/modeling/verify_time_accuracy.py'),
    'benchmark':rec(ROOT/'paper_output/code/modeling/validate_bessel.py')}
report['elapsed_seconds']=time.perf_counter()-START
report['finished_at']=datetime.now(timezone.utc).isoformat()
report['helper']=rec(__file__)
path=OUT/'numerical_recheck.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps({'report':rec(path),'elapsed_seconds':report['elapsed_seconds'],
    'time_reductions':[{'question':x['question'],'maxima':x['max_absolute_difference'],'rounded':x['rounded_4dp_comparison']} for x in report['time_reductions']],
    'richardson':report['richardson'],'Bessel_new':report['Bessel']['independent_heat_recurrence'],
    'mass_new':{q:report['production'][q]['saved_mean_plus_loss_max_abs_residual'] for q in report['production']}},ensure_ascii=False))
