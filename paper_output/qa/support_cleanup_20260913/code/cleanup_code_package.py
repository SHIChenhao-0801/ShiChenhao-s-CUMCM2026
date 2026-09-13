"""Migrate the CURRENT code package inputs and readable notes; do not rebuild it."""
from pathlib import Path
import ast
import csv
import hashlib
import json
import pprint
import shutil

QA = Path(__file__).resolve().parent
ROOT = QA.parents[3]
PACKAGE = (ROOT/'支撑材料/03_程序代码').resolve()
BEFORE = QA/'before_current_03'
if BEFORE.exists():
    raise FileExistsError('Current-package snapshot already exists; do not silently rebuild')
shutil.copytree(PACKAGE, BEFORE)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

old_reference = json.loads((PACKAGE/'reference/numerical_reference.json').read_text(encoding='utf-8'))
reference_code = ('"""Frozen numerical reference data; no solver or file I/O is executed here."""\n'
                  'REFERENCE_DATA = '+pprint.pformat(old_reference, width=100, sort_dicts=False)+'\n')
reference_path = PACKAGE/'reference/reference_data.py'
reference_path.write_text(reference_code, encoding='utf-8')
tree = ast.parse(reference_code)
assert len(tree.body) == 2 and isinstance(tree.body[1], ast.Assign)
new_reference = ast.literal_eval(tree.body[1].value)

def exact(left, right):
    assert type(left) is type(right), (type(left), type(right))
    if isinstance(left, dict):
        assert list(left) == list(right)
        for key in left: exact(left[key], right[key])
    elif isinstance(left, list):
        assert len(left) == len(right)
        for a, b in zip(left, right): exact(a, b)
    elif isinstance(left, float):
        assert left.hex() == right.hex()
    else:
        assert left == right
exact(old_reference, new_reference)

manifest = json.loads((PACKAGE/'input_manifest.json').read_text(encoding='utf-8'))['files']
with (PACKAGE/'input_manifest.csv').open('w', encoding='utf-8-sig', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=['path', 'bytes', 'sha256'])
    writer.writeheader()
    for item in manifest:
        if item['path'] == 'reference/numerical_reference.json':
            item = {'path':'reference/reference_data.py', 'bytes':reference_path.stat().st_size,
                    'sha256':sha(reference_path)}
        writer.writerow({key:item[key] for key in writer.fieldnames})

runner = PACKAGE/'runDelivery.py'
old = runner.read_text(encoding='utf-8')
replacements = [
    ('import argparse\n', 'import argparse\nimport csv\n'),
    ("    manifest = json.loads((ROOT/'input_manifest.json').read_text(encoding='utf-8'))\n",
     "    with (ROOT/'input_manifest.csv').open('r', encoding='utf-8-sig', newline='') as stream:\n        manifest = list(csv.DictReader(stream))\n"),
    ("    for expected in manifest['files']:\n", "    for expected in manifest:\n"),
    ("    reference = json.loads((ROOT/'reference/numerical_reference.json').read_text(encoding='utf-8'))['questions'][question]\n",
     "    from reference.reference_data import REFERENCE_DATA\n    reference = REFERENCE_DATA['questions'][question]\n")]
new = old
for left, right in replacements:
    assert left in new, left
    new = new.replace(left, right)
restored = new
for left, right in reversed(replacements):
    restored = restored.replace(right, left)
assert ast.dump(ast.parse(restored), include_attributes=False) == ast.dump(ast.parse(old), include_attributes=False)
runner.write_text(new, encoding='utf-8')

core_records = []
for name in ['dryingCore.py','analyticJacobian.py','diskDense.py','exportOutputs.py',
             'q1Model.py','q2Model.py','q3Model.py','q4Model.py']:
    path = PACKAGE/name
    before = path.read_text(encoding='utf-8')
    after = before.replace('docs/source_changes.json', 'docs/源码变更说明.txt')
    after = after.replace('numerical_design.md', 'numerical_design.txt')
    restored = after.replace('docs/源码变更说明.txt', 'docs/source_changes.json').replace(
        'numerical_design.txt', 'numerical_design.md')
    assert ast.dump(ast.parse(restored), include_attributes=False) == ast.dump(ast.parse(before), include_attributes=False)
    path.write_text(after, encoding='utf-8')
    core_records.append({'path':name, 'beforeSha256':sha(BEFORE/name), 'afterSha256':sha(path),
                         'algorithmAstUnchanged':True})
project = PACKAGE/'A_CodeReview.pyproj'
project.write_text(project.read_text(encoding='utf-8').replace('README.md', 'README.txt'), encoding='utf-8')

# Only known files inside this exact code directory are removed. The current
# versions remain in the QA snapshot; no older package contents are restored.
removed = []
for path in list(PACKAGE.rglob('*')):
    if path.is_file() and path.suffix.lower() in {'.json', '.md'}:
        resolved = path.resolve()
        assert resolved.is_relative_to(PACKAGE)
        removed.append(path.relative_to(PACKAGE).as_posix())
        path.unlink()
# The previous diff points to deleted JSON notes and duplicates the concise
# source-change text now supplied for review.
diff = (PACKAGE/'docs/portable_paths.diff').resolve()
assert diff.is_relative_to(PACKAGE)
if diff.exists():
    removed.append(diff.relative_to(PACKAGE).as_posix())
    diff.unlink()

report = {'status':'FORMAT_MIGRATION_STATIC_PASS', 'referenceDataExactTypeAndFloatEquality':True,
          'coreModules':core_records, 'runnerAstEquivalentAfterOnlyInputFormatNormalization':True,
          'runnerBeforeSha256':sha(BEFORE/'runDelivery.py'), 'runnerAfterSha256':sha(runner),
          'inputManifestRows':len(manifest), 'removedFromDelivery':removed,
          'originalInputsAndTemplatesUnchanged':all(sha(p) == sha(BEFORE/p.relative_to(PACKAGE))
              for p in (PACKAGE/'inputs').rglob('*') if p.is_file()),
          'frozenNpzsUnchanged':all(sha(p) == sha(BEFORE/p.relative_to(PACKAGE))
              for p in (PACKAGE/'reference').rglob('*.npz'))}
(QA/'migration_static.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'status':report['status'], 'removed':removed, 'manifestRows':len(manifest)}, ensure_ascii=False))
