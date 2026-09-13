from pathlib import Path
import json
import shutil
import subprocess
import sys

ROOT = Path.cwd().resolve()
QA = ROOT / 'paper_output/qa/support_completion_20260913/verification'
SOURCE = ROOT / '支撑材料/05_数值检验与实验/Python检验源码'
PYTHON = ROOT / 'tmp/cache/support_completion_verification_venv/Scripts/python.exe'
oldroot = QA / 'missing_input_reproduction'
shutil.copytree(SOURCE / 'paper_output/code/modeling', oldroot / 'paper_output/code/modeling')
tasks = [
    ('missing_input', [str(PYTHON), '-X', 'utf8', '-B', str(oldroot / 'paper_output/code/modeling/verify_convergence.py'),
                       '--question', 'Q1', '--grids', '2', '4', '--tag', 'missing_input'], oldroot, 1,
     'A_environment_observed.csv'),
    ('help', [str(PYTHON), '-X', 'utf8', '-B', str(SOURCE / 'run_checks.py'), '--help'], ROOT, 0,
     '--output-dir'),
    ('reject_support_output', [str(PYTHON), '-X', 'utf8', '-B', str(SOURCE / 'run_checks.py'),
                              '--check', 'method', '--quick', '--output-dir', str(SOURCE / 'invalid_output')], ROOT, 2,
     'must be outside'),
    ('reject_existing_output', [str(PYTHON), '-X', 'utf8', '-B', str(SOURCE / 'run_checks.py'),
                               '--check', 'method', '--quick', '--output-dir', str(QA)], ROOT, 2,
     'must be a new directory'),
]
records = []
for name, command, cwd, expected, text in tasks:
    result = subprocess.run(command, cwd=cwd, capture_output=True, encoding='utf-8', errors='replace')
    (QA / (name + '.stdout.log')).write_text(result.stdout, encoding='utf-8')
    (QA / (name + '.stderr.log')).write_text(result.stderr, encoding='utf-8')
    record = {'name': name, 'argv': command, 'cwd': str(cwd), 'returncode': result.returncode,
              'expected_returncode': expected, 'expected_text': text,
              'passed': result.returncode == expected and text in result.stdout + result.stderr}
    records.append(record)
assert not (SOURCE / 'invalid_output').exists()
(QA / 'guard_results.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(records, ensure_ascii=False, indent=2))
assert all(r['passed'] for r in records)
