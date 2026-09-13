from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import traceback

EVIDENCE = Path("C:/Evidence")
WORK = Path("C:/Work")
RUNTIME = Path("C:/Runtime/python.exe")
CONTROL = Path("C:/Control")
ORIGINAL = Path("D:/Document/数学建模/2026CUMCM")

def save(name, data):
    (EVIDENCE/name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def execute(name, command, cwd, timeout=2400):
    start = time.perf_counter()
    rec = {"name":name,"command":list(map(str,command)),"cwd":str(cwd),
           "startUtc":datetime.now(timezone.utc).isoformat(),"status":"RUNNING"}
    save(name+".process.json", rec)
    with (EVIDENCE/(name+".log")).open("w",encoding="utf-8") as log:
        process = subprocess.Popen(command, cwd=cwd, env=ENV, stdout=log, stderr=subprocess.STDOUT)
        rec["pid"] = process.pid
        save(name+".process.json", rec)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            code = process.wait()
            rec["timedOut"] = True
    rec.update(returncode=code,elapsedSeconds=time.perf_counter()-start,
               endUtc=datetime.now(timezone.utc).isoformat(),status="EXIT_ZERO" if code==0 else "EXIT_NONZERO")
    save(name+".process.json", rec)
    return rec

def core():
    package = WORK/"03"
    shutil.copytree("C:/Candidate/03_程序代码", package,
                    ignore=shutil.ignore_patterns(".vs","results","tmp","__pycache__","UpgradeLog.htm"))
    records = {p.relative_to(package).as_posix():digest(p) for p in package.rglob("*") if p.is_file()}
    save("core_input_hashes.json", records)
    prefix = [str(RUNTIME),"-I","-X","utf8","-B",str(CONTROL/"entry_runner.py"),str(package/"runDelivery.py")]
    pre = execute("core_preflight", prefix+["--preflight-only","--run-id","vm_preflight"], WORK)
    if pre["returncode"]!=0:
        return pre
    result = execute("core_final", prefix+["--profile","final","--run-id","vm_final"], WORK)
    if (package/"results").exists():
        shutil.copytree(package/"results", EVIDENCE/"core_results")
    after = {rel:digest(package/rel) for rel in records}
    result["sourceAndInputHashesUnchanged"] = after==records
    final = package/"results/vm_final/runResult.json"
    result["programStatus"] = json.loads(final.read_text(encoding="utf-8"))["status"] if final.exists() else "NO_RESULT"
    result["accepted"] = result["returncode"]==0 and result["programStatus"]=="PASS" and after==records
    save("core_final_result.json",result)
    return result

def verification():
    raw = WORK/"05_original"
    fixed = WORK/"05_path_adapted"
    shutil.copytree("C:/Verification/unadapted",raw,ignore=shutil.ignore_patterns("__pycache__","tmp","matrix_*","*.log"))
    shutil.copytree("C:/Verification/path_adapted",fixed,ignore=shutil.ignore_patterns("__pycache__","tmp","matrix_*","*.log"))
    shutil.copy2("C:/Verification/verification_jobs.py",fixed/"verification_jobs.py")
    rawcmd = [str(RUNTIME),"-I","-X","utf8","-B",str(CONTROL/"entry_runner.py"),
              str(raw/"paper_output/code/verification/threshold_and_scaling_checks.py")]
    execute("verification_original_path_probe",rawcmd,WORK,120)
    command = [str(RUNTIME),"-I","-X","utf8","-B","C:/Verification/execute_matrix.py",
               "--python",str(RUNTIME),"--root",str(fixed),"--workers","2","--label","windows_vm"]
    record = execute("verification_matrix",command,WORK,1500)
    matrix = fixed/"matrix_windows_vm"
    if matrix.exists():
        shutil.copytree(matrix,EVIDENCE/"verification_matrix")
    output=fixed/"paper_output"
    for section in ["results/verification","reports","figures"]:
        p=output/section
        if p.exists():
            shutil.copytree(p,EVIDENCE/"verification_generated"/section.replace("/","_"),
                            ignore=shutil.ignore_patterns("*.dat","*.bin","__pycache__"))
    return record

try:
    EVIDENCE.mkdir(exist_ok=True)
    WORK.mkdir(exist_ok=False)
    assert not ORIGINAL.exists(), "Original host workspace is unexpectedly visible inside VM"
    assert Path(sys.prefix).resolve()==Path("C:/Runtime"), (sys.prefix,sys.path)
    ENV=os.environ.copy()
    for key in ["PYTHONPATH","PYTHONHOME"]:
        ENV.pop(key,None)
    ENV.update(PYTHONUTF8="1",PYTHONNOUSERSITE="1",PYTHONDONTWRITEBYTECODE="1",
               OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1",MPLBACKEND="Agg")
    temp=WORK/"temp";temp.mkdir()
    for key in ["TEMP","TMP","TMPDIR"]:
        ENV[key]=str(temp)
    save("vm_environment.json",{"startedAtUtc":datetime.now(timezone.utc).isoformat(),
        "python":sys.version,"executable":sys.executable,"prefix":sys.prefix,"platform":platform.platform(),
        "computerName":os.environ.get("COMPUTERNAME"),"originalHostWorkspaceVisible":ORIGINAL.exists(),
        "sysPath":sys.path,"libraries":{n:importlib.metadata.version(n) for n in ["numpy","scipy","openpyxl","matplotlib"]},
        "networkDisabledByWSB":True,"candidateReadOnlyByWSB":True})
    with ThreadPoolExecutor(max_workers=2) as pool:
        a=pool.submit(core)
        b=pool.submit(verification)
        core_result=a.result()
        verification_result=b.result()
    save("vm_complete.json",{"finishedAtUtc":datetime.now(timezone.utc).isoformat(),
         "core":core_result,"verificationProcess":verification_result,
         "note":"Matrix exit zero means the test queue finished; inspect each job and its numerical result."})
except BaseException as error:
    save("vm_fatal.json",{"error":repr(error),"traceback":traceback.format_exc()})
