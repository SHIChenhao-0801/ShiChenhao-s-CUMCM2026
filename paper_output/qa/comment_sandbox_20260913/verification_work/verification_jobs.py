from __future__ import annotations
import argparse
import importlib
import json
import os
from pathlib import Path
import sys
import time
import traceback


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--job', required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    os.chdir(root)
    sys.path[:0] = [str(root / 'paper_output/code/modeling'), str(root / 'paper_output/code/verification')]
    os.environ['MPLCONFIGDIR'] = str(root / 'tmp/cache/matplotlib')
    os.environ['OPENBLAS_NUM_THREADS'] = '1'
    os.environ['OMP_NUM_THREADS'] = '1'
    import numpy as np
    from dataclasses import replace
    import drying_core as core
    out = root / 'execution_records'
    out.mkdir(exist_ok=True)
    started = time.perf_counter()
    report = {'job': args.job, 'scope': 'Explicit function-level numerical check; not every default long experiment', 'status': 'RUNNING'}

    def short_settings(question='Q1', **kw):
        defaults = dict(question=question, intervals=20, shrink=question == 'Q4', face_scheme='kirchhoff',
                        rtol=1e-9, atol_temperature=1e-9, atol_moisture=1e-11,
                        early_max_step_s=2., max_step_s=120., dense_storage='memory')
        defaults.update(kw)
        return core.Settings(**defaults)

    try:
        if args.job == 'crossvalidate_solver_pair':
            import crossvalidate_solver as cv
            rows = [cv.runCase('sandbox_Q1_' + method, short_settings(method=method)) for method in ('BDF', 'Radau')]
            assert all(r['status'] == 'computed' and r['diagnostics']['solver_success'] for r in rows)
            report['rows'] = rows
        elif args.job == 'latent_single':
            import latent_heat_scenarios as latent
            row = latent.scenario('Q23', False, .25, 20)
            assert row['diagnostics']['solver_success'] and row['eventTimeS'] > 0
            assert len(row['sampleTimesS']) == len(row['surfaceTemperatureC']) == len(row['surfaceMoisture'])
            report['row'] = row
        elif args.job == 'energy_q1':
            import energy_balance_check as energy
            row = energy.runCase('Q1', 20, False)
            assert row['rateIdentityMaxRelativeDeviation'] < 1e-8
            report['row'] = row
            report['cumulativeCriterionPassed'] = row['cumulativePassed']
        elif args.job == 'sensitivity_control':
            import sensitivity_analysis as sensitivity
            row = sensitivity.control_check()
            assert np.isfinite(row['differenceSeconds']) and row['differenceSeconds'] < .01
            report['row'] = row
        elif args.job == 'isotherm_old_interface':
            import isotherm_diagnose as diagnose
            diagnose.main()
            raise AssertionError('Expected legacy ActivityModel B keyword failure did not occur')
        elif args.job == 'isotherm_extract':
            import isotherm_activity_closure as iso
            run = core.solve_case(short_settings())
            try:
                report['actualFieldShape'] = list(run.fields(np.array([0., 10., 20.]), material_x=np.array([0., 1.]))[1].shape)
                iso._extract({}, run, 1., .6)
            finally:
                run.close()
            raise AssertionError('Expected legacy time/space indexing failure did not occur')
        elif args.job == 'isotherm_probe':
            import isotherm_jacobian_probe as probe
            row = probe.probe(1e-7, p=1., intervals=8, horizon_h=.001)
            report['row'] = row
            report['numericalSolveCompleted'] = row['status'] == 'computed'
            report['injectedJacobianActuallyCalled'] = row.get('numJacCalls', 0) > 0
            if not report['injectedJacobianActuallyCalled']:
                report['status'] = 'FAIL_DIAGNOSTIC_INJECTION_NOT_CALLED'
        elif args.job == 'threshold_full_small':
            import threshold_and_scaling_checks as threshold
            report['rows'] = threshold.solver_checks(intervals=20)
        elif args.job == 'q_wrappers':
            import q1_model, q2_model, q3_model, q4_model
            rows = []
            for name, wrapper in [('Q1', q1_model), ('Q23', q2_model), ('Q4', q4_model)]:
                run = wrapper.solve(20)
                try:
                    row = {'question': name, 'diagnostics': run.diagnostics()}
                    assert row['diagnostics']['solver_success']
                    if name != 'Q1':
                        row['completion'] = q3_model.completion(run)
                        assert row['completion']['max_C_at_reported_time'] < .15
                    core.save_run(run, root / 'paper_output/results/sandbox_wrappers' / name)
                    rows.append(row)
                finally:
                    run.close()
            report['rows'] = rows
        elif args.job == 'isotherm_identity_rhs':
            import isotherm_activity_closure as iso
            report['identities'] = iso.identityChecks(.6)
            rows = []
            for q in ('Q1', 'Q23', 'Q4'):
                setting = short_settings(q)
                model = core.RadialModel(setting)
                altered = iso.ActivityModel(setting, p=1., awRef=.6, latentFraction=0.)
                a, b = model.rhs(0., model.initial()), altered.rhs(0., altered.initial())
                delta = float(np.max(np.abs(a-b)))
                assert delta == 0.
                rows.append({'question': q, 'maxRhsDifferenceP1': delta})
            report['rhsChecks'] = rows
        elif args.job == 'series_constant_diagnostic':
            import crossvalidate_series as series
            row = series.sequential_mk(np.ones(40))
            report['constantSeries'] = row
            report['expectedNoTrend'] = True
            if row['firstExceedanceIndex'] is not None:
                report['status'] = 'FAIL_LEGACY_CONSTANT_SERIES_PSEUDOTREND'
        else:
            raise ValueError('Unknown job ' + args.job)
        if report['status'] == 'RUNNING':
            report['status'] = 'PASS_FUNCTION_SCOPE'
    except Exception as error:
        report['status'] = 'FAIL_ACTUAL_EXCEPTION'
        report['error'] = repr(error)
        report['traceback'] = traceback.format_exc()
    report['elapsedSeconds'] = time.perf_counter() - started
    report['python'] = sys.executable
    (out / (args.job + '.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return 0 if report['status'].startswith('PASS') else 1


if __name__ == '__main__':
    raise SystemExit(main())
