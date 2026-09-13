from pathlib import Path
import ast
import csv
import hashlib
import io
import json
import re
import shutil
import tokenize

ROOT = Path.cwd().resolve()
SUPPORT = ROOT / '支撑材料/05_数值检验与实验'
QA = ROOT / 'paper_output/qa/support_completion_20260913/verification'
before = json.loads((QA / 'before_sha256.json').read_text(encoding='utf-8'))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

changed_source = 'Python检验源码/paper_output/code/verification/method_comparison.py'
changes = [{'path': name, 'before': digest, 'after': sha(SUPPORT / name)}
           for name, digest in before.items()
           if name.endswith(('.py', '.m', '.mjs')) and sha(SUPPORT / name) != digest]
assert [item['path'] for item in changes] == [changed_source]
old = ast.parse((QA / 'method_comparison.before.py').read_text(encoding='utf-8'))
new = ast.parse((SUPPORT / changed_source).read_text(encoding='utf-8'))
for tree in (old, new):
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ROOT' for t in node.targets):
            node.value = ast.Constant(value='ROOT_PATH_ONLY')
assert ast.dump(old, include_attributes=False) == ast.dump(new, include_attributes=False)
for name in ('独立沙盒逐源码核查.txt', '独立沙盒运行矩阵.csv'):
    assert sha(SUPPORT / name) == before[name]

code = list(SUPPORT.rglob('*.py'))
for path in code:
    text = path.read_text(encoding='utf-8-sig')
    compile(text, str(path), 'exec')
    assert not any(token.type == tokenize.COMMENT for token in tokenize.generate_tokens(io.StringIO(text).readline))

data = []
for name, count in (('A_environment_observed.csv', 241), ('A_radius_observed.csv', 145)):
    path = SUPPORT / 'Python检验源码/paper_output/data_cleaned' / name
    reference = ROOT / '支撑材料/03_程序代码/inputs/cleaned' / name
    assert path.read_bytes() == reference.read_bytes()
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding='utf-8-sig'))))
    assert len(rows) == count
    data.append({'path': path.relative_to(SUPPORT).as_posix(), 'rows': count, 'sha256': sha(path)})

runs = {name: json.loads((QA / ('isolated_' + name) / 'run_result.json').read_text(encoding='utf-8'))
        for name in ('grid', 'time', 'method')}
for run in runs.values():
    assert run['returncode'] == 0 and run['source_input_unchanged']
    assert run['runtime']['packages'] == {'numpy':'2.5.2', 'scipy':'1.18.1', 'openpyxl':'3.1.5', 'matplotlib':'3.11.2'}
    for item in run['input_files']:
        assert sha(SUPPORT / 'Python检验源码' / item['path']) == item['sha256']
grid = json.loads((QA / 'isolated_grid/paper_output/results/convergence/reproduction/convergence_report.json').read_text(encoding='utf-8'))
time = json.loads((QA / 'isolated_time/paper_output/results/time_accuracy/reproduction/time_accuracy_report.json').read_text(encoding='utf-8'))
method = json.loads((QA / 'isolated_method/paper_output/results/crossvalidation/method_v1/method_comparison.json').read_text(encoding='utf-8'))
assert grid['status'] == 'computed_and_zero_solver_warnings'
assert time['status'] == 'computed_zero_solver_warnings'
assert [x['process']['returncode'] for x in time['runs']] == [0, 0]
assert method['variableD']['passedDeclaredTolerance']
assert all(r['fluxPathUsed'] == r['scheme'] for r in method['records'])
assert all(r['maxAbsDifference'] == 0 for r in method['limitingCaseConstantD']['rows'])

checksum_path = SUPPORT / '源码文件与校验值.txt'
shutil.copy2(checksum_path, QA / '源码文件与校验值.before.txt')
text = checksum_path.read_text(encoding='utf-8-sig')
text = text.replace('以下33项均为真实源代码的去注释版本。', '以下34项为33份原检验源码及新增独立入口；原检验源码保留去注释版本。')
text = text.replace('没有修改计算语句、模型参数或输出数据字符串。', '本轮仅将第22项method_comparison.py的ROOT赋值改为由文件位置定位；其余计算语句、模型参数、阈值与输出数据字符串不变。第34项独立入口只负责副本、路径、参数和运行记录。')
section = re.search(r'22\. Python检验源码/paper_output/code/verification/method_comparison\.py\n.*?(?=\n23\.)', text, re.S).group(0)
new_section = re.sub(r'大小：\d+ 字节', f'大小：{(SUPPORT / changed_source).stat().st_size} 字节', section)
new_section = re.sub(r'(?m)^SHA256：\w+', 'SHA256：' + sha(SUPPORT / changed_source), new_section)
new_section += '\n路径适配前SHA256：' + changes[0]['before'] + '\n本轮修改：仅第11行ROOT赋值；归一化该赋值后AST相同。\n'
text = text.replace(section, new_section)
runner = SUPPORT / 'Python检验源码/run_checks.py'
text += (f'\n34. Python检验源码/run_checks.py\n用途：在指定的新实验根复制输入/源码，调用grid/time/method并记录真实进程退出及SHA\n'
         f'来源：本轮新增独立交付入口，不参与数值求解公式\n大小：{runner.stat().st_size} 字节\nSHA256：{sha(runner)}\n')
checksum_path.write_text(text, encoding='utf-8')

description = SUPPORT / '数值检验说明.txt'
shutil.copy2(description, QA / '数值检验说明.before.txt')
text = description.read_text(encoding='utf-8-sig')
text = text.replace('共有31个Python源文件、1个MATLAB源文件和1个Node.js源文件', '共有32个Python源文件（31个原源码及1个新增独立入口）、1个MATLAB源文件和1个Node.js源文件')
text = text.replace('逐文件用途、原来源和SHA256见“源码文件与校验值.txt”。', '逐文件用途、原来源和SHA256见“源码文件与校验值.txt”。本轮补齐论文采用的三类检验，优先阅读“论文采用检验_独立运行说明.txt”和“本轮补件与运行核验.txt”。')
text = text.replace('这些源码已去注释，仍保留当时的路径、输出结构和数据读取约定。', '原检验源码已去注释，输出结构和数据读取约定保留。本轮仅适配method_comparison.py的根目录一行，其余历史程序的路径限制仍在。')
text = text.replace('Python基本依赖为NumPy和SciPy；compare_analytic、crossvalidate_series、latent_heat_scenarios及publication_plots的绘图部分还需要Matplotlib；原export_outputs依赖openpyxl。实际生产依赖版本以03目录的requirements和运行说明为准。', 'Python检验独立依赖见Python检验源码/requirements.txt：NumPy 2.5.2、SciPy 1.18.1、openpyxl 3.1.5、Matplotlib 3.11.2，配合Python 3.14.7。Matplotlib不仅用于绘图，时间检验监督器也无条件读取其安装版本。03正式生产入口依赖仍以03自己的requirements为准。')
text = text.replace('运行前须在独立实验目录准备所需输入、核对路径及磁盘预算。', '这两CSV已放在上述预期层级；新增run_checks.py会逐字节复制输入及源码到所选新实验根，再运行采用的检验，仍需核对磁盘预算。')
text = text.replace('verification中的若干程序把原本届工作区写为绝对ROOT路径；', 'verification除本轮适配的method_comparison.py外，若干历史程序仍把原本届工作区写为绝对ROOT路径；')
text = text.replace('这些路径适配没有混入本目录候选源码。', '该历史副本的整批路径修改没有移入交付；当前仅method_comparison.py的一行ROOT适配单独采用并重跑，其新证据见本轮补件说明。')
text = text.replace('本轮已完成去注释、逐文件SHA和Python非注释AST检查，', '此前已完成去注释、逐文件SHA和Python非注释AST检查，')
description.write_text(text, encoding='utf-8')

report_text = f'''本轮补件与实际运行核验（2026-09-13）
======================================

范围：只补齐论文采用的网格、固定N时间误差、两种通量方法对照的交付运行条件。

新增run_checks.py、requirements.txt、两CSV及两份TXT说明。原33源码中仅method_comparison.py第11行ROOT赋值变化；其余32份源码逐字节不变。将ROOT赋值归一化后，两版method_comparison.py的AST完全一致。旧独立沙盒矩阵CSV及逐源码核查TXT的SHA256保持原样，原有失败与限制不改写。

环境：本轮在新建的独立venv实际安装CPython 3.14.7所需NumPy 2.5.2、SciPy 1.18.1、openpyxl 3.1.5、Matplotlib 3.11.2。pip install实际exit 0；pip check实际exit 0，输出“No broken requirements found.”。主机原Matplotlib 3.11.1未被冒作本轮依赖版本。

两CSV原值、字节和SHA均与03/inputs/cleaned相同：
{data[0]['path']}：{data[0]['rows']}行，SHA256 {data[0]['sha256']}
{data[1]['path']}：{data[1]['rows']}行，SHA256 {data[1]['sha256']}

本轮三个不同的新实验根实际运行如下（均在支撑目录外，直接调用本目录run_checks.py复制的源码）：

1. 网格：--check grid --question Q1 --grids 20 40
   实际exit 0，耗时{runs['grid']['wall_seconds']:.3f}秒，内部computed_and_zero_solver_warnings。
   1801个整数秒×21半径，N20/N40最大温度差0.0014693875993998518 K，最大含水率差0.046707078419066406。
   与热方程Bessel基准最大误差：N20为0.0019600449535914777 K，N40为0.0004906573541916259 K。
   N20/N40是入口与计算链检查；较大的水分网格差明确表明不能把此小网格视为论文精度通过。

2. 时间：--check time --question Q1 --n 20
   实际exit 0，耗时{runs['time']['wall_seconds']:.3f}秒；baseline与tight两个被监督子进程均实际exit 0，内部computed_zero_solver_warnings。
   同一N20、1801秒×21半径最大温度差1.0329394513064472e-6 K，最大含水率差3.4171576679398186e-9。
   只证明N20的时间控制敏感性检查已实际运行，不替代N3200/N6400论文细网格检查。

3. 方法：--check method --quick
   实际exit 0，耗时{runs['method']['wall_seconds']:.3f}秒，N100/N200共8次求解，8项实际通量路径守卫均吻合。
   常D两种通量最大差均为0；变D在N100差1.4891388507853875e-5、N200差3.728809559122581e-6，小于原1e-4阈值，passedDeclaredTolerance=true。
   此次观察收敛阶1.9976912588688045；源码原expectedOrder=1.0字段未改，不把该字段误作此次实测阶。
   这是原方法对照的quick批次，不冒称本轮重算N200/N400/N800/N1600完整批次。

其他核验：缺CSV的旧层级在独立副本实际复现FileNotFoundError/exit 1；补入后上列三入口成功。--help实际exit 0；支撑目录内部输出及已有输出目录均按预期拒绝（exit 2）。32份Python源码静态编译通过，未发现Python注释。三个运行副本的源码与输入在运行后全部与交付SHA一致。

源码变更：
{changed_source}
适配前SHA256：{changes[0]['before']}
当前SHA256：{changes[0]['after']}
唯一需要同步到已有论文源代码附录的旧程序行：
ROOT = pathlib.Path(__file__).resolve().parents[3]

run_checks.py为新增运行入口，当前SHA256：{sha(runner)}。若论文逐行刊入所有支撑程序，应另加入该入口；完整文件列表必须包括此入口、requirements及两CSV。

原始机器证据位于本届paper_output/qa/support_completion_20260913/verification/：依赖安装日志、pip check、freeze、guard_results、isolated_grid/time/method中的run_result、原数值报告、标准输出以及最终audit.json。它们为内部运行证据，不在本交付目录恢复JSON/Markdown。

本轮无Visual Studio GUI操作，GUI复现和团队人工审查均仍待本人完成；CLI、源码比较和AI审查不代填这些状态。未重算正式四题生产结果、未改变论文采用值、未修改历史弃用试验或其失败状态。
'''
(SUPPORT / '本轮补件与运行核验.txt').write_text(report_text, encoding='utf-8')

files = sorted(p for p in SUPPORT.rglob('*') if p.is_file())
assert not [p for p in files if p.suffix.lower() in ('.json', '.md', '.pyc')]
assert not [p for p in SUPPORT.rglob('*') if p.is_dir() and p.name in ('__pycache__', '.vs')]
audit = {'status': 'PORTABILITY_CHECKS_COMPLETED_WITH_DECLARED_SCOPE', 'source_changes': changes,
         'method_AST_identical_except_ROOT': True, 'old_sources_unchanged': 32,
         'historical_matrix_and_report_unchanged': True, 'python_compile_count': len(code),
         'data': data, 'runs': {k: {'returncode':v['returncode'], 'seconds':v['wall_seconds'],
                                  'runtime':v['runtime'], 'source_input_unchanged':v['source_input_unchanged']} for k,v in runs.items()},
         'grid': {'status':grid['status'], 'comparisons':grid['comparisons']},
         'time': {'status':time['status'], 'comparison':time['comparison']},
         'method': {'levels':method['levels'], 'variableD':method['variableD']},
         'visual_studio_gui':'pending', 'human_review':'pending', 'fine_grid_rerun':False,
         'file_count':len(files), 'bytes':sum(p.stat().st_size for p in files),
         'files':[{'path':p.relative_to(SUPPORT).as_posix(), 'bytes':p.stat().st_size, 'sha256':sha(p)} for p in files]}
(QA / 'audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
(QA / '源码变更与附录同步.txt').write_text(report_text[report_text.index('源码变更：'):report_text.index('原始机器证据')], encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k in ('status','source_changes','method_AST_identical_except_ROOT','old_sources_unchanged','historical_matrix_and_report_unchanged','python_compile_count','file_count','bytes')}, ensure_ascii=False, indent=2))
