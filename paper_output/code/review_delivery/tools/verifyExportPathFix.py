"""实际 N40 Q3/Q4 导出、完整回读与 live Run 验证；只验元数据路径修复。"""
from __future__ import annotations
import ast
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import sys
import time
import warnings

deliveryDir = Path(__file__).resolve().parents[1]
projectRoot = deliveryDir.parents[2]
sys.path.insert(0, str(deliveryDir))
import exportOutputs
import q2Model
import q4Model

runtimeDir = deliveryDir / 'runtime/exportPathFix_v2'
runtimeDir.mkdir(parents=True, exist_ok=False)
startedAtUtc = datetime.now(timezone.utc).isoformat()
timer = time.perf_counter()


def record(filePath):
    content = filePath.read_bytes()
    return {'path': filePath.relative_to(projectRoot).as_posix(), 'bytes': len(content),
            'sha256': hashlib.sha256(content).hexdigest()}


beforeReport = json.loads((deliveryDir / 'tools/exportPathFixBefore/coreRenameReport_v1.json').read_text(encoding='utf-8'))
afterReport = json.loads((deliveryDir / 'tools/coreRenameReport.json').read_text(encoding='utf-8'))
unchangedModules = []
for before, after in zip(beforeReport['files'], afterReport['files']):
    if Path(after['reviewPath']).name != 'exportOutputs.py':
        assert before['reviewSha256'] == after['reviewSha256'] == record(projectRoot / after['reviewPath'])['sha256']
        unchangedModules.append(after['reviewPath'])

beforeText = (deliveryDir / 'tools/exportPathFixBefore/exportOutputs_v1.py.txt').read_text(encoding='utf-8')
afterText = (deliveryDir / 'exportOutputs.py').read_text(encoding='utf-8')
assert afterText == beforeText.replace("SOURCE.with_name('q3_model.py')", "SOURCE.with_name('q3Model.py')")
assert beforeText.count("SOURCE.with_name('q3_model.py')") == 1
pathAudit = []
oldModules = set(afterReport['moduleMap'])
for fileInfo in afterReport['files']:
    sourcePath = projectRoot / fileInfo['reviewPath']
    tree = ast.parse(sourcePath.read_text(encoding='utf-8'))
    docstringNodes = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                docstringNodes.add(id(first.value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstringNodes:
            oldReferences = [name for name in oldModules if name + '.py' in node.value]
            assert not oldReferences, (sourcePath, node.lineno, node.value)
            if '.py' in node.value:
                pathAudit.append({'module': fileInfo['reviewPath'], 'line': node.lineno, 'literal': node.value})

inputPaths = [deliveryDir / Path(item['reviewPath']).name for item in afterReport['files']]
inputPaths += [projectRoot / 'paper_output/data_cleaned/A_environment_observed.csv',
               projectRoot / 'paper_output/data_cleaned/A_radius_observed.csv',
               Path(__file__), deliveryDir / 'tools/buildCamelCopies.py',
               projectRoot / 'paper_output/results/code_delivery/camel_final_v1/stdout.log',
               projectRoot / 'paper_output/results/code_delivery/camel_final_v1/runResult.json']
inputRecords = [record(item) for item in inputPaths]
caseRecords = []
warningMessages = []
for question, module in [('Q3', q2Model), ('Q4', q4Model)]:
    print(datetime.now(timezone.utc).isoformat(), 'SOLVE_EXPORT_READBACK', question, 'N40', flush=True)
    run = None
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            run = module.solve(40)
            exported = exportOutputs.exportQuestion(run, question, runtimeDir / question)
            checked = exportOutputs.validateExports([exported], runs={question: run})
        warningMessages.extend(str(item.message) for item in caught)
        assert checked['status'] == 'PASS' and checked['fully_verified_with_live_Run']
        paper = checked['exports'][0]['paper_CSV_live_Run_validation']
        expectedSource = record(deliveryDir / 'q3Model.py')
        assert paper['completion_source']['path'] == expectedSource['path']
        assert paper['completion_source']['sha256'] == expectedSource['sha256']
        caseRecords.append({'question': question, 'intervals': 40, 'export': exported,
                            'validation': checked, 'completionSourceMatched': True,
                            'diagnostics': run.diagnostics()})
        print(json.dumps({'question': question, 'status': 'PASS',
                          'workbookCells': checked['exports'][0]['checked_cells'],
                          'paperCells': paper['checked_cells'], 'completionSource': expectedSource}, ensure_ascii=False), flush=True)
    finally:
        if run is not None:
            run.close()

assert not warningMessages, warningMessages
assert inputRecords == [record(item) for item in inputPaths], 'Inputs changed while validating'
report = {'status': 'PASS', 'startedAtUtc': startedAtUtc, 'finishedAtUtc': datetime.now(timezone.utc).isoformat(),
          'elapsedSeconds': time.perf_counter() - timer, 'python': sys.version, 'executable': sys.executable,
          'cause': "The renamed import used q3Model, but completion_source still looked up literal q3_model.py.",
          'fixScope': 'One exporter provenance basename string; generator registers basenames and full paths for all local modules.',
          'exporterDiff': list(difflib.unified_diff(beforeText.splitlines(), afterText.splitlines(), fromfile='exportOutputs_v1', tofile='exportOutputs_v2')),
          'unchangedOtherCoreModules': unchangedModules, 'executablePythonPathLiteralsAudit': pathAudit,
          'allEightNormalizedAstChecksPass': all(item['normalizedAstIdentical'] for item in afterReport['files']),
          'inputRecords': inputRecords, 'cases': caseRecords, 'warnings': warningMessages,
          'priorFailureRetained': 'paper_output/results/code_delivery/camel_final_v1',
          'actualProcessExitCode': None, 'exitEvidence': 'external process-exit.json written by PowerShell supervisor',
          'scope': 'Actual N40 Q3/Q4 full workbook/raw-archive readback, live-Run samples, all paper CSV cells, and completion source provenance',
          'productionAccuracy': 'not asserted by N40 exporter check', 'guiReproduced': False, 'humanReview': 'pending'}
(runtimeDir / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
outputRecords = [record(item) for item in sorted(runtimeDir.rglob('*')) if item.is_file()]
(runtimeDir / 'artifactManifest.json').write_text(json.dumps({'status': 'PASS', 'outputs': outputRecords}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': 'PASS', 'questions': ['Q3', 'Q4'], 'warnings': 0,
                  'elapsedSeconds': report['elapsedSeconds'], 'report': str(runtimeDir / 'verification.json')}), flush=True)
