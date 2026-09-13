"""Create and verify a provisional lossless RAR of the entire support folder."""
from pathlib import Path
import hashlib,json,subprocess,time,datetime,sys

qa=Path(__file__).resolve().parent
root=qa.parents[3]
source=root/'支撑材料'
rar=root/'tmp/cache/support-rar/runtime/Rar.exe'
exhaustive='--exhaustive' in sys.argv
label='exhaustive' if exhaustive else 'standard'
archive=qa.parent/('provisional_exhaustive.rar' if exhaustive else 'provisional.rar')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest():return {str(p.relative_to(source)).replace('\\','/'):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(source.rglob('*')) if p.is_file()}
before=manifest()
(qa/f'{label}_input_manifest.json').write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding='utf-8')
calls=[]
extract_dir=root/f'tmp/cache/support-rar/extracted_{label}'
extract_dir.mkdir(parents=True,exist_ok=True)
for name,args in [
    ('compress',[str(rar),'a','-cfg-','-r','-m5','-md128m','-s','-mt4','-qo-','-idq']+(['-mcx'] if exhaustive else [])+[str(archive),'支撑材料']),
    ('test',[str(rar),'t','-cfg-','-idq',str(archive)]),
    ('extract',[str(rar),'x','-cfg-','-idq','-y',str(archive),str(extract_dir)+'\\']),
]:
    started=time.monotonic()
    result=subprocess.run(args,cwd=root,capture_output=True)
    (qa/f'{label}_{name}.stdout.log').write_bytes(result.stdout)
    (qa/f'{label}_{name}.stderr.log').write_bytes(result.stderr)
    calls.append({'name':name,'args':args,'exitCode':result.returncode,'seconds':time.monotonic()-started})
    if result.returncode:break
after=manifest()
changed=[k for k in set(before)|set(after) if before.get(k)!=after.get(k)]
extracted={str(p.relative_to(extract_dir/'支撑材料')).replace('\\','/'):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted((extract_dir/'支撑材料').rglob('*')) if p.is_file()}
extract_mismatches=[k for k in set(before)|set(extracted) if before.get(k)!=extracted.get(k)]
report={'createdAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'archive':str(archive.relative_to(root)),'bytes':archive.stat().st_size if archive.exists() else None,'sha256':sha(archive) if archive.exists() else None,'sourceFiles':len(before),'sourceBytes':sum(v['bytes'] for v in before.values()),'inputChangedDuringRun':changed,'extractedFiles':len(extracted),'extractionHashMismatches':extract_mismatches,'calls':calls,'allExitZero':all(c['exitCode']==0 for c in calls),'under20DecimalMB':archive.exists() and archive.stat().st_size<20_000_000,'under20MiB':archive.exists() and archive.stat().st_size<20*1024*1024,'provisional':True}
(qa/f'{label}_rar_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
