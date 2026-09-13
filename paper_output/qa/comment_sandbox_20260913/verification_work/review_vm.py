import hashlib
import json
from pathlib import Path


base = Path(__file__).resolve().parent
evidence = base.parent/'vm_output'
folder = evidence/'verification_matrix'
matrix = json.loads((folder/'process_matrix.json').read_text(encoding='utf-8'))
source_checks = []
for item in matrix['sources']:
    local = base/'path_adapted'/item['path']
    if local.suffix == '.py' and item['path'].startswith('paper_output/code/'):
        source_checks.append({'path':item['path'], 'vmRecordedSha256':item['sha256'],
            'hostAdaptedSha256':hashlib.sha256(local.read_bytes()).hexdigest(),
            'sameSource':item['sha256']==hashlib.sha256(local.read_bytes()).hexdigest()})
assert len(source_checks)==31 and all(row['sameSource'] for row in source_checks)
rows=[]
for process in matrix['results']:
    path=folder/(process['job']+'.log')
    text=path.read_text(encoding='utf-8')
    classification='EXIT_ZERO_CHECK_NUMERICAL_REPORT'
    if process['returncode']!=0:
        classification='STALE_COPIED_OUTPUT_DIRECTORY' if 'FileExistsError' in text else 'ORIGINAL_CODE_OR_DIAGNOSTIC_FAILURE'
    final=None
    lines=text.splitlines(keepends=True)
    for first in range(len(lines)-1,-1,-1):
        if lines[first].startswith('{'):
            try:
                final=json.loads(''.join(lines[first:]))
                break
            except json.JSONDecodeError:
                pass
    if final and final.get('status')=='REVIEW_REQUIRED':
        classification='EXIT_ZERO_NUMERICAL_CRITERIA_REVIEW_REQUIRED'
    if process['job']=='series':
        classification='COMPLETED_BUT_NEGATIVE_CONSTANT_SERIES_TEST_FAILS'
    if process['job']=='analytic_metric':
        classification='COMPLETED_BUT_STATIC_INTERPRETATION_CONTRADICTS_REFINEMENT'
    row={'job':process['job'],'actualExit':process['returncode'],'elapsedSeconds':process['elapsedSeconds'],
         'classification':classification,'log':str(path),'logSha256':hashlib.sha256(path.read_bytes()).hexdigest(),
         'parsedFinalOutput':final}
    rows.append(row)
report={'scope':'Actual Windows Sandbox VM first attempt. Six pre-existing output directories were copied from the host and must be retried in a clean root.',
        'environment':json.loads((evidence/'vm_environment.json').read_text(encoding='utf-8')),
        'jobCount':len(rows),'exitZeroCount':sum(r['actualExit']==0 for r in rows),
        'staleOutputFailures':[r['job'] for r in rows if r['classification']=='STALE_COPIED_OUTPUT_DIRECTORY'],
        'originalFailures':[r['job'] for r in rows if r['classification']=='ORIGINAL_CODE_OR_DIAGNOSTIC_FAILURE'],
        'testedSourceChecks':source_checks,'rows':rows,
        'doNotCertifyAllProgramsPassed':True,'originalCandidateNotModified':True}
(base/'vm_first_attempt_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'jobs':report['jobCount'],'exitZero':report['exitZeroCount'],
                  'staleOutputFailures':report['staleOutputFailures'],'originalFailures':report['originalFailures'],
                  'sourceShaMatched':len(source_checks)},ensure_ascii=False))
