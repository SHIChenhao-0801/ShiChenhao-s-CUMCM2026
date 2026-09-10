"""Independent, bounded algebra/constitutive audit; no PDE integration or output mutation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys, warnings
import numpy as np
from scipy.integrate import quad
from scipy.special import expi
import pymupdf

ROOT = Path.cwd().resolve()
OUT = ROOT / 'paper_output/qa/recheck_20260910_1828'
assert ROOT.name == '2026CUMCM'
sys.path.insert(0, str(ROOT / 'paper_output/code/modeling'))
import drying_core as core
import analytic_jacobian as jac

def record(path):
    p = ROOT / path
    return {'path':path, 'bytes':p.stat().st_size,
            'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

result = {'started_utc':datetime.now(timezone.utc).isoformat(),
          'scope':'Fresh small algebra checks and read-only extraction; no PDE solver called',
          'python':sys.version, 'numpy':np.__version__, 'checks':[]}
sources = ['problem_files/CUMCM2026Problems/A题/A题.pdf',
           'notes/problem-reading/2026-09-10/A_problem_text.txt',
           'notes/A-modeling/2026-09-10/A题_完整建模与公式推导.md',
           'paper_output/code/modeling/drying_core.py',
           'paper_output/code/modeling/analytic_jacobian.py',
           'paper_output/data_cleaned/A_environment_observed.csv',
           'paper_output/data_cleaned/A_radius_observed.csv',
           'paper_output/results/production/final_v6a/numerical_summaries.json']
pdf = pymupdf.open(ROOT / sources[0])
text = '\n'.join(f'--- PAGE {i+1} ---\n'+p.get_text() for i,p in enumerate(pdf))
(OUT / 'original_pdf_fresh_text.txt').write_text(text, encoding='utf-8')
for i in [2,3]:
    pdf[i].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).save(OUT/f'original_pdf_page_{i+1}.png')
pdf.close()

environment = np.genfromtxt(ROOT/sources[5], delimiter=',',names=True,encoding='utf-8-sig')
radius = np.genfromtxt(ROOT/sources[6], delimiter=',',names=True,encoding='utf-8-sig')
result['observations'] = {'environment_rows':len(environment),
    'environment_time_range_s':[float(environment['time_s'][0]),float(environment['time_s'][-1])],
    'radius_rows':len(radius),
    'radius_time_range_s':[float(radius['time_s'][0]),float(radius['time_s'][-1])]}
rd0 = (760+90*2.55)/3.55
rcrit = .02*np.sqrt(rd0/760)
r_end = float(radius['radius_m'][-1])
first = int(np.flatnonzero(radius['radius_m'] < rcrit)[0])
result['density_incompatibility'] = {'rho_d0_kg_m3':rd0,
    'necessary_min_radius_m':rcrit,
    'first_literal_below_bound_time_h':float(radius['time_s'][first]/3600),
    'first_literal_below_bound_radius_m':float(radius['radius_m'][first]),
    'required_mean_rho_d_72h_kg_m3':rd0*(.02/r_end)**2,
    'maximum_conserved_dry_mass_fraction_72h':760*(r_end/.02)**2/rd0,
    'note':'First crossing refers to printed data, not an inferred true measurement crossing.'}

capacities=[]
for q, a,b,cd,cw,rd,R in [('Q23',650,128,1450,4186,(650+128*2.55)/3.55,.02),
                          ('Q4',760,90,1850,4000,rd0*(.02/.012)**2,.012)]:
    for C in [2.55,.15,.05265]:
        cp=(cd+cw*C)/(1+C)
        bmodel=(a+b*C)*cp
        bphysical=rd*(cd+cw*C)
        capacities.append({'question':q,'C':C,'R_m':R,'rho_d_kg_m3':rd,
                           'B_effective_J_m3_K':bmodel,'B_component_mixture_J_m3_K':bphysical,
                           'effective_to_component_ratio':bmodel/bphysical})
result['capacity_comparison_conditional_component_interpretation'] = capacities

primitive=[]
for a in [.89,.45,.30]:
    for left,right in [(.052,.15),(.15,2.55),(.052,.052000001)]:
        exact_quad=quad(lambda c:np.exp(-a/c),left,right,epsabs=1e-20,epsrel=1e-12)[0]
        phi=lambda c:c*np.exp(-a/c)+a*expi(-a/c)
        analytic=phi(right)-phi(left)
        if abs(right-left)<1e-7*max((left+right)/2,1e-3):
            coded=np.exp(-a/((left+right)/2))*(right-left)
        else: coded=analytic
        err=abs(coded-exact_quad)/abs(exact_quad)
        primitive.append({'a':a,'left':left,'right':right,'relative_error':float(err),
                          'pass':bool(err<1e-10)})
result['kirchhoff_primitive_quadrature']=primitive

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always')
    for q,scheme,latent,close in [
        ('Q1','kirchhoff',0,False),('Q23','kirchhoff',0,False),
        ('Q4','kirchhoff',0,False),('Q23','harmonic',0,False),
        ('Q4','harmonic',0,False),('Q4','kirchhoff',1,False),
        ('Q23','kirchhoff',0,True)]:
        model=core.RadialModel(core.Settings(question=q,intervals=8,shrink=(q=='Q4'),
             face_scheme=scheme,surface_latent_fraction=latent))
        state=model.initial()
        state[:-1:2]=312+8*model.x**2
        state[1:-1:2]=1.2 if close else 2.4-2.3*model.x**2
        state[-1]=.7
        t=18000.
        f=model.rhs(t,state)
        J=jac.jacobian(model,t,state).toarray()
        FD=np.zeros_like(J)
        for col in range(len(state)):
            step=(1e-3 if col%2==0 else (1e-8 if close else 1e-5))
            if col==len(state)-1:step=1e-3
            vals=[]
            for multiple in [2,1,-1,-2]:
                probe=state.copy();probe[col]+=multiple*step
                vals.append(model.rhs(t,probe))
            FD[:,col]=(-vals[0]+8*vals[1]-8*vals[2]+vals[3])/(12*step)
        row_scale=np.maximum(np.max(abs(J),axis=1),1e-12)
        scaled_error=float(np.max(abs(J-FD)/row_scale[:,None]))
        mass_weight=np.zeros_like(state);mass_weight[1:-1:2]=2*model.w;mass_weight[-1]=1
        mass_res=float(abs(mass_weight@f))
        mass_j=float(np.max(abs(mass_weight@J)))
        result['checks'].append({'case':f'{q}_{scheme}_latent{latent}_close{close}',
          'Jacobian_five_point_max_row_scaled_error':scaled_error,
          'Jacobian_five_point_max_abs_error':float(np.max(abs(J-FD))),
          'mass_rhs_residual_per_s':mass_res,'mass_jacobian_left_null_residual':mass_j,
          'passive_column_max_abs':float(np.max(abs(J[:,-1]))),
          'pass':bool(scaled_error<3e-5 and mass_res<1e-14 and mass_j<1e-14
                      and np.all(J[:,-1]==0))})
    result['warnings']=[str(w.message) for w in caught]

# Chain rule check independent of the model implementation.
kappa=2e-5;t=4321.;R=.02*np.exp(-kappa*t);r=.4*R
f_t_at_r=1+2*kappa*(r/R)**2
f_r=2*r/R**2;u=-kappa*r
result['material_chain_rule']={'manufactured_F':'F(t,x)=t+x^2; R=.02 exp(-2e-5 t)',
    'Eulerian_material_derivative':f_t_at_r+u*f_r,'fixed_x_derivative':1.,
    'residual':abs(f_t_at_r+u*f_r-1.)}

latent=[]
for q,upper_C,upper_psat in [('Q23',11.,1313.),('Q4',15.,1705.8)]:
    p=f'paper_output/results/experiments/physical_{q}_latent_N200_K/sampled_solution.npz'
    sources.append(p)
    with np.load(ROOT/p) as z:
        ii,jj=np.unravel_index(np.argmin(z['T_K']),z['T_K'].shape)
        ts=float(z['times_s'][ii]);TK=float(z['T_K'][ii,jj]);C=float(z['C'][ii,jj])
        R=float(z['radius_m'][ii]);x=float(z['material_x'][jj])
    Y=float(np.interp(ts,environment['time_s'],environment['air_moisture_kg_per_kg']))
    pv=101325*Y/(.621945+Y)
    rhod=((650+128*2.55)/3.55 if q=='Q23' else rd0)*(.02/R)**2
    jw=rhod*8e-7*(C-Y)
    latent.append({'question':q,'time_s':ts,'material_x':x,'T_C':TK-273.15,'C':C,
        'air_Y_kg_water_per_kg_dry_air_assumed':Y,'assumed_total_pressure_Pa':101325,
        'air_vapor_partial_pressure_Pa':pv,'NIST_upper_temperature_C':upper_C,
        'NIST_psat_upper_bound_Pa':upper_psat,'predicted_outward_jw_kg_m2_s':jw,
        'latent_heat_flux_W_m2':2.4e6*jw,
        'conditional_vapor_direction_conflict':bool(x==1 and TK-273.15<upper_C and pv>upper_psat and jw>0)})
result['fresh_saved_latent_sample_recheck']=latent

scale=[]
for q in ['Q1','Q23','Q4']:
    model=core.RadialModel(core.Settings(question=q,intervals=8,shrink=(q=='Q4')))
    for T,C,R in [(301.15,2.55,.02),(323.15,.15,.012 if q=='Q4' else .02),
                  (323.15,.05265,.012 if q=='Q4' else .02)]:
        rho,cp,conductivity,D=[float(v[0]) for v in model.properties(np.array([T]),np.array([C]))]
        scale.append({'question':q,'T_K':T,'C':C,'R_m':R,'rho_effective':rho,'cp':cp,
                      'k':conductivity,'D_m2_s':D,'heat_Biot_hR_over_k':25*R/conductivity,
                      'mass_Biot_betaR_over_D':8e-7*R/D,'R2_over_D_h':R**2/D/3600})
result['constitutive_scales_at_stated_probe_states_not_field_extrema']=scale
result['sources']=[record(p) for p in sources]
result['helper_source']=record('paper_output/qa/recheck_20260910_1828/physics_small_checks.py')
result['algebra_checks_pass']=bool(all(c['pass'] for c in result['checks']) and
    all(c['pass'] for c in primitive) and result['material_chain_rule']['residual']<1e-12)
result['physical_model_status']='CONDITIONAL_EFFECTIVE_MODEL; physical validation absent'
result['ended_utc']=datetime.now(timezone.utc).isoformat()
(OUT/'physics_small_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'algebra_checks_pass':result['algebra_checks_pass'],
      'jacobian_cases':result['checks'],'warnings':result['warnings'],
      'density':result['density_incompatibility'],'latent':latent},ensure_ascii=False,indent=2))
raise SystemExit(0 if result['algebra_checks_pass'] else 1)
