import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const scriptPath = fileURLToPath(import.meta.url);
const projectRoot = path.resolve(path.dirname(scriptPath), '../../../..');
const matlabRoot = path.join(projectRoot, 'paper_output/qa/matlab_crosscheck_20260911');
const pythonRoot = path.join(projectRoot, 'paper_output/results/code_delivery/camel_audit_v1');
const outputJson = path.join(matlabRoot, 'comparison-python.json');
const outputMarkdown = path.join(matlabRoot, 'comparison-python.md');

const thresholds = Object.freeze({ temperatureK: 1e-4, moistureDryBasis: 1e-6, eventSec: 0.01 });
const scriptRecord = fileRecord(scriptPath);

function now() { return new Date().toISOString(); }
function digest(bytes) { return crypto.createHash('sha256').update(bytes).digest('hex'); }
function fileRecord(filePath) {
  const bytes = fs.readFileSync(filePath);
  return { path: path.relative(projectRoot, filePath).split(path.sep).join('/'),
    bytes: bytes.length, sha256: digest(bytes) };
}
function readJson(filePath) { return JSON.parse(fs.readFileSync(filePath, 'utf8').replace(/^\uFEFF/, '')); }
function writeJson(filePath, value) { fs.writeFileSync(filePath, JSON.stringify(value, null, 2) + '\n', 'utf8'); }
function assert(condition, message) { if (!condition) throw new Error(message); }
function finite(value, label) { assert(typeof value === 'number' && Number.isFinite(value), `Nonfinite ${label}`); return value; }

function compareWorker() {
  const startedAtUtc = now();
  const startTime = process.hrtime.bigint();
  const inputPaths = [path.join(matlabRoot, 'runSummary.json'), path.join(matlabRoot, 'runLog.txt'),
    path.join(pythonRoot, 'launch.json'), path.join(pythonRoot, 'runResult.json'),
    path.join(pythonRoot, 'artifactManifest.json')];
  for (const question of ['Q1', 'Q23', 'Q4']) {
    inputPaths.push(path.join(matlabRoot, `${question}_crossCheck.json`),
      path.join(pythonRoot, question, 'summary.json'), path.join(pythonRoot, question, 'sampled_solution.npz'));
  }
  const matlabRun = readJson(inputPaths[0]);
  const pythonLaunch = readJson(path.join(pythonRoot, 'launch.json'));
  const pythonRun = readJson(path.join(pythonRoot, 'runResult.json'));
  const noMatlabException = matlabRun.exception == null || (Array.isArray(matlabRun.exception) && matlabRun.exception.length === 0);
  assert(matlabRun.status === 'COMPLETED_NUMERICAL_CHECKS' && noMatlabException, 'MATLAB run is incomplete');
  assert(pythonRun.status === 'PASS', 'Python baseline is incomplete');
  const provenanceChecks = [];

  function verifyDeclared(record, label) {
    const resolved = path.isAbsolute(record.path) ? record.path : path.join(projectRoot, record.path);
    const actual = fileRecord(resolved);
    assert(actual.sha256 === record.sha256, `Declared hash differs: ${label}`);
    inputPaths.push(resolved);
    provenanceChecks.push({ label, actual, matchedRecordedHash: true });
  }
  verifyDeclared({ path: matlabRun.sourcePath, sha256: matlabRun.sourceSha256 }, 'MATLAB source');
  for (const record of matlabRun.inputs) verifyDeclared(record, 'MATLAB observed input');
  for (const question of ['Q1', 'Q23', 'Q4']) {
    const baseline = readJson(path.join(pythonRoot, question, 'summary.json'));
    for (const key of ['code', 'jacobian_code', 'dense_storage_code']) verifyDeclared(baseline[key], `${question}/${key}`);
    for (const record of baseline.inputs) verifyDeclared(record, `${question}/observed input`);
  }
  const uniqueInputPaths = [...new Set(inputPaths.map(item => path.resolve(item)))];
  const inputRecords = uniqueInputPaths.map(fileRecord);
  const questions = [];
  const failures = [];
  for (const question of ['Q1', 'Q23', 'Q4']) {
    const matlab = readJson(path.join(matlabRoot, `${question}_crossCheck.json`));
    const python = readJson(path.join(pythonRoot, question, 'summary.json'));
    const sample = python.crossLanguageSamples;
    assert(matlab.question === question && python.settings.question === question, `${question}: question mismatch`);
    assert(matlab.intervalCount === 40 && python.settings.intervals === 40, `${question}: require N40`);
    const settingsPairs = [
      ['rtol', 'relativeTolerance'], ['atolTemperature', 'temperatureAbsoluteTolerance'],
      ['atolMoisture', 'moistureAbsoluteTolerance'], ['earlyMaxStepS', 'earlyMaxStepSec'],
      ['maxStepS', 'lateMaxStepSec'], ['h', 'heatTransferCoefficient'], ['beta', 'massTransferCoefficient']];
    for (const [pythonKey, matlabKey] of settingsPairs) {
      assert(python.settings[pythonKey] === matlabRun.settings[matlabKey], `${question}: ${pythonKey} differs`);
    }
    assert(python.settings.faceScheme.toLowerCase() === matlabRun.settings.waterFaceScheme.toLowerCase(), `${question}: face scheme differs`);
    assert(matlab.sampleTimesSec.length === matlab.sampleTypes.length, `${question}: sample types malformed`);
    const times = question === 'Q1' ? [0, 1800] : [0, 1800, 10800];
    if (question !== 'Q1') {
      assert(Number.isInteger(matlab.endSec) && matlab.endSec === python.diagnostics.end_s, `${question}: no common post-event integer second`);
      const postIndex = matlab.sampleTimesSec.indexOf(matlab.endSec);
      assert(postIndex >= 0 && matlab.sampleTypes[postIndex] === 'postEventIntegerSecond', `${question}: endpoint is not postEventIntegerSecond`);
      times.push(matlab.endSec);
    }
    const coordinates = [0, 0.25, 0.5, 0.75, 1];
    const pairs = [];
    const maxima = { temperatureK: null, moistureDryBasis: null };
    for (const timeSec of times) {
      const matlabTimeIndex = matlab.sampleTimesSec.indexOf(timeSec);
      const pythonTimeIndex = sample.timesS.indexOf(timeSec);
      assert(matlabTimeIndex >= 0 && pythonTimeIndex >= 0, `${question}: missing exact common time ${timeSec}`);
      for (const materialX of coordinates) {
        const matlabXIndex = matlab.sampleMaterialX.indexOf(materialX);
        const pythonXIndex = sample.materialX.indexOf(materialX);
        assert(matlabXIndex >= 0 && pythonXIndex >= 0, `${question}: missing exact common coordinate ${materialX}`);
        const item = { timeSec, materialX, matlabTimeIndexZeroBased: matlabTimeIndex, pythonTimeIndexZeroBased: pythonTimeIndex,
          matlabXIndexZeroBased: matlabXIndex, pythonXIndexZeroBased: pythonXIndex };
        for (const field of ['temperatureK', 'moistureDryBasis']) {
          const matlabValue = finite(matlab[field][matlabTimeIndex][matlabXIndex], `${question}/${field}/MATLAB`);
          const pythonValue = finite(sample[field][pythonTimeIndex][pythonXIndex], `${question}/${field}/Python`);
          const signedDifference = matlabValue - pythonValue;
          const absoluteDifference = Math.abs(signedDifference);
          const passed = absoluteDifference <= thresholds[field];
          item[field] = { matlabValue, pythonValue, signedDifferenceMatlabMinusPython: signedDifference, absoluteDifference, passed };
          if (maxima[field] === null || absoluteDifference > maxima[field].absoluteDifference) {
            maxima[field] = { timeSec, materialX, ...item[field] };
          }
          if (!passed) failures.push(`${question}/${field}/t=${timeSec}/x=${materialX}`);
        }
        pairs.push(item);
      }
    }
    let event = { applicable: false, reason: 'Q1 stops at 1800 s and has no drying event' };
    if (question !== 'Q1') {
      const matlabEventSec = finite(matlab.eventSec, `${question}/MATLAB event`);
      const pythonEventSec = finite(python.diagnostics.event_s, `${question}/Python event`);
      const signedDifferenceSec = matlabEventSec - pythonEventSec;
      const absoluteDifferenceSec = Math.abs(signedDifferenceSec);
      const passed = absoluteDifferenceSec <= thresholds.eventSec;
      event = { applicable: true, matlabEventSec, pythonEventSec, signedDifferenceSec, absoluteDifferenceSec, passed };
      if (!passed) failures.push(`${question}/event`);
    }
    questions.push({ question, status: failures.some(item => item.startsWith(question + '/')) ? 'FAIL' : 'PASS',
      intervals: 40, commonTimesSec: times, commonMaterialX: coordinates, matchedCoordinatePairs: pairs.length,
      maxima, event, comparisons: pairs,
      excludedPythonTimesSec: sample.timesS.filter(value => !times.includes(value)),
      excludedMatlabTimesSec: matlab.sampleTimesSec.filter(value => !times.includes(value)),
      exclusionReason: 'Python strict reported time and MATLAB critical event are different times; their field rows are not paired.',
      matlabWarnings: matlab.warnings, matlabWarningCapture: matlab.warningCapture, pythonWarningCount: python.warningCount });
  }
  assert(JSON.stringify(inputRecords) === JSON.stringify(uniqueInputPaths.map(fileRecord)), 'Inputs changed during comparison');
  assert(scriptRecord.sha256 === fileRecord(scriptPath).sha256, 'Comparison script changed while running');
  return { schemaVersion: 1, status: failures.length ? 'FAIL' : 'PASS', failures,
    startedAtUtc, finishedAtUtc: now(), elapsedSeconds: Number(process.hrtime.bigint() - startTime) / 1e9,
    thresholds, thresholdPolicy: 'Fixed before reading results; not changed after observing differences',
    matchingPolicy: 'Exact common time values and exact common material coordinates; no row-index pairing or interpolation',
    differenceConvention: 'MATLAB minus Python', script: scriptRecord, inputRecords, provenanceChecks,
    runtime: { nodeVersion: process.version, executable: process.execPath, platform: process.platform, architecture: process.arch,
      matlabVersion: matlabRun.matlabVersion, matlabSolver: matlabRun.settings.solver,
      matlabJacobian: matlabRun.settings.jacobianMode, pythonVersion: pythonLaunch.python,
      pythonLibraries: pythonLaunch.libraries, pythonSolver: 'SciPy BDF', pythonJacobian: 'analytic sparse' },
    sourceRunTimes: { matlabStartedAtUtc: matlabRun.startedAtUtc, matlabFinishedAtUtc: matlabRun.finishedAtUtc,
      pythonStartedAtUtc: pythonRun.startedAtUtc, pythonFinishedAtUtc: pythonRun.finishedAtUtc },
    comparedFieldScalars: questions.reduce((total, item) => total + 2 * item.matchedCoordinatePairs, 0),
    comparedEvents: 2, questions,
    scope: 'Independent N40 implementation agreement at recorded common times and five material coordinates, plus continuous event times',
    limitations: ['NPZ files are hashed for provenance; numerical comparisons read crossLanguageSamples in Python summary.json.',
      'No full-time/full-space error bound, physical calibration accuracy, production-grid acceptance, or confidence interval is established.',
      'MATLAB GUI execution evidence is recorded separately by the main agent; this comparison does not infer GUI completion.',
      'Human code review remains pending.'], guiEvidence: 'separate external record', humanReview: 'pending' };
}

function markdown(report) {
  if (!report.questions?.length) {
    return `# MATLAB/Python N40 独立实现比较\n\n状态：**FAIL**。监督进程实际读取的退出码：${report.processSupervision.workerActualExitCode}。\n\n比较器未生成可用数值报告：\n\n\`\`\`text\n${report.processSupervision.workerStderr}\n\`\`\`\n\n没有放宽阈值或填充成功状态。\n`;
  }
  const number = value => value === null || value === undefined ? '不适用' : value.toExponential(12);
  const rows = report.questions.map(item => `| ${item.question} | ${item.commonTimesSec.join(', ')} | ${item.matchedCoordinatePairs} | ${number(item.maxima.temperatureK.absoluteDifference)} | ${number(item.maxima.moistureDryBasis.absoluteDifference)} | ${number(item.event.absoluteDifferenceSec)} | ${item.status} |`);
  return `# MATLAB/Python N40 独立实现比较\n\n状态：**${report.status}**。比较进程实际退出码：**${report.processSupervision.workerActualExitCode}**，由父 Node 监督进程读取。\n\n固定接纳阈值为温度 ${thresholds.temperatureK} K、干基含水率 ${thresholds.moistureDryBasis} kg/kg、连续事件时间 ${thresholds.eventSec} s；未根据观察结果调整。全部比较按精确相同时间及材料坐标 x 配对，x 为 0、0.25、0.5、0.75、1。\n\n| 问题轨迹 | 共同时间 / s | 时间坐标配对数 | 最大温差 / K | 最大干基含水率差 / kg/kg | 连续事件绝对差 / s | 结论 |\n|---|---|---:|---:|---:|---:|---|\n${rows.join('\n')}\n\n共比较 ${report.comparedFieldScalars} 个场标量和 ${report.comparedEvents} 个连续事件。Q23 同时服务 Q2 与 Q3，不另造第二份轨迹。Q1 没有完整干燥事件。\n\nPython 的额外一行是严格四位报告时刻，MATLAB 的额外一行是其连续事件时刻，两者不同；这些场值未按行相减。连续事件只单独比较秒。最大值所在的时间、坐标、原始数值和有符号差均保存在 comparison-python.json。\n\n开始：${report.startedAtUtc}；结束：${report.finishedAtUtc}；比较耗时：${report.elapsedSeconds.toFixed(6)} s。Node ${report.runtime.nodeVersion}；MATLAB ${report.runtime.matlabVersion}，ode15s 默认 NDF 与稀疏数值差分；Python 使用 SciPy BDF 和解析稀疏 Jacobian。\n\n输入文件、声明的源码与观测数据哈希已经实际回读匹配，并在比较结束时再次检查未改变。Python NPZ 只作来源哈希记录，比较数值取自 summary.json 的 crossLanguageSamples。比较脚本 SHA-256：\`${report.script.sha256}\`。监督过程和两个输出文件的 SHA-256 见 comparison-python-manifest.json，避免报告文件自哈希的循环依赖。\n\n这只是 N40 在共同记录时间和五个材料坐标的跨实现一致性检查，不能推广为连续全域误差上界、正式网格精度、物理预测精度或置信区间。MATLAB GUI 操作证据由主代理另存，本脚本不补写 GUI 成功；用户人工代码审查仍待完成。\n`;
}

if (process.argv.includes('--worker')) {
  try {
    const report = compareWorker();
    process.stdout.write(JSON.stringify(report));
    process.exitCode = report.status === 'PASS' ? 0 : 1;
  } catch (error) {
    process.stderr.write(String(error.stack ?? error) + '\n');
    process.exitCode = 2;
  }
} else {
  const supervisorStartedAtUtc = now();
  const worker = spawnSync(process.execPath, [scriptPath, '--worker'], { cwd: projectRoot, encoding: 'utf8', maxBuffer: 8 * 1024 * 1024 });
  const supervision = { supervisorStartedAtUtc, supervisorFinishedAtUtc: now(),
    executable: process.execPath, commandArguments: [scriptPath, '--worker'], cwd: projectRoot,
    workerActualExitCode: worker.status, workerSignal: worker.signal, workerSpawnError: worker.error ? String(worker.error) : null,
    workerStderr: worker.stderr, source: 'Node parent process spawnSync return status; not a child prefilled success flag' };
  fs.appendFileSync(path.join(matlabRoot, 'comparison-python-process.jsonl'), JSON.stringify({
    script: scriptRecord, ...supervision, stdoutSha256: digest(Buffer.from(worker.stdout ?? '', 'utf8')) }) + '\n', 'utf8');
  const report = worker.stdout?.length ? JSON.parse(worker.stdout) : {
    schemaVersion: 1, status: 'FAIL', failures: ['Worker did not produce a numerical report'],
    script: scriptRecord, thresholds, startedAtUtc: supervisorStartedAtUtc, finishedAtUtc: now(),
    comparedFieldScalars: 0, comparedEvents: 0, questions: [], humanReview: 'pending' };
  report.processSupervision = supervision;
  if (worker.status !== 0) report.status = 'FAIL';
  writeJson(outputJson, report);
  fs.writeFileSync(outputMarkdown, markdown(report), 'utf8');
  writeJson(path.join(matlabRoot, 'comparison-python-manifest.json'), {
    status: report.status, createdAtUtc: now(), script: scriptRecord, processSupervision: supervision,
    outputs: [fileRecord(outputJson), fileRecord(outputMarkdown)] });
  process.stdout.write(JSON.stringify({ status: report.status, workerActualExitCode: worker.status,
    comparedFieldScalars: report.comparedFieldScalars, comparedEvents: report.comparedEvents,
    maxima: report.questions.map(item => ({ question: item.question,
      temperatureK: item.maxima.temperatureK.absoluteDifference, moistureDryBasis: item.maxima.moistureDryBasis.absoluteDifference,
      eventSec: item.event.absoluteDifferenceSec ?? null })) }) + '\n');
  process.exitCode = worker.status ?? 2;
}
