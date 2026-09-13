"""External process observer for the exact portable package sources and inputs."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import time
import zipfile

QA = Path(__file__).resolve().parent
ROOT = QA.parents[3]
PACKAGE = ROOT/'支撑材料/03_程序代码'
PYTHON = ROOT/'tmp/cache/portability_20260912/dependency_probe/venv/Scripts/python.exe'
ARCHIVE = QA/'code_candidate.zip'
EXTRACTED = QA/'isolated/03_程序代码'

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def now():
    return datetime.now(timezone.utc).isoformat()

if EXTRACTED.exists():
    raise FileExistsError('Refuse to reuse an existing isolated extraction')
files = sorted(p for p in PACKAGE.rglob('*') if p.is_file())
with zipfile.ZipFile(ARCHIVE, 'x', zipfile.ZIP_DEFLATED) as z:
    for p in files:
        z.write(p, p.relative_to(PACKAGE).as_posix())
with zipfile.ZipFile(ARCHIVE) as z:
    assert z.testzip() is None
    z.extractall(EXTRACTED)
records = [{'path':p.relative_to(PACKAGE).as_posix(), 'sha256':sha(p)} for p in files]
for item in records:
    assert sha(EXTRACTED/item['path']) == item['sha256']
environment = dict(os.environ)
for key in ['PYTHONPATH', 'PYTHONHOME']:
    environment.pop(key, None)
environment.update(PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
report = {'startedAtUtc':now(), 'status':'RUNNING', 'archiveSha256':sha(ARCHIVE),
          'sourceArchive':'code_candidate.zip', 'isolatedDirectory':'isolated/03_程序代码',
          'files':records, 'cases':[], 'guiNewVersion':'NOT_PERFORMED',
          'humanReview':'PENDING_USER_REVIEW', 'physicalSecondDevice':'NOT_TESTED'}
write(QA/'execution.json', report)
cases = [
    ('environment', ['-c', "import sys,site,json,importlib.metadata as m; print(json.dumps({'version':sys.version,'prefix':sys.prefix,'basePrefix':sys.base_prefix,'userSiteEnabled':site.ENABLE_USER_SITE,'libraries':{n:m.version(n) for n in ['numpy','scipy','openpyxl']}},ensure_ascii=False))"]),
    ('pip_check', ['-m', 'pip', 'check']),
    ('preflight', [str(EXTRACTED/'runDelivery.py'), '--preflight-only', '--run-id', 'preflight_isolated']),
    ('quick', [str(EXTRACTED/'runDelivery.py'), '--profile', 'quick', '--run-id', 'quick_isolated']),
    ('final', [str(EXTRACTED/'runDelivery.py'), '--profile', 'final', '--run-id', 'final_isolated'])]
try:
    for name, args in cases:
        command = [str(PYTHON), '-X', 'utf8', '-B'] + args
        started, timestamp = time.perf_counter(), now()
        print(timestamp+' START '+name, flush=True)
        with (QA/(name+'.stdout.log')).open('w', encoding='utf-8') as stdout, (QA/(name+'.stderr.log')).open('w', encoding='utf-8') as stderr:
            completed = subprocess.run(command, cwd=EXTRACTED, env=environment, stdout=stdout,
                                       stderr=stderr, timeout=2400, check=False)
        item = {'name':name, 'startedAtUtc':timestamp, 'finishedAtUtc':now(),
                'actualExitCode':completed.returncode, 'elapsedSeconds':time.perf_counter()-started,
                'command':command, 'cwd':str(EXTRACTED), 'stdout':name+'.stdout.log', 'stderr':name+'.stderr.log'}
        report['cases'].append(item)
        write(QA/'execution.json', report)
        print(json.dumps(item, ensure_ascii=False), flush=True)
        if completed.returncode != 0:
            raise RuntimeError('Isolated process failed: '+name)
    for item in records:
        assert sha(EXTRACTED/item['path']) == item['sha256']
        assert sha(PACKAGE/item['path']) == item['sha256']
    report['status'] = 'PASS'
except BaseException as error:
    report.update(status='FAIL', error=repr(error))
    raise
finally:
    report['finishedAtUtc'] = now()
    write(QA/'execution.json', report)
