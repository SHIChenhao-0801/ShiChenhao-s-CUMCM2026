import ast
import hashlib
import json
from pathlib import Path
import shutil


base = Path(__file__).resolve().parent
qa = base.parent
candidate = qa / 'candidate'
source = candidate / '05_数值检验与实验/Python检验源码'
inputs = candidate / '03_程序代码'
records = []
for variant in ('unadapted', 'path_adapted'):
    target = base / variant
    if target.exists():
        raise FileExistsError(target)
    shutil.copytree(source, target)
    for name in ('A_environment_observed.csv', 'A_radius_observed.csv'):
        origin = inputs / 'inputs/cleaned' / name
        dest = target / 'paper_output/data_cleaned' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origin, dest)
        records.append({'variant': variant, 'role': 'explicit_supplied_input', 'from': str(origin), 'to': str(dest), 'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()})
    if variant == 'path_adapted':
        for file in target.rglob('*.py'):
            content = file.read_text(encoding='utf-8-sig')
            before = hashlib.sha256(file.read_bytes()).hexdigest()
            changed = content.replace('pathlib.Path(r"D:\\Document\\数学建模\\2026CUMCM")', 'pathlib.Path(__file__).resolve().parents[3]')
            changed = changed.replace('Path(r"D:\\Document\\数学建模\\2026CUMCM").resolve()', 'Path(__file__).resolve().parents[3]')
            if changed != content:
                tree_a, tree_b = ast.parse(content), ast.parse(changed)
                file.write_text(changed, encoding='utf-8', newline='\n')
                records.append({'variant': variant, 'role': 'root_path_only_adaptation', 'file': str(file), 'beforeSha256': before, 'afterSha256': hashlib.sha256(file.read_bytes()).hexdigest()})
        for name in ('result1.xlsx', 'result2.xlsx', 'result3.xlsx', 'result4.xlsx'):
            origin = inputs / 'inputs/templates' / name
            dest = target / 'problem_files/CUMCM2026Problems/A题/附件/附件3' / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(origin, dest)
            records.append({'variant': variant, 'role': 'explicit_supplied_template', 'from': str(origin), 'to': str(dest), 'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()})
        origin = inputs / 'reference/Q23/sampled_solution.npz'
        dest = target / 'paper_output/results/production/final_v6a/Q23/sampled_solution.npz'
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origin, dest)
        records.append({'variant': variant, 'role': 'explicit_supplied_frozen_NPZ_for_descriptive_series_only', 'from': str(origin), 'to': str(dest), 'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()})
        shutil.copyfile(base / 'verification_jobs.py', target / 'verification_jobs.py')
(base / 'preparation_manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'prepared': ['unadapted', 'path_adapted'], 'records': len(records)}, ensure_ascii=False))
