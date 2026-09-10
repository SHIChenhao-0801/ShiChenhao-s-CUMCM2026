"""N8 小网格验证：驼峰副本与冻结源码的状态、物性、RHS、Jacobian 应逐字节一致。"""
from __future__ import annotations
from dataclasses import asdict
from datetime import datetime, timezone
import importlib
import json
from pathlib import Path
import sys
import time
import warnings

import numpy as np
import scipy

deliveryDir = Path(__file__).resolve().parents[1]
projectRoot = deliveryDir.parents[2]
sys.path.insert(0, str(projectRoot / 'paper_output/code/modeling'))
originalCore = importlib.import_module('drying_core')
originalJacobian = importlib.import_module('analytic_jacobian')
sys.path.insert(0, str(deliveryDir))
reviewCore = importlib.import_module('dryingCore')
reviewJacobian = importlib.import_module('analyticJacobian')
renameReport = json.loads((deliveryDir / 'tools/coreRenameReport.json').read_text(encoding='utf-8'))
renameMap = renameReport['identifierMap']
started = time.perf_counter()
checks = []


def sameArray(label, original, review):
    original = np.asarray(original)
    review = np.asarray(review)
    passed = original.shape == review.shape and original.dtype == review.dtype and original.tobytes() == review.tobytes()
    checks.append({'label': label, 'shape': list(original.shape), 'bitwiseIdentical': passed,
                   'maxAbsDifference': float(np.max(np.abs(original - review))) if original.size else 0.0})
    if not passed:
        raise AssertionError(label)


def reviewSettings(original):
    return reviewCore.Settings(**{renameMap.get(key, key): value for key, value in asdict(original).items()})


with warnings.catch_warnings(record=True) as captured:
    warnings.simplefilter('always')
    for question in ('Q1', 'Q23', 'Q4'):
        settings = originalCore.Settings(question=question, intervals=8, face_scheme='kirchhoff', shrink=question == 'Q4')
        originalModel = originalCore.RadialModel(settings)
        reviewModel = reviewCore.RadialModel(reviewSettings(settings))
        for stateLabel in ('initial', 'nonuniform', 'nearUniform'):
            state = originalModel.initial()
            if stateLabel != 'initial':
                state[:-1:2] = 303.0 + 17.0 * originalModel.x ** 2
                state[1:-1:2] = (2.4 - 2.0 * originalModel.x ** 2 if stateLabel == 'nonuniform'
                                  else 0.15 + 1e-10 * originalModel.x)
            prefix = question + '/' + stateLabel
            sameArray(prefix + '/rhs', originalModel.rhs(18000.0, state), reviewModel.rhs(18000.0, state))
            sameArray(prefix + '/jacobian', originalJacobian.jacobian(originalModel, 18000.0, state).toarray(),
                      reviewJacobian.jacobian(reviewModel, 18000.0, state).toarray())
            for index, (left, right) in enumerate(zip(originalModel.properties(state[:-1:2], state[1:-1:2]),
                                                     reviewModel.properties(state[:-1:2], state[1:-1:2]))):
                sameArray(prefix + '/property' + str(index), left, right)

    runRecords = []
    for storage in ('memory', 'disk'):
        settings = originalCore.Settings(question='Q1', intervals=8, face_scheme='kirchhoff',
                                         rtol=1e-10, atol_temperature=1e-10, atol_moisture=1e-12,
                                         early_max_step_s=2.0, max_step_s=120.0, dense_storage=storage)
        originalRun = originalCore.solve_case(settings)
        reviewRun = reviewCore.solveCase(reviewSettings(settings))
        try:
            for index, (left, right) in enumerate(zip(originalRun.pieces, reviewRun.pieces)):
                sameArray(storage + '/acceptedTimes' + str(index), left.t, right.t)
                sameArray(storage + '/acceptedStates' + str(index), left.y, right.y)
            knots = np.unique(np.concatenate([piece.t for piece in originalRun.pieces]))
            times = np.unique(np.concatenate((knots, np.nextafter(knots[1:], -np.inf),
                                              np.nextafter(knots[:-1], np.inf), np.arange(0.0, 1801.0, 30.0))))
            sameArray(storage + '/denseQuery', originalRun.state(times), reviewRun.state(times))
            for index, (left, right) in enumerate(zip(originalRun.fields([0.0, 60.0, 1800.0], radii_m=[0.0, 0.01, 0.02]),
                                                     reviewRun.fields([0.0, 60.0, 1800.0], radiiM=[0.0, 0.01, 0.02]))):
                sameArray(storage + '/physicalFields' + str(index), left, right)
            runRecords.append({'question': 'Q1', 'intervals': 8, 'storage': storage,
                               'reviewDiagnostics': reviewRun.diagnostics(), 'denseQueryCount': len(times)})
        finally:
            originalRun.close()
            reviewRun.close()

messages = [str(item.message) for item in captured]
report = {'status': 'PASS' if not messages else 'FAIL', 'createdUtc': datetime.now(timezone.utc).isoformat(),
          'runtime': {'python': sys.version, 'executable': sys.executable, 'numpy': np.__version__, 'scipy': scipy.__version__},
          'elapsedS': time.perf_counter() - started, 'checks': checks, 'runs': runRecords,
          'warnings': messages, 'allChecksBitwiseIdentical': all(item['bitwiseIdentical'] for item in checks),
          'limitations': ['N8 rename/storage compatibility only; not production grid accuracy',
                          'CLI run only; Visual Studio GUI and user review not asserted'],
          'humanReview': 'pending', 'guiReproduced': False}
runtimeDir = deliveryDir / 'runtime'
runtimeDir.mkdir(exist_ok=True)
(runtimeDir / 'coreRenameVerification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': report['status'], 'checks': len(checks), 'warnings': len(messages),
                  'elapsedS': report['elapsedS'], 'allChecksBitwiseIdentical': report['allChecksBitwiseIdentical']}))
raise SystemExit(0 if report['status'] == 'PASS' else 1)
