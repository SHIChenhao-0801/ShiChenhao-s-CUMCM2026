import hashlib
import json
from pathlib import Path
import shutil


output = Path('C:/Evidence/verification_remaining_entries/native_scope.json')
source = Path('C:/Work/extra_entries/matlab/compareMatlab.mjs')
candidate = Path('C:/Candidate/05_数值检验与实验/MATLAB对照证据/compareMatlab.mjs')
records = json.loads(Path('C:/Evidence/extra_entries/processes.json').read_text(encoding='utf-8'))
node = next(item for item in records if item['name'] == 'node_original_worker')
assert node['returncode'] == 2
source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
candidate_sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
assert source_sha == candidate_sha
report = {'matlabExecutableFound': shutil.which('matlab'),
          'matlabStatus': 'NOT_EXECUTED_RUNTIME_UNAVAILABLE',
          'nodeSourceSha256': source_sha, 'candidateNodeSha256': candidate_sha,
          'records': [item for item in records if item['name'] in ('node_version', 'node_original_worker')],
          'scope': 'Read-only binding of the already completed original Node worker run; no second execution and no PowerShell-wrapper completion claim.'}
output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False), flush=True)
