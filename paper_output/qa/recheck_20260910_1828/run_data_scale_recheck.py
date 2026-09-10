"""Record a real independent audit subprocess exit, with no solver execution."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

out = Path(__file__).resolve().parent
root = out.parents[2]
assert root.name == '2026CUMCM'
helper = out / 'data_scale_recheck_helper.py'
tag = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
command = [sys.executable, '-B', str(helper)]
env = dict(os.environ, PYTHONUTF8='1', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
started = datetime.now(timezone.utc).isoformat()
tic = time.perf_counter()
with (out / f'data_scale_{tag}.stdout.log').open('w',encoding='utf-8') as stdout, (out / f'data_scale_{tag}.stderr.log').open('w',encoding='utf-8') as stderr:
    child = subprocess.Popen(command, cwd=root, env=env, stdout=stdout, stderr=stderr)
    returncode = child.wait()
record = {'started_utc':started,'ended_utc':datetime.now(timezone.utc).isoformat(),
          'wall_s':time.perf_counter()-tic,'command':command,'cwd':str(root),'pid':child.pid,
          'actual_child_returncode':returncode,'observed_by':'subprocess.Popen.wait',
          'helper_sha256':hashlib.sha256(helper.read_bytes()).hexdigest(),
          'stdout':f'data_scale_{tag}.stdout.log','stderr':f'data_scale_{tag}.stderr.log',
          'GUI_observed':False,'PDE_run':False}
(out / f'data_scale_process_{tag}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,ensure_ascii=True))
raise SystemExit(returncode)
