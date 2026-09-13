"""Supervised, versioned production and Visual Studio reproduction of A.

The parent snapshots inputs, observes the actual worker exit, and publishes only
verified contracts. The worker retains one Run; Q2/Q3 share Q23 before close().
--review runs fresh solves; --review-exports also repeats the complete exports.
GUI and human acceptance need
separate observed evidence and are never certified by this script.
"""
from __future__ import annotations

import gc
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import uuid
import warnings

SOURCE = Path(__file__).resolve()
ROOT = SOURCE.parents[3]
LOADED_CODE_SHA256 = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
import production_provenance as provenance

ASSUMPTIONS = [
    '一维径向有效模型，忽略轴向/端面基线，以二维独立程序检验端面影响。',
    '题给rho*cp作为有效体积显热容量；不强制它等于守恒骨架的真实湿质量密度。',
    '附件烘房kg/kg数值直接作为材料干基等效Ceq；这不是已证明的气固吸附平衡换算。',
    '基线不显式加入潜热；给定等效驱动力的潜热试验仅是能量负荷压力测试。',
    '前4h采用原始线性插值，4h后Tair=50摄氏度、Ceq=0.05作为长期延拓假设。',
    'Q4固定长度并采用同比径向材料收缩，半径轨迹来自附件2而非模型预测。',
    'Q2/Q3从t=0统一附录3；Q4从t=0整组改用附录4；h和beta沿用题给值。',
]
LIMITATIONS = [
    '没有内部温度/水分实测真值，数值校核不构成实测预测精度认证。',
    '密度、气固湿度映射、潜热闭合和外生收缩是模型解释边界，需团队主导确认。',
    '四位小数为输出格式；网格比较是采样差值，不能冒称连续解严格误差上界。',
    'Visual Studio复现与用户人工代码审查分别留有独立状态。',
]
CONTRACT_TARGETS = {
    'model_results.json': 'paper_output/results/model_results.json',
    'metrics.json': 'paper_output/results/metrics.json',
    'conclusions.json': 'paper_output/results/conclusions.json',
    'table_index.json': 'paper_output/tables/table_index.json',
    'figure_index.json': 'paper_output/figure_index.json',
}


def dependencies():
    # Inventory also covers disk_dense and future local helper modules. Being
    # inventoried is not a claim that a script was actually executed.
    paths = list(SOURCE.parent.glob('*.py'))
    paths += [ROOT / 'paper_output/data_cleaned' / name for name in
              ('A_environment_observed.csv', 'A_radius_observed.csv')]
    paths += [ROOT / 'paper_output/plan/model_route.json']
    paths += list((ROOT / 'problem_files/CUMCM2026Problems/A题').rglob('*.xlsx'))
    return [provenance.file_record(path) for path in sorted(set(paths))]


def font_record():
    font = Path('C:/Windows/Fonts/msyh.ttc')
    return {'path': str(font), 'bytes': font.stat().st_size, 'sha256': provenance.sha256(font)}


def assert_dependencies(start):
    if dependencies() != start['input_files']:
        raise RuntimeError('Source/input inventory changed after launch')
    if font_record() != start['font']:
        raise RuntimeError('Rendering font changed after launch')
    if provenance.runtime_record() != start['runtime']:
        raise RuntimeError('Runtime environment changed after launch')
    expected = {rec['path']: rec['sha256'] for rec in start['input_files']}
    for path, loaded in ((SOURCE, LOADED_CODE_SHA256), (provenance.SOURCE, provenance.LOADED_CODE_SHA256)):
        if loaded != expected[path.relative_to(ROOT).as_posix()]:
            raise RuntimeError('Loaded entry/provenance module differs from launch snapshot')


def imported_model_records():
    paths = set()
    for module in list(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename:
            path = Path(filename).resolve()
            if path.is_relative_to(SOURCE.parent) and path.suffix == '.py':
                paths.add(path)
    return [provenance.file_record(path) for path in sorted(paths)]


def question_plot(plots, run, qid, directory):
    public = getattr(plots, 'make_question_plot', None)
    if callable(public):
        return public(run, qid, directory)
    name = '_profiles' if qid in ('Q1', 'Q2') else '_drying'
    function = getattr(plots, name, None)
    if not callable(function):
        raise RuntimeError('Publication plot API is missing: ' + name)
    return function(run, qid, directory)


def describe_question(qid, key, summary, export, figure, args, directory, start):
    sample = summary['metric_samples'][qid]
    T, C, sampletime = sample['T_K'][0], sample['C'][0], sample['time_s']
    result_text = (f'在t={sampletime/3600:.4f}h，中心/表面温度分别为'
        f'{T[0]-273.15:.4f}/{T[1]-273.15:.4f}摄氏度，干基含水率为'
        f'{C[0]:.4f}/{C[1]:.4f}kg/kg。')
    if qid in ('Q3', 'Q4'):
        done = summary['completion']
        result_text = (f'连续临界时刻{done["critical_event_h"]:.9f}h；向上到四位小数并复核后'
            f'报告{done["reported_drying_time_h"]:.4f}h，原精度最大含水率'
            f'{done["max_C_at_reported_time"]:.12f}<0.15kg/kg。')
    artifacts = [rec['path'] for rec in export['artifacts']] + [export['validation_report']['path']]
    artifacts += [rec['path'] for rec in provenance.figure_artifact_records(figure)]
    artifacts = sorted(set(artifacts))
    source = next(rec for rec in start['input_files'] if rec['path'] == SOURCE.relative_to(ROOT).as_posix())
    question = {'question_id': qid, 'status': 'computed', 'source_run_id': args.version,
        'source_trajectory_id': args.version + ':' + key,
        'model_name': '圆柱有效显热与干基扩散；守恒有限体积、Kirchhoff面通量、解析Jacobian BDF',
        'result_summary': result_text, 'result_files': artifacts,
        'execution_provenance': {'source_code_path': source['path'], 'source_code_sha256': source['sha256'],
            'run_command': start['worker_command'], 'run_exit_code': None,
            'process_status': 'awaiting_parent_observed_exit', 'output_artifacts': artifacts},
        'assumptions_used': ASSUMPTIONS, 'limitations': LIMITATIONS, 'validation_summary': summary}
    values = [
        ('mass_balance_absolute_residual', summary['diagnostics']['max_mass_balance_abs_kg_per_kg'], 'kg/kg',
         '离散干物质基准下，平均C与累计流出之和减初值。', '/diagnostics/max_mass_balance_abs_kg_per_kg'),
        ('radial_intervals', summary['settings']['intervals'], '1', '实际求解空间分辨率。', '/settings/intervals'),
        ('center_C_at_report_time', C[0], 'kg/kg', '已记录指定时刻的中心含水率。', f'/metric_samples/{qid}/C/0/0'),
    ]
    if qid in ('Q3', 'Q4'):
        values.append(('reported_drying_time', summary['completion']['reported_drying_time_h'], 'h',
            '向上取四位小数并用原精度最大值验证严格阈值。', '/completion/reported_drying_time_h'))
    evidence = (directory / key / 'summary.json').relative_to(ROOT).as_posix()
    metrics = [{'question_id': qid, 'metric_name': name, 'metric_role': 'numerical_result',
        'value': value, 'unit': unit, 'status': 'computed', 'evidence_path': evidence,
        'evidence_json_pointer': pointer, 'question_report_time_s': sampletime, 'interpretation': interpretation}
        for name, value, unit, interpretation, pointer in values]
    conclusion = {'question_id': qid, 'conclusion_text': result_text, 'status': 'computed',
        'supporting_metrics': [value[0] for value in values], 'supporting_artifacts': artifacts,
        'assumptions': ASSUMPTIONS, 'limitations': LIMITATIONS}
    return question, metrics, conclusion


def worker(args, directory, start):
    assert_dependencies(start)
    import numpy as np
    core = importlib.import_module('drying_core')
    modules = {key: importlib.import_module(name) for key, name in
               [('Q1', 'q1_model'), ('Q23', 'q2_model'), ('Q4', 'q4_model')]}
    completion = importlib.import_module('q3_model').completion
    solve_only_review = args.review and not getattr(args, 'review_exports', False)
    exporter = None if solve_only_review else importlib.import_module('export_outputs')
    plots = None if solve_only_review else importlib.import_module('publication_plots')
    if core.ROOT.resolve() != ROOT:
        raise RuntimeError('Core workspace differs from production workspace')
    # The pre/post checks enclose imports; model APIs also enforce their loaded hashes.
    assert_dependencies(start)
    imported = imported_model_records()
    started, timer = provenance.utc_now(), time.perf_counter()
    summaries, exports, tables, figures, export_checks = {}, [], [], [], []
    questions, metrics, conclusions = [], [], []
    for name, n, qids in [('Q1', args.n1, ['Q1']), ('Q23', args.n23, ['Q2', 'Q3']),
                          ('Q4', args.n4, ['Q4'])]:
        run = None
        try:
            print(f'SOLVE {name} N={n} UTC={provenance.utc_now()}', flush=True)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                run = modules[name].solve(n)
            if caught:
                raise RuntimeError('Solver warning: ' + '; '.join(str(item.message) for item in caught))
            summary = core.save_run(run, directory / name)
            summary['solver_warning_count'] = len(caught)
            summary['source_run_id'] = args.version
            summary['source_trajectory_id'] = args.version + ':' + name
            if name != 'Q1':
                summary['completion'] = completion(run)
            times = np.unique(np.array([0., min(1800., run.end_s), min(10800., run.end_s), run.end_s] +
                ([] if name == 'Q1' else [summary['completion']['reported_time_s']])))
            T, C = run.fields(times, material_x=np.array([0., .25, .5, .75, 1.]))
            summary['reproduction_samples'] = {'times_s': times.tolist(),
                'material_x': [0., .25, .5, .75, 1.], 'T_K': T.tolist(), 'C': C.tolist()}
            summary['metric_samples'] = {}
            for qid in qids:
                sampletime = 1800. if qid == 'Q1' else 10800. if qid == 'Q2' else summary['completion']['reported_time_s']
                T, C = run.fields([sampletime], material_x=[0., 1.])
                summary['metric_samples'][qid] = {'time_s': sampletime, 'material_x': [0., 1.],
                    'T_K': T.tolist(), 'C': C.tolist(), 'source': 'live_Run_dense_solution'}
            provenance.write_json(directory / name / 'summary.json', summary)
            summaries[name] = summary
            print(json.dumps({'question': name, **summary['diagnostics']}, ensure_ascii=False), flush=True)
            if solve_only_review:
                continue
            for qid in qids:
                print('EXPORT ' + qid, flush=True)
                export = exporter.export_question(run, qid, directory / 'outputs')
                check = exporter.validate_exports([export], runs={qid: run})
                if check.get('status') != 'PASS' or not check.get('fully_verified_with_live_Run'):
                    raise RuntimeError('Export did not pass live Run validation: ' + qid)
                export['validation_report'] = provenance.file_record(check['exports'][0]['report_path'])
                export['validation_status'] = 'PASS'
                export_checks.append(check)
                exports.append(export)
                for rec in export['artifacts']:
                    if rec.get('role') in ('paper_table', 'paper_surface_coordinates'):
                        tables.append({'table_id': Path(rec['path']).stem, 'question_id': qid,
                            'title': Path(rec['path']).stem, 'purpose': '题目指定正文位置/时间采样',
                            **provenance.file_record(ROOT / rec['path']), 'status': 'computed',
                            'placeholder': False, 'ok': True, 'source_run_id': args.version,
                            'source_trajectory_id': args.version + ':' + name})
                print('PLOT ' + qid, flush=True)
                figure = question_plot(plots, run, qid, directory / 'figures')
                figure.update({'status': 'computed', 'placeholder': False, 'ok': True,
                    'source_run_id': args.version, 'source_trajectory_id': args.version + ':' + name})
                figures.append(figure)
                question, question_metrics, conclusion = describe_question(
                    qid, name, summary, export, figure, args, directory, start)
                questions.append(question)
                metrics.extend(question_metrics)
                conclusions.append(conclusion)
                print(json.dumps({'question': qid, 'export_size': export['size'], 'validation': check['status']},
                                 ensure_ascii=False), flush=True)
        finally:
            if run is not None:
                close = getattr(run, 'close', None)
                try:
                    if callable(close):
                        close()
                finally:
                    close = None  # A bound close method otherwise retains its Run.
                    run = None
                    gc.collect()
            print('RELEASED ' + name, flush=True)
    assert_dependencies(start)
    provenance.assert_records(imported)
    provenance.write_json(directory / 'numerical_summaries.json', summaries)
    if args.review:
        provenance.write_json(directory / 'review_result.json', {
            'status': 'COMPUTED_PENDING_GUI_OBSERVATION',
            'mode': 'independent_actual_resolve_and_full_exports' if args.review_exports else 'independent_actual_resolve',
            'source': provenance.file_record(SOURCE),
            'inputs': start['input_files'], 'runtime': start['runtime'], 'imported_model_modules': imported,
            'started_at': started, 'finished_at': provenance.utc_now(), 'summaries': summaries,
            'exports': exports, 'export_checks': export_checks, 'figures': figures,
            'elapsed_s': time.perf_counter() - timer,
            'visual_studio_gui': 'Requires separate observed GUI evidence', 'human_review': 'pending'})
        print('REPRODUCTION_SOLVES_COMPLETED', flush=True)
    else:
        provenance.write_json(directory / 'metric_evidence_validation.json', provenance.validate_metric_evidence(metrics))
        provenance.write_json(directory / 'export_validation.json', {'status': 'PASS', 'checks': export_checks})
        meta = {'schema_version': '1.0', 'generated_by': SOURCE.relative_to(ROOT).as_posix(),
            'generated_at': provenance.utc_now(), 'source_run_id': args.version,
            'publication_state': 'version_only_awaiting_parent_observed_exit'}
        contracts = {'model_results.json': {**meta, 'questions': questions},
            'metrics.json': {**meta, 'items': metrics}, 'conclusions.json': {**meta, 'items': conclusions},
            'table_index.json': {**meta, 'tables': tables}, 'figure_index.json': {**meta, 'figures': figures}}
        for filename, content in contracts.items():
            provenance.write_json(directory / 'contracts' / filename, content)
    assert_dependencies(start)
    output_paths = [p for p in directory.rglob('*') if p.is_file() and p.name not in
                    ('stdout.log', 'worker_success.json', 'process_result.json')]
    provenance.write_json(directory / 'worker_success.json', {
        'started_at': started, 'finished_at': provenance.utc_now(), 'elapsed_seconds': time.perf_counter() - timer,
        'input_files': start['input_files'], 'runtime': start['runtime'], 'font': start['font'],
        'imported_model_modules': imported, 'output_artifacts': [provenance.file_record(p) for p in sorted(output_paths)],
        'question_ids': ['Q1', 'Q2', 'Q3', 'Q4'], 'summaries': summaries, 'exports': exports,
        'mode': 'review' if args.review else 'production', 'human_review': 'pending', 'visual_studio_gui': 'pending'})
    print('ALL_SOLVES_AND_REQUESTED_VALIDATIONS_COMPLETED', flush=True)


def publish(args, directory, start, success, process):
    assert_dependencies(start)
    provenance.assert_records(success['output_artifacts'])
    with provenance.publication_lock(ROOT, args.version):
        contracts = {name: json.loads((directory / 'contracts' / name).read_text(encoding='utf-8'))
                     for name in CONTRACT_TARGETS}
        for data in contracts.values():
            data['publication_state'] = 'parent_verified_actual_worker_exit_zero'
        for question in contracts['model_results.json']['questions']:
            question['execution_provenance'].update({'run_exit_code': process['returncode'],
                'process_status': 'parent_observed_exit_zero',
                'process_evidence_path': (directory / 'process_result.json').relative_to(ROOT).as_posix()})
        index_path = ROOT / 'paper_output/figure_index.json'
        prior = json.loads(index_path.read_text(encoding='utf-8')) if index_path.exists() else None
        merged, merge_note = provenance.merge_figure_index(prior, contracts['figure_index.json']['figures'])
        contracts['figure_index.json']['figures'] = merged
        contracts['figure_index.json']['merge_record'] = merge_note
        provenance.validate_metric_evidence(contracts['metrics.json']['items'])
        published = directory / 'published_contracts'
        for name, content in contracts.items():
            provenance.write_json(published / name, content)
        records = {rec['path']: rec for rec in success['output_artifacts']}
        for path in [directory / 'worker_success.json', directory / 'stdout.log', directory / 'process_result.json']:
            rec = provenance.file_record(path)
            records[rec['path']] = rec
        for name in CONTRACT_TARGETS:
            rec = provenance.file_record(published / name)
            records[rec['path']] = rec
            # The transaction verifies the real global bytes before committing PASS.
            target = {**rec, 'path': CONTRACT_TARGETS[name]}
            records[target['path']] = target
        for figure in merged:
            for rec in provenance.figure_artifact_records(figure):
                records[rec['path']] = rec
        assert_dependencies(start)
        source = next(rec for rec in start['input_files'] if rec['path'] == SOURCE.relative_to(ROOT).as_posix())
        record = {'run_id': args.version, 'script': source['path'], 'script_sha256': source['sha256'],
            'command': process['command'], 'question_ids': success['question_ids'],
            'returncode': process['returncode'], 'cwd': str(ROOT), 'process': process,
            'started_at': process['started_at'], 'finished_at': process['finished_at'],
            'worker_started_at': success['started_at'], 'worker_finished_at': success['finished_at'],
            'elapsed_seconds': success['elapsed_seconds'], 'python': start['runtime'], 'font': start['font'],
            'input_files': start['input_files'], 'imported_model_modules': success['imported_model_modules'],
            'output_artifacts': [records[path] for path in sorted(records)],
            'version_contract_directory': published.relative_to(ROOT).as_posix(),
            'human_review': 'pending', 'visual_studio_gui': 'pending'}
        manifest = {'schema_version': '1.0', 'generated_by': SOURCE.relative_to(ROOT).as_posix(),
            'generated_at': provenance.utc_now(), 'status': 'PASS', 'runs': [record],
            'scope': 'Actual worker exit zero, source/input/output hashes and export checks; not human model acceptance.'}
        provenance.publish_transaction(ROOT, directory,
            {CONTRACT_TARGETS[name]: data for name, data in contracts.items()}, manifest)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    parser.add_argument('--n1', type=int, default=3200)
    parser.add_argument('--n23', type=int, default=3200)
    parser.add_argument('--n4', type=int, default=6400)
    parser.add_argument('--blas-threads', type=int, default=1)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--launch-token', help=argparse.SUPPRESS)
    parser.add_argument('--review', action='store_true')
    parser.add_argument('--review-exports', action='store_true',
        help='With --review, also reproduce all Excel/CSV readbacks and figures in the GUI process')
    args = parser.parse_args()
    if args.review_exports and not args.review:
        raise ValueError('--review-exports requires --review')
    if args.blas_threads < 1:
        raise ValueError('BLAS thread count must be positive')
    # These are task-process settings, before the lazy NumPy/SciPy imports.
    # No global Windows environment or registry setting is modified.
    os.environ['OPENBLAS_NUM_THREADS'] = str(args.blas_threads)
    os.environ['OMP_NUM_THREADS'] = str(args.blas_threads)
    if Path.cwd().resolve() != ROOT:
        raise RuntimeError('Run with the competition workspace as cwd')
    if not args.version or any(ch not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for ch in args.version):
        raise ValueError('Use a simple version label')
    if min(args.n1, args.n23, args.n4) < 2:
        raise ValueError('All radial interval counts must be at least 2')
    directory = ROOT / ('paper_output/results/gui_reproduction' if args.review else
                        'paper_output/results/production') / args.version
    if args.worker:
        if args.review:
            raise ValueError('--review uses a single process so Visual Studio can hit solver breakpoints')
        start = json.loads((directory / 'launch.json').read_text(encoding='utf-8'))
        config = {'n1': args.n1, 'n23': args.n23, 'n4': args.n4, 'review': args.review,
                  'review_exports': args.review_exports,
                  'blas_threads': args.blas_threads}
        if not args.launch_token or args.launch_token != start['launch_token'] or config != start['configuration']:
            raise RuntimeError('Worker must be launched by its matching supervising parent')
        provenance.exclusive_json(directory / 'worker_started.json', {'pid': os.getpid(), 'started_at': provenance.utc_now()})
        print('WORKER_PID=' + str(os.getpid()), flush=True)
        try:
            worker(args, directory, start)
        except BaseException as error:
            provenance.write_json(directory / 'worker_failure.json', {'status': 'FAIL', 'error': repr(error),
                'traceback': traceback.format_exc(), 'generated_at': provenance.utc_now(),
                'returncode': None, 'returncode_note': 'Supervising parent records the actual process exit.'})
            raise
        return 0
    if args.launch_token:
        raise ValueError('--launch-token is reserved for the supervised worker')
    directory.parent.mkdir(parents=True, exist_ok=True)
    directory.mkdir(exist_ok=False)  # Atomic claim; failed versions also remain immutable.
    token = uuid.uuid4().hex
    provenance.exclusive_json(directory / 'launch_claim.json', {'parent_pid': os.getpid(),
        'run_id': args.version, 'claimed_at': provenance.utc_now(), 'launch_token': token})
    process = None
    try:
        command = [sys.executable, '-B', str(SOURCE), '--version', args.version,
            '--n1', str(args.n1), '--n23', str(args.n23), '--n4', str(args.n4),
            '--blas-threads', str(args.blas_threads)]
        if args.review:
            command.append('--review')
            if args.review_exports:
                command.append('--review-exports')
        else:
            command += ['--worker', '--launch-token', token]
        start = {'run_id': args.version, 'parent_pid': os.getpid(), 'launch_token': token,
            'created_at': provenance.utc_now(), 'configuration': {'n1': args.n1, 'n23': args.n23,
                'n4': args.n4, 'review': args.review, 'review_exports': args.review_exports,
                'blas_threads': args.blas_threads}, 'input_files': dependencies(),
            'runtime': provenance.runtime_record(), 'font': font_record(),
            'worker_command': subprocess.list2cmdline(command), 'worker_argv': command,
            'dependency_scope': 'Local module inventory plus A inputs/templates and route; inventory does not claim execution.'}
        assert_dependencies(start)
        provenance.exclusive_json(directory / 'launch.json', start)
        if args.review:
            # Direct execution is deliberate: VS F5 can hit core/wrapper
            # breakpoints without attaching to a child process. An observed
            # application exit is supplied separately by the GUI operator.
            provenance.exclusive_json(directory / 'review_started.json', {
                'pid': os.getpid(), 'started_at': provenance.utc_now(), 'mode': 'single_process_VS_review'})
            worker(args, directory, start)
            assert_dependencies(start)
            success = json.loads((directory / 'worker_success.json').read_text(encoding='utf-8'))
            provenance.assert_records(success['output_artifacts'])
            provenance.write_json(directory / 'review_evidence_validation.json', {
                'status': 'COMPUTED_PENDING_GUI_OBSERVATION', 'input_files': start['input_files'],
                'worker_success': provenance.file_record(directory / 'worker_success.json'),
                'scope': 'Direct solve function and saved hashes checked; no process exit code is self-certified.',
                'visual_studio_gui': 'pending', 'human_review': 'pending'})
            print('REVIEW_FUNCTION_COMPLETED; GUI_OBSERVATION_AND_ACTUAL_EXIT_NOT_SELF_CERTIFIED', flush=True)
            return 0
        process = provenance.measured_process(command, ROOT, directory / 'stdout.log')
        provenance.write_json(directory / 'process_result.json', process)
        if process['returncode'] != 0:
            raise RuntimeError('Worker failed with actual return code ' + str(process['returncode']))
        assert_dependencies(start)
        success = json.loads((directory / 'worker_success.json').read_text(encoding='utf-8'))
        if success['input_files'] != start['input_files'] or success['runtime'] != start['runtime']:
            raise RuntimeError('Worker success differs from launch snapshot')
        provenance.assert_records(success['output_artifacts'])
        publish(args, directory, start, success, process)
        print('ACTUAL_WORKER_RETURN_CODE=0; VERIFIED_RUN_MANIFEST_PUBLISHED', flush=True)
        return 0
    except BaseException as error:
        if process is None and (directory / 'process_result.json').exists():
            process = json.loads((directory / 'process_result.json').read_text(encoding='utf-8'))
        provenance.write_json(directory / 'parent_failure.json', {'status': 'FAIL',
            'generated_at': provenance.utc_now(), 'error': repr(error), 'traceback': traceback.format_exc(),
            'actual_worker_returncode': None if process is None else process['returncode'],
            'process': process, 'version_is_retained': True,
            'publication_note': 'Worker does not publish global contracts; publication failure records rollback.'})
        raise


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
