from __future__ import annotations

import argparse
import gc
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
import uuid
import warnings

SOURCE = Path(__file__).resolve()
ROOT = SOURCE.parents[3]
LOADED_CODE_SHA256 = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
import production_provenance as provenance

BASELINE = {'rtol': 1e-10, 'atol_temperature': 1e-10, 'atol_moisture': 1e-12,
            'early_max_step_s': 2., 'max_step_s': 120.}
TIGHT = {'rtol': 1e-11, 'atol_temperature': 1e-11, 'atol_moisture': 1e-13,
         'early_max_step_s': 1., 'max_step_s': 60.}


def dependencies():
    names = ['verify_time_accuracy.py', 'production_provenance.py', 'drying_core.py',
        'disk_dense.py', 'analytic_jacobian.py', 'verify_convergence.py', 'validate_bessel.py',
        'q1_model.py', 'q2_model.py', 'q3_model.py', 'q4_model.py']
    paths = [SOURCE.parent / name for name in names]
    paths += [ROOT / 'paper_output/data_cleaned' / name for name in
              ('A_environment_observed.csv', 'A_radius_observed.csv')]
    return [provenance.file_record(path) for path in sorted(paths)]


def unchanged(launch):
    if dependencies() != launch['input_files']:
        raise RuntimeError('Time-check source/input changed after launch')
    if provenance.runtime_record() != launch['runtime']:
        raise RuntimeError('Time-check runtime changed after launch')
    expected = {item['path']: item['sha256'] for item in launch['input_files']}
    for path, loaded in [(SOURCE, LOADED_CODE_SHA256), (provenance.SOURCE, provenance.LOADED_CODE_SHA256)]:
        if loaded != expected[path.relative_to(ROOT).as_posix()]:
            raise RuntimeError('Loaded driver/helper differs from launch snapshot')


def worker(args, directory, launch):
    unchanged(launch)
    import numpy as np
    from dataclasses import asdict, replace
    core = importlib.import_module('drying_core')
    checker = importlib.import_module('verify_convergence')
    wrapper = importlib.import_module({'Q1': 'q1_model', 'Q23': 'q2_model', 'Q4': 'q4_model'}[args.question])
    unchanged(launch)
    case = directory / args.variant
    provenance.exclusive_json(case / 'worker_started.json', {'pid': os.getpid(), 'started_at': provenance.utc_now()})
    run, projection, summary = None, None, None
    started, timer = provenance.utc_now(), time.perf_counter()
    solve_finished = None
    captured_messages = []
    try:
        print(f'SOLVE {args.variant} {args.question} N={args.n} UTC={started}', flush=True)
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter('always')
            if args.variant == 'baseline':

                run = wrapper.solve(args.n)
            else:
                baseline = json.loads((directory / 'baseline/summary.json').read_text(encoding='utf-8'))
                run = core.solve_case(replace(core.Settings(**baseline['settings']), **TIGHT))
            solve_finished = provenance.utc_now()
            expected = core.Settings(question=args.question, intervals=args.n,
                face_scheme='kirchhoff', shrink=args.question == 'Q4', **(BASELINE if args.variant == 'baseline' else TIGHT))
            if asdict(run.model.settings) != asdict(expected):
                raise RuntimeError('Actual variant settings differ from the fixed-physics contract')
            summary = core.save_run(run, case)
            points = np.linspace(0., .02, 21)
            projection = checker.project_run(run, points, args.full_second_comparison or args.question == 'Q1')
            np.savez_compressed(case / 'comparison_projection.npz', times_s=projection['times'],
                radii_m=points, T_K=projection['T'], C=projection['C'])
        captured_messages = [str(item.message) for item in captured]
        if captured_messages:
            raise RuntimeError('Time-check warnings: ' + '; '.join(captured_messages))
        if args.question != 'Q1' and run.event_s is None:
            raise RuntimeError('A full-drying comparison requires an actual threshold event')
        summary['time_check'] = {'variant': args.variant, 'question': args.question,
            'spatial_intervals': args.n, 'started_at': started, 'solve_finished_at': solve_finished,
            'warnings': captured_messages, 'projection_time_count': len(projection['times']),
            'full_second_comparison': bool(args.full_second_comparison or args.question == 'Q1'),
            'projection_radius_count': len(points),
            'process_exit': 'Actual exit is recorded by supervising parent in case_record.json.'}
        provenance.write_json(case / 'summary.json', summary)
    except BaseException as error:
        provenance.write_json(case / 'worker_failure.json', {'status': 'FAIL', 'error': repr(error),
            'traceback': traceback.format_exc(), 'started_at': started, 'failed_at': provenance.utc_now(),
            'wall_seconds': time.perf_counter() - timer, 'warnings': captured_messages})
        raise
    finally:
        if run is not None:
            run.close()
        run, projection = None, None
        gc.collect()
    unchanged(launch)
    finished = provenance.utc_now()
    summary['time_check'].update({'finished_at': finished, 'wall_seconds': time.perf_counter() - timer,
                                 'Run_closed': True})
    provenance.write_json(case / 'summary.json', summary)
    outputs = [provenance.file_record(path) for path in sorted(case.rglob('*'))
               if path.is_file() and path.name not in ('stdout.log', 'worker_success.json', 'process_result.json')]
    provenance.write_json(case / 'worker_success.json', {'variant': args.variant, 'question': args.question,
        'started_at': started, 'finished_at': finished, 'wall_seconds': time.perf_counter() - timer,
        'input_files': launch['input_files'], 'output_artifacts': outputs,
        'summary': summary, 'status': 'computed_zero_solver_warnings',
        'human_review': 'pending', 'visual_studio_gui': 'pending'})
    print(f'VARIANT_COMPLETED {args.variant}; RUN_CLOSED', flush=True)


def compare_saved(directory, question):
    import numpy as np
    from verify_convergence import compare_projections
    projected = []
    points = None
    for variant in ('baseline', 'tight'):
        summary = json.loads((directory / variant / 'summary.json').read_text(encoding='utf-8'))
        with np.load(directory / variant / 'comparison_projection.npz', allow_pickle=False) as archive:
            if points is not None and not np.array_equal(points, archive['radii_m']):
                raise ValueError('Projection radius grids differ')
            points = archive['radii_m'].copy()
            projected.append({'times': archive['times_s'].copy(), 'T': archive['T_K'].copy(),
                'C': archive['C'].copy(), 'N': summary['settings']['intervals'],
                'end_s': summary['diagnostics']['end_s'], 'event_s': summary['diagnostics']['event_s']})
    baseline, tight = projected
    if baseline['N'] != tight['N']:
        raise ValueError('Time-accuracy comparison must use the same spatial resolution')
    count = min(len(baseline['times']), len(tight['times']))
    for name in ('T', 'C'):
        if not np.array_equal(np.isfinite(baseline[name][:count]), np.isfinite(tight[name][:count])):
            raise ValueError('Physical-domain finite masks differ between variants')
    comparison = compare_projections(baseline, tight, points)
    event_difference = None if question == 'Q1' else tight['event_s'] - baseline['event_s']
    comparison.update({'baseline_N': baseline['N'], 'tight_N': tight['N'],
        'baseline_event_s': baseline['event_s'], 'tight_event_s': tight['event_s'],
        'event_difference_s': event_difference,
        'absolute_event_difference_s': None if event_difference is None else abs(event_difference),
        'difference_direction': 'tight minus baseline for the event; absolute differences for fields',
        'baseline_projection_time_count': len(baseline['times']), 'tight_projection_time_count': len(tight['times']),
        'common_last_time_s': float(baseline['times'][count - 1]),
        'scope': 'Numerical sensitivity to simultaneous tighter tolerances and smaller maximum steps at fixed N.',
        'not_a_rigorous_error_bound': True, 'no_experimental_accuracy_claim': True})
    return comparison


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--question', choices=['Q1', 'Q23', 'Q4'], required=True)
    parser.add_argument('--n', type=int, required=True)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--full-second-comparison', action='store_true')
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--variant', choices=['baseline', 'tight'], help=argparse.SUPPRESS)
    parser.add_argument('--launch-token', help=argparse.SUPPRESS)
    args = parser.parse_args()
    os.environ['OPENBLAS_NUM_THREADS'] = '1'
    os.environ['OMP_NUM_THREADS'] = '1'
    if Path.cwd().resolve() != ROOT:
        raise RuntimeError('Use the competition workspace as cwd')
    if args.n < 2 or not args.tag or any(ch not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for ch in args.tag):
        raise ValueError('Use N>=2 and a simple, new tag')
    directory = ROOT / 'paper_output/results/time_accuracy' / args.tag
    config = {'question': args.question, 'n': args.n, 'full_second_comparison': args.full_second_comparison}
    if args.worker:
        launch = json.loads((directory / 'launch.json').read_text(encoding='utf-8'))
        if not args.variant or args.launch_token != launch['token'] or config != launch['configuration']:
            raise RuntimeError('Worker does not match the supervising launch')
        worker(args, directory, launch)
        return 0
    if args.variant or args.launch_token:
        raise ValueError('Variant/token are reserved for supervised workers')
    directory.parent.mkdir(parents=True, exist_ok=True)
    directory.mkdir(exist_ok=False)
    started, timer = provenance.utc_now(), time.perf_counter()
    launch = {'created_at': started, 'parent_pid': os.getpid(), 'token': uuid.uuid4().hex,
        'configuration': config, 'input_files': dependencies(), 'runtime': provenance.runtime_record()}
    provenance.exclusive_json(directory / 'launch.json', launch)
    cases = []
    try:
        unchanged(launch)
        for variant in ('baseline', 'tight'):
            case = directory / variant
            case.mkdir(exist_ok=False)
            command = [sys.executable, '-B', str(SOURCE), '--question', args.question, '--n', str(args.n),
                '--tag', args.tag, '--worker', '--variant', variant, '--launch-token', launch['token']]
            if args.full_second_comparison:
                command.append('--full-second-comparison')
            process = provenance.measured_process(command, ROOT, case / 'stdout.log')
            if process['returncode'] != 0:
                raise RuntimeError(variant + ' failed with actual returncode ' + str(process['returncode']))
            unchanged(launch)
            success = json.loads((case / 'worker_success.json').read_text(encoding='utf-8'))
            if success['input_files'] != launch['input_files']:
                raise RuntimeError('Variant evidence belongs to another launch')
            provenance.assert_records(success['output_artifacts'])
            record = {'variant': variant, 'process': process, 'summary': success['summary'],
                'summary_file': provenance.file_record(case / 'summary.json'),
                'output_artifacts': success['output_artifacts'] + [provenance.file_record(case / name)
                    for name in ('worker_success.json', 'stdout.log', 'process_result.json')],
                'status': 'computed_actual_process_exit_zero'}
            provenance.write_json(case / 'case_record.json', record)
            cases.append(record)
        comparison = compare_saved(directory, args.question)
        unchanged(launch)
        for case in cases:
            provenance.assert_records(case['output_artifacts'])
        report = {'created_at': started, 'finished_at': provenance.utc_now(),
            'wall_seconds': time.perf_counter() - timer, 'question': args.question, 'N': args.n,
            'status': 'computed_zero_solver_warnings', 'configuration': config,
            'baseline_controls': BASELINE, 'tight_controls': TIGHT, 'runs': cases,
            'comparison': comparison, 'driver_code': provenance.file_record(SOURCE),
            'input_files': launch['input_files'], 'runtime': launch['runtime'],
            'scope': 'Fixed-N temporal sensitivity only; small grids are functional checks, not final accuracy evidence.',
            'human_review': 'pending', 'visual_studio_gui': 'pending'}
        provenance.write_json(directory / 'time_accuracy_report.json', report)
        print(json.dumps({'status': report['status'], 'question': args.question, 'N': args.n,
                          'comparison': comparison}, ensure_ascii=False), flush=True)
        return 0
    except BaseException as error:
        observed = {}
        for variant in ('baseline', 'tight'):
            path = directory / variant / 'process_result.json'
            if path.exists():
                observed[variant] = json.loads(path.read_text(encoding='utf-8'))
        provenance.write_json(directory / 'failure.json', {'status': 'FAIL', 'error': repr(error),
            'traceback': traceback.format_exc(), 'started_at': started, 'failed_at': provenance.utc_now(),
            'wall_seconds': time.perf_counter() - timer, 'observed_processes': observed})
        raise


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
