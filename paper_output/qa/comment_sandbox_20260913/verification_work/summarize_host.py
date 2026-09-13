import csv
import hashlib
import json
from pathlib import Path


base = Path(__file__).resolve().parent
root = base / 'path_adapted'
result = root / 'paper_output/results'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


entries = [
    ('drying_core.py', '通过（实际三轨迹N20）', 'q_wrappers', '共用PDE、物性、输入、状态/场查询、保存、诊断、关闭缓存真实调用。'),
    ('analytic_jacobian.py', '通过（完整原自检）', 'jacobian', '84状态、336方向、全部3差分步长及4个短BDF测试，无警告。'),
    ('disk_dense.py', '通过（完整原存储自检）', 'dense_storage', 'N40 Q1/Q23/Q4，接受步与状态逐位相同，38337次稠密查询差值全0，close后缓存清除。'),
    ('q1_model.py', '通过（实际Q1 N20）', 'q_wrappers', '原solve封装；也由时间误差检查实际调用。'),
    ('q2_model.py', '通过（实际Q23 N20）', 'q_wrappers', '原solve封装至严格达标。'),
    ('q3_model.py', '通过（实际共享轨迹泛函）', 'q_wrappers', 'Q23/Q4事件、四位上取及未舍入阈值实际核验。'),
    ('q4_model.py', '通过（实际Q4 N20）', 'q_wrappers', '原收缩solve封装至严格达标。'),
    ('validate_bessel.py', '通过（路径适配后完整原自检）', 'bessel', '8项解析自检全部满足原容差。'),
    ('compare_analytic.py', '运行完成，但原误差门槛未全通过', 'compare_analytic', 'exit0，报告REVIEW_REQUIRED；N400密集采样冻结D水分误差2.875083008730961e-4超过1e-4；N800为7.158659870798445e-5。'),
    ('verify_convergence.py', '通过（原入口Q1小网格）', 'convergence', 'N20/N40两条1800s真实解和1801整数秒×21半径的独立比较；不代替正式网格收敛。'),
    ('verify_time_accuracy.py', '通过（原监督入口Q1 N20）', 'time_accuracy', '基准/紧容差两个真实子进程，退出码、投影、输入/源码快照和原比较链均完成。'),
    ('verify_dense_storage.py', '通过（完整原N40入口）', 'dense_storage', 'Q1/Q23/Q4各两条完整轨迹；3829+16162+18346=38337个查询。'),
    ('run_experiments.py', '通过（原baseline入口N20）', 'run_experiments', '显式参数--batch baseline --n20 --tag _sandbox --face-scheme kirchhoff；三条轨迹均computed，未跑其他批次。'),
    ('production_provenance.py', '通过（完整原tinyfixture自检）', 'provenance', '10项合同与故障注入检查，含真实exit0/exit7子进程；不冒充PDE计算。'),
    ('run_modeling.py', '失败（缺少原要求的输入）', 'production_missing_inputs', '实际exit1：缺paper_output/plan/model_route.json；未删掉要求或虚造路由。'),
    ('export_outputs.py', '通过（原Q1 selfcheck）', 'export_selfcheck', '原N40 Q1解导出后回读79244个工作簿格、84正文CSV格，live Run校验PASS。'),
    ('publication_plots.py', '生成完成（原selfcheck）', 'plot_selfcheck', '三条N40解及4个真实图件已生成，内部状态GENERATED_PENDING_VISUAL_REVIEW；未宣称图像逐页视觉通过。'),
    ('axisymmetric_check.py', '小网格运行完成', 'axisymmetric', '原入口nr6/nz4/end-faces off；2D与1D事件差-1.898558063354964e-7h；不把此小网格当原30×30精度验收。'),
    ('crossvalidate_series.py', '运行完成，但旧M-K算法负例失败', 'series', '显式附带Q23参考NPZ与两CSV；常数序列被旧sequential_mk报告伪趋势，不恢复该方法结论。'),
    ('crossvalidate_solver.py', '通过（Q1 N20函数级实算）', 'crossvalidate_solver_pair', 'runCase分别使用BDF/Radau真实求解；原8/12/10条N800以上默认长批次未运行。'),
    ('threshold_and_scaling_checks.py', '通过（原标度入口及N20阈值函数）', 'threshold_full_small', 'Q23/Q4实际二分事件差8.73e-11/5.82e-11s，严格核验均成立；静态越域可能本次未触发，未列实际失败。'),
    ('method_comparison.py', '通过（完整原quick入口）', 'method_quick', '8条Q1真解；变量D两通量差N100=1.4891388507853875e-5，N200=3.728809559122581e-6，观察阶1.99769，原1e-4门槛通过。'),
    ('latent_heat_scenarios.py', '通过（完整事件单情景函数）', 'latent_single', 'Q23 N20潜热比例.25，真实事件和热湿采样；原8条N800情景并未全部运行。'),
    ('sensitivity_analysis.py', '通过（原N200 control函数）', 'sensitivity_control', '真实两条N200对照事件差6.614868652832229e-7s；未运行Morris 362条或Sobol。'),
    ('isotherm_activity_closure.py', '部分通过、原采样接口失败', 'isotherm_extract', 'p1恒等式与三题RHS差0；真实Run.fields为时间×空间，原_extract C[1,i]在第三时点IndexError。'),
    ('isotherm_diagnose.py', '失败（原历史接口不匹配）', 'isotherm_old_interface', '实际TypeError：ActivityModel构造函数不接受B；也不能擅把B=4.2解释为p=4.2。'),
    ('isotherm_jacobian_probe.py', '计算完成、注入诊断失败', 'isotherm_probe', 'N8/3.6s实际BDF计算成功，但numJacCalls=0，不能把未被调用的替代Jacobian声称为成功。'),
    ('energy_balance_diagnose.py', '原入口运行完成', 'energy_diagnose', 'N50/1h真实诊断；原打印关系是用于查错的历史量，不称能量守恒证明。'),
    ('energy_balance_diagnose2.py', '原入口运行完成', 'energy_diagnose2', 'Q23/Q4 N100各1h，2001/20001/200001点三种积分密度；大累计残差仍存在，符合其诊断作用。'),
    ('energy_balance_check.py', '通过（Q1 N20函数级检查）', 'energy_q1', '瞬时率最大相对偏差4.44e-16，累计残差2.3854515166021883e-4<原1e-3门槛；未扩大到Q23/Q4累计能量。'),
    ('analytic_metric_check.py', '运行完成，但静态解释不符合输出', 'analytic_metric', 'N800→6400点值/单元平均最大差0.00205117→0.00025647K，逐次减半；原interpretation却称不随细化减少。'),
    ('runCrossCheck.m', '未执行（需独立MATLAB环境）', 'matlab_pending', '原相对层级推导失配且05缺CSV；MATLAB GUI运行由根代理另行记录，不用Python结果代替。'),
    ('compareMatlab.mjs', '失败（隔离权限/历史输入缺失）', 'node_failure', 'Node --permission实际旧入口exit2；仅修ROOT后仍exit2，缺runSummary.json等历史MATLAB/Python证据。'),
]
sources = {p.name: p for p in (base.parent / 'candidate/05_数值检验与实验').rglob('*') if p.suffix in ('.py', '.m', '.mjs')}
processes = []
for folder in ('matrix_quick1', 'matrix_numerical1'):
    processes.extend(read(root / folder / 'process_matrix.json')['results'])
by_job = {row['job']: row for row in processes}
by_job['run_experiments'] = {'job': 'run_experiments', 'returncode': 0, 'scope': 'Observed exec tool result 628959; command output explicitly ActualExit=0', 'log': str(root/'matrix_numerical1/run_experiments.log')}
by_job['energy_diagnose2'] = {'job': 'energy_diagnose2', 'returncode': 0, 'scope': 'Observed write_stdin session95683 result00c5d7; command output explicitly ActualExit=0', 'log': str(root/'matrix_numerical1/energy_diagnose2.log')}
by_job['node_failure'] = {'job': 'node_failure', 'returncode': 2, 'pathAdaptedReturncode': 2, 'logs': [str(root/'native/node_unadapted.log'), str(root/'native/node_path_adapted.log')]}
rows = []
for filename, status, job, scope in entries:
    p = sources[filename]
    applied = next((q for q in (root/'paper_output/code').rglob(filename)), None) if p.suffix == '.py' else None
    rows.append({'file': filename, 'candidatePath': str(p), 'candidateSha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                 'testedSha256': hashlib.sha256(applied.read_bytes()).hexdigest() if applied else None,
                 'status': status, 'job': job, 'scope': scope, 'process': by_job.get(job)})
assert len(rows) == 33
guard_events = [json.loads(line) for line in (root/'blocked_access.jsonl').read_text(encoding='utf-8').splitlines()]
report = {'scope': 'HOST clean venv + Python audit hook / Node permission flags. This is not the separate Windows Sandbox VM run.',
          'pythonVersion': '3.14.7', 'numpy': '2.5.2', 'scipy': '1.18.1', 'openpyxl': '3.1.5', 'matplotlib': '3.11.1',
          'pythonSourceCount': 31, 'allSourceCount': 33, 'rootOnlyAdaptations': 14,
          'venvSystemSitePackages': False, 'networkBlockedDuringNumerics': True,
          'unadaptedOldRootObservedExit': 1, 'unadaptedBlockedOldRootEvidence': str(base/'unadapted/blocked_access.jsonl'),
          'matrixCommandCount': 27, 'matrixZeroExits': sum(p['returncode']==0 for p in processes),
          'supplementalPythonEntrypoints': ['run_experiments', 'energy_diagnose2'],
          'nodeObservedFailure': by_job['node_failure'], 'matlabActualRun': False,
          'guardBlockedFontFallbackReads': guard_events, 'files': rows,
          'sourcePlan': str(base/'05_dependencies_and_plan.md'),
          'formal03ProductionRunsAreSeparate': True, 'VS_GUI_and_human_review_not_certified': True}
(base/'host_verification_matrix.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
with (base/'05源码独立运行矩阵_HOST.csv').open('w',encoding='utf-8-sig',newline='') as stream:
    writer=csv.writer(stream)
    writer.writerow(['源码','运行判定','实际任务','实际退出码','范围与局限','候选源码SHA256','实测源码SHA256'])
    for row in rows:
        writer.writerow([row['file'],row['status'],row['job'],(row['process'] or {}).get('returncode','未执行'),row['scope'],row['candidateSha256'],row['testedSha256']])
lines=['05源码独立运行核查（本机受限干净venv）','====================================',
       '本报告并非另行执行的Windows Sandbox虚拟机结果，两者必须分开引用。',
       '已实际阅读33源码；31 Python均有真实入口/函数调用，MATLAB尚未执行，Node真实失败。',
       '原去注释源码在隔离条件下先以实际exit1证明写死旧ROOT；数值实算使用仅14处ROOT适配的隔离副本。',
       '两CSV、4模板和Q23参考NPZ从03显式复制并逐SHA记录，没有直接读取生产工作区。',
       'Python3.14.7，NumPy2.5.2，SciPy1.18.1，openpyxl3.1.5，Matplotlib3.11.1；全新venv不继承site-packages，pip check通过。',
       '审计hook阻止旧工作区/其他用户数据和网络访问，仅允许实验目录写入、运行库和系统字体读取。已记录的字体权限拒绝由Matplotlib自身处理；不扩大读取范围。',
       '27项主矩阵实际22项exit0、5项exit1；另2个Python原入口exit0；Node旧路径及修路径后均exit2。外层exit0仍逐项检查内部报告。','']
for index,row in enumerate(rows,1):
    lines += [f'{index:02d}. {row["file"]}：{row["status"]}',row['scope'],'']
lines += ['未改模型算法、误差阈值和生产结果。Morris/Sobol及原全量高网格历史实验未全部执行。',
          '当前结论不能概括成“所有代码都跑通”。明确问题包括缺model_route、经验闭合旧接口/转置、Jacobian注入未被调用、M-K伪趋势、解析比较门槛未过以及Node历史输入缺失。',
          'core03正式N3200/N6400、Windows Sandbox VM、MATLAB GUI、VS GUI和用户人工审查由相应独立证据另行说明。']
(base/'05源码独立运行核查_HOST.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'files':len(rows),'matrixJobs':len(processes),'zeroExit':sum(p['returncode']==0 for p in processes),'report':str(base/'host_verification_matrix.json')},ensure_ascii=False))
