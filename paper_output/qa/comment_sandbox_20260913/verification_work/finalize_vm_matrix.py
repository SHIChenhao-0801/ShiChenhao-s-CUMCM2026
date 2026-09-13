import csv
import hashlib
import json
from pathlib import Path


base = Path(__file__).resolve().parent
evidence = base.parent / 'vm_output'
first_folder = evidence / 'verification_matrix'
retry_folder = evidence / 'verification_clean_retry'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def last_json(path):
    lines = Path(path).read_text(encoding='utf-8').splitlines(keepends=True)
    for index in range(len(lines) - 1, -1, -1):
        if lines[index].startswith('{'):
            try:
                return json.loads(''.join(lines[index:]))
            except json.JSONDecodeError:
                pass
    return None


host = read(base / 'host_verification_matrix.json')
first = read(first_folder / 'process_matrix.json')
retry = read(retry_folder / 'matrix/process_matrix.json')
retry_record = read(retry_folder / 'retry_process.json')
environment = read(evidence / 'vm_environment.json')
assert environment['originalHostWorkspaceVisible'] is False
assert retry_record['status'] == 'COMPLETED_QUEUE'
assert retry_record['copiedSourcesAndInputsUnchanged'] is True
assert len(first['results']) == 27 and len(retry['results']) == 6
first_by_job = {item['job']: item for item in first['results']}
retry_by_job = {item['job']: item for item in retry['results']}
source_checks = []
for attempt, matrix in [('first', first), ('clean_retry', retry)]:
    local_sources = [item for item in matrix['sources'] if item['path'].startswith('paper_output/code/')]
    assert len(local_sources) == 31
    for item in local_sources:
        sha = digest(base / 'path_adapted' / item['path'])
        source_checks.append({'attempt': attempt, 'path': item['path'], 'vmSha256': item['sha256'], 'localAdaptedSha256': sha, 'matches': item['sha256'] == sha})
assert all(item['matches'] for item in source_checks)
input_checks = []
for item in retry_record['inputs']:
    sha = digest(base / 'path_adapted' / item['path'])
    input_checks.append({**item, 'matchesLocalExplicitInput': item['sha256'] == sha})
assert len(input_checks) == 38 and all(item['matchesLocalExplicitInput'] for item in input_checks)

failure_classification = {
    'isotherm_old_interface': 'FAIL_OLD_ACTIVITYMODEL_B_ARGUMENT',
    'isotherm_extract': 'FAIL_TIME_SPACE_AXES_INDEX_ERROR',
    'isotherm_probe': 'FAIL_DIAGNOSTIC_INJECTION_NOT_CALLED',
    'series_constant_diagnostic': 'FAIL_CONSTANT_SERIES_FALSE_TREND',
    'production_missing_inputs': 'FAIL_MISSING_REQUIRED_MODEL_ROUTE_INPUT',
}
semantic_classification = {
    'compare_analytic': 'COMPLETED_REVIEW_REQUIRED_DENSE_N400_MISSES_TOLERANCE',
    'series': 'COMPLETED_BUT_CONSTANT_SERIES_NEGATIVE_TEST_FAILS',
    'analytic_metric': 'COMPLETED_BUT_STATIC_INTERPRETATION_CONTRADICTS_REFINEMENT',
    'plot_selfcheck': 'GENERATED_PENDING_VISUAL_REVIEW',
    'energy_diagnose': 'COMPLETED_HISTORICAL_DIAGNOSTIC_NOT_CONSERVATION_PROOF',
    'convergence': 'COMPLETED_SMALL_GRID_COMPARISON_NOT_FINAL_GRID_ACCEPTANCE',
    'time_accuracy': 'COMPLETED_FIXED_SMALL_GRID_TOLERANCE_COMPARISON',
    'axisymmetric': 'COMPLETED_SMALL_GRID_END_FACES_OFF_COMPARISON',
}
process_rows = []
for original in first['results']:
    job = original['job']
    process = retry_by_job.get(job, original)
    folder = retry_folder / 'matrix' if job in retry_by_job else first_folder
    log = folder / (job + '.log')
    classification = failure_classification.get(job, semantic_classification.get(job, 'COMPLETED_WITH_STATED_TEST_SCOPE'))
    if job in retry_by_job:
        original_text = (first_folder / (job + '.log')).read_text(encoding='utf-8')
        assert original['returncode'] == 1 and 'FileExistsError' in original_text
        assert 'FileExistsError' not in log.read_text(encoding='utf-8')
    if process['returncode']:
        assert job in failure_classification
    process_rows.append({'job': job, 'actualExit': process['returncode'], 'classification': classification,
                         'acceptedAttempt': 'clean_retry' if job in retry_by_job else 'first',
                         'process': process, 'log': str(log), 'logSha256': digest(log),
                         'finalLogJson': last_json(log),
                         'firstAttemptExit': original['returncode'],
                         'firstAttemptSetupFailure': 'STALE_COPIED_OUTPUT_DIRECTORY' if job in retry_by_job else None})
assert sum(row['actualExit'] == 0 for row in process_rows) == 22
by_job = {row['job']: row for row in process_rows}
generated = retry_folder / 'first_attempt_generated/paper_output/results'
fresh_results = retry_folder / 'results'
reports = {
    'bessel': generated / 'bessel_validation/bessel_selfcheck.json',
    'jacobian': generated / 'jacobian_validation/analytic_jacobian_selftest.json',
    'method': generated / 'crossvalidation/method_v1/method_comparison.json',
    'analytic': generated / 'analytic_comparison/analytic_comparison_report.json',
    'plots': generated / 'plot_selfcheck/plot_selfcheck_report.json',
    'convergence': fresh_results / 'convergence/sandbox/convergence_report.json',
    'time_accuracy': fresh_results / 'time_accuracy/sandbox/time_accuracy_report.json',
    'storage': fresh_results / 'dense_storage_verification_v6/verification.json',
    'export': fresh_results / 'export_selfcheck/result1.validation.json',
    'axisymmetric': fresh_results / 'axisymmetric_check/Nr6_Nz4_end_off_sandbox/summary.json',
}
values = {name: read(path) for name, path in reports.items()}
assert values['bessel']['status'] == 'PASS' and len(values['bessel']['checks']) == 8
assert values['jacobian']['status'] == 'PASS' and values['jacobian']['case_state_count'] == 84
assert values['jacobian']['direction_count'] == 336 and not values['jacobian']['failures']
assert values['storage']['status'] == 'PASS'
assert all(row['accepted_times_and_states_bitwise_equal'] and row['event_and_endpoint_bitwise_equal'] and row['dense_query_max_difference'] == 0 and row['private_cache_removed_after_close'] for row in values['storage']['runs'])
assert sum(row['query_count'] for row in values['storage']['runs']) == 38337
assert values['export']['status'] == 'PASS' and values['export']['checked_cells'] == 79244
assert values['export']['fully_verified_with_live_Run'] is True and not values['export']['errors']
assert values['analytic']['status'] == 'REVIEW_REQUIRED'
assert values['analytic']['convergence']['dense']['N400_frozen_water_max_error_below_0_0001'] is False
assert values['plots']['status'] == 'GENERATED_PENDING_VISUAL_REVIEW'
assert all(row['process']['returncode'] == 0 for row in values['time_accuracy']['runs'])

remaining_folder = evidence / 'verification_remaining_entries'
remaining = read(remaining_folder / 'processes.json')
assert remaining['status'] == 'COMPLETED' and remaining['sourcesAndInputsUnchanged'] is True
assert len(remaining['results']) == 2 and all(row['returncode'] == 0 for row in remaining['results'])
remaining_source_checks = []
for item in remaining['inputs']:
    remaining_source_checks.append({**item, 'matchesLocalExplicitInput': digest(base / 'path_adapted' / item['path']) == item['sha256']})
assert len(remaining_source_checks) == 33 and all(item['matchesLocalExplicitInput'] for item in remaining_source_checks)
for process in remaining['results']:
    job = process['job']
    log = remaining_folder / (job + '.log')
    by_job[job] = {'job': job, 'actualExit': process['returncode'],
                  'classification': 'COMPLETED_HISTORICAL_DIAGNOSTIC_NOT_CONSERVATION_PROOF' if job == 'energy_diagnose2' else 'COMPLETED_THREE_N20_BASELINE_TRAJECTORIES',
                  'acceptedAttempt': 'remaining_fresh_entries', 'process': process,
                  'log': str(log), 'logSha256': digest(log), 'finalLogJson': last_json(log),
                  'firstAttemptExit': None, 'firstAttemptSetupFailure': None}
trial_records = [read(path) for path in (remaining_folder / 'results/experiments').rglob('trial_record.json')]
assert len(trial_records) == 3 and all(row['status'] == 'computed' and row['exit_code'] == 0 for row in trial_records)
assert all(row['solver_success'] for row in trial_records)
extra = read(remaining_folder / 'native_scope.json')
assert extra['matlabStatus'] == 'NOT_EXECUTED_RUNTIME_UNAVAILABLE' and extra['matlabExecutableFound'] is None
node_process = next(row for row in extra['records'] if row['name'] == 'node_original_worker')
node_log = evidence / 'extra_entries/node_original_worker.log'
assert node_process['returncode'] == 2 and 'runSummary.json' in node_log.read_text(encoding='utf-8')
by_job['node_failure'] = {'job': 'node_failure', 'actualExit': 2, 'classification': 'FAIL_MISSING_REQUIRED_HISTORICAL_RUN_SUMMARY',
                         'acceptedAttempt': 'vm_native_original_candidate', 'process': node_process,
                         'log': str(node_log), 'logSha256': digest(node_log), 'finalLogJson': None}

files = []
for row in host['files']:
    vm_job = by_job.get(row['job'])
    is_python = row['file'].endswith('.py')
    vm_scope = row['status'] if vm_job else '未在本次 VM 执行；见 HOST 记录' if is_python else '未在本次 VM 执行'
    scope = row['scope']
    if row['file'] == 'compareMatlab.mjs':
        assert extra['nodeSourceSha256'] == row['candidateSha256']
        vm_scope = '失败（原候选缺少历史输入）'
        scope = 'Windows Sandbox Node v24.20.0原候选worker实际exit2：缺C:/paper_output/qa/matlab_crosscheck_20260911/runSummary.json；源SHA与无注释候选一致。'
    elif row['file'] == 'runCrossCheck.m':
        vm_scope = '未执行（VM未提供MATLAB运行环境）'
        scope = 'VM中matlab可执行入口查找为空；未运行原M脚本，不能使用Python或Node代替此验证。'
    elif row['file'] == 'run_experiments.py':
        scope = '原入口--batch baseline --n 20 --tag _vm_remaining --face-scheme kirchhoff；三条轨迹均computed，未跑其他批次。'
    files.append({**row, 'hostProcess': row['process'], 'windowsSandboxStatus': vm_scope,
                  'windowsSandboxProcess': vm_job,
                  'windowsSandboxScope': scope,
                  'windowsSandboxTestedSha256': extra['nodeSourceSha256'] if row['file'] == 'compareMatlab.mjs' else row['testedSha256'] if is_python else None,
                  'candidateStillMatchesFrozenHash': digest(row['candidatePath']) == row['candidateSha256']})
assert len(files) == 33 and len({row['file'] for row in files}) == 33
assert all(row['candidateStillMatchesFrozenHash'] for row in files)
assert sum(row['file'].endswith('.py') and row['windowsSandboxProcess'] is not None for row in files) == 31

result = {
    'scope': 'Actual Windows Sandbox VM: 27 original scoped commands; six stale-directory startup failures were retried in a fresh root; two remaining Python entrypoints were run in another clean source-and-CSV-only root; original Node worker also executed.',
    'allSourceCount': 33, 'pythonSourceCount': 31, 'pythonSourcesWithVmExecutionCoverage': 31,
    'pythonSourcesHostOnly': [],
    'matlabVmExecuted': False, 'nodeVmExecuted': True,
    'originalHostWorkspaceVisible': False, 'environment': environment,
    'rootOnlyPathAdaptations': 14, 'candidateModifiedByThisAgent': False,
    'vmOriginalPathProbe': read(evidence / 'verification_original_path_probe.process.json'),
    'firstAttemptProcessCount': 27, 'firstAttemptZeroExits': 17,
    'cleanRetryProcessCount': 6, 'cleanRetryZeroExits': 5,
    'acceptedScopedCommandCount': 27, 'acceptedZeroExits': 22, 'acceptedNonzeroExits': 5,
    'supplementalPythonEntrypoints': remaining['results'],
    'allAcceptedPythonCommands': 29, 'allAcceptedPythonZeroExits': 24, 'allAcceptedPythonNonzeroExits': 5,
    'supplementalSourcesAndInputs': remaining_source_checks, 'extraNativeEvidence': extra,
    'failedJobs': list(failure_classification), 'queueZeroIsNotAllPass': True,
    'retryProcess': retry_record, 'sourceHashChecks': source_checks, 'explicitInputHashChecks': input_checks,
    'reportEvidence': {name: {'path': str(path), 'sha256': digest(path)} for name, path in reports.items()},
    'keyEvidence': {
        'denseQueryCount': 38337, 'denseQueryMaxDifference': 0,
        'exportCheckedWorkbookCells': 79244,
        'analyticDenseFrozenWaterN400Error': values['analytic']['convergence']['dense']['water_max_abs_errors_kg_per_kg'][-1],
        'analyticDenseFrozenWaterN800Error': values['analytic']['convergence']['dense']['N800_frozen_water_max_abs_error'],
        'convergence': values['convergence']['comparisons'],
        'timeAccuracy': values['time_accuracy']['comparison'],
        'axisymmetricEventDifferenceHours': values['axisymmetric']['comparison']['event_difference_h_2d_minus_1d'],
    },
    'processes': list(by_job.values()), 'files': files,
    'limits': ['Small-grid/function tests do not establish every default historical experiment completed.',
               'Copied HOST outputs are not counted as VM execution; the remaining two entrypoints have accepted later fresh-directory evidence.',
               'Original Node worker failed in the VM because required historical inputs are absent; no MATLAB runtime was supplied in the VM.',
               'No model algorithms, scientific thresholds or production results were changed to obtain passing status.',
               'Formal03 full-grid calculations, VS GUI, MATLAB GUI and team review require their separate records.'],
}
(base / 'windows_sandbox_verification_matrix.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
with (base / '05源码独立运行矩阵_WINDOWS_SANDBOX.csv').open('w', encoding='utf-8-sig', newline='') as stream:
    writer = csv.writer(stream)
    writer.writerow(['源码', 'HOST判定', 'HOST退出码', 'Windows Sandbox判定', 'VM退出码', 'VM采用轮次', 'VM范围及局限', '原无注释候选SHA256', 'VM实测源码SHA256'])
    for row in files:
        vm = row['windowsSandboxProcess'] or {}
        writer.writerow([row['file'], row['status'], (row['hostProcess'] or {}).get('returncode', '未执行'), row['windowsSandboxStatus'], vm.get('actualExit', '未执行'), vm.get('acceptedAttempt', ''), row['windowsSandboxScope'], row['candidateSha256'], row['windowsSandboxTestedSha256']])
lines = [
    '05源码独立运行核查（Windows Sandbox 实际运行）',
    '============================================',
    '已完整阅读33份源码：31个Python、1个MATLAB、1个Node.js。本机与Windows Sandbox实测分开记录。',
    '本次VM环境：Windows 11；独立Python 3.14.7、NumPy 2.5.2、SciPy 1.18.1、openpyxl 3.1.5、Matplotlib 3.11.2；网络关闭，原D盘工作区不可见。',
    '原去注释版本先实测旧绝对根路径失败。后续VM数值检查使用仅14处根目录表达式适配的副本，未改物理模型、求解算法或误差门槛。',
    '两CSV、4个附件3工作簿模板及Q23参考NPZ从已冻结材料显式复制；31源码与7输入共38文件SHA均核对，干净重试前后不变。',
    '首轮27项中17项退出0；6项因测试副本误带旧输出目录触发FileExistsError。已在仅含源码/必需输入的全新目录实际重试，5项退出0，1项实际缺model_route.json。首轮记录保留，未将目录准备问题记成模型算法失败。',
    '合并有效轮次后，27项受控任务中22项退出0、5项退出1。退出0只表示进程完成，解析误差、趋势负例、图像状态等继续单独核验，不能写成“全部源码均通过”。',
    '另在只含31源码及两CSV的全新VM目录运行run_experiments.py baseline N20和energy_balance_diagnose2.py原入口，两者实际退出0，前者三条轨迹均computed。合计29项Python受控任务为24项退出0、5项退出1，31个Python源码均有入口/函数实际调用覆盖。首轮拷入的旧输出不计这两项VM结果。',
    '原Node候选在VM Node v24.20.0中实际worker退出2：缺C:/paper_output/qa/matlab_crosscheck_20260911/runSummary.json，源SHA与无注释候选一致。原MATLAB脚本未执行，VM未提供MATLAB运行环境、可执行入口查找为空。不得把Python成功等同MATLAB/Node成功。', '',
    '实际通过的代表性数值证据：',
    'Bessel原8项解析自检通过；解析Jacobian原84状态、336方向、每个方向全部3差分步长及4条短BDF轨迹通过。',
    'N40三问各采用内存/磁盘两种存储完成原自检；接受步、状态、事件及末时刻逐位相同，38337个稠密输出查询差全0，关闭后缓存移除。',
    '原Q1导出自检实际回读79244个工作簿格，并以live Run逐格核验84个正文CSV格，内部PASS。',
    'Q1 N20/N40网格比较、Q1 N20紧容差双子进程、二维nr6/nz4关闭端面比较均实际完成。此处小网格结果不作为正式网格精度验收。', '',
    '仍然存在的真实问题：',
    'run_modeling.py要求的paper_output/plan/model_route.json未随05提供，干净VM实际FileNotFoundError。',
    'isotherm_diagnose.py向ActivityModel传已不存在的B参数，实际TypeError；未把旧B参数强行改释为p。',
    'isotherm_activity_closure.py的_extract把时间×空间数组按相反方向访问，真实fields形状为3×2，第三时点实际IndexError；p=1恒等式/RHS测试通过不消除此失败。',
    'isotherm_jacobian_probe.py实际短时求解完成，但替代Jacobian调用计数为0，诊断注入没有被调用。',
    'crossvalidate_series.py旧sequential_mk对40个相等值给出伪趋势；主入口即使退出0，也不能把这一统计检验称为可靠。',
    'compare_analytic.py内部REVIEW_REQUIRED：密集采样N400冻结扩散水分最大误差2.875083008730961e-4，超过原1e-4门槛；N800为7.158659870798445e-5。未放宽门槛。',
    'analytic_metric_check.py计算的点值/单元平均差随N800→6400逐次减半，但原静态解释称不减少，两者矛盾。',
    'publication_plots.py真实生成4图，内部仍为GENERATED_PENDING_VISUAL_REVIEW；本核查不追加视觉通过声明。', '',
]
for index, row in enumerate(files, 1):
    vm = row['windowsSandboxProcess'] or {}
    lines += [f'{index:02d}. {row["file"]}',
              f'Windows Sandbox：{row["windowsSandboxStatus"]}；退出码={vm.get("actualExit", "未执行")}。',
              row['windowsSandboxScope'],
              f'HOST：{row["status"]}。', '']
lines += ['本报告没有将历史长批次、Morris/Sobol全量、原N800以上批次标成已全部执行。',
          '正式03完整网格、Visual Studio GUI、MATLAB GUI及团队人工审查另见对应证据，不由本报告认证。']
(base / '05源码独立运行核查_WINDOWS_SANDBOX.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(json.dumps({'sourceRows': len(files), 'vmPythonCovered': 31, 'acceptedPrimaryJobs': 27, 'primaryExitZero': 22, 'primaryExitNonzero': 5, 'allPythonJobs': 29, 'allPythonExitZero': 24, 'nodeExit': 2, 'matlab': 'NOT_EXECUTED_RUNTIME_UNAVAILABLE', 'verifiedSourceHashes': 62, 'verifiedRetryInputsAndSources': 38, 'verifiedRemainingInputsAndSources': 33, 'report': str(base / 'windows_sandbox_verification_matrix.json')}, ensure_ascii=False))
