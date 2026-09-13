"""A题独立复现入口：CPU 求解、四题导出、全量回读及冻结采样对照。"""
from __future__ import annotations
import argparse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import gc
import hashlib
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import sys
import time
import traceback
import warnings

ROOT = Path(__file__).resolve().parent
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
sys.dont_write_bytecode = True
for key in ['TMPDIR', 'TEMP', 'TMP']:
    os.environ[key] = str(ROOT/'tmp/cache/runtime')
(ROOT/'tmp/cache/runtime').mkdir(parents=True, exist_ok=True)


def utcNow():
    return datetime.now(timezone.utc).isoformat()


def writeJson(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def fileRecord(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size, 'sha256': sha256(path)}


class Tee:
    def __init__(self, screen, log):
        self.screen, self.log = screen, log
    def write(self, text):
        self.screen.write(text)
        self.log.write(text)
        self.flush()
        return len(text)
    def flush(self):
        self.screen.flush()
        self.log.flush()


def preflight():
    """检查全部必需包内输入、模板和基准的哈希，不依赖原工作区。"""
    if sys.maxsize <= 2**32:
        raise RuntimeError('Use a 64-bit Python interpreter.')
    manifest = json.loads((ROOT/'input_manifest.json').read_text(encoding='utf-8'))
    checked = []
    for expected in manifest['files']:
        path = (ROOT/expected['path']).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise FileNotFoundError(expected['path'])
        actual = fileRecord(path)
        if actual['sha256'] != expected['sha256']:
            raise AssertionError('Input/reference checksum mismatch: '+expected['path'])
        checked.append(actual)
    import dryingCore
    import exportOutputs
    env, rad = dryingCore.loadInputs()
    if len(env) != 241 or len(rad) != 145:
        raise AssertionError('Observed input row counts differ from audited attachments')
    templates = {qid: exportOutputs.loadTemplate(qid)['sheet_names'] for qid in ['Q1', 'Q2', 'Q3', 'Q4']}
    return {'status': 'PASS', 'observedRows': {'environment':len(env), 'radius':len(rad)},
            'templates': templates, 'checkedFiles': checked}


def compareReference(run, question, summary, output):
    """使用运行前公开的数值容限；严格干燥条件及报告格点另作硬检查。"""
    import numpy as np
    reference = json.loads((ROOT/'reference/numerical_reference.json').read_text(encoding='utf-8'))['questions'][question]
    tolerances = {'T_K':5e-6, 'C':5e-7, 'mean_C':5e-7, 'cumulative_loss':5e-7,
                  'radius_m':1e-10, 'event_s':0.005}
    checks = []
    # Compare every fixed-time reference sample on the original 21 material
    # coordinates. Event-dependent rows are checked separately below.
    with np.load(ROOT/'reference'/question/'sampled_solution.npz', allow_pickle=False) as frozen:
        ts = frozen['times_s']
        event = reference['diagnostics']['event_s']
        mask = ts < min(run.endS, reference['diagnostics']['end_s'])-1e-5
        if event is not None:
            mask &= np.abs(ts-event) > 1e-5
        selected = ts[mask]
        values = {key: [] for key in ['T_K', 'C', 'mean_C', 'cumulative_loss', 'radius_m']}
        for first in range(0, len(selected), 128):
            times = selected[first:first+128]
            T, C = run.fields(times, materialX=frozen['material_x'])
            raw = run.state(times)
            values['T_K'].append(T)
            values['C'].append(C)
            values['mean_C'].append(2*run.model.w@raw[1:-1:2])
            values['cumulative_loss'].append(raw[-1])
            values['radius_m'].append(run.model.radius(times))
        for key, arrays in values.items():
            actual = np.concatenate(arrays, axis=0)
            expected = frozen[key][mask]
            difference = float(np.max(np.abs(actual-expected)))
            if not np.isfinite(actual).all() or difference > tolerances[key]:
                raise AssertionError(f'Frozen reference mismatch {question}/{key}: {difference}')
            checks.append({'array':key, 'valuesCompared':int(actual.size), 'maximumAbsoluteDifference':difference,
                           'absoluteTolerance':tolerances[key], 'status':'PASS'})
        with np.load(output/'sampled_solution.npz', allow_pickle=False) as actual_npz:
            exact = {key:bool(actual_npz[key].shape == frozen[key].shape and
                     np.array_equal(actual_npz[key], frozen[key], equal_nan=True)) for key in frozen.files}
    sample = reference['reproduction_samples']
    T, C = run.fields(sample['times_s'], materialX=sample['material_x'])
    for key, actual in [('T_K', T), ('C', C)]:
        difference = float(np.max(np.abs(actual-np.asarray(sample[key]))))
        if difference > tolerances[key]:
            raise AssertionError('Fixed reproduction sample mismatch: '+question+'/'+key)
        checks.append({'array':'reproduction_samples/'+key, 'maximumAbsoluteDifference':difference,
                       'absoluteTolerance':tolerances[key], 'status':'PASS'})
    if question != 'Q1':
        difference = abs(run.eventS-reference['diagnostics']['event_s'])
        if difference > tolerances['event_s']:
            raise AssertionError('Continuous event mismatch')
        completion = summary['completion']
        if completion['reported_drying_time_h'] != reference['completion']['reported_drying_time_h']:
            raise AssertionError('Strict report time moved to a different 0.0001-hour grid point')
        if not completion['max_C_at_reported_time'] < .15:
            raise AssertionError('Reported state does not satisfy the strict threshold')
        checks.append({'array':'event_s', 'maximumAbsoluteDifference':difference,
                       'absoluteTolerance':tolerances['event_s'], 'status':'PASS',
                       'strictReportGridMatches':True, 'strictUnroundedThreshold':True})
    return {'status':'PASS', 'source':'final_v6a', 'checks':checks,
            'supplementaryExactEqualityOfAllSavedArrays':exact,
            'scope':'Numerical reproducibility, not physical prediction accuracy'}


def runQuestion(question, intervals, output, profile):
    import dryingCore
    import exportOutputs
    import q3Model
    name = {'Q1':'q1Model', 'Q23':'q2Model', 'Q4':'q4Model'}[question]
    run = None
    try:
        print(f'{utcNow()} SOLVE {question} N={intervals}', flush=True)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            run = importlib.import_module(name).solve(intervals)
        if caught:
            raise RuntimeError('Solver warning: '+'; '.join(str(w.message) for w in caught))
        directory = output/question
        summary = dryingCore.saveRun(run, directory)
        summary['solverWarningCount'] = 0
        if question != 'Q1':
            summary['completion'] = q3Model.completion(run)
            if not run.diagnostics()['strictly_dry_at_end']:
                raise AssertionError('Post-event state is not dry')
        writeJson(directory/'summary.json', summary)
        comparison = compareReference(run, question, summary, directory) if profile == 'final' else {
            'status':'NOT_APPLICABLE', 'reason':'N40 quick checks are not the fine-grid numerical result'}
        exports = []
        for qid in (['Q2', 'Q3'] if question == 'Q23' else [question]):
            print(f'{utcNow()} EXPORT_AND_FULL_READBACK {qid}', flush=True)
            artifact = exportOutputs.exportQuestion(run, qid, output/'outputs')
            validation = exportOutputs.validateExports([artifact], runs={qid:run})
            if validation['status'] != 'PASS' or not validation['fully_verified_with_live_Run']:
                raise AssertionError('Workbook/archive/live Run verification failed')
            exports.append(validation)
            print(f'{utcNow()} VERIFIED {qid} cells={validation["exports"][0]["checked_cells"]}', flush=True)
        checks = {'referenceComparison':comparison, 'exports':exports}
        writeJson(directory/'comparison.json', checks)
        return summary, checks
    finally:
        if run is not None:
            run.close()
        gc.collect()
        print(f'{utcNow()} RELEASED {question}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=['quick', 'final'], default='quick')
    parser.add_argument('--run-id', default=None)
    parser.add_argument('--preflight-only', action='store_true')
    args = parser.parse_args()
    run_id = args.run_id or args.profile+'_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', run_id):
        parser.error('run-id may contain only letters, digits, underscore, hyphen')
    output = ROOT/'results'/run_id
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    sources = [fileRecord(path) for path in sorted(ROOT.glob('*.py'))]
    report = {'status':'RUNNING', 'profile':args.profile, 'runId':run_id, 'startedAtUtc':utcNow(),
              'guiReproduced':'NOT_PERFORMED', 'humanReview':'PENDING_USER_REVIEW',
              'environment':{'python':sys.version, 'libraries':{n:importlib.metadata.version(n)
                   for n in ['numpy', 'scipy', 'openpyxl']}, 'cpuThreads':1},
              'sources':sources, 'randomSeed':None, 'deterministic':True,
              'historical107FileRegression':'NOT_RUN_NOT_REQUIRED_FOR_INDEPENDENT_REPRODUCTION'}
    with (output/'stdout.log').open('w', encoding='utf-8') as log:
        with redirect_stdout(Tee(sys.stdout, log)), redirect_stderr(Tee(sys.stderr, log)):
            try:
                report['preflight'] = preflight()
                print(f'{utcNow()} PREFLIGHT PASS profile={args.profile}', flush=True)
                if not args.preflight_only:
                    report['summaries'], report['comparisons'] = {}, {}
                    for q, n in [('Q1', 3200), ('Q23', 3200), ('Q4', 6400)]:
                        report['summaries'][q], report['comparisons'][q] = runQuestion(
                            q, 40 if args.profile == 'quick' else n, output, args.profile)
                if sources != [fileRecord(path) for path in sorted(ROOT.glob('*.py'))]:
                    raise AssertionError('Source changed during run')
                report['status'] = 'PASS'
                print(f'{utcNow()} ALL_REQUESTED_CHECKS_COMPLETED', flush=True)
            except BaseException as error:
                report.update(status='FAIL', error=repr(error))
                traceback.print_exc()
                raise
            finally:
                report.update(finishedAtUtc=utcNow(), elapsedSeconds=time.perf_counter()-started)
                writeJson(output/'runResult.json', report)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
