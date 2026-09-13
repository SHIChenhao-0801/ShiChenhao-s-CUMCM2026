from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

out=Path('C:/Evidence/wrapper_stable')
out.mkdir(exist_ok=False)
sys.stdout=(out/'observer.log').open('w',encoding='utf-8')
sys.stderr=sys.stdout
package=Path('C:/Work/wrapper_stable')
shutil.copytree('C:/Candidate/03_程序代码',package,
    ignore=shutil.ignore_patterns('.vs','results','tmp','__pycache__','UpgradeLog.htm'))
records={p.relative_to(package).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
         for p in package.rglob('*') if p.is_file()}
environment=os.environ.copy()
environment.update(PYTHONUTF8='1',PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
command=['C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass',
         '-File',str(package/'runLogged.ps1'),'-Python','C:/Runtime/python.exe','-Profile','quick','-RunId','vm_wrapper_stable']
record={'argv':command,'cwd':'C:/Work','startedUtc':datetime.now(timezone.utc).isoformat(),
        'status':'RUNNING','inputHashes':records,'reason':'Retest original wrapper with dedicated hidden console and observer retained until process exit.'}
(out/'process.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
startup=subprocess.STARTUPINFO()
startup.dwFlags=subprocess.STARTF_USESHOWWINDOW
startup.wShowWindow=0
started=time.perf_counter()
with (out/'stdout.log').open('w',encoding='utf-8') as log:
    process=subprocess.Popen(command,cwd='C:/Work',env=environment,stdout=log,stderr=subprocess.STDOUT,
                             creationflags=subprocess.CREATE_NEW_CONSOLE,startupinfo=startup)
    record['pid']=process.pid
    (out/'process.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    code=process.wait(timeout=2400)
record.update(actualExitCode=code,status='OBSERVED_EXIT',elapsedSeconds=time.perf_counter()-started,
              finishedUtc=datetime.now(timezone.utc).isoformat(),
              inputHashesUnchanged=all(hashlib.sha256((package/rel).read_bytes()).hexdigest()==digest for rel,digest in records.items()))
(out/'process.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copytree(package/'results',out/'results')
run=json.loads((package/'results/vm_wrapper_stable/runResult.json').read_text(encoding='utf-8'))
record.update(programStatus=run['status'],profile=run['profile'],questions=list(run.get('summaries',{})),
              accepted=code==0 and run['status']=='PASS' and record['inputHashesUnchanged'])
(out/'result.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'actualExitCode':code,'programStatus':run['status'],'accepted':record['accepted']}),flush=True)
