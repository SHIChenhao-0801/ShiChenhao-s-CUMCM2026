from __future__ import annotations
import ast
import csv
import hashlib
import importlib.metadata
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
QA = Path(__file__).resolve().parent
SUPPORT = ROOT / '支撑材料'
CORE = SUPPORT / '03_程序代码'
HIST = SUPPORT / '05_数值检验与实验'
OLD = ROOT / 'paper_output/qa/comment_sandbox_20260913'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def record(p):
    return {'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p)}

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

sources = sorted(p for base in (CORE, HIST) for p in base.rglob('*') if p.is_file() and p.suffix in ('.py', '.m', '.mjs', '.ps1'))
before = [record(p) for p in sources]
compiled = []
imports = {}
for p in sources:
    if p.suffix != '.py':
        continue
    content = p.read_text(encoding='utf-8-sig')
    parsed = ast.parse(content, filename=str(p))
    compile(parsed, str(p), 'exec')
    compiled.append(p.relative_to(ROOT).as_posix())
    modules = set()
    for node in ast.walk(parsed):
        if isinstance(node, ast.Import):
            modules.update(n.name.split('.')[0] for n in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split('.')[0])
    imports[p.relative_to(SUPPORT).as_posix()] = sorted(modules)

manifest = []
with (CORE/'input_manifest.csv').open(encoding='utf-8-sig', newline='') as f:
    for item in csv.DictReader(f):
        p = CORE/item['path']
        manifest.append({'path': item['path'], 'exists': p.is_file(), 'matchesSha': p.is_file() and sha(p)==item['sha256'], 'matchesBytes': p.is_file() and p.stat().st_size==int(item['bytes'])})

old = read(OLD/'final_delivery_audit.json')
oldfiles = {r['path']:r for r in old['formalFiles']}
source_binding = [{'path': p.relative_to(SUPPORT).as_posix(), 'matchesPriorSandboxDelivery': sha(p)==oldfiles[p.relative_to(SUPPORT).as_posix()]['sha256']} for p in sources]
run = read(OLD/'vm_output/core_results/vm_final/runResult.json')
core_binding = [{'path': r['path'], 'matchesCurrent': sha(CORE/r['path'])==r['sha256']} for r in run['sources']+run['preflight']['checkedFiles']]
bound_evidence = [{'path':r['path'],'matchesSha':sha(ROOT/r['path'])==r['sha256']} for r in old['evidenceBindings']]

identity_hits = []
project_path_files = []
identity_terms = ['Shi Chenhao','SHIChenhao','福州大学','厦门大学','Users\\','Users/']
for base in (CORE,HIST):
    for p in base.rglob('*'):
        if not p.is_file():
            continue
        b=p.read_bytes()
        for term in identity_terms:
            encodings=[e for e in ('utf-8','utf-16-le','gb18030') if term.encode(e,errors='ignore') in b]
            if encodings:
                identity_hits.append({'path':p.relative_to(SUPPORT).as_posix(),'term':term,'encodings':encodings})
        if p.suffix in ('.py','.m','.mjs','.txt','.json','.htm','.pyproj','.sln'):
            t=b.decode('utf-8-sig',errors='replace')
            for i,line in enumerate(t.splitlines(),1):
                if re.search(r'[A-Z]:[/\\]',line):
                    project_path_files.append({'path':p.relative_to(SUPPORT).as_posix(),'line':i,'text':line.strip()[:300]})

copy = QA/'isolated03'
copy.mkdir(exist_ok=False)
for p in CORE.rglob('*'):
    if p.is_file() and '.vs' not in p.relative_to(CORE).parts and p.name != 'UpgradeLog.htm':
        dest=copy/p.relative_to(CORE)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,dest)

commands=[]
for name,args in [('help',['--help']),('preflight',['--preflight-only','--run-id','support_recheck'])]:
    cmd=[sys.executable,'-X','utf8','-B',str(copy/'runDelivery.py'),*args]
    p=subprocess.run(cmd,cwd=QA,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=45)
    (QA/(name+'.stdout.log')).write_text(p.stdout,encoding='utf-8')
    (QA/(name+'.stderr.log')).write_text(p.stderr,encoding='utf-8')
    commands.append({'name':name,'argv':cmd,'cwd':str(QA),'returncode':p.returncode})

missing_input_paths = [
    HIST/'Python检验源码/paper_output/data_cleaned/A_environment_observed.csv',
    HIST/'Python检验源码/paper_output/data_cleaned/A_radius_observed.csv',
    HIST/'Python检验源码/paper_output/plan/model_route.json',
    HIST/'Python检验源码/paper_output/results/production/final_v6a/Q23/sampled_solution.npz',
]
result={
    'utc':datetime.now(timezone.utc).isoformat(),
    'scope':'Independent static/source binding and isolated input preflight only; no new PDE solve, no new VS run, no formal-support mutation by this agent.',
    'sourceCount':len(sources),'pythonCompiledCount':len(compiled),
    'sources':before,'pythonImports':imports,'inputManifest':manifest,
    'allSourceHashesMatchPreviousSandboxDelivery':all(x['matchesPriorSandboxDelivery'] for x in source_binding),
    'sourceBindings':source_binding,'coreRunBindings':core_binding,'priorEvidenceBindings':bound_evidence,
    'sourceHashesUnchangedDuringAudit':before==[record(p) for p in sources],
    'priorFullRun':{'external':read(OLD/'vm_output/core_final_result.json'),'programStatus':run['status'],'profile':run['profile'],'guiReproduced':run['guiReproduced'],'humanReview':run['humanReview']},
    'currentPreflightCommands':commands,
    'identityLiteralHits':identity_hits,'absolutePathOccurrences':project_path_files,
    'historicalExpectedInputs':[{'path':p.relative_to(ROOT).as_posix(),'exists':p.is_file()} for p in missing_input_paths],
    'runtime':{'python':sys.version,'packages':{n:importlib.metadata.version(n) for n in ('numpy','scipy','openpyxl')}},
}
(QA/'code_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['sourceCount','pythonCompiledCount','allSourceHashesMatchPreviousSandboxDelivery','sourceHashesUnchangedDuringAudit','currentPreflightCommands','identityLiteralHits','historicalExpectedInputs']},ensure_ascii=False,indent=2))
