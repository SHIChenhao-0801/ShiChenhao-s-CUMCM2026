"""Read-only, local algebra/RHS checks. Does not integrate any PDE/ODE trajectory."""
from __future__ import annotations

import ast
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'paper_output/code/modeling'))
import numpy as np
from scipy.integrate import quad
from scipy.special import expi
import drying_core as core

paths = ['paper_output/code/modeling/drying_core.py',
         'paper_output/code/modeling/analytic_jacobian.py',
         'paper_output/code/verification/isotherm_activity_closure.py',
         'paper_output/code/verification/energy_balance_check.py',
         'paper_output/data_cleaned/A_environment_observed.csv',
         'paper_output/data_cleaned/A_radius_observed.csv']
def hashes():
    return {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
before = hashes()

# Extract only definitions; do not execute the scenario script's top-level code.
source = ROOT / paths[2]
tree = ast.parse(source.read_text(encoding='utf-8-sig'))
selected = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))
            and n.name in {'waterActivity', 'partitionFactor', 'ActivityModel'}]
namespace = {'np': np, 'core': core, 'AW_REF_DEFAULT': .6, 'C_REF': .05}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(source), 'exec'), namespace)
partition = namespace['partitionFactor']
activity = namespace['waterActivity']
ActivityModel = namespace['ActivityModel']

rhoD0 = (760 + 90*2.55)/(1+2.55)
radiusBound = .02*math.sqrt(rhoD0/760)
capacityRatio72 = (.01198/.02)**2*760/rhoD0

rhs_checks = []
for question, shrink in [('Q1', False), ('Q23', False), ('Q4', True)]:
    settings = core.Settings(question=question, intervals=8, shrink=shrink,
        face_scheme='kirchhoff', dense_storage='memory')
    model = core.RadialModel(settings)
    state = model.initial()
    state[:-1:2] = 301.15 + 12*model.x**2
    state[1:-1:2] = 1.3 + .5*(1-model.x**2)
    t = 3601.
    rhs = model.rhs(t, state)
    T, C = state[:-1:2], state[1:-1:2]
    dT, dC = rhs[:-1:2], rhs[1:-1:2]
    rho, cp, _, _ = model.properties(T,C)
    B = rho*cp
    radius = float(model.radius(t))
    tair, ceq = model.environment(t)
    lhs = float(2*math.pi*radius**2*np.sum(model.w*B*dT))
    boundary = float(2*math.pi*radius*settings.h*(tair-T[-1]))
    if question == 'Q1':
        dBdC = np.zeros_like(C)
    else:
        rho_slope, cp_amp = (128,2736) if question=='Q23' else (90,2150)
        dBdC = rho_slope*cp + rho*cp_amp/(1+C)**2
    Rdot = 0.
    if shrink:
        j = np.searchsorted(model.rad['time_s'], t)-1
        Rdot = float((model.rad['radius_m'][j+1]-model.rad['radius_m'][j]) /
                     (model.rad['time_s'][j+1]-model.rad['time_s'][j]))
    theta = T-273.15
    changing_capacity = float(2*math.pi*radius**2*np.sum(model.w*theta*dBdC*dC))
    changing_volume = float(4*math.pi*radius*Rdot*np.sum(model.w*B*theta))
    # Exact chain derivative of H'=sum(V_i per length * B_i * theta_i).
    total_H_derivative = lhs + changing_capacity + changing_volume
    p1 = ActivityModel(settings,p=1,awRef=.6).rhs(t,state)
    lowAw = ActivityModel(settings,p=2,awRef=.2).rhs(t,state)
    highAw = ActivityModel(settings,p=2,awRef=.8).rhs(t,state)
    item = {'question':question, 'intervals':8, 'time_s':t,
        'stateOrigin':'manufactured positive state; not a solved trajectory',
        'thermalWeightedRate_W_per_m':lhs,'boundaryHeatRate_W_per_m':boundary,
        'thermalAbsoluteResidual_W_per_m':abs(lhs-boundary),
        'thermalScaledResidual':abs(lhs-boundary)/max(1,abs(boundary)),
        'dryBasisMassRateResidual':float(2*model.w@dC+rhs[-1]),
        'instantaneousCapacityChainTerm_W_per_m':changing_capacity,
        'movingVolumeChainTerm_W_per_m':changing_volume,
        'actualDerivativeOfSumVBTheta_W_per_m':total_H_derivative,
        'oldTotalEnergyIdentityDefect_W_per_m':total_H_derivative-boundary,
        'p1RhsBitwiseIdentical':bool(np.array_equal(rhs,p1)),
        'awRef02Vs08RhsBitwiseIdenticalAtP2':bool(np.array_equal(lowAw,highAw))}
    assert item['thermalScaledResidual'] < 1e-12
    assert abs(item['dryBasisMassRateResidual']) < 1e-12
    assert item['p1RhsBitwiseIdentical'] and item['awRef02Vs08RhsBitwiseIdenticalAtP2']
    if question!='Q1':
        assert abs(item['oldTotalEnergyIdentityDefect_W_per_m']) > 1e-3
    rhs_checks.append(item)

potential_checks = []
for a in [.89,.45,.30]:
    for lo, hi in [(.05,.07),(.1,.3),(1.,2.55)]:
        phi = lambda c: c*np.exp(-a/c)+a*expi(-a/c)
        value = float(phi(hi)-phi(lo))
        integral, quadrature_estimate = quad(lambda c: math.exp(-a/c),lo,hi,
                                            epsabs=1e-25,epsrel=1e-12)
        relative = abs(value-integral)/abs(integral)
        assert relative < 1e-10
        potential_checks.append({'a':a,'lo':lo,'hi':hi,'potentialDifference':value,
            'independentScalarQuadrature':integral,'relativeDifference':relative,
            'quadratureEstimatedAbsoluteError':quadrature_estimate})

Cgrid = np.r_[.05,np.geomspace(.050001,3,100)]
parameter_checks = []
for p in [1.,1.5,2.,4.]:
    K = partition(Cgrid,p,.6)
    assert np.all(K >= 1/p-1e-12) and np.all(K <= 1+1e-12)
    parameter_checks.append({'p':p,'minimumK':float(K.min()),'maximumK':float(K.max()),
        'anchorK':float(partition(.05,p,.6)),'analyticAnchorLimit':1/p,
        'anchorActivity':float(activity(.05,p,.6))})
pbelow = activity(Cgrid,.5,.6)
assert np.all((pbelow>=.6)&(pbelow<=1))

# A pressure-drive counterexample at Cs=Ceq under an explicit 1-atm/50-C scenario.
pv = 101325*.05/(.621945+.05)
psat = 610.94*math.exp(17.625*50/(50+243.04))
assert psat-pv>0
phi02 = .2*math.exp(-.45/.2)+.45*expi(-.45/.2)
false_extra_flux = 2.4e-3*(math.exp(-3850/320)-math.exp(-3850/310))*phi02
assert false_extra_flux != 0

after = hashes()
assert after == before
report = {'status':'PASS_WITH_EXPLICIT_SCOPE', 'generatedAtUtc':datetime.now(timezone.utc).isoformat(),
    'scope':'Independent algebra, scalar quadrature, source-definition extraction and RHS evaluations; no PDE/ODE trajectory was integrated; no GUI or human review claimed.',
    'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'sourceHashes':before, 'sourceHashesUnchanged':before==after,
    'environment':{'python':sys.version,'numpy':np.__version__},
    'densityCompatibility':{'rhoD0_kg_m3':rhoD0,'necessaryMinimumRadius_m':radiusBound,
                           'maximumDryMassCapacityRatioAt72h':capacityRatio72},
    'instantaneousRhsChecks':rhs_checks,'kirchhoffPotentialChecks':potential_checks,
    'partitionFactorChecks':parameter_checks,
    'pBelowOneCounterexample':{'p':.5,'domain_C': [.05,3.], 'awRef':.6,
       'minActivity':float(pbelow.min()),'maxActivity':float(pbelow.max()),
       'conclusion':'p<1 does not force negative activity for C>=Cref; p>=1 is a slowing-scenario design choice.'},
    'pressureDriveCounterexample':{'CsEqualsCeq':.05,'baselineConcentrationDifference':0,
      'explicitAssumedPressure_Pa':101325,'temperature_C':50,'psatMinusPvAtAw1_Pa':psat-pv,
      'conclusion':'A nonzero pressure-transfer coefficient with aw=1 cannot identically represent the frozen concentration Robin at this state.'},
    'falseWholePotentialDifference':{'equal_C':.2,'T_left_K':310,'T_right_K':320,
      'intendedConcentrationFlux':0,'erroneousDifferenceOfThermalFactorTimesPotential':float(false_extra_flux)},
    'limits':['Manufactured RHS states are not evidence of prediction accuracy.',
      'The K inequalities do not establish monotonic PDE completion times.',
      'Empirical density reinterpretation remains an explicit closure assumption.',
      'No claim of calibrated sorption, full thermodynamics, or first originality.']}
(OUT/'innovation_proof_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':report['status'],'sourceHashesUnchanged':before==after,
  'density':report['densityCompatibility'],
  'rhs':[{'q':r['question'],'heatResidual':r['thermalScaledResidual'],
          'oldEnergyDefect':r['oldTotalEnergyIdentityDefect_W_per_m']} for r in rhs_checks],
  'maxKirchhoffRelativeDifference':max(r['relativeDifference'] for r in potential_checks)},ensure_ascii=False))
