from pathlib import Path
from datetime import datetime, timezone
import ctypes
from ctypes import wintypes
import hashlib
import json
import shutil
import subprocess
import sys
import time

out = Path('C:/Evidence/extra_entries')
sys.stdout = (out/'wrapper_watcher.log').open('a',encoding='utf-8')
sys.stderr = sys.stdout
ps = 'C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe'
query = "Get-CimInstance Win32_Process -Filter \"Name='powershell.exe'\" | Where-Object { $_.CommandLine -match '-RunId vm_wrapper_quick' } | Select-Object ProcessId,CommandLine | ConvertTo-Json"
probe = subprocess.run([ps,'-NoProfile','-Command',query],capture_output=True,text=True,check=True)
print(probe.stdout,flush=True)
target = json.loads(probe.stdout)
if isinstance(target,list):
    targets = [p for p in target if p['CommandLine'].endswith('-RunId vm_wrapper_quick')]
    assert len(targets)==1, targets
    target = targets[0]
assert isinstance(target,dict), target
kernel = ctypes.WinDLL('kernel32',use_last_error=True)
kernel.OpenProcess.argtypes = [wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
kernel.OpenProcess.restype = wintypes.HANDLE
kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE,wintypes.DWORD]
kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
kernel.CloseHandle.argtypes = [wintypes.HANDLE]
handle = kernel.OpenProcess(0x100000|0x1000,False,target['ProcessId'])
assert handle, ctypes.get_last_error()
record = {'process':target,'observerStartedUtc':datetime.now(timezone.utc).isoformat(),
          'status':'WAITING_EXISTING_WRAPPER','reason':'Retain the process exit handle independently of the initial 600-second observer budget.'}
(out/'wrapper_external_exit.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
try:
    assert kernel.WaitForSingleObject(handle,1200000)==0, 'External observation budget exceeded'
    exit_code = wintypes.DWORD()
    assert kernel.GetExitCodeProcess(handle,ctypes.byref(exit_code))
    record.update(actualExitCode=exit_code.value,status='OBSERVED_PROCESS_EXIT',finishedUtc=datetime.now(timezone.utc).isoformat())
finally:
    kernel.CloseHandle(handle)
(out/'wrapper_external_exit.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
package = Path('C:/Work/extra_entries/03_wrapper')
shutil.copytree(package/'results',out/'wrapper_results_external')
report = {'matlabExecutableFound':shutil.which('matlab'),'matlabStatus':'NOT_EXECUTED_RUNTIME_UNAVAILABLE',
          'nodeSourceSha256':hashlib.sha256(Path('C:/Work/extra_entries/matlab/compareMatlab.mjs').read_bytes()).hexdigest(),
          'powershellSourceSha256':hashlib.sha256((package/'runLogged.ps1').read_bytes()).hexdigest(),
          'earlyRecords':json.loads((out/'processes.json').read_text(encoding='utf-8')),'wrapperExternalExit':record,
          'wrapperProgramResult':json.loads((package/'results/vm_wrapper_quick/runResult.json').read_text(encoding='utf-8'))}
(out/'extra_result_external.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'wrapperActualExit':exit_code.value,'programStatus':report['wrapperProgramResult']['status']}),flush=True)
