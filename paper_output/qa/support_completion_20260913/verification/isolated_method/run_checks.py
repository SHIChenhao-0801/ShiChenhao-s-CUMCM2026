from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


SOURCE = Path(__file__).resolve().parent
SCRIPTS = {
    'grid': 'paper_output/code/modeling/verify_convergence.py',
    'time': 'paper_output/code/modeling/verify_time_accuracy.py',
    'method': 'paper_output/code/verification/method_comparison.py',
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description='Run a selected check in a new independent experiment directory.')
    parser.add_argument('--check', choices=sorted(SCRIPTS), required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--question', choices=['Q1', 'Q23', 'Q4'])
    parser.add_argument('--grids', type=int, nargs='+')
    parser.add_argument('--n', type=int)
    parser.add_argument('--full-second-comparison', action='store_true')
    parser.add_argument('--frozen-d', type=float)
    parser.add_argument('--quick', action='store_true')
    args = parser.parse_args()
    destination = args.output_dir.resolve()
    if destination == SOURCE.parent or destination.is_relative_to(SOURCE.parent):
        parser.error('--output-dir must be outside the supplied verification directory')
    if destination.exists():
        parser.error('--output-dir must be a new directory; existing files are never overwritten')
    if args.check == 'grid':
        if args.question is None or not args.grids or len(args.grids) < 2:
            parser.error('grid requires --question and at least two --grids values')
        if any(n < 2 for n in args.grids) or args.grids != sorted(set(args.grids)):
            parser.error('--grids must contain strictly increasing integers >= 2')
        if args.n is not None or args.quick:
            parser.error('--n and --quick are not grid options')
    elif args.check == 'time':
        if args.question is None or args.n is None or args.n < 2:
            parser.error('time requires --question and --n >= 2')
        if args.grids is not None or args.quick or args.frozen_d is not None:
            parser.error('--grids, --quick and --frozen-d are not time options')
    elif any((args.question is not None, args.grids is not None, args.n is not None,
              args.full_second_comparison, args.frozen_d is not None)):
        parser.error('method accepts only --quick in addition to --output-dir')
    runtime = {'python': sys.version, 'executable': sys.executable,
               'packages': {name: importlib.metadata.version(name)
                            for name in ('numpy', 'scipy', 'openpyxl', 'matplotlib')}}
    files = sorted((SOURCE / 'paper_output/code').rglob('*.py'))
    files += [SOURCE / 'paper_output/data_cleaned' / name for name in
              ('A_environment_observed.csv', 'A_radius_observed.csv')]
    files += [SOURCE / 'requirements.txt', SOURCE / 'run_checks.py']
    inventory = [{'path': path.relative_to(SOURCE).as_posix(), 'sha256': sha256(path),
                  'bytes': path.stat().st_size} for path in files]
    destination.mkdir(parents=True, exist_ok=False)
    for item in inventory:
        target = destination / item['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE / item['path'], target)
        if sha256(target) != item['sha256']:
            raise RuntimeError('Copied source/input differs: ' + item['path'])
    command = [sys.executable, '-X', 'utf8', '-B', str(destination / SCRIPTS[args.check])]
    if args.check in ('grid', 'time'):
        command += ['--question', args.question, '--tag', 'reproduction']
        if args.full_second_comparison:
            command.append('--full-second-comparison')
    if args.check == 'grid':
        command += ['--grids', *map(str, args.grids)]
        if args.frozen_d is not None:
            command += ['--frozen-d', str(args.frozen_d)]
    elif args.check == 'time':
        command += ['--n', str(args.n)]
    elif args.quick:
        command.append('--quick')
    environment = os.environ.copy()
    environment.update({'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONUTF8': '1',
                        'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1',
                        'PYTHONPYCACHEPREFIX': str(destination / 'tmp/cache/python'),
                        'MPLCONFIGDIR': str(destination / 'tmp/cache/matplotlib')})
    started = time.time()
    record = {'check': args.check, 'argv': command, 'cwd': str(destination),
              'runtime': runtime, 'input_files': inventory, 'started_unix': started,
              'scope': 'Actual process exit is separate from numerical acceptance.',
              'human_review': 'pending', 'visual_studio_gui': 'pending'}
    (destination / 'run_launch.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    with (destination / 'stdout.log').open('x', encoding='utf-8') as log:
        result = subprocess.run(command, cwd=destination, env=environment,
                                stdout=log, stderr=subprocess.STDOUT, check=False)
    record.update({'returncode': result.returncode, 'wall_seconds': time.time() - started})
    record['source_input_unchanged'] = all(
        sha256(SOURCE / item['path']) == item['sha256'] and
        sha256(destination / item['path']) == item['sha256'] for item in inventory)
    (destination / 'run_result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'check': args.check, 'returncode': result.returncode,
                      'source_input_unchanged': record['source_input_unchanged'],
                      'wall_seconds': record['wall_seconds'], 'output_dir': str(destination)},
                     ensure_ascii=False))
    return result.returncode if record['source_input_unchanged'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
