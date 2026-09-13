from pathlib import Path
import ast
import hashlib
import json
import shutil

ROOT = Path.cwd().resolve()
SUPPORT = ROOT / '支撑材料/05_数值检验与实验'
QA = ROOT / 'paper_output/qa/support_completion_20260913/verification'
QA.mkdir(parents=True, exist_ok=True)
before = {p.relative_to(SUPPORT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in SUPPORT.rglob('*') if p.is_file()}
(QA / 'before_sha256.json').write_text(json.dumps(before, ensure_ascii=False, indent=2), encoding='utf-8')
target = SUPPORT / 'Python检验源码/paper_output/code/verification/method_comparison.py'
old = target.read_text(encoding='utf-8')
shutil.copy2(target, QA / 'method_comparison.before.py')
needle = 'ROOT = pathlib.Path(r"D:\\Document\\数学建模\\2026CUMCM")'
assert old.count(needle) == 1
new = old.replace(needle, 'ROOT = pathlib.Path(__file__).resolve().parents[3]')
a, b = ast.parse(old), ast.parse(new)
for tree in (a, b):
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ROOT' for t in node.targets):
            node.value = ast.Constant(value='ROOT_PATH_ONLY')
assert ast.dump(a, include_attributes=False) == ast.dump(b, include_attributes=False)
target.write_text(new, encoding='utf-8', newline='\n')
data = SUPPORT / 'Python检验源码/paper_output/data_cleaned'
data.mkdir(parents=True, exist_ok=True)
for name in ('A_environment_observed.csv', 'A_radius_observed.csv'):
    source = ROOT / '支撑材料/03_程序代码/inputs/cleaned' / name
    shutil.copy2(source, data / name)
    assert source.read_bytes() == (data / name).read_bytes()
print('Prepared two exact CSV copies; method_comparison AST unchanged except ROOT assignment.')
