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


def _harmonic_partials(left, right):

    total = left + right
    tiny = np.finfo(float).tiny
    denominator = np.maximum(total, tiny)
    ordinary = total > tiny
    dl = np.where(ordinary, 2 * (right / denominator) ** 2, 2 * right / denominator)
    dr = np.where(ordinary, 2 * (left / denominator) ** 2, 2 * left / denominator)
    return dl, dr


def jacobian(model, t, y):


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
        a, d0, temp_constant = .89, 7e-9, 0.
        rho_c, cp_c, k_c = np.zeros(n), np.zeros(n), np.zeros(n)
    elif s.question in ('Q2', 'Q3', 'Q23'):
        a, d0, temp_constant = .45, 2.4e-3, 3850.
        rho_c = np.full(n, 128.) * active
        cp_c = 2736. / (1. + cc)**2 * active
        k_c = .38 / (1. + cc)**2 * active
    elif s.question == 'Q4':
        a, d0, temp_constant = .30, 4.2e-4, 3850.
        rho_c = np.full(n, 90.) * active
        cp_c = 2150. / (1. + cc)**2 * active
        k_c = .20 / (1. + cc)**2 * active
    else:
        raise ValueError(s.question)
    if s.constant_thermal:
        rho_c, cp_c, k_c = np.zeros(n), np.zeros(n), np.zeros(n)
    capacity = rho * cp
    capacity_c = rho_c * cp + rho * cp_c
    if s.constant_D is None:
        d_c = D * (a / cc**2) * active
        d_t = D * temp_constant / T**2
    else:
        d_c, d_t = np.zeros(n), np.zeros(n)

    radius = float(model.radius(t))
    if radius <= 0:
        raise ValueError("Nonpositive radius")
    tair, ceq = model.environment(t)
    geom = model.internal_faces / model.dx
    delta_t, delta_c = np.diff(T), np.diff(C)


    k_harm = model.harmonic(k)
    kh_l, kh_r = _harmonic_partials(k[:-1], k[1:])
    heat_deriv = np.column_stack((
        -geom * k_harm,
        geom * kh_l * k_c[:-1] * delta_t,
        geom * k_harm,
        geom * kh_r * k_c[1:] * delta_t,
    ))
    heat_g = np.zeros(n + 1)
    heat_g[1:-1] = geom * k_harm * delta_t
    heat_g[-1] = -s.h * radius * (T[-1] - tair)

    if s.face_scheme == 'harmonic' or s.constant_D is not None:
        dh = model.harmonic(D)
        dh_l, dh_r = _harmonic_partials(D[:-1], D[1:])
        water_deriv = np.column_stack((
            geom * dh_l * d_t[:-1] * delta_c,
            geom * (dh_l * d_c[:-1] * delta_c - dh),
            geom * dh_r * d_t[1:] * delta_c,
            geom * (dh_r * d_c[1:] * delta_c + dh),
        ))
    elif s.face_scheme == 'kirchhoff':
        primitive = cc * np.exp(-a / cc) + a * expi(-a / cc)
        primitive_delta = np.diff(primitive)
        mean_c = (cc[:-1] + cc[1:]) / 2.
        mean_t = (T[:-1] + T[1:]) / 2.
        delta_cc = np.diff(cc)
        small = np.abs(delta_cc) < 1e-7 * np.maximum(mean_c, 1e-3)
        exp_left, exp_right = np.exp(-a/cc[:-1]), np.exp(-a/cc[1:])
        primitive_l = -exp_left * active[:-1]
        primitive_r = exp_right * active[1:]
        if np.any(small):
            f_mid = np.exp(-a / mean_c[small])
            f_prime_mid = f_mid * a / mean_c[small]**2
            primitive_delta[small] = f_mid * delta_cc[small]
            primitive_l[small] = (0.5*f_prime_mid*delta_cc[small]-f_mid)*active[:-1][small]
            primitive_r[small] = (0.5*f_prime_mid*delta_cc[small]+f_mid)*active[1:][small]
        temperature_factor = np.exp(-temp_constant / mean_t)
        coefficient = geom * d0 * temperature_factor
        water_g = coefficient * primitive_delta
        water_t = water_g * temp_constant / (2 * mean_t**2)
        water_deriv = np.column_stack((water_t, coefficient*primitive_l,
                                      water_t, coefficient*primitive_r))
    else:
        raise ValueError('Unknown nonlinear face scheme')

    heat_scale = 1. / (radius**2 * model.w * capacity)
    water_scale = 1. / (radius**2 * model.w)
    surface_heat_c = 0.
    if s.surface_latent_fraction:
        rho_d = model.rho_d0 * (.02 / radius)**2
        surface_heat_c = -radius*s.surface_latent_fraction*s.latent_J_kg*rho_d*s.beta
        heat_g[-1] += surface_heat_c * (C[-1] - ceq)
    temp_derivative = np.diff(heat_g) * heat_scale

    face_index = np.arange(n-1)
    face_columns = np.column_stack((2*face_index, 2*face_index+1,
                                    2*face_index+2, 2*face_index+3)).ravel()
    rows, columns, values = [], [], []

    def add_face(row_index, derivatives, factor):
        rows.append(np.repeat(row_index, 4))
        columns.append(face_columns)
        values.append((derivatives * factor[:, None]).ravel())

    add_face(2*face_index, heat_deriv, heat_scale[:-1])
    add_face(2*face_index+2, heat_deriv, -heat_scale[1:])
    add_face(2*face_index+1, water_deriv, water_scale[:-1])
    add_face(2*face_index+3, water_deriv, -water_scale[1:])
    cell_index = np.arange(n)
    rows.append(2*cell_index)
    columns.append(2*cell_index+1)
    values.append(-temp_derivative * capacity_c / capacity)
    rows.append(np.array([2*n-2, 2*n-2, 2*n-1, 2*n]))
    columns.append(np.array([2*n-2, 2*n-1, 2*n-1, 2*n-1]))
    values.append(np.array([-s.h*radius*heat_scale[-1],
                            surface_heat_c*heat_scale[-1],
                            -s.beta*radius*water_scale[-1], 2*s.beta/radius]))
    matrix = coo_matrix((np.concatenate(values),
                        (np.concatenate(rows), np.concatenate(columns))),
                       shape=(2*n+1, 2*n+1)).tocsc()
    matrix.sum_duplicates()
    matrix.eliminate_zeros()
    return matrix


def _self_test(output_directory):

    import scipy
    from drying_core import ROOT, Settings, RadialModel, LOADED_CODE_SHA256 as CORE_LOADED_CODE_SHA256

    started = time.perf_counter()
    rng = np.random.default_rng(20260910)
    relative_tolerance, absolute_tolerance = 5e-6, 5e-10
    cases = []
    for question in ['Q1', 'Q23', 'Q4']:
        for scheme in ['harmonic', 'kirchhoff']:
            for latent in [0., 1.]:
                cases.append(Settings(question=question, intervals=8, face_scheme=scheme,
                                      shrink=(question=='Q4'), surface_latent_fraction=latent))
    for question in ['Q1', 'Q23', 'Q4']:
        for constant_d, constant_thermal in [(2e-9, False), (None, True), (2e-9, True)]:
            cases.append(Settings(question=question, intervals=8, face_scheme='kirchhoff',
                                  shrink=(question=='Q4'), constant_D=constant_d,
                                  constant_thermal=constant_thermal, surface_latent_fraction=1.))
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
        for state_name, (t, y) in states.items():
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
                        finite_difference = (model.rhs(t, y+step*direction)-
                                             model.rhs(t, y-step*direction))/(2*step)
                        absolute_error = float(np.max(np.abs(predicted-finite_difference)))
                        scale = max(float(np.max(np.abs(predicted))),
                                    float(np.max(np.abs(finite_difference))), 1e-30)
                        scaled = float(np.max(np.abs(predicted-finite_difference)/
                            (absolute_tolerance + relative_tolerance*np.maximum(
                                np.abs(predicted), np.abs(finite_difference)))))
                        steps.append({'step':step, 'max_abs_error':absolute_error,
                                      'relative_inf_error':absolute_error/scale,
                                      'max_component_tolerance_ratio':scaled})
                    best = min(steps, key=lambda item:item['max_component_tolerance_ratio'])
                    directional.append({'all_step_errors':steps, 'best':best})
                passive = np.zeros(y.size); passive[-1] = 1.
                passive_analytic = float(np.max(np.abs(matrix @ passive)))
                passive_fd = float(np.max(np.abs(model.rhs(t, y+passive)-model.rhs(t,y-passive))))
                mass_weights = np.zeros(y.size)
                mass_weights[1:-1:2] = 2*model.w
                mass_weights[-1] = 1.
                conservation = float(np.max(np.abs(np.asarray(mass_weights @ matrix))))
            warning_messages = [str(w.message) for w in captured]
            passed = (all(step['max_component_tolerance_ratio'] <= 1
                          for d in directional for step in d['all_step_errors'])
                      and passive_analytic == 0 and passive_fd == 0 and conservation < 1e-11
                      and np.isfinite(matrix.data).all() and not warning_messages)
            record = {'settings':asdict(settings), 'state':state_name, 'time_s':t,
                      'status':'PASS' if passed else 'FAIL', 'matrix_shape':matrix.shape,
                      'matrix_nnz':matrix.nnz, 'directional_checks':directional,
                      'passive_column_analytic_abs':passive_analytic,
                      'passive_column_finite_difference_abs':passive_fd,
                      'mass_balance_derivative_abs':conservation, 'warnings':warning_messages}
            records.append(record)
            if not passed:
                failures.append(f"{settings.question}/{settings.face_scheme}/latent={settings.surface_latent_fraction}/{state_name}/constant_D={settings.constant_D}/constant_thermal={settings.constant_thermal}")
    smoke_records = []
    for scheme in ['harmonic', 'kirchhoff']:
        for question in ['Q23', 'Q4']:
            settings = Settings(question=question, intervals=8, face_scheme=scheme,
                                shrink=(question=='Q4'), surface_latent_fraction=1.)
            model = RadialModel(settings)
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter('always')
                result = solve_ivp(model.rhs, (0., 2.), model.initial(), method='BDF',
                                   jac=lambda t,y:jacobian(model,t,y), rtol=1e-10,
                                   atol=1e-12, max_step=.2)
            msgs = [str(w.message) for w in captured]
            passed = bool(result.success and np.isfinite(result.y).all() and not msgs)
            smoke_records.append({'question':question, 'face_scheme':scheme, 'interval_s':[0,2],
                                  'status':'PASS' if passed else 'FAIL', 'warnings':msgs,
                                  'nfev':result.nfev, 'njev':result.njev, 'nlu':result.nlu,
                                  'purpose':'Short Jacobian/BDF wiring check, not production accuracy'})
            if not passed:
                failures.append(f"BDF_smoke/{question}/{scheme}")
    current_source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    current_core_hash = hashlib.sha256((ROOT/'paper_output/code/modeling/drying_core.py').read_bytes()).hexdigest()
    if current_source_hash != LOADED_CODE_SHA256 or current_core_hash != CORE_LOADED_CODE_SHA256:
        failures.append('Source file changed after module load during validation')
    report = {'schema_version':'1.0', 'created_utc':datetime.now(timezone.utc).isoformat(),
              'status':'PASS' if not failures else 'FAIL', 'failures':failures,
              'source_sha256':LOADED_CODE_SHA256,
              'core_sha256':CORE_LOADED_CODE_SHA256,
              'source_hash_policy':'SHA-256 frozen when each module is imported; files checked unchanged before report save.',
              'runtime':{'python':sys.version,'executable':sys.executable,'numpy':np.__version__,'scipy':scipy.__version__},
              'seed':20260910,'relative_component_tolerance':relative_tolerance,
              'absolute_component_tolerance':absolute_tolerance,
              'finite_difference_policy':'Central directional differences, three decreasing steps; every step must satisfy the mixed absolute/relative component tolerance. Best comparison is supplementary only.',
              'case_state_count':len(records), 'direction_count':4*len(records),
              'checks':records,'short_BDF_checks':smoke_records,
              'elapsed_s':time.perf_counter()-started,
              'limitations':['No full production run or grid convergence performed here.',
                             'Tiny denominator/underflow extensions at nonphysical Newton probes are not calibrated physical data.',
                             'Only this module and the short tests use analytic Jacobian until main agent hooks core.',
                             'Visual Studio reproduction and human review remain pending.']}
    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory/'analytic_jacobian_selftest.json').write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    brief = {key:report[key] for key in ['status','failures','case_state_count','direction_count','elapsed_s']}
    brief['max_best_component_tolerance_ratio'] = max(
        d['best']['max_component_tolerance_ratio'] for r in records for d in r['directional_checks'])
    brief['max_all_steps_component_tolerance_ratio'] = max(
        step['max_component_tolerance_ratio'] for r in records
        for d in r['directional_checks'] for step in d['all_step_errors'])
    brief['max_mass_balance_derivative_abs'] = max(r['mass_balance_derivative_abs'] for r in records)
    brief['warning_count'] = sum(len(r['warnings']) for r in records+smoke_records)
    print(json.dumps(brief,ensure_ascii=False,indent=2))
    return 0 if not failures else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--output-dir', type=Path,
        default=Path(__file__).resolve().parents[2]/'results/jacobian_validation')
    arguments = parser.parse_args()
    if not arguments.self_test:
        parser.error('Use --self-test, or import jacobian(model,t,y) from this module.')
    raise SystemExit(_self_test(arguments.output_dir))
