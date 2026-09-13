"""Independently compare production nodal-dual FVM with Bessel benchmarks.

This script owns results/analytic_comparison only. It neither modifies the
solver nor writes the production run manifest or figure index. The Q1
nonlinear run validates temperature only against the exact linear heat PDE;
moisture comparison is deliberately performed in a separate frozen-D case.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import platform
import sys
import time

import numpy as np

from drying_core import Settings, solve_case, load_inputs, LOADED_CODE_SHA256
from validate_bessel import bessel_temperature, bessel_moisture

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'paper_output/results/analytic_comparison'
SOURCE=Path(__file__).resolve()
CORE=SOURCE.with_name('drying_core.py')
REFERENCE=SOURCE.with_name('validate_bessel.py')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def file_record(path):
    p=Path(path)
    return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}


def write_json(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def norm_summary(actual,reference,times,radii):
    err=actual-reference
    idx=np.unravel_index(np.argmax(np.abs(err)),err.shape)
    return {
        'max_abs_error':float(np.max(np.abs(err))),
        'rms_error':float(np.sqrt(np.mean(err**2))),
        'mean_signed_error':float(np.mean(err)),
        'max_error_time_s':float(times[idx[0]]),
        'max_error_radius_m':float(radii[idx[1]]),
        'error_at_max_location':float(err[idx]),
        'centre_max_abs_error':float(np.max(np.abs(err[:,0]))),
        'surface_max_abs_error':float(np.max(np.abs(err[:,-1]))),
        'finite_values':bool(np.all(np.isfinite(actual)) and np.all(np.isfinite(reference))),
    }


def write_comparison_csv(path,times,radii,T,Tref,C,Cref):
    with path.open('w',encoding='utf-8',newline='') as fh:
        writer=csv.writer(fh)
        writer.writerow(['time_s','radius_m','fvm_temperature_K','analytic_temperature_K',
                         'temperature_error_K','fvm_moisture_kg_per_kg',
                         'analytic_frozen_D_moisture_kg_per_kg','moisture_error_kg_per_kg'])
        for i,t in enumerate(times):
            for j,r in enumerate(radii):
                numeric=[t,r,T[i,j],Tref[i,j],T[i,j]-Tref[i,j],C[i,j]]
                values=[format(float(v),'.17g') for v in numeric]
                values += ['', ''] if Cref is None else [format(Cref[i,j],'.17g'),format(C[i,j]-Cref[i,j],'.17g')]
                writer.writerow(values)


def main():
    started=time.perf_counter()
    if Path.cwd().resolve()!=ROOT:
        raise RuntimeError('Run from the 2026CUMCM workspace root')
    OUT.mkdir(parents=True,exist_ok=True)
    source_records=[file_record(p) for p in [SOURCE,CORE,REFERENCE]]
    if sha(CORE)!=LOADED_CODE_SHA256:
        raise RuntimeError('Solver file changed after import')
    env,_,inputs=load_inputs(with_records=True)
    env_t,env_T,env_C=env['time_s'],env['temperature_K'],env['air_moisture_kg_per_kg']
    paper_times=np.array([100.,300.,600.,900.,1200.,1500.,1800.])
    paper_radii=np.array([0.,.005,.01,.015,.02])
    dense_times=np.arange(0.,1800.+1,10.)
    dense_radii=np.linspace(0.,.02,21)
    D=float(7e-9*np.exp(-.89/2.55))
    analytic={}
    for grid,ts,rs in [('paper',paper_times,paper_radii),('dense',dense_times,dense_radii)]:
        exact_T=bessel_temperature(ts,rs,env_t,env_T,n_terms=240)
        exact_C=bessel_moisture(ts,rs,env_t,env_C,D,n_terms=240)
        exact_T_refined=bessel_temperature(ts,rs,env_t,env_T,n_terms=480)
        exact_C_refined=bessel_moisture(ts,rs,env_t,env_C,D,n_terms=480)
        analytic[grid]=(exact_T,exact_C,{
            'heat_240_480_max_difference_K':float(np.max(np.abs(exact_T-exact_T_refined))),
            'frozen_water_240_480_max_difference_kg_per_kg':float(np.max(np.abs(exact_C-exact_C_refined)))})
    case_results=[]
    plot_payload=[]
    for mode,N in [('nonlinear_Q1',100),('nonlinear_Q1',200),('nonlinear_Q1',400),('frozen_D',100),('frozen_D',400),('frozen_D',800)]:
        name=f'{mode}_N{N}'
        setting=Settings(question='Q1',intervals=N,rtol=1e-10,
            atol_temperature=1e-10,atol_moisture=1e-11,
            early_max_step_s=2.,max_step_s=2.,
            face_scheme='kirchhoff',constant_D=D if mode=='frozen_D' else None)
        print(json.dumps({'event':'starting_case','case':name,'elapsed_total_s':time.perf_counter()-started}),flush=True)
        run=solve_case(setting)
        for rec in source_records+inputs:
            if sha(ROOT/rec['path'])!=rec['sha256']:
                raise RuntimeError('Source/input changed during comparison: '+rec['path'])
        case={'case_id':name,'settings':asdict(setting),'diagnostics':run.diagnostics(),
              'comparison_scope':'temperature only; nonlinear C has no Bessel reference' if mode=='nonlinear_Q1'
                                 else 'constant-property heat and frozen-D linear moisture',
              'comparisons':{},'output_artifacts':[]}
        for grid,ts,rs in [('paper',paper_times,paper_radii),('dense',dense_times,dense_radii)]:
            T,C=run.fields(ts,radii_m=rs)
            Tref,Cref,truncation=analytic[grid]
            if mode!='frozen_D':
                Cref=None
            comparisons={'temperature':norm_summary(T,Tref,ts,rs),'analytic_truncation_sensitivity':truncation}
            if Cref is not None:
                comparisons['frozen_D_moisture']=norm_summary(C,Cref,ts,rs)
            case['comparisons'][grid]=comparisons
            path=OUT/f'{name}_{grid}.csv'
            write_comparison_csv(path,ts,rs,T,Tref,C,Cref)
            case['output_artifacts'].append(file_record(path))
            if grid=='dense':
                plot_payload.append((mode,N,ts,np.max(np.abs(T-Tref),axis=1),
                                     None if Cref is None else np.max(np.abs(C-Cref),axis=1)))
        # State is a collocated nodal field whose balance is integrated over
        # surrounding dual cells. This separate diagnostic quantifies how a
        # strict cell-average interpretation differs; main comparison is point.
        node_T,node_C=run.fields(paper_times)
        node_r=run.model.x*.02
        edges=np.r_[0.,(node_r[1:]+node_r[:-1])/2.,.02]
        mean_T=bessel_temperature(paper_times,node_r,env_t,env_T,n_terms=240,cell_edges_m=edges)
        point_T=bessel_temperature(paper_times,node_r,env_t,env_T,n_terms=240)
        case['representation_diagnostic']={
            'primary_interpretation':'collocated nodal values with surrounding dual control-volume balances',
            'strict_cell_average_interpretation_is_not_primary':True,
            'heat_node_max_abs_error_K':float(np.max(np.abs(node_T-point_T))),
            'heat_vs_annular_average_max_abs_error_K':float(np.max(np.abs(node_T-mean_T))),
            'analytic_point_vs_annular_average_max_difference_K':float(np.max(np.abs(point_T-mean_T))),
            'note':'Endpoint dual cells are one-sided, so point-vs-average differences can be first order; they are not physical model error.'}
        if mode=='frozen_D':
            early_times=np.array([1.,2.,5.,10.,20.,30.,60.])
            early_radii=np.array([0.,.019,.02])
            early_T,early_C=run.fields(early_times,radii_m=early_radii)
            early_Tref=bessel_temperature(early_times,early_radii,env_t,env_T,n_terms=480)
            early_Cref=bessel_moisture(early_times,early_radii,env_t,env_C,D,n_terms=480)
            early_Cref240=bessel_moisture(early_times,early_radii,env_t,env_C,D,n_terms=240)
            case['early_boundary_layer']={
                'times_s':early_times.tolist(),'radii_m':early_radii.tolist(),
                'moisture':norm_summary(early_C,early_Cref,early_times,early_radii),
                'surface_errors_kg_per_kg':(early_C[:,-1]-early_Cref[:,-1]).tolist(),
                'analytic_240_480_max_difference':float(np.max(np.abs(early_Cref240-early_Cref)))}
            early_path=OUT/f'{name}_early.csv'
            write_comparison_csv(early_path,early_times,early_radii,early_T,early_Tref,early_C,early_Cref)
            case['output_artifacts'].append(file_record(early_path))
        case_results.append(case)
        write_json(OUT/f'{name}_report.json',case)
        print(json.dumps({'event':'completed_case','case':name,'elapsed_s':run.elapsed_s,
                         'paper_T_error':case['comparisons']['paper']['temperature']['max_abs_error'],
                         'dense_T_error':case['comparisons']['dense']['temperature']['max_abs_error'],
                         'dense_C_error':case['comparisons']['dense'].get('frozen_D_moisture',{}).get('max_abs_error')}),flush=True)
    heat=[c for c in case_results if c['case_id'].startswith('nonlinear_Q1')]
    water=[c for c in case_results if c['case_id'] in ['frozen_D_N100','frozen_D_N400']]
    refined_water=[c for c in case_results if c['case_id']=='frozen_D_N800'][0]
    convergence={}
    for grid in ['paper','dense']:
        eT=[c['comparisons'][grid]['temperature']['max_abs_error'] for c in heat]
        eC=[c['comparisons'][grid]['frozen_D_moisture']['max_abs_error'] for c in water]
        convergence[grid]={
            'heat_intervals':[100,200,400],'heat_max_abs_errors_K':eT,
            'heat_observed_orders':[float(np.log(eT[i]/eT[i+1])/np.log(2.)) for i in [0,1]],
            'water_intervals':[100,400],'water_max_abs_errors_kg_per_kg':eC,
            'water_observed_order_100_400':float(np.log(eC[0]/eC[1])/np.log(4.)),
            'both_refinements_reduce_heat_error':bool(eT[0]>eT[1]>eT[2]),
            'water_refinement_reduces_error':bool(eC[0]>eC[1]),
            'N400_heat_max_error_below_0_0001_K':bool(eT[-1]<1e-4),
            'N400_frozen_water_max_error_below_0_0001':bool(eC[-1]<1e-4),
            'N800_frozen_water_max_abs_error':refined_water['comparisons'][grid]['frozen_D_moisture']['max_abs_error'],
            'water_observed_order_400_800':float(np.log(eC[-1]/refined_water['comparisons'][grid]['frozen_D_moisture']['max_abs_error'])/np.log(2.)),
        }
    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'tmp/cache/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(11,4.3),constrained_layout=True)
    for mode,N,ts,eT,eC in plot_payload:
        if mode=='nonlinear_Q1':
            axes[0].semilogy(ts[1:],np.maximum(eT[1:],1e-16),label=f'N={N}')
        if mode=='frozen_D':
            axes[1].semilogy(ts[1:],np.maximum(eC[1:],1e-16),label=f'N={N}')
    for ax in axes:
        ax.set_xlabel('Time (s)');ax.grid(alpha=.25);ax.legend()
    axes[0].set(title='Q1 heat: FVM vs Bessel',ylabel='Maximum radial absolute error (K)')
    axes[1].set(title='Frozen-D moisture benchmark',ylabel='Maximum radial absolute error (kg/kg)')
    plot_path=OUT/'analytic_error_history.png'
    fig.savefig(plot_path,dpi=180);plt.close(fig)
    for rec in source_records+inputs:
        if sha(ROOT/rec['path'])!=rec['sha256']:
            raise RuntimeError('Source/input changed before final report: '+rec['path'])
    validation_pass=all(v['both_refinements_reduce_heat_error'] and v['water_refinement_reduces_error']
        and v['N400_heat_max_error_below_0_0001_K'] and v['N400_frozen_water_max_error_below_0_0001']
        for v in convergence.values())
    report={
        'schema_version':'1.0','question_id':'Q1','generated_by':'paper_output/code/modeling/compare_analytic.py',
        'generated_at':datetime.now(timezone.utc).isoformat(),'status':'PASS' if validation_pass else 'REVIEW_REQUIRED',
        'validation_criteria':'Both heat refinements and 100-to-400 frozen-water refinement reduce max error; N400 sampled max errors below 1e-4 in physical units.',
        'scope':'Numerical verification against the selected constant-coefficient PDE; no internal experimental accuracy claim.',
        'point_value_comparison':'Nodal-dual state is compared to exact point values at the same physical radii. Separate representation diagnostics quantify strict annular averages.',
        'primary_space_time_samples':{'paper_times_s':paper_times.tolist(),'paper_radii_m':paper_radii.tolist(),
                                     'dense_time_step_s':10.,'dense_time_range_s':[0.,1800.],
                                     'dense_radius_step_m':.001,'dense_radius_range_m':[0.,.02]},
        'nonlinear_moisture_note':'The nonlinear Q1 C solution is stored for provenance only, not compared with constant-D Bessel or labeled analytic truth.',
        'constant_diffusion_coefficient_m2_s':D,
        'core_static_review':{
            'kirchhoff_primitive':'F(C)=C*exp(-a/C)+a*Ei(-a/C), so F_prime(C)=exp(-a/C)',
            'water_face_flux':'Internal face radius times D0*exp(-3850/T_face)*(F(C_right)-F(C_left))/dx, with no thermal factor in the differenced potential.',
            'Q1_temperature_factor':'Exactly one, since D1 has no temperature dependence.',
            'no_spurious_soret_term':True,
            'internal_flux_cancellation':'Each face occurs with opposite signs in adjacent control-volume balances; weighted sum leaves only the surface flux.',
            'density_interpretation':'rho*cp is effective thermal capacity; independent dry-matter weighting is used for conserved moisture.',
            'scope_limitation':'Static consistency and linear benchmark do not alone validate all nonlinear long-time or shrinkage scenarios.'},
        'convergence':convergence,'cases':case_results,
        'total_elapsed_s':time.perf_counter()-started,
        'visual_studio_gui':'pending','human_review':'pending',
        'execution_provenance':{'run_command':sys.executable+' -B '+' '.join(sys.argv),
            'run_exit_code':0,'python_version':platform.python_version(),
            'source_files':source_records,'input_artifacts':inputs,
            'output_artifacts':[file_record(p) for p in sorted(OUT.glob('*.csv'))]+[file_record(plot_path)]},
    }
    write_json(OUT/'analytic_comparison_report.json',report)
    print(json.dumps({'status':report['status'],'convergence':convergence,'total_elapsed_s':report['total_elapsed_s']},indent=2),flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
