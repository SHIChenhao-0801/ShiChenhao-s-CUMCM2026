from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--python', required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--jobs', nargs='+')
    parser.add_argument('--workers', type=int, default=1)
    parser.add_argument('--label', default='run1')
    args = parser.parse_args()
    root = args.root.resolve()
    m = 'paper_output/code/modeling/'
    v = 'paper_output/code/verification/'
    commands = {
        'bessel': [m+'validate_bessel.py'],
        'jacobian': [m+'analytic_jacobian.py', '--self-test'],
        'provenance': [m+'production_provenance.py', '--selfcheck'],
        'scaling': [v+'threshold_and_scaling_checks.py'],
        'analytic_metric': [v+'analytic_metric_check.py'],
        'series': [v+'crossvalidate_series.py'],
        'energy_diagnose': [v+'energy_balance_diagnose.py'],
        'convergence': [m+'verify_convergence.py', '--question', 'Q1', '--grids', '20', '40', '--tag', 'sandbox'],
        'time_accuracy': [m+'verify_time_accuracy.py', '--question', 'Q1', '--n', '20', '--tag', 'sandbox'],
        'dense_storage': [m+'verify_dense_storage.py'],
        'method_quick': [v+'method_comparison.py', '--quick'],
        'compare_analytic': [m+'compare_analytic.py'],
        'export_selfcheck': [m+'export_outputs.py', '--selfcheck'],
        'plot_selfcheck': [m+'publication_plots.py', '--selfcheck'],
        'axisymmetric': [m+'axisymmetric_check.py', '--nr', '6', '--nz', '4', '--end-faces', 'off', '--budget-s', '120', '--tag', '_sandbox'],
        'production_missing_inputs': [m+'run_modeling.py', '--version', 'sandbox_missing_inputs', '--n1', '20', '--n23', '20', '--n4', '20', '--review'],
    }
    functions = ['crossvalidate_solver_pair', 'latent_single', 'energy_q1', 'sensitivity_control',
                 'isotherm_old_interface', 'isotherm_extract', 'isotherm_probe', 'threshold_full_small',
                 'q_wrappers', 'isotherm_identity_rhs', 'series_constant_diagnostic']
    for job in functions:
        commands[job] = ['verification_jobs.py', '--root', str(root), '--job', job]
    selected = args.jobs or list(commands)
    directory = root / ('matrix_' + args.label)
    directory.mkdir(exist_ok=False)
    environment = os.environ.copy()
    environment.update(PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
                       MPLCONFIGDIR=str(root / 'tmp/cache/matplotlib'))
    source_records = []
    for p in sorted(root.rglob('*.py')):
        if '/tmp/' not in p.as_posix():
            source_records.append({'path': p.relative_to(root).as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
    results = []

    def execute(name):
        command = [args.python, '-B', *commands[name]]
        started = time.perf_counter()
        record = {'job': name, 'argv': command, 'cwd': str(root), 'startedAtUtc': datetime.now(timezone.utc).isoformat()}
        with (directory / (name + '.log')).open('w', encoding='utf-8') as log:
            process = subprocess.Popen(command, cwd=root, env=environment, stdout=log, stderr=subprocess.STDOUT)
            record['pid'] = process.pid
            try:
                record['returncode'] = process.wait(timeout=600)
            except subprocess.TimeoutExpired:
                process.kill()
                record['returncode'] = process.wait()
                record['timeoutSeconds'] = 600
        record['elapsedSeconds'] = time.perf_counter() - started
        record['finishedAtUtc'] = datetime.now(timezone.utc).isoformat()
        (directory / (name + '.process.json')).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(record, ensure_ascii=False), flush=True)
        return record

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(execute, name): name for name in selected}
        for future in as_completed(futures):
            results.append(future.result())
            report = {'sources': source_records, 'results': results, 'remaining': len(selected) - len(results)}
            (directory / 'process_matrix.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'finished': len(results), 'zeroExit': sum(r['returncode'] == 0 for r in results), 'directory': str(directory)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
