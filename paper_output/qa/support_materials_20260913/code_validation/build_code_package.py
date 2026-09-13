"""Create the portable support-code copy without modifying production sources."""
from pathlib import Path
import ast
import difflib
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[4]
TARGET = ROOT / '支撑材料/03_程序代码'
SOURCE = ROOT / 'paper_output/code/review_delivery'
QA = Path(__file__).resolve().parent
TARGET.mkdir(parents=True, exist_ok=True)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

records, differences = [], []
for name in ['dryingCore.py', 'analyticJacobian.py', 'diskDense.py', 'q1Model.py',
             'q2Model.py', 'q3Model.py', 'q4Model.py', 'exportOutputs.py']:
    src = SOURCE/name
    old = src.read_text(encoding='utf-8')
    text = old.replace('来源、改名与 AST 核验见 tools/coreRenameReport.json。',
                       '本次便携路径调整见 docs/source_changes.json。')
    replacements = []
    if name in ['dryingCore.py', 'exportOutputs.py']:
        replacements.append(('ROOT = Path(__file__).resolve().parents[3]',
                             'ROOT = Path(__file__).resolve().parent'))
    if name == 'dryingCore.py':
        replacements.append(("'paper_output/data_cleaned'", "'inputs/cleaned'"))
    elif name == 'exportOutputs.py':
        replacements += [
            ("'problem_files/CUMCM2026Problems/A题/附件/附件3'", "'inputs/templates'"),
            ("ROOT/'problem_files'", "ROOT/'inputs'"),
            ('Outputs must be inside the competition workspace, outside problem_files',
             'Outputs must be inside the extracted code package, outside inputs'),
            ("'paper_output/code/review_delivery/exportOutputs.py'", "'exportOutputs.py'"),
            ("'paper_output/code/review_delivery/runtime/exportSelfcheck'", "'results/exportSelfcheck'"),
            ('Use the competition workspace as cwd', 'Use the extracted code package as cwd')]
    elif name == 'analyticJacobian.py':
        replacements += [
            (r'C:\\Python314\\python.exe -B paper_output/code/modeling/analytic_jacobian.py --self-test',
             'python -B analyticJacobian.py --self-test'),
            ("ROOT/'paper_output/code/review_delivery/dryingCore.py'", "ROOT/'dryingCore.py'"),
            ("Path(__file__).resolve().parents[2]/'code/review_delivery/runtime/jacobianValidation'",
             "Path(__file__).resolve().parent/'results/jacobianValidation'")]
    for left, right in replacements:
        if left not in text:
            raise ValueError((name, left, 'replacement target missing'))
        text = text.replace(left, right)
    dest = TARGET/name
    dest.write_text(text, encoding='utf-8')
    restored = text
    for left, right in reversed(replacements):
        restored = restored.replace(right, left)
    # Ignore comments, but require every executable AST node to match after
    # reversing only the listed path/description substitutions.
    equivalent = ast.dump(ast.parse(restored), include_attributes=False) == ast.dump(
        ast.parse(old), include_attributes=False)
    if not equivalent:
        raise AssertionError('Unapproved executable change: '+name)
    records.append({'source': src.relative_to(ROOT).as_posix(), 'sourceSha256': sha(src),
                    'delivered': name, 'deliveredSha256': sha(dest),
                    'replacements': replacements, 'algorithmAstEquivalentAfterPathNormalization': equivalent})
    differences.extend(difflib.unified_diff(old.splitlines(True), text.splitlines(True),
                                         fromfile='original/'+name, tofile='portable/'+name))

copies = []
for name in ['A_environment_observed.csv', 'A_radius_observed.csv']:
    copies.append((ROOT/'paper_output/data_cleaned'/name, TARGET/'inputs/cleaned'/name))
for name in ['附件1.xlsx', '附件2.xlsx']:
    copies.append((ROOT/'problem_files/CUMCM2026Problems/A题/附件'/name, TARGET/'inputs/original'/name))
for i in range(1, 5):
    name = f'result{i}.xlsx'
    copies.append((ROOT/'problem_files/CUMCM2026Problems/A题/附件/附件3'/name, TARGET/'inputs/templates'/name))
for q in ['Q1', 'Q23', 'Q4']:
    copies.append((ROOT/'paper_output/results/production/final_v6a'/q/'sampled_solution.npz',
                   TARGET/'reference'/q/'sampled_solution.npz'))
copy_records = []
for src, dst in copies:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    assert sha(src) == sha(dst)
    copy_records.append({'source': src.relative_to(ROOT).as_posix(),
                         'path': dst.relative_to(TARGET).as_posix(), 'bytes': dst.stat().st_size,
                         'sha256': sha(dst)})
full = json.loads((ROOT/'paper_output/results/production/final_v6a/numerical_summaries.json').read_text(encoding='utf-8'))
reference = {q: {key: v for key, v in full[q].items() if key in
             ['diagnostics', 'completion', 'reproduction_samples']} for q in full}
write(TARGET/'reference/numerical_reference.json', {'sourceVersion': 'final_v6a',
      'purpose': 'Frozen numerical reference, not a new solve or measured physical data', 'questions': reference})
write(TARGET/'docs/source_changes.json', {'status': 'PASS',
      'scope': 'Only explicitly listed package paths and descriptive strings changed in eight core modules; solver AST unchanged after normalization.',
      'files': records, 'copiedInputsAndReference': copy_records,
      'originalProductionFilesModified': False, 'visualStudioNewGui': 'NOT_PERFORMED', 'humanReview': 'PENDING_USER_REVIEW'})
(TARGET/'docs/portable_paths.diff').write_text(''.join(differences), encoding='utf-8')
write(TARGET/'input_manifest.json', {'files': [r for r in copy_records if r['path'].startswith('inputs/') or r['path'].startswith('reference/')] +
      [{'path': 'reference/numerical_reference.json', 'sha256': sha(TARGET/'reference/numerical_reference.json'),
        'bytes': (TARGET/'reference/numerical_reference.json').stat().st_size}]})
shutil.copy2(SOURCE/'requirements.txt', TARGET/'requirements.txt')
shutil.copy2(SOURCE/'A_CodeReview.sln', TARGET/'A_CodeReview.sln')
print(json.dumps({'target': str(TARGET), 'coreModules': len(records), 'copiedFiles':len(copies)}, ensure_ascii=False))
