"""Focused isolated tests of CSV/reference-module I/O; no full three-case rerun."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

QA = Path(__file__).resolve().parent
ROOT = QA.parents[3]
PACKAGE = ROOT/'支撑材料/03_程序代码'
ISOLATED = QA/'isolated_current_03'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, content):
    path.write_text(json.dumps(content, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

if len(sys.argv) > 1 and sys.argv[1] == '--worker':
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ISOLATED))
    import runDelivery
    report = {'preflight':runDelivery.preflight(), 'cases':{}}
    for profile, n in [('quick',40), ('final',3200)]:
        output = ISOLATED/'results'/('cleanup_q1_'+profile)
        output.mkdir(parents=True, exist_ok=False)
        summary, checks = runDelivery.runQuestion('Q1', n, output, profile)
        report['cases'][profile] = {'summary':summary, 'checks':checks}
    report.update(status='PASS', scope='Q1 N40/full-grid input, export, readback and frozen-reference tests only; no Q23/Q4 rerun')
    write(QA/'targeted_result.json', report)
    print('TARGETED_IO_AND_Q1_EXPORT_CHECKS_PASS', flush=True)
    raise SystemExit(0)

if ISOLATED.exists():
    raise FileExistsError('Refuse to overwrite an existing focused-test directory')
shutil.copytree(PACKAGE, ISOLATED)
files = [{'path':p.relative_to(PACKAGE).as_posix(), 'sha256':sha(p)}
         for p in sorted(PACKAGE.rglob('*')) if p.is_file()]
environment = dict(os.environ)
for key in ['PYTHONPATH','PYTHONHOME']: environment.pop(key, None)
environment.update(PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
started, timer = datetime.now(timezone.utc).isoformat(), time.perf_counter()
command = [sys.executable, '-X','utf8','-B',str(Path(__file__).resolve()),'--worker']
with (QA/'focused.stdout.log').open('w', encoding='utf-8') as stdout, (QA/'focused.stderr.log').open('w', encoding='utf-8') as stderr:
    result = subprocess.run(command, cwd=QA, env=environment, stdout=stdout, stderr=stderr,
                            timeout=240, check=False)
observed = {'startedAtUtc':started, 'finishedAtUtc':datetime.now(timezone.utc).isoformat(),
            'actualExitCode':result.returncode, 'elapsedSeconds':time.perf_counter()-timer,
            'command':command, 'cwd':str(QA), 'sourceFiles':files,
            'status':'PASS' if result.returncode == 0 else 'FAIL'}
write(QA/'process_result.json', observed)
if result.returncode != 0:
    raise RuntimeError('Focused test failed; see focused.stderr.log')
for item in files:
    assert sha(ISOLATED/item['path']) == item['sha256']
    assert sha(PACKAGE/item['path']) == item['sha256']
print(json.dumps({'status':'PASS', 'actualExitCode':result.returncode,
                  'elapsedSeconds':observed['elapsedSeconds']}, ensure_ascii=False))
