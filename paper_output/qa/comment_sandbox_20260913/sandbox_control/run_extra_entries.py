from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import shutil
import subprocess
import time

out = Path('C:/Evidence/extra_entries')
out.mkdir(exist_ok=False)
work = Path('C:/Work/extra_entries')
work.mkdir(exist_ok=False)
assert not Path('D:/Document/数学建模/2026CUMCM').exists()
records = []

def execute(name, argv, cwd):
    start = time.perf_counter()
    entry = {'name': name, 'argv': argv, 'cwd': str(cwd), 'startUtc': datetime.now(timezone.utc).isoformat()}
    env = os.environ.copy()
    env.update(PYTHONUTF8='1', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
    with (out / (name + '.log')).open('w', encoding='utf-8') as log:
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
        entry['pid'] = proc.pid
        entry['returncode'] = proc.wait(timeout=600)
    entry.update(elapsedSeconds=time.perf_counter()-start, endUtc=datetime.now(timezone.utc).isoformat())
    records.append(entry)
    (out / 'processes.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    return entry

matlab_candidate = Path('C:/Candidate/05_数值检验与实验/MATLAB对照证据')
node_file = work / 'matlab' / 'compareMatlab.mjs'
node_file.parent.mkdir()
shutil.copyfile(matlab_candidate / node_file.name, node_file)
execute('node_version', ['C:/Runtime/node.exe', '--version'], work)
execute('node_original_worker', ['C:/Runtime/node.exe', str(node_file), '--worker'], work)
package = work / '03_wrapper'
shutil.copytree('C:/Candidate/03_程序代码', package,
                ignore=shutil.ignore_patterns('.vs', 'results', 'tmp', '__pycache__', 'UpgradeLog.htm'))
ps = 'C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'
execute('powershell_version', [ps, '-NoProfile', '-Command', '$PSVersionTable.PSVersion.ToString()'], work)
execute('powershell_quick_wrapper', [ps, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(package/'runLogged.ps1'),
                                    '-Python', 'C:/Runtime/python.exe', '-Profile', 'quick', '-RunId', 'vm_wrapper_quick'], work)
shutil.copytree(package / 'results', out / 'wrapper_results')
report = {'matlabExecutableFound': shutil.which('matlab'), 'matlabStatus': 'NOT_EXECUTED_RUNTIME_UNAVAILABLE',
          'nodeSourceSha256': hashlib.sha256(node_file.read_bytes()).hexdigest(),
          'powershellSourceSha256': hashlib.sha256((package/'runLogged.ps1').read_bytes()).hexdigest(), 'records': records}
(out / 'extra_result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False), flush=True)
