"""A题四问可审查入口：求解、导出、回读、回归核验和运行留痕。

默认 final 配置重算 N3200/N3200/N6400；audit 配置采用 N40 对照旧实现。
本入口产生独立版本目录。GUI 操作记录和用户人工审查由人另行填写。
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import gc
import gzip
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

# 必须在加载 NumPy/SciPy 前限制线程，避免三个大网格争用内存和CPU。
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
sys.dont_write_bytecode = True
projectRoot = Path(__file__).resolve().parents[3]
codeRoot = Path(__file__).resolve().parent
os.environ["MPLCONFIGDIR"] = str(projectRoot / "tmp/cache/matplotlib")
os.environ["TMPDIR"] = str(projectRoot / "tmp/cache/review_delivery")
os.environ["TEMP"] = os.environ["TMPDIR"]
os.environ["TMP"] = os.environ["TMPDIR"]
Path(os.environ["TMPDIR"]).mkdir(parents=True, exist_ok=True)


def utcNow():
    """UTC ISO 时间戳；北京时间可在日志中按 +08:00 换算。"""
    return datetime.now(timezone.utc).isoformat()


def writeJson(filePath, content):
    filePath.parent.mkdir(parents=True, exist_ok=True)
    filePath.write_text(json.dumps(content, ensure_ascii=False, indent=2,
                                  allow_nan=False), encoding="utf-8")


def fileRecord(filePath):
    """分块哈希避免把大型原精度文件整体读入内存。"""
    digest = hashlib.sha256()
    with filePath.open("rb") as fileHandle:
        for block in iter(lambda: fileHandle.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": filePath.relative_to(projectRoot).as_posix(),
            "bytes": filePath.stat().st_size, "sha256": digest.hexdigest()}


class TeeStream:
    """同时保留IDE可见输出和UTF-8持久日志。"""
    def __init__(self, screen, logFile):
        self.screen, self.logFile = screen, logFile

    def write(self, text):
        self.screen.write(text)
        self.logFile.write(text)
        self.flush()
        return len(text)

    def flush(self):
        self.screen.flush()
        self.logFile.flush()


def compareArrays(actualPath, baselinePath):
    """独立读取两份NPZ；要求同名数组逐值相等，含NaN位置。"""
    import numpy as np
    checks = []
    with np.load(actualPath, allow_pickle=False) as actual, np.load(
            baselinePath, allow_pickle=False) as baseline:
        if set(actual.files) != set(baseline.files):
            raise AssertionError("NPZ字段不一致")
        for key in baseline.files:
            left, right = actual[key], baseline[key]
            equal = left.shape == right.shape and np.array_equal(left, right, equal_nan=True)
            if not equal:
                raise AssertionError(f"重命名后数值改变：{actualPath.name}/{key}")
            checks.append({"array": key, "shape": list(left.shape), "exactEqual": True})
    return {"actual": fileRecord(actualPath), "baseline": fileRecord(baselinePath),
            "status": "PASS", "arrays": checks}


def compareArchives(actualPath, baselinePath):
    """比较解压后的逐秒原精度CSV，忽略gzip容器时间戳。"""
    checkedBytes = 0
    with gzip.open(actualPath, "rb") as actual, gzip.open(baselinePath, "rb") as baseline:
        while True:
            left, right = actual.read(1024 * 1024), baseline.read(1024 * 1024)
            if left != right:
                raise AssertionError(f"原精度CSV与冻结结果不同：{actualPath.name}")
            checkedBytes += len(left)
            if not left:
                break
    return {"status": "PASS", "uncompressedBytes": checkedBytes,
            "actual": fileRecord(actualPath), "baseline": fileRecord(baselinePath)}


def verifyFrozenBaseline():
    """以历史实际退出0的账本核对冻结输入/输出，避免拿变动文件作基准。"""
    manifestPath = projectRoot / "paper_output/results/production/final_v6a/run_manifest.json"
    manifest = json.loads(manifestPath.read_text(encoding="utf-8-sig"))
    frozenRun = manifest["runs"][0]
    if manifest["status"] != "PASS" or frozenRun["returncode"] != 0:
        raise RuntimeError("历史基准没有有效的生产退出记录")
    checkedRecords = []
    for record in frozenRun["input_files"] + frozenRun["output_artifacts"]:
        actualRecord = fileRecord(projectRoot / record["path"])
        if actualRecord["sha256"] != record["sha256"]:
            raise AssertionError("冻结基准哈希改变：" + record["path"])
        checkedRecords.append(actualRecord)
    return {"status": "PASS", "manifest": fileRecord(manifestPath), "checkedRecords": checkedRecords}


def runQuestion(questionKey, intervalCount, outputDirectory, profile):
    """一个轨迹求解一次；Q2和Q3共享Q23轨迹，导出后立即释放缓存。"""
    import numpy as np
    import dryingCore
    import q3Model
    moduleName = {"Q1": "q1Model", "Q23": "q2Model", "Q4": "q4Model"}[questionKey]
    questionModule = importlib.import_module(moduleName)
    questionDirectory = outputDirectory / questionKey
    baselineRoot = projectRoot / "paper_output/results/production/final_v6a"
    solutionRun = None
    try:
        print(f"{utcNow()} SOLVE {questionKey} N={intervalCount}", flush=True)
        # 人工审查断点：下一行进入逐问入口，再进入 solveCase / rhs。
        with warnings.catch_warnings(record=True) as caughtWarnings:
            warnings.simplefilter("always")
            solutionRun = questionModule.solve(intervalCount)
        if caughtWarnings:
            raise RuntimeError("求解器警告：" + "; ".join(str(item.message) for item in caughtWarnings))
        summary = dryingCore.saveRun(solutionRun, questionDirectory)
        summary["warningCount"] = len(caughtWarnings)
        if questionKey != "Q1":
            summary["completion"] = q3Model.completion(solutionRun)
        sampleTimes = np.unique(np.array([0., min(1800., solutionRun.endS),
            min(10800., solutionRun.endS), solutionRun.endS] + ([] if questionKey == "Q1"
            else [summary["completion"]["reported_time_s"]])))
        sampleCoordinates = np.array([0., .25, .5, .75, 1.])
        temperature, moisture = solutionRun.fields(sampleTimes, materialX=sampleCoordinates)
        summary["crossLanguageSamples"] = {"timesS": sampleTimes.tolist(),
            "materialX": sampleCoordinates.tolist(), "temperatureK": temperature.tolist(),
            "moistureDryBasis": moisture.tolist()}
        writeJson(questionDirectory / "summary.json", summary)
        print(json.dumps({"question": questionKey, "diagnostics": summary["diagnostics"]},
                         ensure_ascii=False), flush=True)
        comparison = {}
        if profile == "final":
            comparison["sampledSolution"] = compareArrays(questionDirectory / "sampled_solution.npz",
                baselineRoot / questionKey / "sampled_solution.npz")
            frozenSummary = json.loads((baselineRoot / "numerical_summaries.json").read_text(encoding="utf-8"))[questionKey]
            if summary["diagnostics"]["event_s"] != frozenSummary["diagnostics"]["event_s"]:
                raise AssertionError("连续临界事件与冻结基线不同")
            if questionKey != "Q1" and summary["completion"] != frozenSummary["completion"]:
                raise AssertionError("严格达标时刻与冻结基线不同")
            import exportOutputs
            comparison["exports"] = []
            questionIds = ["Q2", "Q3"] if questionKey == "Q23" else [questionKey]
            for questionId in questionIds:
                print(f"{utcNow()} EXPORT_AND_READBACK {questionId}", flush=True)
                exportResult = exportOutputs.exportQuestion(solutionRun, questionId,
                                                             outputDirectory / "outputs")
                validation = exportOutputs.validateExports([exportResult], runs={questionId: solutionRun})
                if validation.get("status") != "PASS" or not validation.get("fully_verified_with_live_Run"):
                    raise AssertionError("工作簿/原精度文件/live Run核对失败")
                rawName = f"result{questionId[-1]}_unrounded.csv.gz"
                archiveCheck = compareArchives(outputDirectory / "outputs" / rawName,
                                                baselineRoot / "outputs" / rawName)
                tableChecks = []
                for tablePath in sorted((outputDirectory / "outputs").glob(questionId.lower() + "_paper_*.csv")):
                    referencePath = baselineRoot / "outputs" / tablePath.name
                    if tablePath.read_bytes() != referencePath.read_bytes():
                        raise AssertionError("正文CSV与冻结结果不同：" + tablePath.name)
                    tableChecks.append({"file": fileRecord(tablePath), "exactEqual": True})
                comparison["exports"].append({"questionId": questionId, "validation": validation,
                                               "archiveCheck": archiveCheck, "paperTables": tableChecks})
        writeJson(questionDirectory / "comparison.json", comparison)
        return summary, comparison
    finally:
        if solutionRun is not None:
            solutionRun.close()
            solutionRun = None
        gc.collect()
        print(f"{utcNow()} RELEASED {questionKey}", flush=True)


def runLegacyAudit(outputDirectory):
    """固定评价器：N40同参数旧源码真实重算，与本轮副本逐值比较。"""
    legacyRoot = projectRoot / "paper_output/code/modeling"
    sys.path.insert(0, str(legacyRoot))
    import drying_core as legacyCore
    checks = []
    for questionKey, moduleName in [("Q1", "q1_model"), ("Q23", "q2_model"), ("Q4", "q4_model")]:
        legacyRun = None
        try:
            print(f"{utcNow()} AUTORESEARCH_BASELINE {questionKey} N=40", flush=True)
            legacyRun = importlib.import_module(moduleName).solve(40)
            legacyDirectory = outputDirectory / "legacyBaseline" / questionKey
            legacyCore.save_run(legacyRun, legacyDirectory)
            checks.append(compareArrays(outputDirectory / questionKey / "sampled_solution.npz",
                                         legacyDirectory / "sampled_solution.npz"))
        finally:
            if legacyRun is not None:
                legacyRun.close()
            gc.collect()
    return {"status": "KEEP", "primaryMetric": "maximum absolute sampled field difference",
            "primaryMetricValue": 0., "criterion": "exact equality at fixed N40, same settings and inputs",
            "randomSeed": None, "deterministic": True, "checks": checks,
            "heldOutCheck": "final grid and all unrounded output rows against frozen final_v6a"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=["final", "audit"], default="final")
    parser.add_argument("--run-id", dest="runId", default=None)
    arguments = parser.parse_args()
    runId = arguments.runId or (arguments.profile + "_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", runId) is None:
        raise ValueError("run-id仅可含字母、数字、下划线和连字符")
    if Path.cwd().resolve() != projectRoot:
        raise RuntimeError("请在2026CUMCM根目录启动，或使用已配置的VS工程")
    outputDirectory = projectRoot / "paper_output/results/code_delivery" / runId
    outputDirectory.mkdir(parents=True, exist_ok=False)
    startedAt, timer = utcNow(), time.perf_counter()
    sourcePaths = sorted(codeRoot.glob("*.py"))
    dataPaths = sorted((projectRoot / "paper_output/data_cleaned").glob("A_*observed.csv"))
    templatePaths = sorted((projectRoot / "problem_files/CUMCM2026Problems/A题/附件/附件3").glob("result*.xlsx"))
    inputRecords = [fileRecord(filePath) for filePath in sourcePaths + dataPaths + templatePaths]
    launchRecord = {"startedAtUtc": startedAt, "runId": runId, "profile": arguments.profile,
        "command": [sys.executable] + sys.argv, "cwd": str(Path.cwd()), "python": sys.version,
        "libraries": {name: importlib.metadata.version(name) for name in ["numpy", "scipy", "openpyxl"]},
        "inputRecords": inputRecords, "blasThreads": 1, "humanReview": "pending", "guiObserved": False,
        "baseline": "paper_output/results/production/final_v6a", "seed": None,
        "seedReason": "deterministic PDE solve; no pseudorandom numbers", "experimentBudgetSeconds": 1800}
    writeJson(outputDirectory / "launch.json", launchRecord)
    result = {"runId": runId, "startedAtUtc": startedAt, "status": "RUNNING",
              "humanReview": "pending", "guiObservation": "separate external evidence required",
              "actualProcessExitCode": None}
    with (outputDirectory / "stdout.log").open("w", encoding="utf-8") as logFile:
        with redirect_stdout(TeeStream(sys.stdout, logFile)), redirect_stderr(TeeStream(sys.stderr, logFile)):
            try:
                print(f"{startedAt} START {runId} {arguments.profile}", flush=True)
                result["frozenBaselineVerification"] = verifyFrozenBaseline()
                summaries, comparisons = {}, {}
                for questionKey, finalIntervals in [("Q1", 3200), ("Q23", 3200), ("Q4", 6400)]:
                    intervalCount = 40 if arguments.profile == "audit" else finalIntervals
                    summaries[questionKey], comparisons[questionKey] = runQuestion(
                        questionKey, intervalCount, outputDirectory, arguments.profile)
                result["summaries"], result["comparisons"] = summaries, comparisons
                if arguments.profile == "audit":
                    result["autoresearch"] = runLegacyAudit(outputDirectory)
                    writeJson(outputDirectory / "autoresearch.json", result["autoresearch"])
                if inputRecords != [fileRecord(filePath) for filePath in sourcePaths + dataPaths + templatePaths]:
                    raise RuntimeError("运行期间源码或输入发生改变，结果不能签核")
                result["status"] = "PASS"
                print(f"{utcNow()} ALL_Q1_Q4_SOLVES_AND_CHECKS_COMPLETED", flush=True)
            except BaseException as error:
                result["status"], result["error"] = "FAIL", repr(error)
                traceback.print_exc()
                raise
            finally:
                result["finishedAtUtc"], result["elapsedSeconds"] = utcNow(), time.perf_counter() - timer
                writeJson(outputDirectory / "runResult.json", result)
                stablePaths = [filePath for filePath in sorted(outputDirectory.rglob("*"))
                    if filePath.is_file() and filePath.name not in ["stdout.log", "artifactManifest.json"]]
                writeJson(outputDirectory / "artifactManifest.json", {"status": result["status"],
                    "createdAtUtc": utcNow(), "artifacts": [fileRecord(filePath) for filePath in stablePaths]})


if __name__ == "__main__":
    main()
