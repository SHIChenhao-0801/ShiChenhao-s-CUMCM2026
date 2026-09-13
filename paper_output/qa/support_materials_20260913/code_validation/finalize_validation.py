"""Aggregate observed isolated runs and compare newly computed final exports."""
from pathlib import Path
import ast
from datetime import datetime, timezone
import gzip
import hashlib
import json
import re
import xml.etree.ElementTree as ET

QA = Path(__file__).resolve().parent
ROOT = QA.parents[3]
PACKAGE = ROOT/'支撑材料/03_程序代码'
ISOLATED = QA/'isolated/03_程序代码'
BASELINE = ROOT/'paper_output/results/production/final_v6a'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024), b''): h.update(block)
    return h.hexdigest()

def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

execution = json.loads((QA/'execution.json').read_text(encoding='utf-8'))
if execution['status'] != 'PASS':
    raise RuntimeError('Isolated run is incomplete or failed')
cases = {v['name']:v for v in execution['cases']}
assert set(cases) == {'environment', 'pip_check', 'preflight', 'quick', 'final'}
assert all(v['actualExitCode'] == 0 for v in cases.values())
core = []
for path in sorted(PACKAGE.glob('*.py')):
    ast.parse(path.read_text(encoding='utf-8'))
    original = next(v for v in execution['files'] if v['path'] == path.name)
    assert sha(path) == sha(ISOLATED/path.name) == original['sha256']
    core.append({'path':path.name, 'sha256':sha(path), 'pythonSyntax':'PASS', 'matchesActuallyExecutedSource':True})
ET.parse(PACKAGE/'A_CodeReview.pyproj')
hardcoded = []
for path in sorted(PACKAGE.glob('*.py')):
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if re.search(r'[A-Za-z]:[\\/]', line):
            hardcoded.append({'path':path.name, 'line':number, 'text':line})
assert not hardcoded
runs = {}
for profile in ['quick', 'final']:
    raw = json.loads((ISOLATED/'results'/f'{profile}_isolated/runResult.json').read_text(encoding='utf-8'))
    assert raw['status'] == 'PASS'
    values = {'actualExitCode':cases[profile]['actualExitCode'],
              'observedElapsedSeconds':cases[profile]['elapsedSeconds'],
              'startedAtUtc':cases[profile]['startedAtUtc'], 'finishedAtUtc':cases[profile]['finishedAtUtc'],
              'questions':{}, 'workbookCellsChecked':0, 'paperCellsChecked':0,
              'status':'PASS', 'environment':raw['environment']}
    for q in ['Q1', 'Q23', 'Q4']:
        summary = raw['summaries'][q]
        item = {'intervals':summary['settings']['intervals'], 'diagnostics':summary['diagnostics'],
                'completion':summary.get('completion'), 'solverWarnings':summary['solverWarningCount'],
                'referenceComparison':raw['comparisons'][q]['referenceComparison'], 'exports':[]}
        for export in raw['comparisons'][q]['exports']:
            for rec in export['exports']:
                assert rec['status'] == 'PASS' and rec['fully_verified_with_live_Run']
                cells = rec['checked_cells']
                paper_cells = rec['paper_CSV_live_Run_validation']['checked_cells']
                values['workbookCellsChecked'] += cells
                values['paperCellsChecked'] += paper_cells
                item['exports'].append({'question':rec['question_id'], 'status':rec['status'],
                    'workbookCellsChecked':cells, 'paperCellsChecked':paper_cells,
                    'liveRunSamples':rec['live_Run_sample_validation'], 'fullyVerifiedWithLiveRun':True})
        values['questions'][q] = item
    runs[profile] = values
byte_checks = []
generated = ISOLATED/'results/final_isolated/outputs'
for path in sorted(generated.glob('*_unrounded.csv.gz')):
    size = 0
    with gzip.open(path, 'rb') as left, gzip.open(BASELINE/'outputs'/path.name, 'rb') as right:
        while True:
            a, b = left.read(1024*1024), right.read(1024*1024)
            if a != b: raise AssertionError('Raw archive differs: '+path.name)
            size += len(a)
            if not a: break
    byte_checks.append({'path':path.name, 'comparison':'decompressed bytes', 'uncompressedBytes':size,
                        'exactEqualToFrozenFinalV6a':True})
for path in sorted(generated.glob('q*_paper_*.csv')):
    assert path.read_bytes() == (BASELINE/'outputs'/path.name).read_bytes()
    byte_checks.append({'path':path.name, 'comparison':'file bytes', 'bytes':path.stat().st_size,
                        'exactEqualToFrozenFinalV6a':True, 'sha256':sha(path)})
assert len(byte_checks) == 11
exact_arrays = sum(sum(bool(v) for v in runs['final']['questions'][q]['referenceComparison'][
    'supplementaryExactEqualityOfAllSavedArrays'].values()) for q in ['Q1','Q23','Q4'])
assert exact_arrays == 21
changes = json.loads((PACKAGE/'docs/source_changes.json').read_text(encoding='utf-8'))
for item in changes['files']:
    assert sha(ROOT/item['source']) == item['sourceSha256']
    assert sha(PACKAGE/item['delivered']) == item['deliveredSha256']
    assert item['algorithmAstEquivalentAfterPathNormalization']
for item in changes['copiedInputsAndReference']:
    assert sha(ROOT/item['source']) == item['sha256']
    assert sha(PACKAGE/item['path']) == item['sha256']
report = {'status':'PASS_SAME_MACHINE_ISOLATED_CLI_REPRODUCTION',
          'createdAtUtc':datetime.now(timezone.utc).isoformat(),
          'scope':'New ZIP extraction in a directory independent of the original code layout, with the previously created clean venv and user-site packages disabled. No source edits during execution.',
          'environmentRebuiltOnPreviousAudit':True, 'dependenciesCheckedAgain':True,
          'sourceArchiveSha256':execution['archiveSha256'],
          'sourceAndInputFilesInExecutedArchive':len(execution['files']),
          'executedPythonSources':core, 'runs':runs, 'finalExportFrozenComparison':byte_checks,
          'staticChecks':{'pythonFiles':len(core), 'projectXml':'PASS', 'hardcodedDrivePathsInPython':0,
                          'PowerShell7_6_5ParseErrors':0, 'PowerShell5_1_26100_9444ParseErrors':0},
          'limitations':{'secondPhysicalDevice':'NOT_TESTED', 'otherOperatingSystems':'NOT_TESTED',
                         'newVisualStudioProjectGui':'NOT_PERFORMED', 'humanReview':'PENDING_USER_REVIEW',
                         'physicalPredictionAccuracy':'NO_INTERNAL_MEASURED_T_C_GROUND_TRUTH',
                         'portablePowerShellWrapperFullRun':'NOT_EXECUTED_ONLY_SYNTAX_CHECKED'}}
write(QA/'validation_summary.json', report)
write(PACKAGE/'docs/validation_summary.json', report)
audit = {'status':'PASS', 'scope':'same-machine isolated CLI reproduction of the delivered Python sources and inputs',
    'createdAtUtc':report['createdAtUtc'], 'quickExitCode':cases['quick']['actualExitCode'],
    'finalExitCode':cases['final']['actualExitCode'],
    'quickElapsedSeconds':cases['quick']['elapsedSeconds'], 'finalElapsedSeconds':cases['final']['elapsedSeconds'],
    'coreAlgorithmAstEquivalentAfterPathNormalization':8, 'executedPythonFilesMatchingDelivery':len(core),
    'originalSourceAndFrozenInputFilesUnchanged':True,
    'quickWorkbookCellsChecked':runs['quick']['workbookCellsChecked'],
    'finalWorkbookCellsChecked':runs['final']['workbookCellsChecked'],
    'finalPaperCellsChecked':runs['final']['paperCellsChecked'],
    'exactFrozenSavedArrays':exact_arrays, 'exactDecompressedRawGzipArchives':4,
    'exactFrozenPaperCsvFiles':7,
    'dryingTimesH':{q:runs['final']['questions'][q]['completion']['reported_drying_time_h'] for q in ['Q23','Q4']},
    'newVisualStudioGui':'NOT_PERFORMED', 'humanReview':'PENDING_USER_REVIEW', 'physicalSecondDevice':'NOT_TESTED',
    'detailedReport':'validation_summary.json', 'externalProcessEvidence':'execution.json',
    'sourceArchiveSha256':execution['archiveSha256'],
    'deliveredSources':core}
write(QA/'code_package_audit.json', audit)
notes = f'''# 本次代码包实际运行验收

状态：同机隔离目录的 CLI 复现通过。源代码从候选 ZIP 重新解压到独立目录，使用此前审计创建的干净虚拟环境，关闭用户 site-packages，重新通过环境检查、pip check和输入预检。

| 项目 | 实际结果 |
|---|---|
| N40三条轨迹、四题完整导出/回读 | 退出0；{runs['quick']['observedElapsedSeconds']:.3f}秒 |
| N3200/N3200/N6400正式网格 | 退出0；{runs['final']['observedElapsedSeconds']:.3f}秒 |
| 正式四表完整回读 | {runs['final']['workbookCellsChecked']:,}个工作簿单元格 |
| 正式正文CSV从live Run逐格核验 | {runs['final']['paperCellsChecked']}格 |
| 冻结采样对照 | 三轨迹、21个保存数组逐值完全相同；预设数值容差检查通过 |
| 四份原精度归档 | 解压后的全部CSV字节与final_v6a一致 |
| 七份正文CSV | 全部文件字节与final_v6a一致 |
| Q3严格报告时间 | {runs['final']['questions']['Q23']['completion']['reported_drying_time_h']:.4f} h |
| Q4严格报告时间 | {runs['final']['questions']['Q4']['completion']['reported_drying_time_h']:.4f} h |
| 八核心模块 | 只替换包路径/说明；路径反向归一化后的算法AST一致 |
| 新入口与核心源码 | 九个Python文件语法通过，提交副本SHA256与实际执行源一致 |
| PowerShell辅助入口 | PS7.6.5及PS5.1静态解析均0错误；未重复全量运行此封装 |
| Visual Studio工程 | XML可解析；新版GUI打开、断点和运行尚未实测 |
| 用户人工审查 | 待用户本人完成，不由本验收代签 |

环境：Windows AMD64/Python3.14.7、NumPy2.5.2、SciPy1.18.1、openpyxl3.1.5；CPU单线程。当前证据未覆盖第二台物理电脑或其他操作系统，也不证明条件模型的真实预测准确率。原工作区的冻结数值和源码未修改。

机器可读的详细结果、每题诊断/回读格数/连续事件/原精度严格阈值及源码SHA256见同目录 `validation_summary.json`。`source_changes.json` 与 `portable_paths.diff` 给出原源码对应关系及逐行差异。该代码包不带虚拟环境、运行缓存和作者机器Visual Studio配置。
'''
(PACKAGE/'docs/运行验收说明.md').write_text(notes, encoding='utf-8')
print(json.dumps({'status':report['status'], 'quickSeconds':runs['quick']['observedElapsedSeconds'],
      'finalSeconds':runs['final']['observedElapsedSeconds'], 'finalWorkbookCells':runs['final']['workbookCellsChecked'],
      'finalPaperCells':runs['final']['paperCellsChecked'], 'exactFrozenExports':len(byte_checks)}, ensure_ascii=False))
