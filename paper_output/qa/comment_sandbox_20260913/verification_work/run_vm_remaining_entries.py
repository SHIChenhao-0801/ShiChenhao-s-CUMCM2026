from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


source = Path('C:/Verification/path_adapted')
work = Path('C:/Work/05_remaining_entry')
output = Path('C:/Evidence/verification_remaining_entries')
assert source.is_dir() and not Path('D:/Document/数学建模/2026CUMCM').exists()
work.mkdir(exist_ok=False)
output.mkdir(exist_ok=False)
inputs = []
for path in list((source / 'paper_output/code').rglob('*.py')) + list((source / 'paper_output/data_cleaned').glob('*.csv')):
    relative = path.relative_to(source)
    target = work / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
    inputs.append({'path': relative.as_posix(), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
assert len(inputs) == 33
environment = os.environ.copy()
environment.update(PYTHONUTF8='1', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
commands = {
    'run_experiments': ['C:/Runtime/python.exe', '-B', 'paper_output/code/modeling/run_experiments.py', '--batch', 'baseline', '--n', '20', '--tag', '_vm_remaining', '--face-scheme', 'kirchhoff'],
    'energy_diagnose2': ['C:/Runtime/python.exe', '-B', 'paper_output/code/verification/energy_balance_diagnose2.py'],
}
record = {'status': 'RUNNING', 'startedAtUtc': datetime.now(timezone.utc).isoformat(), 'root': str(work), 'inputs': inputs, 'commands': commands, 'results': []}
(output / 'processes.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')


def execute(job, command):
    started = time.perf_counter()
    item = {'job': job, 'argv': command, 'cwd': str(work), 'startedAtUtc': datetime.now(timezone.utc).isoformat()}
    with (output / (job + '.log')).open('w', encoding='utf-8') as stream:
        process = subprocess.Popen(command, cwd=work, env=environment, stdout=stream, stderr=subprocess.STDOUT)
        item['pid'] = process.pid
        item['returncode'] = process.wait(timeout=600)
    return {**item, 'finishedAtUtc': datetime.now(timezone.utc).isoformat(), 'elapsedSeconds': time.perf_counter() - started}


with ThreadPoolExecutor(max_workers=2) as pool:
    futures = [pool.submit(execute, job, command) for job, command in commands.items()]
    for future in as_completed(futures):
        record['results'].append(future.result())
        (output / 'processes.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
record.update(status='COMPLETED', finishedAtUtc=datetime.now(timezone.utc).isoformat(), sourcesAndInputsUnchanged=all(hashlib.sha256((work / item['path']).read_bytes()).hexdigest() == item['sha256'] for item in inputs))
(output / 'processes.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
shutil.copytree(work / 'paper_output/results', output / 'results')
print(json.dumps(record, ensure_ascii=False), flush=True)
