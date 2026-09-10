# 本文件为冻结求解源码的驼峰审查副本；来源、改名与 AST 核验见 tools/coreRenameReport.json。
"""Analytic sparse Jacobian for drying_core.RadialModel.rhs.

The ordering is T0,C0,...,TN,CN,A. A is a passive cumulative loss variable;
its entire column is exactly zero and must not use adaptive numdiff factors.
This file does not modify the core or select a production configuration.

Self-check from the contest root:
  C:\\Python314\\python.exe -B paper_output/code/modeling/analytic_jacobian.py --self-test
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import warnings

import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import coo_matrix
from scipy.special import expi


LOADED_CODE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


# 调和平均面对左右节点的解析偏导，供热通量与调和水通量使用。
def harmonicPartials(left, right):
    """Positive-coefficient partials; respect the core's tiny denominator guard."""
    total = left + right
    tiny = np.finfo(float).tiny
    denominator = np.maximum(total, tiny)
    ordinary = total > tiny
    dl = np.where(ordinary, 2 * (right / denominator) ** 2, 2 * right / denominator)
    dr = np.where(ordinary, 2 * (left / denominator) ** 2, 2 * left / denominator)
    return dl, dr


# 稀疏 Jacobian 按交错 T/C 状态组装；保留物性、水通量与容量分母的全部链式法则项。
def jacobian(model, t, y):
    """Return d(rhs)/d(y) as CSC without calling rhs or numerical differentiation.

Each internal face contributes opposite flux derivatives to its two cells.
For heat, differentiating 1/(rho*cp) adds -Tdot*cap_C/cap locally.
Kirchhoff's temperature factor is frozen at the symmetric face temperature;
the primitive's close-concentration branch is differentiated exactly as coded.
"""
    state = np.asarray(y, dtype=float)
    n = model.n
    if state.ndim != 1 or state.size != 2*n + 1:
        raise ValueError("Jacobian requires interleaved 1D state of length 2*n+1")
    s = model.settings
    T, C = state[:-1:2], state[1:-1:2]
    cc = np.maximum(C, 1e-12)
    active = (C > 1e-12).astype(float)
    rho, cp, k, D = model.properties(T, C)
    if s.question == 'Q1':
        a, d0, tempConstant = .89, 7e-9, 0.
        rhoC, cpC, kC = np.zeros(n), np.zeros(n), np.zeros(n)
    elif s.question in ('Q2', 'Q3', 'Q23'):
        a, d0, tempConstant = .45, 2.4e-3, 3850.
        rhoC = np.full(n, 128.) * active
        cpC = 2736. / (1. + cc)**2 * active
        kC = .38 / (1. + cc)**2 * active
    elif s.question == 'Q4':
        a, d0, tempConstant = .30, 4.2e-4, 3850.
        rhoC = np.full(n, 90.) * active
        cpC = 2150. / (1. + cc)**2 * active
        kC = .20 / (1. + cc)**2 * active
    else:
        raise ValueError(s.question)
    if s.constantThermal:
        rhoC, cpC, kC = np.zeros(n), np.zeros(n), np.zeros(n)
    capacity = rho * cp
    capacityC = rhoC * cp + rho * cpC
    if s.constantD is None:
        dC = D * (a / cc**2) * active
        dT = D * tempConstant / T**2
    else:
        dC, dT = np.zeros(n), np.zeros(n)

    radius = float(model.radius(t))
    if radius <= 0:
        raise ValueError("Nonpositive radius")
    tair, ceq = model.environment(t)
    geom = model.internalFaces / model.dx
    deltaT, deltaC = np.diff(T), np.diff(C)

    # Derivative columns for each face are (T_left,C_left,T_right,C_right).
    kHarm = model.harmonic(k)
    khL, khR = harmonicPartials(k[:-1], k[1:])
    # 每个面的四列依次为 T左、C左、T右、C右，对相邻两个控制体施加相反符号。
    heatDeriv = np.column_stack((
        -geom * kHarm,
        geom * khL * kC[:-1] * deltaT,
        geom * kHarm,
        geom * khR * kC[1:] * deltaT,
    ))
    heatG = np.zeros(n + 1)
    heatG[1:-1] = geom * kHarm * deltaT
    heatG[-1] = -s.h * radius * (T[-1] - tair)

    if s.faceScheme == 'harmonic' or s.constantD is not None:
        dh = model.harmonic(D)
        dhL, dhR = harmonicPartials(D[:-1], D[1:])
        waterDeriv = np.column_stack((
            geom * dhL * dT[:-1] * deltaC,
            geom * (dhL * dC[:-1] * deltaC - dh),
            geom * dhR * dT[1:] * deltaC,
            geom * (dhR * dC[1:] * deltaC + dh),
        ))
    elif s.faceScheme == 'kirchhoff':
        primitive = cc * np.exp(-a / cc) + a * expi(-a / cc)
        primitiveDelta = np.diff(primitive)
        meanC = (cc[:-1] + cc[1:]) / 2.
        meanT = (T[:-1] + T[1:]) / 2.
        deltaCc = np.diff(cc)
        small = np.abs(deltaCc) < 1e-7 * np.maximum(meanC, 1e-3)
        expLeft, expRight = np.exp(-a/cc[:-1]), np.exp(-a/cc[1:])
        primitiveL = -expLeft * active[:-1]
        primitiveR = expRight * active[1:]
        # 近等浓度时对实际 RHS 使用的中点分支求导，避免与求解器分支不一致。
        if np.any(small):
            fMid = np.exp(-a / meanC[small])
            fPrimeMid = fMid * a / meanC[small]**2
            primitiveDelta[small] = fMid * deltaCc[small]
            primitiveL[small] = (0.5*fPrimeMid*deltaCc[small]-fMid)*active[:-1][small]
            primitiveR[small] = (0.5*fPrimeMid*deltaCc[small]+fMid)*active[1:][small]
        temperatureFactor = np.exp(-tempConstant / meanT)
        coefficient = geom * d0 * temperatureFactor
        waterG = coefficient * primitiveDelta
        waterT = waterG * tempConstant / (2 * meanT**2)
        waterDeriv = np.column_stack((waterT, coefficient*primitiveL,
                                      waterT, coefficient*primitiveR))
    else:
        raise ValueError('Unknown nonlinear face scheme')

    heatScale = 1. / (radius**2 * model.w * capacity)
    waterScale = 1. / (radius**2 * model.w)
    surfaceHeatC = 0.
    if s.surfaceLatentFraction:
        rhoD = model.rhoD0 * (.02 / radius)**2
        surfaceHeatC = -radius*s.surfaceLatentFraction*s.latentJKg*rhoD*s.beta
        heatG[-1] += surfaceHeatC * (C[-1] - ceq)
    tempDerivative = np.diff(heatG) * heatScale

    faceIndex = np.arange(n-1)
    faceColumns = np.column_stack((2*faceIndex, 2*faceIndex+1,
                                    2*faceIndex+2, 2*faceIndex+3)).ravel()
    rows, columns, values = [], [], []

    def addFace(rowIndex, derivatives, factor):
        rows.append(np.repeat(rowIndex, 4))
        columns.append(faceColumns)
        values.append((derivatives * factor[:, None]).ravel())

    addFace(2*faceIndex, heatDeriv, heatScale[:-1])
    addFace(2*faceIndex+2, heatDeriv, -heatScale[1:])
    addFace(2*faceIndex+1, waterDeriv, waterScale[:-1])
    addFace(2*faceIndex+3, waterDeriv, -waterScale[1:])
    cellIndex = np.arange(n)
    rows.append(2*cellIndex)
    columns.append(2*cellIndex+1)
    # 热容量随 C 改变，必须保留 -Tdot*(容量对C偏导)/容量 这一局部项。
    values.append(-tempDerivative * capacityC / capacity)
    rows.append(np.array([2*n-2, 2*n-2, 2*n-1, 2*n]))
    columns.append(np.array([2*n-2, 2*n-1, 2*n-1, 2*n-1]))
    values.append(np.array([-s.h*radius*heatScale[-1],
                            surfaceHeatC*heatScale[-1],
                            -s.beta*radius*waterScale[-1], 2*s.beta/radius]))
    # 面模板只有邻近耦合；COO 合并重复贡献后转 CSC，交给 BDF 稀疏线性求解。
    matrix = coo_matrix((np.concatenate(values),
                        (np.concatenate(rows), np.concatenate(columns))),
                       shape=(2*n+1, 2*n+1)).tocsc()
    matrix.sum_duplicates()
    matrix.eliminate_zeros()
    return matrix


# 此历史自检入口仅验证导数和小网格接线，不能替代正式网格与人工代码审核。
def selfTest(outputDirectory):
    """Independent RHS perturbation checks, a conservation derivative, and tiny BDF runs."""
    import scipy
    from dryingCore import ROOT, Settings, RadialModel, LOADED_CODE_SHA256 as CORE_LOADED_CODE_SHA256

    started = time.perf_counter()
    rng = np.random.default_rng(20260910)
    relativeTolerance, absoluteTolerance = 5e-6, 5e-10
    cases = []
    for question in ['Q1', 'Q23', 'Q4']:
        for scheme in ['harmonic', 'kirchhoff']:
            for latent in [0., 1.]:
                cases.append(Settings(question=question, intervals=8, faceScheme=scheme,
                                      shrink=(question=='Q4'), surfaceLatentFraction=latent))
    for question in ['Q1', 'Q23', 'Q4']:
        for constantDiffusivity, constantThermal in [(2e-9, False), (None, True), (2e-9, True)]:
            cases.append(Settings(question=question, intervals=8, faceScheme='kirchhoff',
                                  shrink=(question=='Q4'), constantD=constantDiffusivity,
                                  constantThermal=constantThermal, surfaceLatentFraction=1.))
    records, failures = [], []
    for settings in cases:
        model = RadialModel(settings)
        x = model.x
        states = {
            'initial': (0., model.initial()),
            'nonuniform': (18000., model.initial()),
            'late_dry': (150000., model.initial()),
            'near_uniform_small_branch': (14401., model.initial()),
        }
        states['nonuniform'][1][:-1:2] = 303. + 17.*x**2
        states['nonuniform'][1][1:-1:2] = 2.4 - 2.0*x**2
        states['late_dry'][1][:-1:2] = 321. + 2.0*x**2
        states['late_dry'][1][1:-1:2] = .175 - .115*x**2
        states['near_uniform_small_branch'][1][:-1:2] = 303. + 17.*x**2
        states['near_uniform_small_branch'][1][1:-1:2] = .15 + 1e-10*x
        for stateName, (t, y) in states.items():
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter('always')
                matrix = jacobian(model, t, y)
                vectors = []
                for _ in range(4):
                    direction = rng.normal(size=y.size)
                    direction[:-1:2] *= 1.0
                    direction[1:-1:2] *= .02
                    direction[-1] = .3
                    vectors.append(direction)
                directional = []
                for direction in vectors:
                    predicted = matrix @ direction
                    steps = []
                    for step in [1e-4, 3e-5, 1e-5]:
                        finiteDifference = (model.rhs(t, y+step*direction)-
                                             model.rhs(t, y-step*direction))/(2*step)
                        absoluteError = float(np.max(np.abs(predicted-finiteDifference)))
                        scale = max(float(np.max(np.abs(predicted))),
                                    float(np.max(np.abs(finiteDifference))), 1e-30)
                        scaled = float(np.max(np.abs(predicted-finiteDifference)/
                            (absoluteTolerance + relativeTolerance*np.maximum(
                                np.abs(predicted), np.abs(finiteDifference)))))
                        steps.append({'step':step, 'max_abs_error':absoluteError,
                                      'relative_inf_error':absoluteError/scale,
                                      'max_component_tolerance_ratio':scaled})
                    best = min(steps, key=lambda item:item['max_component_tolerance_ratio'])
                    directional.append({'all_step_errors':steps, 'best':best})
                passive = np.zeros(y.size); passive[-1] = 1.
                passiveAnalytic = float(np.max(np.abs(matrix @ passive)))
                passiveFd = float(np.max(np.abs(model.rhs(t, y+passive)-model.rhs(t,y-passive))))
                massWeights = np.zeros(y.size)
                massWeights[1:-1:2] = 2*model.w
                massWeights[-1] = 1.
                conservation = float(np.max(np.abs(np.asarray(massWeights @ matrix))))
            warningMessages = [str(w.message) for w in captured]
            passed = (all(step['max_component_tolerance_ratio'] <= 1
                          for d in directional for step in d['all_step_errors'])
                      and passiveAnalytic == 0 and passiveFd == 0 and conservation < 1e-11
                      and np.isfinite(matrix.data).all() and not warningMessages)
            record = {'settings':asdict(settings), 'state':stateName, 'time_s':t,
                      'status':'PASS' if passed else 'FAIL', 'matrix_shape':matrix.shape,
                      'matrix_nnz':matrix.nnz, 'directional_checks':directional,
                      'passive_column_analytic_abs':passiveAnalytic,
                      'passive_column_finite_difference_abs':passiveFd,
                      'mass_balance_derivative_abs':conservation, 'warnings':warningMessages}
            records.append(record)
            if not passed:
                failures.append(f"{settings.question}/{settings.faceScheme}/latent={settings.surfaceLatentFraction}/{stateName}/constant_D={settings.constantD}/constant_thermal={settings.constantThermal}")
    smokeRecords = []
    for scheme in ['harmonic', 'kirchhoff']:
        for question in ['Q23', 'Q4']:
            settings = Settings(question=question, intervals=8, faceScheme=scheme,
                                shrink=(question=='Q4'), surfaceLatentFraction=1.)
            model = RadialModel(settings)
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter('always')
                result = solve_ivp(model.rhs, (0., 2.), model.initial(), method='BDF',
                                   jac=lambda t,y:jacobian(model,t,y), rtol=1e-10,
                                   atol=1e-12, max_step=.2)
            msgs = [str(w.message) for w in captured]
            passed = bool(result.success and np.isfinite(result.y).all() and not msgs)
            smokeRecords.append({'question':question, 'face_scheme':scheme, 'interval_s':[0,2],
                                  'status':'PASS' if passed else 'FAIL', 'warnings':msgs,
                                  'nfev':result.nfev, 'njev':result.njev, 'nlu':result.nlu,
                                  'purpose':'Short Jacobian/BDF wiring check, not production accuracy'})
            if not passed:
                failures.append(f"BDF_smoke/{question}/{scheme}")
    currentSourceHash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    currentCoreHash = hashlib.sha256((ROOT/'paper_output/code/review_delivery/dryingCore.py').read_bytes()).hexdigest()
    if currentSourceHash != LOADED_CODE_SHA256 or currentCoreHash != CORE_LOADED_CODE_SHA256:
        failures.append('Source file changed after module load during validation')
    report = {'schema_version':'1.0', 'created_utc':datetime.now(timezone.utc).isoformat(),
              'status':'PASS' if not failures else 'FAIL', 'failures':failures,
              'source_sha256':LOADED_CODE_SHA256,
              'core_sha256':CORE_LOADED_CODE_SHA256,
              'source_hash_policy':'SHA-256 frozen when each module is imported; files checked unchanged before report save.',
              'runtime':{'python':sys.version,'executable':sys.executable,'numpy':np.__version__,'scipy':scipy.__version__},
              'seed':20260910,'relative_component_tolerance':relativeTolerance,
              'absolute_component_tolerance':absoluteTolerance,
              'finite_difference_policy':'Central directional differences, three decreasing steps; every step must satisfy the mixed absolute/relative component tolerance. Best comparison is supplementary only.',
              'case_state_count':len(records), 'direction_count':4*len(records),
              'checks':records,'short_BDF_checks':smokeRecords,
              'elapsed_s':time.perf_counter()-started,
              'limitations':['No full production run or grid convergence performed here.',
                             'Tiny denominator/underflow extensions at nonphysical Newton probes are not calibrated physical data.',
                             'Only this module and the short tests use analytic Jacobian until main agent hooks core.',
                             'Visual Studio reproduction and human review remain pending.']}
    outputDirectory.mkdir(parents=True, exist_ok=True)
    (outputDirectory/'analytic_jacobian_selftest.json').write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    brief = {key:report[key] for key in ['status','failures','case_state_count','direction_count','elapsed_s']}
    brief['max_best_component_tolerance_ratio'] = max(
        d['best']['max_component_tolerance_ratio'] for r in records for d in r['directional_checks'])
    brief['max_all_steps_component_tolerance_ratio'] = max(
        step['max_component_tolerance_ratio'] for r in records
        for d in r['directional_checks'] for step in d['all_step_errors'])
    brief['max_mass_balance_derivative_abs'] = max(r['mass_balance_derivative_abs'] for r in records)
    brief['warning_count'] = sum(len(r['warnings']) for r in records+smokeRecords)
    print(json.dumps(brief,ensure_ascii=False,indent=2))
    return 0 if not failures else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--output-dir', type=Path,
        default=Path(__file__).resolve().parents[2]/'code/review_delivery/runtime/jacobianValidation')
    arguments = parser.parse_args()
    if not arguments.self_test:
        parser.error('Use --self-test, or import jacobian(model,t,y) from this module.')
    raise SystemExit(selfTest(arguments.output_dir))
