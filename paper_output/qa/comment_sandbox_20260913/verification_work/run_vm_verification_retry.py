from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


supplied=Path('C:/Verification/path_adapted')
prior=Path('C:/Work/05_path_adapted')
fresh=Path('C:/Work/05_clean_retry')
evidence=Path('C:/Evidence/verification_clean_retry')
python=Path('C:/Runtime/python.exe')
assert Path('C:/Work').is_dir() and supplied.is_dir()
assert not Path('D:/Document/数学建模/2026CUMCM').exists()
fresh.mkdir(exist_ok=False)
evidence.mkdir(exist_ok=False)
files=list((supplied/'paper_output/code').rglob('*.py'))
files += list((supplied/'paper_output/data_cleaned').glob('*.csv'))
files += list((supplied/'problem_files/CUMCM2026Problems/A题/附件/附件3').glob('*.xlsx'))
files.append(supplied/'paper_output/results/production/final_v6a/Q23/sampled_solution.npz')
copied=[]
for path in files:
    relative=path.relative_to(supplied)
    destination=fresh/relative
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(path,destination)
    copied.append({'path':relative.as_posix(),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()})
shutil.copyfile('C:/Verification/verification_jobs.py',fresh/'verification_jobs.py')
environment=os.environ.copy()
environment.update(PYTHONUTF8='1',PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',
                   OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MPLCONFIGDIR=str(fresh/'tmp/cache/matplotlib'))
jobs=['convergence','time_accuracy','dense_storage','export_selfcheck','axisymmetric','production_missing_inputs']
command=[str(python),'-I','-X','utf8','-B','C:/Verification/execute_matrix.py',
         '--python',str(python),'--root',str(fresh),'--workers','2','--label','windows_clean_retry','--jobs',*jobs]
record={'startedAtUtc':datetime.now(timezone.utc).isoformat(),'argv':command,
        'freshRoot':str(fresh),'inputs':copied,'networkDisabledByWSB':True,'jobs':jobs,'status':'RUNNING'}
(evidence/'retry_process.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
started=time.perf_counter()
with (evidence/'retry.log').open('w',encoding='utf-8') as log:
    process=subprocess.Popen(command,cwd=fresh,env=environment,stdout=log,stderr=subprocess.STDOUT)
    record['pid']=process.pid
    code=process.wait(timeout=900)
record.update(returncode=code,finishedAtUtc=datetime.now(timezone.utc).isoformat(),elapsedSeconds=time.perf_counter()-started,status='COMPLETED_QUEUE')
record['copiedSourcesAndInputsUnchanged']=all(hashlib.sha256((fresh/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in copied)
(evidence/'retry_process.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copytree(fresh/'matrix_windows_clean_retry',evidence/'matrix')
shutil.copytree(fresh/'paper_output/results',evidence/'results')
if (fresh/'execution_records').exists():
    shutil.copytree(fresh/'execution_records',evidence/'execution_records')
first=evidence/'first_attempt_generated'
first.mkdir()
for name in ('execution_records','paper_output/results'):
    path=prior/name
    if path.exists():
        shutil.copytree(path,first/name)
print(json.dumps({'status':record['status'],'queueActualExit':code,'copiedSourcesAndInputsUnchanged':record['copiedSourcesAndInputsUnchanged']},ensure_ascii=False),flush=True)
