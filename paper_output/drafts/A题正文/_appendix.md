# 附录

## 附录 A　支撑材料文件清单


| 序号 | 文件/目录 | 说明 |
|---|---|---|
| 1 | `AI工具使用详情.pdf` | 按 AI 规定第 4 条撰写的详情说明（工具与版本、使用目的与环节、主要提示方式与过程、采纳与人工修改核验情况） |
| 2 | `result1.xlsx` | 问题一完整结果（1800 s 内每 1 s、每 0.1 cm） |
| 3 | `result2.xlsx` | 问题二完整结果（全过程每 1 s、每 0.1 cm） |
| 4 | `result3.xlsx` | 问题三完整结果（每 60 s、每 0.1 cm） |
| 5 | `result4.xlsx` | 问题四完整结果（每 60 s、每 0.1 cm，含药材表面列） |
| 6 | `code/` | 建模与求解全部 Python 源程序（正式入口、核心模块、解析 Jacobian、绘图与导出脚本） |
| 7 | `code/matlab/` | MATLAB 独立交叉核验脚本 |
| 8 | `docs/` | 公式与算法说明、参数与运行设置说明 |
| 9 | `figures/` | 正文图件的矢量版本（PDF/SVG）与绘图数据 |
| 10 | `evidence/` | 运行记录、校验输出、交叉验证结果 |


## 附录 B　完整可运行源程序代码


源码在支撑包中的目录与下表一致（`code/` 为经人工审查的交付版，`code/data`、`code/modeling`、`code/verification` 为产生正文全部数值的生产与验证脚本），共 40 个 Python 文件与 1 个 MATLAB 文件。

**B.1　问题求解核心模块（`code/`）**

| 文件 | 作用 |
|---|---|
| `dryingCore.py` | 物理模型与控制方程右端项：物性函数、内部面通量（调和平均与 Kirchhoff 势两种格式）、表面与中心边界、问题一至问题四的设置装配 |
| `analyticJacobian.py` | 解析稀疏 Jacobian 的装配，含式 (55)—(59) 的全部导数项与交叉项 |
| `diskDense.py` | 稠密输出的磁盘存储与任意时刻插值求值（式 (52) 后的说明） |
| `runDelivery.py` | 正式求解入口：读入清洗后数据、逐问求解、事件定位与严格复核、导出四份结果工作簿与正文表格 CSV |
| `exportOutputs.py` | 按附件 3 模板导出 `result1—4.xlsx`：固定物理半径取样、域外留空、真实表面独立列与四位小数舍入 |
| `q1Model.py`—`q4Model.py` | 四个问题的模型装配入口（物性、几何与判据的切换） |

**B.2　数据准备与生产流水线（`code/data/`、`code/modeling/`）**

| 文件 | 作用 |
|---|---|
| `prepare_a_data.py` | 附件 1、附件 2 的读取、单位换算与分段线性插值，生成清洗后数据 |
| `run_modeling.py` | 生产求解驱动：按问题装配设置、调用核心模块、落盘全部数值摘要 |
| `drying_core.py`、`analytic_jacobian.py`、`disk_dense.py`、`export_outputs.py` | 与 B.1 交付版同源的生产实现（蛇形命名） |
| `publication_plots.py` | 生成正文图件的矢量版本与绘图数据 |
| `validate_bessel.py` | 独立重写的圆柱 Bessel 级数解析解与节点 / 控制体平均两种口径的判别（式 (60)、式 (61)） |
| `verify_convergence.py` | 相邻网格在公共采样点上的收敛性检验 |
| `verify_time_accuracy.py` | 基准与更紧时间推进设置下的解差异与事件差 |
| `compare_analytic.py`、`axisymmetric_check.py` | 解析解对照与二维轴对称对照（端面效应） |

**B.3　验证与交叉核验脚本（`code/verification/`）**

| 文件 | 作用 |
|---|---|
| `crossvalidate_solver.py` | 积分器互换（BDF/NDF 与 Radau IIA）与两种湿面离散格式对照 |
| `method_comparison.py` | 同方程两种离散（Kirchhoff 势与二阶守恒中点差分）对照，含 `fluxPathUsed` 守卫 |
| `threshold_and_scaling_checks.py` | 阈值事件的独立二分求根与 $(R_0/R)^{2}$ 尺度折算（式 (67)） |
| `latent_heat_scenarios.py` | 潜热情景包络（式 (65) 与表 27） |
| `isotherm_activity_closure.py` | 数据锚定的吸附闭合情景族（式 (68)—(71) 与表 28） |
| `sensitivity_analysis.py` | 环境延拓、$C_{eq}$、$h$、$\beta$、扩散前因子与导热系数的情景扫描（表 33） |
| `crossvalidate_series.py`、`compile_crossvalidation_report.py` | 三阶段分界的多判据交叉识别与其汇总 |
| `analytic_metric_check.py`、`energy_balance_check.py` | 解析度量口径核对与能量恒等式构造限制的诊断（10.9 节检验二） |

**B.4　MATLAB 独立实现（`code/matlab/`）**

| 文件 | 作用 |
|---|---|
| `runCrossCheck.m` | 独立有限体积离散 + `ode15s` 的跨实现交叉核验（10.9 节检验五） |

@@CODE_BLOCK_START@@

下列清单为产生与核验本文全部数值的完整源程序（人工审查交付版、生产核心模块、验证与交叉核验脚本、MATLAB 独立实现），共 19 个文件、4868 行；完整工作目录（含数据准备、绘图与其余诊断脚本）一并提供于支撑材料。

**B.5　问题求解交付版（人工审查版）**

`review_delivery/runDelivery.py`（正式求解入口：读入清洗数据、逐问求解、事件定位与严格复核、导出四份结果工作簿）

```python
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
```

`review_delivery/dryingCore.py`（物理模型与控制方程右端项、物性函数、内部面通量与边界条件）

```python
# 本文件为冻结求解源码的驼峰审查副本；来源、改名与 AST 核验见 tools/coreRenameReport.json。
"""2026 A: radial heat and dry-basis moisture transport on a material mesh.

Units: s, m, K, kg water / kg dry matter. See numerical_design.md for derivation.
The supplied empirical rho*cp is an effective thermal capacity. Dry-solid mass
is conserved separately on uniformly shrinking material control volumes.
No latent heat in the baseline; optional surface-latent scenario is labelled.
No clipping of solution values. Coefficients use a positive continuation only
for integrator Newton probes; all accepted states are checked independently.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import hashlib
import io
import json
import time

import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import lil_matrix
from scipy.special import expi
import analyticJacobian
import diskDense

ROOT = Path(__file__).resolve().parents[3]
LOADED_CODE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
C0, T0, R0, LENGTH = 2.55, 301.15, 0.02, 0.25


# 原始环境时间单位为秒，温度为 K，含水率为 kg 水 / kg 干物质；记录输入哈希。
def loadInputs(withRecords=False):
    arrays, records = [], []
    for name in ['A_environment_observed.csv', 'A_radius_observed.csv']:
        path = ROOT / 'paper_output/data_cleaned' / name
        content = path.read_bytes()
        arrays.append(np.genfromtxt(io.StringIO(content.decode('utf-8-sig')),
                                    delimiter=',', names=True))
        records.append({'path':path.relative_to(ROOT).as_posix(), 'bytes':len(content),
                        'sha256':hashlib.sha256(content).hexdigest(), 'exists':True})
    return (*arrays, records) if withRecords else tuple(arrays)


@dataclass(frozen=True)
# 数值参数集中配置；四问正式设置由 q1Model/q2Model/q4Model 提供。
class Settings:
    question: str = 'Q23'
    intervals: int = 100
    rtol: float = 1e-7
    atolTemperature: float = 1e-7
    atolMoisture: float = 1e-9
    maxStepS: float = 600.0
    earlyMaxStepS: float = 30.0
    horizonH: float = 240.0
    shrink: bool = False
    boundaryExtension: str = 'nominal'
    tailTemperatureC: float = 50.0
    tailEquilibrium: float = 0.05
    h: float = 25.0
    beta: float = 8e-7
    equilibriumScale: float = 1.0
    surfaceLatentFraction: float = 0.0
    latentJKg: float = 2.4e6
    constantD: float | None = None
    constantThermal: bool = False
    method: str = 'BDF'
    faceScheme: str = 'harmonic'
    jacobianMode: str = 'analytic'
    denseStorage: str = 'disk'


class RadialModel:
    def __init__(self, settings: Settings):
        self.settings = settings
        if settings.intervals < 2 or settings.jacobianMode not in ('analytic', 'finite_difference'):
            raise ValueError('At least two intervals and a supported Jacobian mode are required')
        self.env, self.rad, self.inputRecords = loadInputs(withRecords=True)
        # x=r/R(t) 是无量纲材料坐标；控制体权重来自圆柱半径方向的积分。
        self.x = np.linspace(0., 1., settings.intervals + 1)
        self.dx = 1. / settings.intervals
        faces = np.r_[0., (self.x[1:] + self.x[:-1]) / 2., 1.]
        self.w = np.diff(faces ** 2) / 2.
        self.internalFaces = faces[1:-1]
        self.n = len(self.x)
        self.rhoD0 = (760 + 90 * C0) / (1 + C0) if settings.question == 'Q4' else (
            820. / (1 + C0) if settings.question == 'Q1' else (650 + 128 * C0) / (1 + C0))
        self.evaluations = 0
        self.jacPattern = self.buildSparsity()

    def radius(self, t):
        if self.settings.shrink:
            return np.interp(t, self.rad['time_s'], self.rad['radius_m'])
        return np.asarray(t) * 0. + R0

    # 4 h 之后采用已声明的平台延拓；不能把外推段称为实测环境。
    def environment(self, t):
        s = self.settings
        tair = np.interp(t, self.env['time_s'], self.env['temperature_K'])
        ceq = np.interp(t, self.env['time_s'], self.env['air_moisture_kg_per_kg'])
        after = np.asarray(t) > self.env['time_s'][-1]
        if s.boundaryExtension == 'nominal':
            tair = np.where(after, s.tailTemperatureC + 273.15, tair)
            ceq = np.where(after, s.tailEquilibrium, ceq)
        elif s.boundaryExtension == 'tail_mean':
            tail = self.env['time_s'] >= 10800
            tair = np.where(after, self.env['temperature_K'][tail].mean(), tair)
            ceq = np.where(after, self.env['air_moisture_kg_per_kg'][tail].mean(), ceq)
        elif s.boundaryExtension != 'last':
            raise ValueError('Unknown boundary extension')
        return tair, ceq * s.equilibriumScale

    # rho*cp 为有效显热体积容量；干物质量通过独立的积分守恒式约束。
    def properties(self, T, C):
        s = self.settings
        # 仅延拓 Newton 试探点的系数；不裁剪被接受的温度或含水率状态。
        positiveC = np.maximum(C, 1e-12)  # coefficient continuation, never state clipping
        if np.any(T <= 0):
            raise FloatingPointError('Nonpositive absolute temperature')
        wet = positiveC / (1. + positiveC)
        if s.question == 'Q1':
            rho = np.full_like(C, 820.)
            cp = np.full_like(C, 2600.)
            k = np.full_like(C, .36)
            D = 7e-9 * np.exp(-.89 / positiveC)
        elif s.question in ('Q2', 'Q3', 'Q23'):
            rho, cp, k = 650 + 128 * positiveC, 1450 + 2736 * wet, .21 + .38 * wet
            D = 2.4e-3 * np.exp(-.45 / positiveC - 3850 / T)
        elif s.question == 'Q4':
            rho, cp, k = 760 + 90 * positiveC, 1850 + 2150 * wet, .12 + .20 * wet
            D = 4.2e-4 * np.exp(-.30 / positiveC - 3850 / T)
        else:
            raise ValueError(s.question)
        if s.constantD is not None:
            D = np.full_like(C, s.constantD)
        if s.constantThermal:
            rho, cp, k = np.full_like(C, 820.), np.full_like(C, 2600.), np.full_like(C, .36)
        return rho, cp, k, D

    @staticmethod
    def harmonic(a):
        return 2 * a[:-1] * a[1:] / np.maximum(a[:-1] + a[1:], np.finfo(float).tiny)

    def buildSparsity(self):
        p = lil_matrix((2 * self.n + 1, 2 * self.n + 1), dtype=int)
        for i in range(self.n):
            for j in range(max(0, i - 1), min(self.n, i + 2)):
                p[2*i:2*i+2, 2*j:2*j+2] = 1
        p[-1, 2 * (self.n - 1) + 1] = 1
        return p.tocsr()

    # Kirchhoff 势差积分处理强非线性 D(C)，温度因子在同一面上取值。
    def waterInternalFlux(self, T, C, D):
        if self.settings.faceScheme == 'harmonic' or self.settings.constantD is not None:
            return self.internalFaces * self.harmonic(D) * np.diff(C) / self.dx
        if self.settings.faceScheme != 'kirchhoff':
            raise ValueError('Unknown nonlinear face scheme')
        a, D0 = {'Q1':(.89,7e-9), 'Q23':(.45,2.4e-3), 'Q2':(.45,2.4e-3),
                  'Q3':(.45,2.4e-3), 'Q4':(.30,4.2e-4)}[self.settings.question]
        cc = np.maximum(C, 1e-12)
        # 势 F(C)=C*exp(-a/C)+a*Ei(-a/C)，导数为 exp(-a/C)。
        potential = cc * np.exp(-a/cc) + a * expi(-a/cc)
        difference = np.diff(potential)
        small = np.abs(np.diff(cc)) < 1e-7 * np.maximum((cc[:-1]+cc[1:])/2, 1e-3)
        difference[small] = (np.exp(-a/((cc[:-1][small]+cc[1:][small])/2)) * np.diff(cc)[small])
        # 不能对温度因子乘势后的整体作差，否则会引入题设没有的交叉扩散通量。
        thermalFactor = 1. if self.settings.question == 'Q1' else np.exp(-3850/((T[:-1]+T[1:])/2))
        # Do not difference thermal_factor*potential: that would add a false Soret flux.
        return self.internalFaces * D0 * thermalFactor * difference / self.dx

    # 状态交错排列 T0,C0,T1,C1,...，最后一项累计平均失水；共享面通量保证离散守恒。
    def rhs(self, t, state):
        """REVIEW: actual material-control-volume balance, no extra mesh advection."""
        self.evaluations += 1
        T, C = state[:-1:2], state[1:-1:2]
        rho, cp, k, D = self.properties(T, C)
        radius = float(self.radius(t))
        tair, ceq = self.environment(t)
        heatG = np.zeros(self.n + 1)
        waterG = np.zeros(self.n + 1)
        heatG[1:-1] = self.internalFaces * self.harmonic(k) * np.diff(T) / self.dx
        waterG[1:-1] = self.waterInternalFlux(T, C, D)
        # 表面对流传质和传热采用外法向流出约定；中心面面积为零。
        waterG[-1] = -self.settings.beta * radius * (C[-1] - ceq)
        heatG[-1] = -self.settings.h * radius * (T[-1] - tair)
        if self.settings.surfaceLatentFraction:
            # Scenario: all selected outgoing water vaporizes at the surface.
            rhoD = self.rhoD0 * (R0 / radius) ** 2
            jEvap = rhoD * self.settings.beta * (C[-1] - ceq)
            heatG[-1] -= (radius * self.settings.surfaceLatentFraction *
                            self.settings.latentJKg * jEvap)
        derivative = np.empty_like(state)
        # 除以 R(t)^2 与控制体权重得到材料导数；同比收缩无需额外网格对流项。
        derivative[:-1:2] = np.diff(heatG) / (radius ** 2 * self.w * rho * cp)
        derivative[1:-1:2] = np.diff(waterG) / (radius ** 2 * self.w)
        derivative[-1] = 2 * self.settings.beta / radius * (C[-1] - ceq)
        return derivative

    def initial(self):
        state = np.empty(2 * self.n + 1)
        state[:-1:2], state[1:-1:2], state[-1] = T0, C0, 0.
        return state


class Run:
    def __init__(self, model, pieces, elapsed, eventS, cache=None):
        self.model, self.pieces = model, pieces
        self.cache = cache
        self.elapsedS, self.eventS = elapsed, eventS
        self.endS = float(pieces[-1].t[-1])

    def close(self):
        """Release this Run after its exports/checks; further queries are invalid."""
        self.pieces.clear()
        if self.cache is not None:
            self.cache.close()

    def state(self, times):
        tt = np.atleast_1d(np.asarray(times, dtype=float))
        if np.min(tt) < -1e-10 or np.max(tt) > self.endS + 1e-7:
            raise ValueError('Requested time outside solved interval')
        out = np.empty((2 * self.model.n + 1, len(tt)))
        remaining = np.ones(len(tt), dtype=bool)
        for result in self.pieces:
            select = remaining & (tt >= result.t[0]-1e-7) & (tt <= result.t[-1]+1e-7)
            if np.any(select):
                out[:, select] = result.sol(tt[select])
                remaining[select] = False
        if np.any(remaining):
            raise RuntimeError('Missing dense solution segment')
        return out

    # materialX 查询材料坐标；radiiM 查询实际米制半径，收缩域外返回 NaN。
    def fields(self, times, radiiM=None, materialX=None):
        tt = np.atleast_1d(np.asarray(times, dtype=float))
        state = self.state(tt)
        Ts, Cs = state[:-1:2].T, state[1:-1:2].T
        if materialX is not None:
            points = np.asarray(materialX, dtype=float)
            if np.any(~np.isfinite(points)) or np.any((points < 0.) | (points > 1.)):
                raise ValueError('Material coordinates must be finite and within [0,1]')
            return np.array([np.interp(points, self.model.x, row) for row in Ts]), np.array([
                np.interp(points, self.model.x, row) for row in Cs])
        if radiiM is None:
            return Ts, Cs
        radial = np.asarray(radiiM)
        Tout, Cout = [], []
        for i, t in enumerate(tt):
            xx = radial / self.model.radius(t)
            Tout.append(np.interp(xx, self.model.x, Ts[i], left=np.nan, right=np.nan))
            Cout.append(np.interp(xx, self.model.x, Cs[i], left=np.nan, right=np.nan))
        return np.asarray(Tout), np.asarray(Cout)

    # 每块至多 256 个被接受时刻，避免对高网格状态和物性数组再做整域复制。
    def diagnostics(self):
        # Reduce in bounded blocks: a fine full-domain run may contain tens of
        # millions of accepted state values. Diagnostics must not duplicate all
        # of them and four property arrays at the same time.
        minimumC = minimumT = minimumD = minimumProperty = np.inf
        maximumC = maximumT = maximumD = maximumRadialIncrease = -np.inf
        maximumMassResidual = 0.
        for piece in self.pieces:
            for first in range(0, len(piece.t), 256):
                raw = piece.y[:, first:first+256]
                T, C = raw[:-1:2], raw[1:-1:2]
                residual = 2*self.model.w@C + raw[-1] - C0
                rho, cp, k, D = self.model.properties(T.ravel(), C.ravel())
                minimumC, maximumC = min(minimumC,C.min()), max(maximumC,C.max())
                minimumT, maximumT = min(minimumT,T.min()), max(maximumT,T.max())
                minimumD = min(minimumD,D.min())
                maximumD = max(maximumD,D.max())
                minimumProperty = min(minimumProperty,rho.min(),cp.min(),k.min(),D.min())
                maximumRadialIncrease = max(maximumRadialIncrease,np.max(np.diff(C,axis=0)))
                maximumMassResidual = max(maximumMassResidual,np.max(np.abs(residual)))
        final = self.state([self.endS])[:, 0]
        finalC = final[1:-1:2]
        return {
            'event_s': self.eventS, 'event_h': None if self.eventS is None else self.eventS/3600,
            'end_s': self.endS, 'elapsed_s': self.elapsedS,
            'end_time_convention': 'ceil(critical_event_s)+1: conservative post-crossing verification second; not claimed earliest integer second',
            'max_mass_balance_abs_kg_per_kg': float(maximumMassResidual),
            'min_C': float(minimumC), 'max_C': float(maximumC),
            'min_T_K': float(minimumT), 'max_T_K': float(maximumT),
            'min_D': float(minimumD), 'max_D': float(maximumD),
            'positive_properties': bool(minimumProperty > 0),
            'max_radial_C_increase': float(maximumRadialIncrease),
            'final_max_C': float(finalC.max()), 'final_surface_C': float(finalC[-1]),
            'strictly_dry_at_end': bool(finalC.max() < .15),
            'radius_end_m': float(self.model.radius(self.endS)),
            'radius_extrapolation_used': bool(self.model.settings.shrink and self.endS > 259200),
            'rhs_evaluations': self.model.evaluations,
            'accepted_time_points': sum(len(p.t) for p in self.pieces),
            'nfev': sum(p.nfev for p in self.pieces),
            'njev': sum(p.njev for p in self.pieces), 'nlu': sum(p.nlu for p in self.pieces),
            'solver_success': all(p.success for p in self.pieces),
            'dense_storage': self.model.settings.denseStorage,
            'dense_coefficient_bytes': 0 if self.cache is None else self.cache.bytesWritten,
            'dense_polynomial_count': 0 if self.cache is None else self.cache.polynomialCount,
        }


def solveCase(settings: Settings) -> Run:
    started = time.perf_counter()
    if settings.denseStorage not in ('memory', 'disk'):
        raise ValueError('Dense storage must be memory or disk')
    if settings.denseStorage == 'disk' and settings.method != 'BDF':
        raise ValueError('Exact disk dense storage currently supports BDF only')
    cache = diskDense.DenseCache(ROOT) if settings.denseStorage == 'disk' else None
    try:
        return solveCaseImpl(settings, cache, started)
    except BaseException as error:
        if cache is not None:
            try:
                cache.close()
            except BaseException as cleanup_error:
                error.add_note('Private cache cleanup also failed: '+repr(cleanup_error))
        raise


def solveCaseImpl(settings, cache, started):
    model = RadialModel(settings)
    method = diskDense.DiskBDF if cache is not None else settings.method
    jacobianOptions = ({'jac': lambda t, y: analyticJacobian.jacobian(model, t, y)}
        if settings.jacobianMode == 'analytic' else {'jac_sparsity': model.jacPattern})
    if cache is not None:
        jacobianOptions['dense_cache'] = cache
    # 连续事件取整个离散材料域 max(C)=0.15；严格达标还须在事件后重新检查。
    def dryEvent(t, y):
        return float(np.max(y[1:-1:2]) - .15)
    dryEvent.terminal, dryEvent.direction = True, -1
    atol = np.empty(2 * model.n + 1)
    atol[:-1:2], atol[1:-1:2], atol[-1] = settings.atolTemperature, settings.atolMoisture, settings.atolMoisture
    horizon = 1800. if settings.question == 'Q1' else settings.horizonH * 3600.
    pieces, initial, eventS = [], model.initial(), None
    # A separate segment at 4 h makes the modelling extension explicit.
    endpoints = [0., min(14400., horizon)]
    if horizon > 14400.:
        endpoints.append(horizon)
    for left, right in zip(endpoints[:-1], endpoints[1:]):
        piece = solve_ivp(model.rhs, (left, right), initial, method=method,
            rtol=settings.rtol, atol=atol, **jacobianOptions,
            max_step=settings.earlyMaxStepS if left < 14400. else settings.maxStepS,
            events=None if settings.question == 'Q1' else dryEvent, dense_output=True)
        if cache is not None:
            diskDense.alignBdfSegments(piece)
        pieces.append(piece)
        if not piece.success:
            raise RuntimeError(piece.message)
        initial = piece.y[:, -1].copy()
        if cache is not None:
            piece.y = cache.storeAccepted(piece.y)
        if piece.t_events is not None and len(piece.t_events[0]):
            eventS = float(piece.t_events[0][0])
            # Continue to a genuine post-crossing integer second, not an extrapolation.
            # 从实际事件状态继续积分至 ceil(event)+1 秒，不依赖外推或四位舍入。
            end = float(np.ceil(eventS) + 1)
            tail = solve_ivp(model.rhs, (eventS, end), initial, method=method,
                rtol=settings.rtol, atol=atol, **jacobianOptions,
                max_step=1., dense_output=True)
            if cache is not None:
                diskDense.alignBdfSegments(tail)
            if not tail.success:
                raise RuntimeError(tail.message)
            if cache is not None:
                tail.y = cache.storeAccepted(tail.y)
            pieces.append(tail)
            break
    run = Run(model, pieces, time.perf_counter() - started, eventS, cache)
    diagnostic = run.diagnostics()
    if diagnostic['min_C'] < -1e-8 or not diagnostic['positive_properties']:
        raise FloatingPointError('Physical range/positive property check failed')
    if diagnostic['max_mass_balance_abs_kg_per_kg'] > 1e-6:
        raise FloatingPointError('Dry-basis mass balance failed')
    return run


def fileRecord(path):
    p = Path(path)
    return {'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size,
            'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'exists': True}


# 保存 60 s 等审查采样、源码/输入哈希和状态；整秒题表由 exportOutputs 直接查询 live Run。
def saveRun(run: Run, directory: Path):
    codeRecord = fileRecord(Path(__file__))
    if codeRecord['sha256'] != LOADED_CODE_SHA256:
        raise RuntimeError('Solver file changed after import; restart to obtain valid provenance')
    jacobianRecord = fileRecord(Path(analyticJacobian.__file__))
    if jacobianRecord['sha256'] != analyticJacobian.LOADED_CODE_SHA256:
        raise RuntimeError('Jacobian file changed after import; restart to obtain valid provenance')
    storageRecord = fileRecord(Path(diskDense.__file__))
    if storageRecord['sha256'] != diskDense.LOADED_CODE_SHA256:
        raise RuntimeError('Dense storage file changed after import; restart for valid provenance')
    for record in run.model.inputRecords:
        if fileRecord(ROOT/record['path'])['sha256'] != record['sha256']:
            raise RuntimeError('Input changed after being loaded; retain failure and rerun')
    directory.mkdir(parents=True, exist_ok=True)
    times = np.unique(np.r_[np.arange(0., run.endS, 60.),
                [t for t in [100., 300., 600., 900., 1200., 1500., 1800., 3600., 5400., 7200., 9000., 10800.] if t <= run.endS],
                run.endS, [] if run.eventS is None else [run.eventS]])
    x = np.linspace(0., 1., 21)
    temperature, moisture, means, losses = [], [], [], []
    for first in range(0, len(times), 128):
        blockTimes = times[first:first+128]
        Tb, Cb = run.fields(blockTimes, materialX=x)
        raw = run.state(blockTimes)
        temperature.append(Tb); moisture.append(Cb)
        means.append(2*run.model.w@raw[1:-1:2]); losses.append(raw[-1].copy())
    T, C = np.vstack(temperature), np.vstack(moisture)
    np.savez_compressed(directory/'sampled_solution.npz', times_s=times, material_x=x,
        T_K=T, C=C, radius_m=run.model.radius(times), mean_C=np.concatenate(means),
        cumulative_loss=np.concatenate(losses))
    summary = {'settings': asdict(run.model.settings), 'diagnostics': run.diagnostics(),
               'code': codeRecord,
               'jacobian_code': jacobianRecord,
               'dense_storage_code': storageRecord,
               'inputs': run.model.inputRecords,
               'human_review_status': 'pending', 'gui_reproduced': False}
    (directory/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return summary
```

`review_delivery/analyticJacobian.py`（解析稀疏 Jacobian 装配（式 (55)—(59)））

```python
# 本文件为冻结求解源码的驼峰审查副本；来源、改名与 AST 核验见 tools/coreRenameReport.json。
"""Analytic sparse Jacobian for drying_core.RadialModel.rhs.

The ordering is T0,C0,...,TN,CN,A. A is a passive cumulative loss variable;
its entire column is exactly zero and must not use adaptive numdiff factors.
This file does not modify the core or select a production configuration.

Self-check from the contest root:
  C:\\Python314\\python.exe -B paper_output/code/modeling/analytic_jacobian.py --self-test
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import warnings

import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import coo_matrix
from scipy.special import expi


LOADED_CODE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


# 调和平均面对左右节点的解析偏导，供热通量与调和水通量使用。
def harmonicPartials(left, right):
    """Positive-coefficient partials; respect the core's tiny denominator guard."""
    total = left + right
    tiny = np.finfo(float).tiny
    denominator = np.maximum(total, tiny)
    ordinary = total > tiny
    dl = np.where(ordinary, 2 * (right / denominator) ** 2, 2 * right / denominator)
    dr = np.where(ordinary, 2 * (left / denominator) ** 2, 2 * left / denominator)
    return dl, dr


# 稀疏 Jacobian 按交错 T/C 状态组装；保留物性、水通量与容量分母的全部链式法则项。
def jacobian(model, t, y):
    """Return d(rhs)/d(y) as CSC without calling rhs or numerical differentiation.

Each internal face contributes opposite flux derivatives to its two cells.
For heat, differentiating 1/(rho*cp) adds -Tdot*cap_C/cap locally.
Kirchhoff's temperature factor is frozen at the symmetric face temperature;
the primitive's close-concentration branch is differentiated exactly as coded.
"""
    state = np.asarray(y, dtype=float)
    n = model.n
    if state.ndim != 1 or state.size != 2*n + 1:
        raise ValueError("Jacobian requires interleaved 1D state of length 2*n+1")
    s = model.settings
    T, C = state[:-1:2], state[1:-1:2]
    cc = np.maximum(C, 1e-12)
    active = (C > 1e-12).astype(float)
    rho, cp, k, D = model.properties(T, C)
    if s.question == 'Q1':
        a, d0, tempConstant = .89, 7e-9, 0.
        rhoC, cpC, kC = np.zeros(n), np.zeros(n), np.zeros(n)
    elif s.question in ('Q2', 'Q3', 'Q23'):
        a, d0, tempConstant = .45, 2.4e-3, 3850.
        rhoC = np.full(n, 128.) * active
        cpC = 2736. / (1. + cc)**2 * active
        kC = .38 / (1. + cc)**2 * active
    elif s.question == 'Q4':
        a, d0, tempConstant = .30, 4.2e-4, 3850.
        rhoC = np.full(n, 90.) * active
        cpC = 2150. / (1. + cc)**2 * active
        kC = .20 / (1. + cc)**2 * active
    else:
        raise ValueError(s.question)
    if s.constantThermal:
        rhoC, cpC, kC = np.zeros(n), np.zeros(n), np.zeros(n)
    capacity = rho * cp
    capacityC = rhoC * cp + rho * cpC
    if s.constantD is None:
        dC = D * (a / cc**2) * active
        dT = D * tempConstant / T**2
    else:
        dC, dT = np.zeros(n), np.zeros(n)

    radius = float(model.radius(t))
    if radius <= 0:
        raise ValueError("Nonpositive radius")
    tair, ceq = model.environment(t)
    geom = model.internalFaces / model.dx
    deltaT, deltaC = np.diff(T), np.diff(C)

    # Derivative columns for each face are (T_left,C_left,T_right,C_right).
    kHarm = model.harmonic(k)
    khL, khR = harmonicPartials(k[:-1], k[1:])
    # 每个面的四列依次为 T左、C左、T右、C右，对相邻两个控制体施加相反符号。
    heatDeriv = np.column_stack((
        -geom * kHarm,
        geom * khL * kC[:-1] * deltaT,
        geom * kHarm,
        geom * khR * kC[1:] * deltaT,
    ))
    heatG = np.zeros(n + 1)
    heatG[1:-1] = geom * kHarm * deltaT
    heatG[-1] = -s.h * radius * (T[-1] - tair)

    if s.faceScheme == 'harmonic' or s.constantD is not None:
        dh = model.harmonic(D)
        dhL, dhR = harmonicPartials(D[:-1], D[1:])
        waterDeriv = np.column_stack((
            geom * dhL * dT[:-1] * deltaC,
            geom * (dhL * dC[:-1] * deltaC - dh),
            geom * dhR * dT[1:] * deltaC,
            geom * (dhR * dC[1:] * deltaC + dh),
        ))
    elif s.faceScheme == 'kirchhoff':
        primitive = cc * np.exp(-a / cc) + a * expi(-a / cc)
        primitiveDelta = np.diff(primitive)
        meanC = (cc[:-1] + cc[1:]) / 2.
        meanT = (T[:-1] + T[1:]) / 2.
        deltaCc = np.diff(cc)
        small = np.abs(deltaCc) < 1e-7 * np.maximum(meanC, 1e-3)
        expLeft, expRight = np.exp(-a/cc[:-1]), np.exp(-a/cc[1:])
        primitiveL = -expLeft * active[:-1]
        primitiveR = expRight * active[1:]
        # 近等浓度时对实际 RHS 使用的中点分支求导，避免与求解器分支不一致。
        if np.any(small):
            fMid = np.exp(-a / meanC[small])
            fPrimeMid = fMid * a / meanC[small]**2
            primitiveDelta[small] = fMid * deltaCc[small]
            primitiveL[small] = (0.5*fPrimeMid*deltaCc[small]-fMid)*active[:-1][small]
            primitiveR[small] = (0.5*fPrimeMid*deltaCc[small]+fMid)*active[1:][small]
        temperatureFactor = np.exp(-tempConstant / meanT)
        coefficient = geom * d0 * temperatureFactor
        waterG = coefficient * primitiveDelta
        waterT = waterG * tempConstant / (2 * meanT**2)
        waterDeriv = np.column_stack((waterT, coefficient*primitiveL,
                                      waterT, coefficient*primitiveR))
    else:
        raise ValueError('Unknown nonlinear face scheme')

    heatScale = 1. / (radius**2 * model.w * capacity)
    waterScale = 1. / (radius**2 * model.w)
    surfaceHeatC = 0.
    if s.surfaceLatentFraction:
        rhoD = model.rhoD0 * (.02 / radius)**2
        surfaceHeatC = -radius*s.surfaceLatentFraction*s.latentJKg*rhoD*s.beta
        heatG[-1] += surfaceHeatC * (C[-1] - ceq)
    tempDerivative = np.diff(heatG) * heatScale

    faceIndex = np.arange(n-1)
    faceColumns = np.column_stack((2*faceIndex, 2*faceIndex+1,
                                    2*faceIndex+2, 2*faceIndex+3)).ravel()
    rows, columns, values = [], [], []

    def addFace(rowIndex, derivatives, factor):
        rows.append(np.repeat(rowIndex, 4))
        columns.append(faceColumns)
        values.append((derivatives * factor[:, None]).ravel())

    addFace(2*faceIndex, heatDeriv, heatScale[:-1])
    addFace(2*faceIndex+2, heatDeriv, -heatScale[1:])
    addFace(2*faceIndex+1, waterDeriv, waterScale[:-1])
    addFace(2*faceIndex+3, waterDeriv, -waterScale[1:])
    cellIndex = np.arange(n)
    rows.append(2*cellIndex)
    columns.append(2*cellIndex+1)
    # 热容量随 C 改变，必须保留 -Tdot*(容量对C偏导)/容量 这一局部项。
    values.append(-tempDerivative * capacityC / capacity)
    rows.append(np.array([2*n-2, 2*n-2, 2*n-1, 2*n]))
    columns.append(np.array([2*n-2, 2*n-1, 2*n-1, 2*n-1]))
    values.append(np.array([-s.h*radius*heatScale[-1],
                            surfaceHeatC*heatScale[-1],
                            -s.beta*radius*waterScale[-1], 2*s.beta/radius]))
    # 面模板只有邻近耦合；COO 合并重复贡献后转 CSC，交给 BDF 稀疏线性求解。
    matrix = coo_matrix((np.concatenate(values),
                        (np.concatenate(rows), np.concatenate(columns))),
                       shape=(2*n+1, 2*n+1)).tocsc()
    matrix.sum_duplicates()
    matrix.eliminate_zeros()
    return matrix


# 此历史自检入口仅验证导数和小网格接线，不能替代正式网格与人工代码审核。
def selfTest(outputDirectory):
    """Independent RHS perturbation checks, a conservation derivative, and tiny BDF runs."""
    import scipy
    from dryingCore import ROOT, Settings, RadialModel, LOADED_CODE_SHA256 as CORE_LOADED_CODE_SHA256

    started = time.perf_counter()
    rng = np.random.default_rng(20260910)
    relativeTolerance, absoluteTolerance = 5e-6, 5e-10
    cases = []
    for question in ['Q1', 'Q23', 'Q4']:
        for scheme in ['harmonic', 'kirchhoff']:
            for latent in [0., 1.]:
                cases.append(Settings(question=question, intervals=8, faceScheme=scheme,
                                      shrink=(question=='Q4'), surfaceLatentFraction=latent))
    for question in ['Q1', 'Q23', 'Q4']:
        for constantDiffusivity, constantThermal in [(2e-9, False), (None, True), (2e-9, True)]:
            cases.append(Settings(question=question, intervals=8, faceScheme='kirchhoff',
                                  shrink=(question=='Q4'), constantD=constantDiffusivity,
                                  constantThermal=constantThermal, surfaceLatentFraction=1.))
    records, failures = [], []
    for settings in cases:
        model = RadialModel(settings)
        x = model.x
        states = {
            'initial': (0., model.initial()),
            'nonuniform': (18000., model.initial()),
            'late_dry': (150000., model.initial()),
            'near_uniform_small_branch': (14401., model.initial()),
        }
        states['nonuniform'][1][:-1:2] = 303. + 17.*x**2
        states['nonuniform'][1][1:-1:2] = 2.4 - 2.0*x**2
        states['late_dry'][1][:-1:2] = 321. + 2.0*x**2
        states['late_dry'][1][1:-1:2] = .175 - .115*x**2
        states['near_uniform_small_branch'][1][:-1:2] = 303. + 17.*x**2
        states['near_uniform_small_branch'][1][1:-1:2] = .15 + 1e-10*x
        for stateName, (t, y) in states.items():
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter('always')
                matrix = jacobian(model, t, y)
                vectors = []
                for _ in range(4):
                    direction = rng.normal(size=y.size)
                    direction[:-1:2] *= 1.0
                    direction[1:-1:2] *= .02
                    direction[-1] = .3
                    vectors.append(direction)
                directional = []
                for direction in vectors:
                    predicted = matrix @ direction
                    steps = []
                    for step in [1e-4, 3e-5, 1e-5]:
                        finiteDifference = (model.rhs(t, y+step*direction)-
                                             model.rhs(t, y-step*direction))/(2*step)
                        absoluteError = float(np.max(np.abs(predicted-finiteDifference)))
                        scale = max(float(np.max(np.abs(predicted))),
                                    float(np.max(np.abs(finiteDifference))), 1e-30)
                        scaled = float(np.max(np.abs(predicted-finiteDifference)/
                            (absoluteTolerance + relativeTolerance*np.maximum(
                                np.abs(predicted), np.abs(finiteDifference)))))
                        steps.append({'step':step, 'max_abs_error':absoluteError,
                                      'relative_inf_error':absoluteError/scale,
                                      'max_component_tolerance_ratio':scaled})
                    best = min(steps, key=lambda item:item['max_component_tolerance_ratio'])
                    directional.append({'all_step_errors':steps, 'best':best})
                passive = np.zeros(y.size); passive[-1] = 1.
                passiveAnalytic = float(np.max(np.abs(matrix @ passive)))
                passiveFd = float(np.max(np.abs(model.rhs(t, y+passive)-model.rhs(t,y-passive))))
                massWeights = np.zeros(y.size)
                massWeights[1:-1:2] = 2*model.w
                massWeights[-1] = 1.
                conservation = float(np.max(np.abs(np.asarray(massWeights @ matrix))))
            warningMessages = [str(w.message) for w in captured]
            passed = (all(step['max_component_tolerance_ratio'] <= 1
                          for d in directional for step in d['all_step_errors'])
                      and passiveAnalytic == 0 and passiveFd == 0 and conservation < 1e-11
                      and np.isfinite(matrix.data).all() and not warningMessages)
            record = {'settings':asdict(settings), 'state':stateName, 'time_s':t,
                      'status':'PASS' if passed else 'FAIL', 'matrix_shape':matrix.shape,
                      'matrix_nnz':matrix.nnz, 'directional_checks':directional,
                      'passive_column_analytic_abs':passiveAnalytic,
                      'passive_column_finite_difference_abs':passiveFd,
                      'mass_balance_derivative_abs':conservation, 'warnings':warningMessages}
            records.append(record)
            if not passed:
                failures.append(f"{settings.question}/{settings.faceScheme}/latent={settings.surfaceLatentFraction}/{stateName}/constant_D={settings.constantD}/constant_thermal={settings.constantThermal}")
    smokeRecords = []
    for scheme in ['harmonic', 'kirchhoff']:
        for question in ['Q23', 'Q4']:
            settings = Settings(question=question, intervals=8, faceScheme=scheme,
                                shrink=(question=='Q4'), surfaceLatentFraction=1.)
            model = RadialModel(settings)
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter('always')
                result = solve_ivp(model.rhs, (0., 2.), model.initial(), method='BDF',
                                   jac=lambda t,y:jacobian(model,t,y), rtol=1e-10,
                                   atol=1e-12, max_step=.2)
            msgs = [str(w.message) for w in captured]
            passed = bool(result.success and np.isfinite(result.y).all() and not msgs)
            smokeRecords.append({'question':question, 'face_scheme':scheme, 'interval_s':[0,2],
                                  'status':'PASS' if passed else 'FAIL', 'warnings':msgs,
                                  'nfev':result.nfev, 'njev':result.njev, 'nlu':result.nlu,
                                  'purpose':'Short Jacobian/BDF wiring check, not production accuracy'})
            if not passed:
                failures.append(f"BDF_smoke/{question}/{scheme}")
    currentSourceHash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    currentCoreHash = hashlib.sha256((ROOT/'paper_output/code/review_delivery/dryingCore.py').read_bytes()).hexdigest()
    if currentSourceHash != LOADED_CODE_SHA256 or currentCoreHash != CORE_LOADED_CODE_SHA256:
        failures.append('Source file changed after module load during validation')
    report = {'schema_version':'1.0', 'created_utc':datetime.now(timezone.utc).isoformat(),
              'status':'PASS' if not failures else 'FAIL', 'failures':failures,
              'source_sha256':LOADED_CODE_SHA256,
              'core_sha256':CORE_LOADED_CODE_SHA256,
              'source_hash_policy':'SHA-256 frozen when each module is imported; files checked unchanged before report save.',
              'runtime':{'python':sys.version,'executable':sys.executable,'numpy':np.__version__,'scipy':scipy.__version__},
              'seed':20260910,'relative_component_tolerance':relativeTolerance,
              'absolute_component_tolerance':absoluteTolerance,
              'finite_difference_policy':'Central directional differences, three decreasing steps; every step must satisfy the mixed absolute/relative component tolerance. Best comparison is supplementary only.',
              'case_state_count':len(records), 'direction_count':4*len(records),
              'checks':records,'short_BDF_checks':smokeRecords,
              'elapsed_s':time.perf_counter()-started,
              'limitations':['No full production run or grid convergence performed here.',
                             'Tiny denominator/underflow extensions at nonphysical Newton probes are not calibrated physical data.',
                             'Only this module and the short tests use analytic Jacobian until main agent hooks core.',
                             'Visual Studio reproduction and human review remain pending.']}
    outputDirectory.mkdir(parents=True, exist_ok=True)
    (outputDirectory/'analytic_jacobian_selftest.json').write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    brief = {key:report[key] for key in ['status','failures','case_state_count','direction_count','elapsed_s']}
    brief['max_best_component_tolerance_ratio'] = max(
        d['best']['max_component_tolerance_ratio'] for r in records for d in r['directional_checks'])
    brief['max_all_steps_component_tolerance_ratio'] = max(
        step['max_component_tolerance_ratio'] for r in records
        for d in r['directional_checks'] for step in d['all_step_errors'])
    brief['max_mass_balance_derivative_abs'] = max(r['mass_balance_derivative_abs'] for r in records)
    brief['warning_count'] = sum(len(r['warnings']) for r in records+smokeRecords)
    print(json.dumps(brief,ensure_ascii=False,indent=2))
    return 0 if not failures else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--output-dir', type=Path,
        default=Path(__file__).resolve().parents[2]/'code/review_delivery/runtime/jacobianValidation')
    arguments = parser.parse_args()
    if not arguments.self_test:
        parser.error('Use --self-test, or import jacobian(model,t,y) from this module.')
    raise SystemExit(selfTest(arguments.output_dir))
```

`review_delivery/diskDense.py`（稠密输出的磁盘存储与任意时刻插值）

```python
# 本文件为冻结求解源码的驼峰审查副本；来源、改名与 AST 核验见 tools/coreRenameReport.json。
"""Exact BDF dense polynomials backed by a private, rebuildable disk cache.

This changes storage only: each accepted BDF polynomial is written as float64
bytes, then evaluated with SciPy's original BdfDenseOutput implementation.
No additional time/space interpolation and no solver restart are introduced.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import tempfile
import numpy as np
from scipy.integrate import OdeSolution
from scipy.integrate._ivp.bdf import BDF, BdfDenseOutput
from scipy.integrate._ivp.base import DenseOutput

LOADED_CODE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


# 每个 Run 独享项目内可重建缓存；存原始 float64 字节，不降低插值阶数。
class DenseCache:
    def __init__(self, root):
        self.parent = (Path(root)/'tmp/cache/solver_runs').resolve()
        if not self.parent.is_relative_to(Path(root).resolve()):
            raise ValueError('Private solver cache must remain in this project')
        self.parent.mkdir(parents=True, exist_ok=True)
        self.directory = Path(tempfile.mkdtemp(prefix='bdf_', dir=self.parent)).resolve()
        try:
            self.handle = (self.directory/'polynomials.bin').open('w+b', buffering=0)
        except BaseException as error:
            try:
                self.directory.rmdir()
            except OSError as cleanup_error:
                error.add_note('Private cache directory cleanup failed: '+repr(cleanup_error))
            raise
        self.bytesWritten = 0
        self.polynomialCount = 0
        self.acceptedArrays = []
        self.closed = False

    def append(self, values):
        if self.closed:
            raise RuntimeError('Dense solution cache is closed')
        array = np.ascontiguousarray(values, dtype=np.float64)
        offset = self.bytesWritten
        self.handle.seek(offset)
        array.tofile(self.handle)
        self.bytesWritten += array.nbytes
        self.polynomialCount += 1
        return offset, array.shape

    def read(self, offset, shape):
        if self.closed:
            raise RuntimeError('Dense solution cache is closed')
        count = int(np.prod(shape))
        self.handle.seek(offset)
        values = np.fromfile(self.handle, dtype=np.float64, count=count)
        if values.size != count:
            raise IOError('Incomplete BDF coefficient cache')
        return values.reshape(shape)

    # 被接受的整段状态写为磁盘映射数组，以限制长时高网格运行的常驻内存。
    def storeAccepted(self, values):
        path = self.directory/f'accepted_{len(self.acceptedArrays):03d}.npy'
        mapped = np.lib.format.open_memmap(path, mode='w+', dtype=values.dtype, shape=values.shape)
        # Register before writing so failures can close this Windows mapping.
        self.acceptedArrays.append(mapped)
        mapped[:] = values
        mapped.flush()
        return mapped

    # 先释放 Windows 文件映射，再仅清理当前对象创建并验证过的私有缓存。
    def close(self):
        if self.closed:
            return
        self.handle.close()
        for array in self.acceptedArrays:
            array._mmap.close()
        self.acceptedArrays.clear()
        # Delete only the verified private cache created by this object.
        if self.directory.parent != self.parent or not self.directory.name.startswith('bdf_'):
            raise RuntimeError('Unexpected private cache path; cleanup refused')
        for path in self.directory.iterdir():
            if not path.is_file() or path.is_symlink():
                raise RuntimeError('Unexpected cache entry; cleanup refused')
            path.unlink()
        self.directory.rmdir()
        self.closed = True


class FileBdfDenseOutput(DenseOutput):
    def __init__(self, original, cache):
        super().__init__(original.t_old, original.t)
        self.order = original.order
        self.t_shift = original.t_shift.copy()
        self.denom = original.denom.copy()
        self.cache = cache
        self.offset, self.shape = cache.append(original.D)

    # 保留 SciPy override 名，调用安装版本的原生 BDF 多项式求值器。
    def _call_impl(self, t):
        # Reuse the installed SciPy evaluator with the exact recorded D bytes.
        dense = object.__new__(BdfDenseOutput)
        dense.D = self.cache.read(self.offset, self.shape)
        dense.t_shift, dense.denom = self.t_shift, self.denom
        return dense._call_impl(t)


# dense_cache 是 solve_ivp 注入此子类的协议参数，保留拼写以维持接口。
class DiskBDF(BDF):
    def __init__(self, *args, dense_cache, **kwargs):
        self.dense_cache = dense_cache
        super().__init__(*args, **kwargs)

    def _dense_output_impl(self):
        return FileBdfDenseOutput(super()._dense_output_impl(), self.dense_cache)


# 子类不命中 SciPy 对 BDF 的类身份判断，故恢复其接受断点右侧多项式选择。
def alignBdfSegments(result):
    """Restore the original BDF convention at accepted time breakpoints.

    SciPy solve_ivp tests the exact method class for alt_segment. A subclass
    otherwise selects the opposite polynomial at a shared knot. Reconstructing
    OdeSolution changes only this selection, never coefficients or integration.
    """
    if result.sol is not None:
        result.sol = OdeSolution(result.sol.ts, result.sol.interpolants, alt_segment=True)
```

`review_delivery/exportOutputs.py`（按附件 3 模板导出 result1—4.xlsx（域外留空、真实表面独立列、四位小数））

```python
# 本文件为冻结求解源码的驼峰审查副本；来源、改名与 AST 核验见 tools/coreRenameReport.json。
"""Stream contest A output directly from a live Run, then stream-read it.

The original contest templates have precedence over workbook design defaults.
The requested openpyxl write_only method bounds authoring memory. No 60-second
NPZ is used to fabricate per-second output. Unrounded values on the requested
physical output grid are archived separately as a compressed CSV; all N solver
nodes are deliberately not duplicated in this archive.

Usage by the final runner:
    record = export_question(run, 'Q2', output_directory)
    validation = validate_exports([record], runs={'Q2': run})

The archive is an internal reproducibility artifact, not automatically part of
the size-limited submission package. Nothing is silently truncated or deleted.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import gzip
import hashlib
import inspect
import json
import math
from pathlib import Path
import re
import sys
import tempfile
import time

import numpy as np
from openpyxl import Workbook, load_workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve()
LOADED_EXPORTER_SHA256 = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
TEMPLATE_DIR = ROOT / 'problem_files/CUMCM2026Problems/A题/附件/附件3'
RADII_M = np.arange(21, dtype=float)*0.001
RADII_CM = [i/10 for i in range(21)]
NUMBER_FORMAT = '0.0000'
SIZE_LIMIT_BYTES = 20_000_000  # report also MiB; do not reinterpret an ambiguous M upward


def sha256File(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as fh:
        for block in iter(lambda:fh.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def exportFileRecord(path, role=None):
    path=Path(path).resolve()
    result={'path':path.relative_to(ROOT).as_posix(),'absolute_path':str(path),
            'bytes':path.stat().st_size,'sha256':sha256File(path),'exists':True}
    if role:
        result['role']=role
    return result


def writeJson(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def normalizeQuestionId(questionId):
    value=str(questionId).upper()
    if value in ['1','2','3','4']:
        value='Q'+value
    if value not in ['Q1','Q2','Q3','Q4']:
        raise ValueError('Export requires Q1, Q2, Q3 or Q4')
    return value


def outputTimes(questionId,end,event):
    if questionId=='Q1':
        if end<1800-1e-7:
            raise ValueError('Q1 requires a solved interval covering 0..1800s')
        return np.arange(1801,dtype=float)
    if questionId=='Q2':
        if abs(end-round(end))>1e-7:
            raise ValueError('Q2 needs an integer post-crossing verification endpoint')
        return np.arange(int(round(end))+1,dtype=float)
    if event is None:
        raise ValueError('Q3/Q4 final export requires an actual critical drying event')
    if not 0<=event<=end:
        raise ValueError('Critical event must lie inside the solved interval')
    return np.unique(np.r_[np.arange(math.floor(end/60)+1,dtype=float)*60,event,end])


def roundFourDecimals(x):
    if x is None:
        return None
    if not math.isfinite(float(x)):
        raise ValueError('A non-finite value cannot be exported as a numerical result')
    return float(round(float(x),4))


def loadTemplate(questionId):
    path=TEMPLATE_DIR/f'result{questionId[-1]}.xlsx'
    wb=load_workbook(path,read_only=True,data_only=False)
    try:
        header=next(wb.worksheets[0].iter_rows(values_only=True))
        names=wb.sheetnames
        return {'record':exportFileRecord(path,'original_result_template'),'time_header':header[0],
                'sheet_names':names,'surface_header':header[-1] if questionId=='Q4' else None}
    finally:
        wb.close()


def runProvenance(run):
    module=sys.modules[run.model.__class__.__module__]
    core=Path(inspect.getfile(run.model.__class__)).resolve()
    loaded=getattr(module,'LOADED_CODE_SHA256',None)
    if loaded is not None and loaded!=sha256File(core):
        raise RuntimeError('Core file changed after this Run implementation was imported')
    if sha256File(SOURCE)!=LOADED_EXPORTER_SHA256:
        raise RuntimeError('Exporter changed after import; restart for consistent provenance')
    inputRecords=list(getattr(run.model,'inputRecords',[]))
    for rec in inputRecords:
        if sha256File(ROOT/rec['path'])!=rec['sha256']:
            raise RuntimeError('Observed input changed after solve: '+rec['path'])
    return {'core':exportFileRecord(core,'solver_source'),'exporter':exportFileRecord(SOURCE,'exporter_source'),
            'inputs':inputRecords,'settings':asdict(run.model.settings),
            'event_s':None if run.eventS is None else float(run.eventS),
            'end_s':float(run.endS),'source_kind':'live_Run_dense_solution',
            'per_second_values_are_not_interpolated_from_60s_npz':True}


# 固定 21 个物理半径逐块查询，Q4 域外保持空白；实际表面单独用 x=1 查询。
def fieldBlock(run,times,qid):
    T,C=run.fields(times,radiiM=RADII_M)
    radius=np.asarray(run.model.radius(times),dtype=float)
    if radius.ndim==0:
        radius=np.full(len(times),radius)
    surfaceC=None
    if qid=='Q4':
        _,surface=run.fields(times,materialX=np.array([1.0]))
        surfaceC=surface[:,0]
        inside=RADII_M[None,:] <= radius[:,None]+1e-12
        # A difference below 1e-12 m at a grid/surface coincidence is roundoff.
        nearBoundary=inside & (~np.isfinite(C))
        if np.any(nearBoundary):
            C=np.where(nearBoundary,surfaceC[:,None],C)
        T=np.where(inside,T,np.nan)
        C=np.where(inside,C,np.nan)
        if not np.all(np.isfinite(C[inside])) or not np.all(np.isfinite(surfaceC)):
            raise ValueError('Non-finite moisture inside Q4 domain')
    else:
        inside=np.ones_like(C,dtype=bool)
        if not np.all(np.isfinite(T)) or not np.all(np.isfinite(C)):
            raise ValueError('Non-finite output inside fixed domain')
    return T-273.15,C,radius,surfaceC,inside


def rawHeaders(qid):
    h=['time_s','radius_m']
    if qid in ['Q1','Q2']:
        h += [f'T_C_r_{i/10:.1f}_cm' for i in range(21)]
    h += [f'C_r_{i/10:.1f}_cm' for i in range(21)]
    if qid=='Q4':
        h += ['C_surface']
    return h


def rawRow(qid,t,T,C,R,surface,inside):
    row=[float(t),float(R)]
    if qid in ['Q1','Q2']:
        row+=list(map(float,T))
    row += [float(c) if valid else None for c,valid in zip(C,inside)]
    if qid=='Q4':
        row.append(float(surface))
    return row


def roundedSheets(qid,raw):
    t,R=raw[:2]
    if qid in ['Q1','Q2']:
        return {'温度':[roundFourDecimals(t)]+[roundFourDecimals(v) for v in raw[2:23]],
                '水分浓度':[roundFourDecimals(t)]+[roundFourDecimals(v) for v in raw[23:44]]}
    if qid=='Q3':
        return {'Sheet1':[roundFourDecimals(t)]+[roundFourDecimals(v) for v in raw[2:23]]}
    return {'Sheet1':[roundFourDecimals(t)]+[roundFourDecimals(v) for v in raw[2:24]],
            '半径':[roundFourDecimals(t),roundFourDecimals(R*100)]}


# 按官方表头设置工作簿；write_only 流式输出降低大题表的内存峰值。
def createSheet(wb,name,header):
    ws=wb.create_sheet(name)
    ws.freeze_panes='B2'
    ws.sheet_view.showGridLines=False
    ws.column_dimensions['A'].width=30
    for j in range(2,len(header)+1):
        ws.column_dimensions[get_column_letter(j)].width=13 if j<len(header) else 16
    ws.row_dimensions[1].height=34
    cells=[]
    for value in header:
        cell=WriteOnlyCell(ws,value=value)
        cell.font=Font(name='Arial',size=10,bold=True,color='FFFFFF')
        cell.fill=PatternFill(fill_type='solid',fgColor='334155')
        cell.alignment=Alignment(horizontal='center',vertical='center',wrap_text=True)
        if isinstance(value,(int,float)):
            cell.number_format='0.0'
        cells.append(cell)
    # write_only's first append opens a temporary worksheet XML file. Keep
    # those rebuildable files in this contest workspace instead of OS Temp.
    cache=ROOT/'tmp/cache/openpyxl_exports'
    cache.mkdir(parents=True,exist_ok=True)
    previousTempdir=tempfile.tempdir
    try:
        tempfile.tempdir=str(cache)
        ws.append(cells)
    finally:
        tempfile.tempdir=previousTempdir
    return ws


def appendNumeric(ws,row):
    cells=[]
    for value in row:
        if value is None:
            cells.append(None)
        else:
            cell=WriteOnlyCell(ws,value=value)
            cell.number_format=NUMBER_FORMAT
            cells.append(cell)
    ws.append(cells)


# 正文表独立生成，单位和显示位数跟随题目模板，原精度数值另存。
def paperTables(run,qid,directory):
    if qid=='Q1':
        ts=np.array([100,300,600,900,1200,1500,1800],dtype=float)
    elif qid=='Q2':
        ts=np.arange(1,7,dtype=float)*1800
        if run.endS<10800-1e-7:
            raise ValueError('Q2 paper tables require 3h of actual solution')
    else:
        from q3Model import completion
        reportedEnd=completion(run)['reported_time_s']
        ts=np.unique(np.r_[np.arange(21600.,reportedEnd+1e-8,21600.),reportedEnd])
    rs=np.array([0.,.005,.01,.015,.02])
    T,C=run.fields(ts,radiiM=rs)
    T=T-273.15
    R=np.asarray(run.model.radius(ts))
    headers=['时间/s' if qid=='Q1' else '时间/h']+[0,0.5,1,1.5,2]
    if qid=='Q4':
        headers += ['药材表面']
        _,Cs=run.fields(ts,materialX=[1.])
    outputs=[]
    fields=[('temperature',T),('moisture',C)] if qid in ['Q1','Q2'] else [('moisture',C)]
    for kind,values in fields:
        path=directory/f'{qid.lower()}_paper_{kind}.csv'
        with path.open('w',encoding='utf-8-sig',newline='') as fh:
            w=csv.writer(fh);w.writerow(headers)
            for i,t in enumerate(ts):
                row=[f'{t if qid=="Q1" else t/3600:.4f}']
                for j,r in enumerate(rs):
                    outside=qid=='Q4' and r>R[i]+1e-12
                    value=values[i,j]
                    if not outside and not np.isfinite(value) and qid=='Q4' and abs(r-R[i])<=1e-12:
                        value=Cs[i,0]
                    row.append('' if outside else f'{float(value):.4f}')
                if qid=='Q4':
                    row += [f'{Cs[i,0]:.4f}']
                w.writerow(row)
        outputs.append(exportFileRecord(path,'paper_table'))
    if qid=='Q4':
        path=directory/'q4_paper_radius.csv'
        with path.open('w',encoding='utf-8-sig',newline='') as fh:
            w=csv.writer(fh);w.writerow(['时间/h','表面半径/cm'])
            w.writerows([[f'{t/3600:.4f}',f'{r*100:.4f}'] for t,r in zip(ts,R)])
        outputs.append(exportFileRecord(path,'paper_surface_coordinates'))
    return outputs


def validatePaperTables(manifest,run):
    """Re-read every paper CSV cell and query the live solution independently.

    Do not call _paper_tables or reuse its generated values. The question's
    schedule is reconstructed here. Physical points come from validated CSV
    headers; the final query uses completion's actual seconds, never the
    rounded hour label parsed back from the CSV.
    """
    qid=manifest['question_id']
    if run is None:
        return {'status':'NOT_REQUESTED','checked_cells':0,'files':[],
                'scope':'Paper CSV hashes only; no independent live Run available.'},[]
    errors=[];records=manifest['paper_tables'];completionInfo=None
    if qid=='Q1':
        times=np.asarray([100.,300.,600.,900.,1200.,1500.,1800.])
        expectedKinds=['temperature','moisture']
    elif qid=='Q2':
        times=1800.*np.arange(1,7)
        expectedKinds=['temperature','moisture']
    else:
        from q3Model import completion
        completionInfo=completion(run)
        finalS=float(completionInfo['reported_time_s'])
        # Integer multiples strictly before the report, then the report itself.
        # Construct afresh rather than reading generation-time arrays/labels.
        regular=[21600.*k for k in range(1,math.floor(finalS/21600.)+1)
                 if 21600.*k<finalS-1e-8]
        times=np.asarray([*regular,finalS],dtype=float)
        expectedKinds=['moisture']+(['radius'] if qid=='Q4' else [])
        stored=manifest.get('paper_table_time_contract',{})
        for key in ['reported_time_s','reported_drying_time_h']:
            if key not in stored or not numericEqual(stored[key],completionInfo[key]):
                errors.append('Paper CSV report-time metadata differs from independent completion: '+key)
        if not numericEqual(stored.get('reported_time_h'),completionInfo['reported_drying_time_h']):
            errors.append('Paper CSV reported_time_h alias differs from independent completion')
    if times[-1]>run.endS+1e-7:
        errors.append('Paper CSV contract exceeds the live solution horizon')
        return {'status':'FAIL','checked_cells':0,'files':[]},errors
    expectedNames={f'{qid.lower()}_paper_{kind}.csv':kind for kind in expectedKinds}
    actualNames=[Path(r['path']).name for r in records]
    if set(actualNames)!=set(expectedNames) or len(actualNames)!=len(expectedNames):
        errors.append('Missing, duplicate, or unexpected paper CSV artifact')
    files=[];totalCells=0
    for rec in records:
        path=ROOT/rec['path'];kind=expectedNames.get(path.name)
        if kind is None:continue
        beforeErrors=len(errors)
        with path.open('r',encoding='utf-8-sig',newline='') as fh:
            reader=csv.reader(fh);header=next(reader,None);rows=list(reader)
        desiredTime='时间/s' if qid=='Q1' else '时间/h'
        if kind=='radius':
            correctHeader=['时间/h','表面半径/cm']
            if header!=correctHeader:
                errors.append(path.name+': radius/time units or header mismatch')
                continue
            radii=None
            expected=np.asarray(run.model.radius(times),dtype=float).reshape(-1,1)*100.
            inside=np.ones_like(expected,dtype=bool)
            unit='cm';surfaceColumn=None
        else:
            wantedColumns=7 if qid=='Q4' else 6
            if header is None or len(header)!=wantedColumns or header[0]!=desiredTime:
                errors.append(path.name+': time/column header mismatch');continue
            try:
                radii=np.asarray([float(v)*.01 for v in header[1:6]])
            except ValueError:
                errors.append(path.name+': nonnumeric physical-radius header');continue
            if not np.all(np.isfinite(radii)) or not np.allclose(radii,[0.,.005,.01,.015,.02],rtol=0,atol=1e-12):
                errors.append(path.name+': physical-radius grid must be 0,0.5,1,1.5,2 cm');continue
            if qid=='Q4' and header[-1]!='药材表面':
                errors.append(path.name+': distinct material surface column missing');continue
            temperature,moisture=run.fields(times,radiiM=radii)
            expected=np.asarray(temperature)-273.15 if kind=='temperature' else np.asarray(moisture)
            inside=np.ones_like(expected,dtype=bool);surfaceColumn=None
            if qid=='Q4':
                physicalR=np.asarray(run.model.radius(times),dtype=float)
                inside=radii[None,:] <= physicalR[:,None]+1e-12
                _,surfaceValues=run.fields(times,materialX=np.asarray([1.]))
                # Only roundoff at a coincident physical/surface coordinate
                # may use the separately queried material surface value.
                coincidence=np.abs(radii[None,:]-physicalR[:,None])<=1e-12
                expected=np.where(coincidence & ~np.isfinite(expected),surfaceValues,expected)
                expected=np.column_stack([expected,surfaceValues[:,0]])
                inside=np.column_stack([inside,np.ones(len(times),dtype=bool)])
                surfaceColumn=7
            unit='degC' if kind=='temperature' else 'kg/kg'
        if len(rows)!=len(times):
            errors.append(f'{path.name}: expected {len(times)} data rows, read {len(rows)}')
        checked=0;blanks=0;maxFieldError=0.;maxTimeError=0.
        for i,(row,t) in enumerate(zip(rows,times)):
            if len(row)!=len(header):
                errors.append(f'{path.name}: column count mismatch at row {i+2}');continue
            timeValue=float(t if qid=='Q1' else t/3600.)
            if row[0]!=format(timeValue,'.4f'):
                errors.append(f'{path.name}: time label mismatch at row {i+2}; query time is {t:.17g}s')
            else:maxTimeError=max(maxTimeError,abs(float(row[0])-timeValue))
            checked+=1
            for j,cell in enumerate(row[1:]):
                checked+=1
                if not inside[i,j]:
                    blanks+=1
                    if cell!='':errors.append(f'{path.name}: domain outside must be blank at row {i+2}, column {j+2}')
                    continue
                value=float(expected[i,j])
                if not math.isfinite(value):
                    errors.append(f'{path.name}: live value is not finite inside material');continue
                if not re.fullmatch(r'-?\d+\.\d{4}',cell):
                    errors.append(f'{path.name}: finite four-decimal number required at row {i+2}, column {j+2}')
                    continue
                actual=float(cell)
                if not math.isfinite(actual) or abs(actual-float(format(value,'.4f')))>1e-10:
                    errors.append(f'{path.name}: independently queried value mismatch at row {i+2}, column {j+2}')
                maxFieldError=max(maxFieldError,abs(actual-value))
        totalCells+=checked
        files.append({'artifact':exportFileRecord(path),'kind':kind,'status':'PASS' if len(errors)==beforeErrors else 'FAIL',
            'header':header,'data_rows':len(rows),'expected_data_rows':len(times),'checked_cells':checked,
            'source_query_times_s':times.tolist(),'display_time_unit':'s' if qid=='Q1' else 'h',
            'max_display_time_rounding_error':maxTimeError,'field_unit':unit,
            'max_field_rounding_error_from_live_value':maxFieldError,'outside_domain_blank_cells':blanks,
            'physical_radii_m':None if radii is None else radii.tolist(),
            'surface_column_1based':surfaceColumn,'surface_query':'material_x=1; never fixed 2 cm' if surfaceColumn else None})
    return {'status':'FAIL' if errors else 'PASS','checked_cells':totalCells,'files':files,
        'completion':completionInfo,'completion_source':exportFileRecord(SOURCE.with_name('q3Model.py')) if completionInfo else None,
        'scope':'Every paper CSV cell independently re-evaluated from live Run and fixed question contracts; no generation arrays or 60s archives reused.',
        'rounding_limit':'CSV stores four decimals; matching rounded values cannot distinguish sub-rounding perturbations of the original source value.'},errors


# 逐秒数据直接求值于 live Run 的 BDF 密集解；不从 60 s NPZ 再插值生成。
def exportQuestion(run,questionId,outputDir,*,chunkRows=1000,overwrite=False):
    """Export a complete question and return records plus exact validation rules.

    A fresh output directory/version is preferred. Existing files are rejected
    unless overwrite=True is explicitly passed. This never edits raw templates.
    """
    started=time.perf_counter()
    qid=normalizeQuestionId(questionId)
    directory=Path(outputDir).resolve()
    if not directory.is_relative_to(ROOT) or directory.is_relative_to(ROOT/'problem_files'):
        raise ValueError('Outputs must be inside the competition workspace, outside problem_files')
    if not 1<=int(chunkRows)<=2000:
        raise ValueError('chunk_rows must be between 1 and 2000')
    directory.mkdir(parents=True,exist_ok=True)
    stem='result'+qid[-1]
    bookPath=directory/(stem+'.xlsx')
    rawPath=directory/(stem+'_unrounded.csv.gz')
    manifestPath=directory/(stem+'.export.json')
    if not overwrite and any(p.exists() for p in [bookPath,rawPath,manifestPath]):
        raise FileExistsError('Export target already exists; use a new output version')
    provenance=runProvenance(run)
    allowed={'Q1':{'Q1'},'Q2':{'Q2','Q23'},'Q3':{'Q2','Q3','Q23'},'Q4':{'Q4'}}
    if run.model.settings.question not in allowed[qid]:
        raise ValueError('Run physics/question do not match the requested output question')
    if qid=='Q4' and not run.model.settings.shrink:
        raise ValueError('Formal Q4 output requires the shrinking-domain Run, not its fixed-radius control')
    template=loadTemplate(qid)
    times=outputTimes(qid,run.endS,run.eventS)
    if len(times)+1>1_048_576:
        raise ValueError('Required full time grid exceeds the XLSX worksheet row limit; do not truncate')
    workbook=Workbook(write_only=True)
    workbook.properties.creator=''
    workbook.properties.lastModifiedBy=''
    workbook.properties.title=f'问题{qid[-1]}结果'
    headers={name:[template['time_header']]+RADII_CM for name in template['sheet_names']}
    if qid=='Q4':
        headers['Sheet1'].append(template['surface_header'])
        headers['半径']=['时间/s','药材表面半径/cm']
    sheets={name:createSheet(workbook,name,header) for name,header in headers.items()}
    counts={name:{'data_rows':0,'total_rows':1,'columns':len(header),'outside_domain_blank_cells':0,
                  'first_time_s':None,'last_time_s':None,'header':header} for name,header in headers.items()}
    samplesIdx=set(np.linspace(0,len(times)-1,min(13,len(times)),dtype=int).tolist())
    samplesIdx.update([0,min(1,len(times)-1),len(times)-1])
    if run.eventS is not None:
        samplesIdx.update(np.flatnonzero(times==run.eventS).tolist())
    samples=[]
    with gzip.open(rawPath,'wt',encoding='utf-8',newline='',compresslevel=6) as fh:
        rawWriter=csv.writer(fh);rawWriter.writerow(rawHeaders(qid))
        for start in range(0,len(times),int(chunkRows)):
            ts=times[start:start+int(chunkRows)]
            T,C,R,Cs,inside=fieldBlock(run,ts,qid)
            for i,t in enumerate(ts):
                raw=rawRow(qid,t,T[i],C[i],R[i],None if Cs is None else Cs[i],inside[i])
                rawWriter.writerow(['' if v is None else format(v,'.17g') for v in raw])
                values=roundedSheets(qid,raw)
                for name,row in values.items():
                    appendNumeric(sheets[name],row)
                    count=counts[name]
                    count['data_rows']+=1;count['total_rows']+=1
                    count['outside_domain_blank_cells']+=sum(v is None for v in row)
                    if count['first_time_s'] is None:
                        count['first_time_s']=row[0]
                    count['last_time_s']=row[0]
                if start+i in samplesIdx:
                    samples.append({'data_row_index':start+i,'source_time_s':float(t),
                                    'raw_values':raw,'rounded_sheets':values})
    workbook.save(bookPath)
    paperRecords=paperTables(run,qid,directory)
    paperTimeContract={'unit':'s' if qid=='Q1' else 'h','stored_decimals':4,
                         'query_uses_unrounded_seconds':True}
    if qid in ['Q3','Q4']:
        from q3Model import completion
        completed=completion(run)
        paperTimeContract.update({key:completed[key] for key in
                                   ['reported_time_s','reported_drying_time_h','critical_event_s',
                                    'max_C_at_reported_time','conservative_post_verification_s']})
        paperTimeContract['reported_time_h']=completed['reported_drying_time_h']
        paperTimeContract['regular_step_s']=21600.
        paperTimeContract['endpoint_convention']='6-hour samples plus upward-reported strict-drying time; distinct from workbook post-verification endpoint'
    endProvenance=runProvenance(run)
    if endProvenance!=provenance or sha256File(ROOT/template['record']['path'])!=template['record']['sha256']:
        raise RuntimeError('Source, settings or template changed during export')
    bookRecord=exportFileRecord(bookPath,'contest_result_workbook')
    archiveRecord=exportFileRecord(rawPath,'internal_unrounded_output_grid_archive')
    manifest={
        'schema_version':'1.0','question_id':qid,'generated_by':'paper_output/code/review_delivery/exportOutputs.py',
        'generated_at':datetime.now(timezone.utc).isoformat(),'status':'EXPORTED_PENDING_STREAM_READBACK',
        'workbook':bookRecord,'unrounded_archive':archiveRecord,'paper_tables':paperRecords,
        'paper_table_time_contract':paperTimeContract,
        'provenance':provenance,'template':template['record'],'sheets':counts,
        'time_grid':{'start_s':0.,'end_s':float(times[-1]),'regular_step_s':1 if qid in ['Q1','Q2'] else 60,
                     'critical_event_s':provenance['event_s'] if qid in ['Q3','Q4'] else None,
                     'include_post_verification_endpoint':qid!='Q1',
                     'count':len(times),'rounding_duplicate_time_count':int(np.sum(np.diff(np.round(times,4))==0))},
        'radius_grid':{'fixed_radii_cm':RADII_CM,'surface_column':qid=='Q4','surface_coordinate_sheet':'半径' if qid=='Q4' else None},
        'rounding':{'decimal_places':4,'storage':'numeric rounded to four decimals','number_format':NUMBER_FORMAT,
                    'raw_archive':'17 significant digits, source times in seconds and radius in metres',
                    'threshold_judgement':'use original full precision event and max C, never rounded 0.1500'},
        'domain_rule':{'outside_values':'blank (None); never zero','comparison_tolerance_m':1e-12,
                       'Q4_surface_is_not_fixed_2cm':True},
        'samples':samples,'elapsed_s':time.perf_counter()-started,
        'size':{'workbook_bytes':bookRecord['bytes'],'workbook_MiB':bookRecord['bytes']/2**20,
                'unrounded_archive_bytes':archiveRecord['bytes'],'warning_limit_bytes':SIZE_LIMIT_BYTES,
                'workbook_exceeds_20_decimal_MB':bookRecord['bytes']>SIZE_LIMIT_BYTES,
                'archive_is_internal_not_automatically_in_submission_zip':True,
                'complete_support_archive_still_requires_actual_size_check':True,
                'no_required_time_or_space_values_removed':True},
        'validation_required':'validate_exports([record], runs={question_id: run}); full workbook/archive comparison, live Run workbook samples, and every paper CSV cell independently queried from live Run',
        'visual_studio_gui':'pending','human_review':'pending',
    }
    writeJson(manifestPath,manifest)
    return {'question_id':qid,'workbook_path':str(bookPath),'manifest_path':str(manifestPath),
            'artifacts':[bookRecord,archiveRecord]+paperRecords+[exportFileRecord(manifestPath,'export_manifest')],
            'sheets':counts,'size':manifest['size'],'validation_status':'pending'}


def resolveManifestPath(item):
    if isinstance(item,dict):
        return Path(item['manifest_path'])
    path=Path(item)
    return path.with_suffix('.export.json') if path.suffix=='.xlsx' else path


def numericEqual(a,b,tolerance=1e-10):
    return a is None and b is None or (a is not None and b is not None and
        isinstance(a,(int,float)) and not isinstance(a,bool) and math.isfinite(float(a)) and abs(float(a)-float(b))<=tolerance)


# 回读 XLSX/原精度压缩 CSV 并与同一个 live Run 独立查询比对。
def validateExports(paths,runs=None):
    """Stream every saved cell against the exact schedule and raw float archive.

    Pass runs={'Q1': run1, ...} to re-evaluate workbook sample points and every
    paper CSV cell from question-specific contracts and the live Run. With no
    live Run this reports static/archive consistency only, never full verification.
    Writes a sibling .validation.json for each export. Does not alter the XLSX.
    """
    if isinstance(paths,(str,Path,dict)):
        paths=[paths]
    runs={} if runs is None else runs
    results=[]
    for item in paths:
        started=time.perf_counter()
        manifestPath=resolveManifestPath(item).resolve()
        manifest=json.loads(manifestPath.read_text(encoding='utf-8'))
        qid=manifest['question_id'];errors=[];checkedCells=0;checkedSheets={}
        for rec in [manifest['workbook'],manifest['unrounded_archive'],manifest['template']]+manifest['paper_tables']:
            if not (ROOT/rec['path']).exists() or sha256File(ROOT/rec['path'])!=rec['sha256']:
                errors.append('Hash mismatch or missing artifact: '+rec['path'])
        if errors:
            raise RuntimeError('; '.join(errors))
        times=outputTimes(qid,manifest['provenance']['end_s'],manifest['provenance']['event_s'])
        wb=load_workbook(ROOT/manifest['workbook']['path'],read_only=True,data_only=False)
        if wb.sheetnames!=list(manifest['sheets']):
            errors.append('Sheet names/order differ from export contract')
        try:
            for name,spec in manifest['sheets'].items():
                ws=wb[name]
                rows=ws.iter_rows(min_row=1,max_col=spec['columns'])
                header=[cell.value for cell in next(rows)]
                if header!=spec['header']:
                    errors.append(name+': header/physical radius grid mismatch')
                count=0;blanks=0;first=None;last=None;maxRoundingError=0.
                with gzip.open(ROOT/manifest['unrounded_archive']['path'],'rt',encoding='utf-8',newline='') as rawfh:
                    sourceRows=csv.reader(rawfh)
                    if next(sourceRows)!=rawHeaders(qid):
                        errors.append('Unrounded archive schema mismatch')
                    for index,sourceRow in enumerate(sourceRows):
                        try:
                            cells=next(rows)
                        except StopIteration:
                            errors.append(name+': workbook ends before raw archive');break
                        raw=[None if v=='' else float(v) for v in sourceRow]
                        if index>=len(times) or abs(raw[0]-times[index])>1e-8:
                            errors.append(name+': source time schedule mismatch at '+str(index))
                        if qid=='Q4':
                            for j,r in enumerate(RADII_M):
                                outside=r>raw[1]+1e-12
                                if (raw[2+j] is None)!=outside:
                                    errors.append(name+': incorrect moving-domain mask at '+str(index))
                        elif any(v is None for v in raw):
                            errors.append(name+': unexpected blank in fixed domain')
                        expected=roundedSheets(qid,raw)[name]
                        for j,(cell,value) in enumerate(zip(cells,expected)):
                            if not numericEqual(cell.value,value):
                                errors.append(f'{name}: value mismatch at row {index+2}, column {j+1}')
                            if value is not None:
                                if cell.number_format!=NUMBER_FORMAT:
                                    errors.append(f'{name}: four-decimal format missing at row {index+2}, column {j+1}')
                                if not math.isfinite(float(cell.value)) or abs(float(cell.value)*1e4-round(float(cell.value)*1e4))>1e-5:
                                    errors.append(f'{name}: non-finite or non-four-decimal stored number')
                                maxRoundingError=max(maxRoundingError,abs(float(cell.value)-value))
                            else:
                                blanks+=1
                        checkedCells+=len(cells);count+=1
                        if first is None:first=cells[0].value
                        last=cells[0].value
                        if len(errors)>30:
                            raise RuntimeError('Export validation failed: '+'; '.join(errors[:30]))
                    if next(rows,None) is not None:
                        errors.append(name+': workbook has uncontracted extra rows')
                if count!=spec['data_rows'] or count!=len(times):
                    errors.append(name+': row count differs from time grid')
                if blanks!=spec['outside_domain_blank_cells']:
                    errors.append(name+': blank count mismatch')
                checkedSheets[name]={'data_rows':count,'total_rows':count+1,'first_time_s':first,
                    'last_time_s':last,'outside_domain_blank_cells':blanks,'value_comparison_max_abs_error':maxRoundingError}
        finally:
            wb.close()
        run=runs.get(qid)
        live={'status':'NOT_REQUESTED','samples':0,'max_abs_unrounded_difference':None}
        if run is not None:
            current=runProvenance(run)
            if current!=manifest['provenance']:
                errors.append('Live Run provenance differs from the exported Run')
            samples=manifest['samples'];ts=np.array([s['source_time_s'] for s in samples])
            T,C,R,Cs,inside=fieldBlock(run,ts,qid)
            difference=0.
            for i,sample in enumerate(samples):
                actual=rawRow(qid,ts[i],T[i],C[i],R[i],None if Cs is None else Cs[i],inside[i])
                for a,b in zip(actual,sample['raw_values']):
                    if a is None or b is None:
                        if not (a is None and b is None):errors.append('Live Run sample domain mismatch')
                    else:
                        difference=max(difference,abs(a-b))
            if difference>1e-10:
                errors.append('Independent live Run sample mismatch exceeds 1e-10')
            live={'status':'PASS' if difference<=1e-10 else 'FAIL','samples':len(samples),
                  'max_abs_unrounded_difference':difference}
        paperValidation,paperErrors=validatePaperTables(manifest,run)
        errors.extend(paperErrors)
        report={'schema_version':'1.0','question_id':qid,'generated_by':'paper_output/code/review_delivery/exportOutputs.py',
                'generated_at':datetime.now(timezone.utc).isoformat(),
                'status':'FAIL' if errors else 'PASS','fully_verified_with_live_Run':not errors and run is not None,
                'checked_cells':checkedCells,'sheets':checkedSheets,'live_Run_sample_validation':live,
                'paper_CSV_live_Run_validation':paperValidation,
                'errors':errors,'elapsed_s':time.perf_counter()-started,
                'workbook':manifest['workbook'],'export_manifest':exportFileRecord(manifestPath),
                'scope':'Full workbook/raw-archive validation; independent workbook live Run samples and every paper CSV time/position/value/surface/radius cell when live Run is provided.',
                'four_decimals_are_storage_and_display_not_physical_accuracy_claim':True,
                'visual_render':'pending','visual_studio_gui':'pending','human_review':'pending'}
        reportPath=manifestPath.with_name(manifestPath.name.replace('.export.json','.validation.json'))
        writeJson(reportPath,report);report['report_path']=str(reportPath);results.append(report)
        if errors:
            raise RuntimeError('Export validation failed: '+'; '.join(errors[:30]))
    return {'status':'PASS' if all(r['status']=='PASS' for r in results) else 'FAIL',
            'fully_verified_with_live_Run':all(r['fully_verified_with_live_Run'] for r in results),'exports':results}


def paperCsvSelfcheck(directory):
    """Small actual solves plus deliberate CSV defects, never final results."""
    from dryingCore import Settings,solveCase
    import copy
    directory=Path(directory).resolve()
    directory.mkdir(parents=True,exist_ok=True)
    summaries=[];negativeChecks=[]
    for qid in ['Q1','Q2','Q3','Q4']:
        settings={'question':'Q23' if qid in ['Q2','Q3'] else qid,
                  'intervals':40,'faceScheme':'kirchhoff','shrink':qid=='Q4',
                  'rtol':1e-8,'atolTemperature':1e-8,'atolMoisture':1e-10,
                  'earlyMaxStepS':5.}
        if qid=='Q2':
            settings.update(constantD=2e-8,beta=8e-6,horizonH=24.)
        print('PAPER_CSV_SELFCHECK '+qid+': actual N40 solve',flush=True)
        run=solveCase(Settings(**settings))
        try:
            if qid=='Q2' and (run.eventS is None or run.endS<10800.):
                raise RuntimeError('Accelerated export test must still cover 3h and a real drying event')
            exported=exportQuestion(run,qid,directory/qid)
            checked=validateExports([exported],runs={qid:run})
            manifest=json.loads(Path(exported['manifest_path']).read_text(encoding='utf-8'))
            defects={'Q1':['temperature_value'],'Q2':['moisture_value'],
                     'Q3':['last_time_label'],'Q4':['outside_nonblank','surface_missing','radius_value']}[qid]
            for defect in defects:
                changed=copy.deepcopy(manifest)
                kind='temperature' if defect=='temperature_value' else 'radius' if defect=='radius_value' else 'moisture'
                selected=next(r for r in changed['paper_tables'] if Path(r['path']).name==f'{qid.lower()}_paper_{kind}.csv')
                originalPath=ROOT/selected['path']
                with originalPath.open('r',encoding='utf-8-sig',newline='') as fh:rows=list(csv.reader(fh))
                if defect in ['temperature_value','moisture_value']:
                    rows[1][1]=format(float(rows[1][1])+.01,'.4f')
                elif defect=='last_time_label':
                    rows[-1][0]=format(float(rows[-1][0])-.001,'.4f')
                elif defect=='outside_nonblank':
                    ri,ci=next((i,j) for i in range(1,len(rows)) for j in range(1,6) if rows[i][j]=='')
                    rows[ri][ci]='0.0000'
                elif defect=='surface_missing':rows[-1][-1]=''
                elif defect=='radius_value':rows[-1][1]=format(float(rows[-1][1])+.01,'.4f')
                target=directory/'deliberate_defects'/defect/originalPath.name
                target.parent.mkdir(parents=True,exist_ok=True)
                with target.open('w',encoding='utf-8-sig',newline='') as fh:csv.writer(fh).writerows(rows)
                selected.update(exportFileRecord(target,selected.get('role')))
                result,errors=validatePaperTables(changed,run)
                if not errors or result['status']!='FAIL':
                    raise AssertionError('Independent paper validator missed deliberate defect: '+defect)
                negativeChecks.append({'question_id':qid,'defect':defect,'correctly_rejected':True,
                                        'errors':errors,'artifact':exportFileRecord(target)})
            summaries.append({'question_id':qid,'settings':asdict(run.model.settings),'export':exported,
                              'validation':checked,'event_s':run.eventS,'end_s':run.endS,
                              'Q2_is_accelerated_constant_D_export_test_only':qid=='Q2'})
            print(json.dumps({'question_id':qid,'status':'PASS','end_s':run.endS,
                'paper_cells':checked['exports'][0]['paper_CSV_live_Run_validation']['checked_cells']},ensure_ascii=False),flush=True)
        finally:
            run.close()
    report={'status':'PASS','generated_at':datetime.now(timezone.utc).isoformat(),
            'scope':'N40 exporter fidelity only. Q2 uses constant_D=2e-8 and beta=8e-6 solely to shorten the real full-event export test; these are not formal physical results. Q1/Q3/Q4 use their nominal physics.',
            'source':exportFileRecord(SOURCE),'exports':summaries,'negative_checks':negativeChecks,
            'negative_test_scope':'Copied paper CSVs only; six deliberate defects must be rejected even after their recorded hashes are updated.',
            'visual_studio_gui':'pending','human_review':'pending'}
    writeJson(directory/'paper_csv_selfcheck_report.json',report)
    print(json.dumps({'status':'PASS','questions':4,'deliberate_defects_rejected':len(negativeChecks),
                      'report':str(directory/'paper_csv_selfcheck_report.json')},ensure_ascii=False),flush=True)
    return 0


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selfcheck',action='store_true')
    parser.add_argument('--paper-selfcheck',action='store_true')
    parser.add_argument('--output-dir',default='paper_output/code/review_delivery/runtime/exportSelfcheck')
    args=parser.parse_args()
    if not args.selfcheck and not args.paper_selfcheck:
        parser.error('Use the Python API with final Runs, or --selfcheck for a real Q1 validation export')
    if Path.cwd().resolve()!=ROOT:
        raise RuntimeError('Use the competition workspace as cwd')
    if args.paper_selfcheck:
        return paperCsvSelfcheck(ROOT/args.output_dir)
    from dryingCore import Settings,solveCase
    # Small spatial grid is intentional: this validates exporter fidelity, not
    # four-decimal physical accuracy, and is never a final result1 replacement.
    run=solveCase(Settings(question='Q1',intervals=40,faceScheme='kirchhoff',
                           rtol=1e-8,atolTemperature=1e-8,atolMoisture=1e-10,earlyMaxStepS=5.))
    record=exportQuestion(run,'Q1',ROOT/args.output_dir)
    checks=validateExports([record],runs={'Q1':run})
    output=Path(args.output_dir).resolve()
    note={'status':checks['status'],'scope':'Actual Q1 export selfcheck only, not final production or numerical-accuracy acceptance',
          'settings':asdict(run.model.settings),'export':record,'validation':checks}
    writeJson(output/'selfcheck_summary.json',note)
    print(json.dumps({'status':checks['status'],'fully_verified_with_live_Run':checks['fully_verified_with_live_Run'],
                      'output':str(output),'size':record['size'],'sheets':record['sheets']},ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
```

`review_delivery/q1Model.py`（问题一模型装配入口）

```python
# 本文件为冻结求解源码的驼峰审查副本；来源、改名与 AST 核验见 tools/coreRenameReport.json。
"""Q1 uses Appendix 2 throughout its 1800-second interval."""
from dryingCore import Settings, solveCase


# Q1 全部 1800 秒均采用附录 2 参数，正式空间区间数默认 3200。
def solve(intervals=3200):
    return solveCase(Settings(question='Q1', intervals=intervals, faceScheme='kirchhoff',
        rtol=1e-10, atolTemperature=1e-10, atolMoisture=1e-12,
        earlyMaxStepS=2., maxStepS=120.))
```

`review_delivery/q2Model.py`（问题二模型装配入口）

```python
# 本文件为冻结求解源码的驼峰审查副本；来源、改名与 AST 核验见 tools/coreRenameReport.json。
"""Q2 uses Appendix 3 from t=0; it does not splice the Q1 trajectory."""
from dryingCore import Settings, solveCase


# Q2/Q3 从 t=0 采用附录 3，Q3 必须复用本次同一个 Run，不能拼接 Q1。
def solve(intervals=3200):
    return solveCase(Settings(question='Q23', intervals=intervals, faceScheme='kirchhoff',
        rtol=1e-10, atolTemperature=1e-10, atolMoisture=1e-12,
        earlyMaxStepS=2., maxStepS=120.))
```

`review_delivery/q3Model.py`（问题三模型装配入口与达标判据）

```python
# 本文件为冻结求解源码的驼峰审查副本；来源、改名与 AST 核验见 tools/coreRenameReport.json。
"""Q3 is a threshold functional of the exact same Run used by Q2."""
import math
import numpy as np


# Q3 是 Q2 场解的阈值泛函；先连续定位，再向上取 0.0001 h 并验原精度 max(C)<0.15。
def completion(run):
    if run.eventS is None:
        raise ValueError('No full-domain drying event within the solved horizon')
    # At the continuous root the maximum equals 0.15. Report upward on the
    # required 0.0001-hour grid and verify the unrounded state there.
    count = math.ceil(run.eventS / 3600. * 10000.)
    # 即使四位显示为 0.1500，也只能依据未舍入含水率判定严格干燥。
    while True:
        reportH = count/10000.
        t = reportH*3600.
        if t > run.endS:
            raise RuntimeError('Four-decimal reporting time is outside the verified trajectory')
        values = run.state([t])[1:-1:2,0]
        if float(np.max(values)) < .15:
            break
        count += 1
    return {'critical_event_s':run.eventS,'critical_event_h':run.eventS/3600.,
        'reported_drying_time_h':reportH,'reported_time_s':t,
        'max_C_at_reported_time':float(np.max(values)),
        'slowest_material_coordinate':float(run.model.x[np.argmax(values)]),
        'conservative_post_verification_s':run.endS,
        'rounding_convention':'upward on 0.0001 h grid, followed by actual strict threshold check',
        'interpretation':'A conditional numerical event, not a confidence bound on physical drying time.'}
```

`review_delivery/q4Model.py`（问题四模型装配入口）

```python
# 本文件为冻结求解源码的驼峰审查副本；来源、改名与 AST 核验见 tools/coreRenameReport.json。
"""Q4 switches all properties to Appendix 4 and follows observed radial shrinkage."""
from dryingCore import Settings, solveCase


# Q4 从 t=0 使用整组附录 4 系数，并按观测 R(t) 同比径向收缩，固定长度。
def solve(intervals=6400):
    return solveCase(Settings(question='Q4', intervals=intervals, faceScheme='kirchhoff',
        shrink=True, rtol=1e-10, atolTemperature=1e-10, atolMoisture=1e-12,
        earlyMaxStepS=2., maxStepS=120.))
```

**B.6　生产核心模块（蛇形命名同源实现）**

`modeling/drying_core.py`（与 B.5 同源的生产实现）

```python
"""2026 A: radial heat and dry-basis moisture transport on a material mesh.

Units: s, m, K, kg water / kg dry matter. See numerical_design.md for derivation.
The supplied empirical rho*cp is an effective thermal capacity. Dry-solid mass
is conserved separately on uniformly shrinking material control volumes.
No latent heat in the baseline; optional surface-latent scenario is labelled.
No clipping of solution values. Coefficients use a positive continuation only
for integrator Newton probes; all accepted states are checked independently.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import hashlib
import io
import json
import time

import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import lil_matrix
from scipy.special import expi
import analytic_jacobian
import disk_dense

ROOT = Path(__file__).resolve().parents[3]
LOADED_CODE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
C0, T0, R0, LENGTH = 2.55, 301.15, 0.02, 0.25


def load_inputs(with_records=False):
    arrays, records = [], []
    for name in ['A_environment_observed.csv', 'A_radius_observed.csv']:
        path = ROOT / 'paper_output/data_cleaned' / name
        content = path.read_bytes()
        arrays.append(np.genfromtxt(io.StringIO(content.decode('utf-8-sig')),
                                    delimiter=',', names=True))
        records.append({'path':path.relative_to(ROOT).as_posix(), 'bytes':len(content),
                        'sha256':hashlib.sha256(content).hexdigest(), 'exists':True})
    return (*arrays, records) if with_records else tuple(arrays)


@dataclass(frozen=True)
class Settings:
    question: str = 'Q23'
    intervals: int = 100
    rtol: float = 1e-7
    atol_temperature: float = 1e-7
    atol_moisture: float = 1e-9
    max_step_s: float = 600.0
    early_max_step_s: float = 30.0
    horizon_h: float = 240.0
    shrink: bool = False
    boundary_extension: str = 'nominal'
    tail_temperature_C: float = 50.0
    tail_equilibrium: float = 0.05
    h: float = 25.0
    beta: float = 8e-7
    equilibrium_scale: float = 1.0
    surface_latent_fraction: float = 0.0
    latent_J_kg: float = 2.4e6
    constant_D: float | None = None
    constant_thermal: bool = False
    method: str = 'BDF'
    face_scheme: str = 'harmonic'
    jacobian_mode: str = 'analytic'
    dense_storage: str = 'disk'


class RadialModel:
    def __init__(self, settings: Settings):
        self.settings = settings
        if settings.intervals < 2 or settings.jacobian_mode not in ('analytic', 'finite_difference'):
            raise ValueError('At least two intervals and a supported Jacobian mode are required')
        self.env, self.rad, self.input_records = load_inputs(with_records=True)
        self.x = np.linspace(0., 1., settings.intervals + 1)
        self.dx = 1. / settings.intervals
        faces = np.r_[0., (self.x[1:] + self.x[:-1]) / 2., 1.]
        self.w = np.diff(faces ** 2) / 2.
        self.internal_faces = faces[1:-1]
        self.n = len(self.x)
        self.rho_d0 = (760 + 90 * C0) / (1 + C0) if settings.question == 'Q4' else (
            820. / (1 + C0) if settings.question == 'Q1' else (650 + 128 * C0) / (1 + C0))
        self.evaluations = 0
        self.jac_pattern = self._sparsity()

    def radius(self, t):
        if self.settings.shrink:
            return np.interp(t, self.rad['time_s'], self.rad['radius_m'])
        return np.asarray(t) * 0. + R0

    def environment(self, t):
        s = self.settings
        tair = np.interp(t, self.env['time_s'], self.env['temperature_K'])
        ceq = np.interp(t, self.env['time_s'], self.env['air_moisture_kg_per_kg'])
        after = np.asarray(t) > self.env['time_s'][-1]
        if s.boundary_extension == 'nominal':
            tair = np.where(after, s.tail_temperature_C + 273.15, tair)
            ceq = np.where(after, s.tail_equilibrium, ceq)
        elif s.boundary_extension == 'tail_mean':
            tail = self.env['time_s'] >= 10800
            tair = np.where(after, self.env['temperature_K'][tail].mean(), tair)
            ceq = np.where(after, self.env['air_moisture_kg_per_kg'][tail].mean(), ceq)
        elif s.boundary_extension != 'last':
            raise ValueError('Unknown boundary extension')
        return tair, ceq * s.equilibrium_scale

    def properties(self, T, C):
        s = self.settings
        positive_C = np.maximum(C, 1e-12)  # coefficient continuation, never state clipping
        if np.any(T <= 0):
            raise FloatingPointError('Nonpositive absolute temperature')
        wet = positive_C / (1. + positive_C)
        if s.question == 'Q1':
            rho = np.full_like(C, 820.)
            cp = np.full_like(C, 2600.)
            k = np.full_like(C, .36)
            D = 7e-9 * np.exp(-.89 / positive_C)
        elif s.question in ('Q2', 'Q3', 'Q23'):
            rho, cp, k = 650 + 128 * positive_C, 1450 + 2736 * wet, .21 + .38 * wet
            D = 2.4e-3 * np.exp(-.45 / positive_C - 3850 / T)
        elif s.question == 'Q4':
            rho, cp, k = 760 + 90 * positive_C, 1850 + 2150 * wet, .12 + .20 * wet
            D = 4.2e-4 * np.exp(-.30 / positive_C - 3850 / T)
        else:
            raise ValueError(s.question)
        if s.constant_D is not None:
            D = np.full_like(C, s.constant_D)
        if s.constant_thermal:
            rho, cp, k = np.full_like(C, 820.), np.full_like(C, 2600.), np.full_like(C, .36)
        return rho, cp, k, D

    @staticmethod
    def harmonic(a):
        return 2 * a[:-1] * a[1:] / np.maximum(a[:-1] + a[1:], np.finfo(float).tiny)

    def _sparsity(self):
        p = lil_matrix((2 * self.n + 1, 2 * self.n + 1), dtype=int)
        for i in range(self.n):
            for j in range(max(0, i - 1), min(self.n, i + 2)):
                p[2*i:2*i+2, 2*j:2*j+2] = 1
        p[-1, 2 * (self.n - 1) + 1] = 1
        return p.tocsr()

    def water_internal_flux(self, T, C, D):
        if self.settings.face_scheme == 'harmonic' or self.settings.constant_D is not None:
            return self.internal_faces * self.harmonic(D) * np.diff(C) / self.dx
        if self.settings.face_scheme != 'kirchhoff':
            raise ValueError('Unknown nonlinear face scheme')
        a, D0 = {'Q1':(.89,7e-9), 'Q23':(.45,2.4e-3), 'Q2':(.45,2.4e-3),
                  'Q3':(.45,2.4e-3), 'Q4':(.30,4.2e-4)}[self.settings.question]
        cc = np.maximum(C, 1e-12)
        potential = cc * np.exp(-a/cc) + a * expi(-a/cc)
        difference = np.diff(potential)
        small = np.abs(np.diff(cc)) < 1e-7 * np.maximum((cc[:-1]+cc[1:])/2, 1e-3)
        difference[small] = (np.exp(-a/((cc[:-1][small]+cc[1:][small])/2)) * np.diff(cc)[small])
        thermal_factor = 1. if self.settings.question == 'Q1' else np.exp(-3850/((T[:-1]+T[1:])/2))
        # Do not difference thermal_factor*potential: that would add a false Soret flux.
        return self.internal_faces * D0 * thermal_factor * difference / self.dx

    def rhs(self, t, state):
        """REVIEW: actual material-control-volume balance, no extra mesh advection."""
        self.evaluations += 1
        T, C = state[:-1:2], state[1:-1:2]
        rho, cp, k, D = self.properties(T, C)
        radius = float(self.radius(t))
        tair, ceq = self.environment(t)
        heat_g = np.zeros(self.n + 1)
        water_g = np.zeros(self.n + 1)
        heat_g[1:-1] = self.internal_faces * self.harmonic(k) * np.diff(T) / self.dx
        water_g[1:-1] = self.water_internal_flux(T, C, D)
        water_g[-1] = -self.settings.beta * radius * (C[-1] - ceq)
        heat_g[-1] = -self.settings.h * radius * (T[-1] - tair)
        if self.settings.surface_latent_fraction:
            # Scenario: all selected outgoing water vaporizes at the surface.
            rho_d = self.rho_d0 * (R0 / radius) ** 2
            j_evap = rho_d * self.settings.beta * (C[-1] - ceq)
            heat_g[-1] -= (radius * self.settings.surface_latent_fraction *
                            self.settings.latent_J_kg * j_evap)
        derivative = np.empty_like(state)
        derivative[:-1:2] = np.diff(heat_g) / (radius ** 2 * self.w * rho * cp)
        derivative[1:-1:2] = np.diff(water_g) / (radius ** 2 * self.w)
        derivative[-1] = 2 * self.settings.beta / radius * (C[-1] - ceq)
        return derivative

    def initial(self):
        state = np.empty(2 * self.n + 1)
        state[:-1:2], state[1:-1:2], state[-1] = T0, C0, 0.
        return state


class Run:
    def __init__(self, model, pieces, elapsed, event_s, cache=None):
        self.model, self.pieces = model, pieces
        self.cache = cache
        self.elapsed_s, self.event_s = elapsed, event_s
        self.end_s = float(pieces[-1].t[-1])

    def close(self):
        """Release this Run after its exports/checks; further queries are invalid."""
        self.pieces.clear()
        if self.cache is not None:
            self.cache.close()

    def state(self, times):
        tt = np.atleast_1d(np.asarray(times, dtype=float))
        if np.min(tt) < -1e-10 or np.max(tt) > self.end_s + 1e-7:
            raise ValueError('Requested time outside solved interval')
        out = np.empty((2 * self.model.n + 1, len(tt)))
        remaining = np.ones(len(tt), dtype=bool)
        for result in self.pieces:
            select = remaining & (tt >= result.t[0]-1e-7) & (tt <= result.t[-1]+1e-7)
            if np.any(select):
                out[:, select] = result.sol(tt[select])
                remaining[select] = False
        if np.any(remaining):
            raise RuntimeError('Missing dense solution segment')
        return out

    def fields(self, times, radii_m=None, material_x=None):
        tt = np.atleast_1d(np.asarray(times, dtype=float))
        state = self.state(tt)
        Ts, Cs = state[:-1:2].T, state[1:-1:2].T
        if material_x is not None:
            points = np.asarray(material_x, dtype=float)
            if np.any(~np.isfinite(points)) or np.any((points < 0.) | (points > 1.)):
                raise ValueError('Material coordinates must be finite and within [0,1]')
            return np.array([np.interp(points, self.model.x, row) for row in Ts]), np.array([
                np.interp(points, self.model.x, row) for row in Cs])
        if radii_m is None:
            return Ts, Cs
        radial = np.asarray(radii_m)
        Tout, Cout = [], []
        for i, t in enumerate(tt):
            xx = radial / self.model.radius(t)
            Tout.append(np.interp(xx, self.model.x, Ts[i], left=np.nan, right=np.nan))
            Cout.append(np.interp(xx, self.model.x, Cs[i], left=np.nan, right=np.nan))
        return np.asarray(Tout), np.asarray(Cout)

    def diagnostics(self):
        # Reduce in bounded blocks: a fine full-domain run may contain tens of
        # millions of accepted state values. Diagnostics must not duplicate all
        # of them and four property arrays at the same time.
        minimum_C = minimum_T = minimum_D = minimum_property = np.inf
        maximum_C = maximum_T = maximum_D = maximum_radial_increase = -np.inf
        maximum_mass_residual = 0.
        for piece in self.pieces:
            for first in range(0, len(piece.t), 256):
                raw = piece.y[:, first:first+256]
                T, C = raw[:-1:2], raw[1:-1:2]
                residual = 2*self.model.w@C + raw[-1] - C0
                rho, cp, k, D = self.model.properties(T.ravel(), C.ravel())
                minimum_C, maximum_C = min(minimum_C,C.min()), max(maximum_C,C.max())
                minimum_T, maximum_T = min(minimum_T,T.min()), max(maximum_T,T.max())
                minimum_D = min(minimum_D,D.min())
                maximum_D = max(maximum_D,D.max())
                minimum_property = min(minimum_property,rho.min(),cp.min(),k.min(),D.min())
                maximum_radial_increase = max(maximum_radial_increase,np.max(np.diff(C,axis=0)))
                maximum_mass_residual = max(maximum_mass_residual,np.max(np.abs(residual)))
        final = self.state([self.end_s])[:, 0]
        finalC = final[1:-1:2]
        return {
            'event_s': self.event_s, 'event_h': None if self.event_s is None else self.event_s/3600,
            'end_s': self.end_s, 'elapsed_s': self.elapsed_s,
            'end_time_convention': 'ceil(critical_event_s)+1: conservative post-crossing verification second; not claimed earliest integer second',
            'max_mass_balance_abs_kg_per_kg': float(maximum_mass_residual),
            'min_C': float(minimum_C), 'max_C': float(maximum_C),
            'min_T_K': float(minimum_T), 'max_T_K': float(maximum_T),
            'min_D': float(minimum_D), 'max_D': float(maximum_D),
            'positive_properties': bool(minimum_property > 0),
            'max_radial_C_increase': float(maximum_radial_increase),
            'final_max_C': float(finalC.max()), 'final_surface_C': float(finalC[-1]),
            'strictly_dry_at_end': bool(finalC.max() < .15),
            'radius_end_m': float(self.model.radius(self.end_s)),
            'radius_extrapolation_used': bool(self.model.settings.shrink and self.end_s > 259200),
            'rhs_evaluations': self.model.evaluations,
            'accepted_time_points': sum(len(p.t) for p in self.pieces),
            'nfev': sum(p.nfev for p in self.pieces),
            'njev': sum(p.njev for p in self.pieces), 'nlu': sum(p.nlu for p in self.pieces),
            'solver_success': all(p.success for p in self.pieces),
            'dense_storage': self.model.settings.dense_storage,
            'dense_coefficient_bytes': 0 if self.cache is None else self.cache.bytes_written,
            'dense_polynomial_count': 0 if self.cache is None else self.cache.polynomial_count,
        }


def solve_case(settings: Settings) -> Run:
    started = time.perf_counter()
    if settings.dense_storage not in ('memory', 'disk'):
        raise ValueError('Dense storage must be memory or disk')
    if settings.dense_storage == 'disk' and settings.method != 'BDF':
        raise ValueError('Exact disk dense storage currently supports BDF only')
    cache = disk_dense.DenseCache(ROOT) if settings.dense_storage == 'disk' else None
    try:
        return _solve_case_impl(settings, cache, started)
    except BaseException as error:
        if cache is not None:
            try:
                cache.close()
            except BaseException as cleanup_error:
                error.add_note('Private cache cleanup also failed: '+repr(cleanup_error))
        raise


def _solve_case_impl(settings, cache, started):
    model = RadialModel(settings)
    method = disk_dense.DiskBDF if cache is not None else settings.method
    jacobian_options = ({'jac': lambda t, y: analytic_jacobian.jacobian(model, t, y)}
        if settings.jacobian_mode == 'analytic' else {'jac_sparsity': model.jac_pattern})
    if cache is not None:
        jacobian_options['dense_cache'] = cache
    def dry_event(t, y):
        return float(np.max(y[1:-1:2]) - .15)
    dry_event.terminal, dry_event.direction = True, -1
    atol = np.empty(2 * model.n + 1)
    atol[:-1:2], atol[1:-1:2], atol[-1] = settings.atol_temperature, settings.atol_moisture, settings.atol_moisture
    horizon = 1800. if settings.question == 'Q1' else settings.horizon_h * 3600.
    pieces, initial, event_s = [], model.initial(), None
    # A separate segment at 4 h makes the modelling extension explicit.
    endpoints = [0., min(14400., horizon)]
    if horizon > 14400.:
        endpoints.append(horizon)
    for left, right in zip(endpoints[:-1], endpoints[1:]):
        piece = solve_ivp(model.rhs, (left, right), initial, method=method,
            rtol=settings.rtol, atol=atol, **jacobian_options,
            max_step=settings.early_max_step_s if left < 14400. else settings.max_step_s,
            events=None if settings.question == 'Q1' else dry_event, dense_output=True)
        if cache is not None:
            disk_dense.align_bdf_segments(piece)
        pieces.append(piece)
        if not piece.success:
            raise RuntimeError(piece.message)
        initial = piece.y[:, -1].copy()
        if cache is not None:
            piece.y = cache.store_accepted(piece.y)
        if piece.t_events is not None and len(piece.t_events[0]):
            event_s = float(piece.t_events[0][0])
            # Continue to a genuine post-crossing integer second, not an extrapolation.
            end = float(np.ceil(event_s) + 1)
            tail = solve_ivp(model.rhs, (event_s, end), initial, method=method,
                rtol=settings.rtol, atol=atol, **jacobian_options,
                max_step=1., dense_output=True)
            if cache is not None:
                disk_dense.align_bdf_segments(tail)
            if not tail.success:
                raise RuntimeError(tail.message)
            if cache is not None:
                tail.y = cache.store_accepted(tail.y)
            pieces.append(tail)
            break
    run = Run(model, pieces, time.perf_counter() - started, event_s, cache)
    diagnostic = run.diagnostics()
    if diagnostic['min_C'] < -1e-8 or not diagnostic['positive_properties']:
        raise FloatingPointError('Physical range/positive property check failed')
    if diagnostic['max_mass_balance_abs_kg_per_kg'] > 1e-6:
        raise FloatingPointError('Dry-basis mass balance failed')
    return run


def file_record(path):
    p = Path(path)
    return {'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size,
            'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'exists': True}


def save_run(run: Run, directory: Path):
    code_record = file_record(Path(__file__))
    if code_record['sha256'] != LOADED_CODE_SHA256:
        raise RuntimeError('Solver file changed after import; restart to obtain valid provenance')
    jacobian_record = file_record(Path(analytic_jacobian.__file__))
    if jacobian_record['sha256'] != analytic_jacobian.LOADED_CODE_SHA256:
        raise RuntimeError('Jacobian file changed after import; restart to obtain valid provenance')
    storage_record = file_record(Path(disk_dense.__file__))
    if storage_record['sha256'] != disk_dense.LOADED_CODE_SHA256:
        raise RuntimeError('Dense storage file changed after import; restart for valid provenance')
    for record in run.model.input_records:
        if file_record(ROOT/record['path'])['sha256'] != record['sha256']:
            raise RuntimeError('Input changed after being loaded; retain failure and rerun')
    directory.mkdir(parents=True, exist_ok=True)
    times = np.unique(np.r_[np.arange(0., run.end_s, 60.),
                [t for t in [100., 300., 600., 900., 1200., 1500., 1800., 3600., 5400., 7200., 9000., 10800.] if t <= run.end_s],
                run.end_s, [] if run.event_s is None else [run.event_s]])
    x = np.linspace(0., 1., 21)
    temperature, moisture, means, losses = [], [], [], []
    for first in range(0, len(times), 128):
        block_times = times[first:first+128]
        Tb, Cb = run.fields(block_times, material_x=x)
        raw = run.state(block_times)
        temperature.append(Tb); moisture.append(Cb)
        means.append(2*run.model.w@raw[1:-1:2]); losses.append(raw[-1].copy())
    T, C = np.vstack(temperature), np.vstack(moisture)
    np.savez_compressed(directory/'sampled_solution.npz', times_s=times, material_x=x,
        T_K=T, C=C, radius_m=run.model.radius(times), mean_C=np.concatenate(means),
        cumulative_loss=np.concatenate(losses))
    summary = {'settings': asdict(run.model.settings), 'diagnostics': run.diagnostics(),
               'code': code_record,
               'jacobian_code': jacobian_record,
               'dense_storage_code': storage_record,
               'inputs': run.model.input_records,
               'human_review_status': 'pending', 'gui_reproduced': False}
    (directory/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return summary
```

`modeling/analytic_jacobian.py`（与 B.5 同源的解析 Jacobian）

```python
"""Analytic sparse Jacobian for drying_core.RadialModel.rhs.

The ordering is T0,C0,...,TN,CN,A. A is a passive cumulative loss variable;
its entire column is exactly zero and must not use adaptive numdiff factors.
This file does not modify the core or select a production configuration.

Self-check from the contest root:
  C:\\Python314\\python.exe -B paper_output/code/modeling/analytic_jacobian.py --self-test
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import warnings

import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import coo_matrix
from scipy.special import expi


LOADED_CODE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _harmonic_partials(left, right):
    """Positive-coefficient partials; respect the core's tiny denominator guard."""
    total = left + right
    tiny = np.finfo(float).tiny
    denominator = np.maximum(total, tiny)
    ordinary = total > tiny
    dl = np.where(ordinary, 2 * (right / denominator) ** 2, 2 * right / denominator)
    dr = np.where(ordinary, 2 * (left / denominator) ** 2, 2 * left / denominator)
    return dl, dr


def jacobian(model, t, y):
    """Return d(rhs)/d(y) as CSC without calling rhs or numerical differentiation.

Each internal face contributes opposite flux derivatives to its two cells.
For heat, differentiating 1/(rho*cp) adds -Tdot*cap_C/cap locally.
Kirchhoff's temperature factor is frozen at the symmetric face temperature;
the primitive's close-concentration branch is differentiated exactly as coded.
"""
    state = np.asarray(y, dtype=float)
    n = model.n
    if state.ndim != 1 or state.size != 2*n + 1:
        raise ValueError("Jacobian requires interleaved 1D state of length 2*n+1")
    s = model.settings
    T, C = state[:-1:2], state[1:-1:2]
    cc = np.maximum(C, 1e-12)
    active = (C > 1e-12).astype(float)
    rho, cp, k, D = model.properties(T, C)
    if s.question == 'Q1':
        a, d0, temp_constant = .89, 7e-9, 0.
        rho_c, cp_c, k_c = np.zeros(n), np.zeros(n), np.zeros(n)
    elif s.question in ('Q2', 'Q3', 'Q23'):
        a, d0, temp_constant = .45, 2.4e-3, 3850.
        rho_c = np.full(n, 128.) * active
        cp_c = 2736. / (1. + cc)**2 * active
        k_c = .38 / (1. + cc)**2 * active
    elif s.question == 'Q4':
        a, d0, temp_constant = .30, 4.2e-4, 3850.
        rho_c = np.full(n, 90.) * active
        cp_c = 2150. / (1. + cc)**2 * active
        k_c = .20 / (1. + cc)**2 * active
    else:
        raise ValueError(s.question)
    if s.constant_thermal:
        rho_c, cp_c, k_c = np.zeros(n), np.zeros(n), np.zeros(n)
    capacity = rho * cp
    capacity_c = rho_c * cp + rho * cp_c
    if s.constant_D is None:
        d_c = D * (a / cc**2) * active
        d_t = D * temp_constant / T**2
    else:
        d_c, d_t = np.zeros(n), np.zeros(n)

    radius = float(model.radius(t))
    if radius <= 0:
        raise ValueError("Nonpositive radius")
    tair, ceq = model.environment(t)
    geom = model.internal_faces / model.dx
    delta_t, delta_c = np.diff(T), np.diff(C)

    # Derivative columns for each face are (T_left,C_left,T_right,C_right).
    k_harm = model.harmonic(k)
    kh_l, kh_r = _harmonic_partials(k[:-1], k[1:])
    heat_deriv = np.column_stack((
        -geom * k_harm,
        geom * kh_l * k_c[:-1] * delta_t,
        geom * k_harm,
        geom * kh_r * k_c[1:] * delta_t,
    ))
    heat_g = np.zeros(n + 1)
    heat_g[1:-1] = geom * k_harm * delta_t
    heat_g[-1] = -s.h * radius * (T[-1] - tair)

    if s.face_scheme == 'harmonic' or s.constant_D is not None:
        dh = model.harmonic(D)
        dh_l, dh_r = _harmonic_partials(D[:-1], D[1:])
        water_deriv = np.column_stack((
            geom * dh_l * d_t[:-1] * delta_c,
            geom * (dh_l * d_c[:-1] * delta_c - dh),
            geom * dh_r * d_t[1:] * delta_c,
            geom * (dh_r * d_c[1:] * delta_c + dh),
        ))
    elif s.face_scheme == 'kirchhoff':
        primitive = cc * np.exp(-a / cc) + a * expi(-a / cc)
        primitive_delta = np.diff(primitive)
        mean_c = (cc[:-1] + cc[1:]) / 2.
        mean_t = (T[:-1] + T[1:]) / 2.
        delta_cc = np.diff(cc)
        small = np.abs(delta_cc) < 1e-7 * np.maximum(mean_c, 1e-3)
        exp_left, exp_right = np.exp(-a/cc[:-1]), np.exp(-a/cc[1:])
        primitive_l = -exp_left * active[:-1]
        primitive_r = exp_right * active[1:]
        if np.any(small):
            f_mid = np.exp(-a / mean_c[small])
            f_prime_mid = f_mid * a / mean_c[small]**2
            primitive_delta[small] = f_mid * delta_cc[small]
            primitive_l[small] = (0.5*f_prime_mid*delta_cc[small]-f_mid)*active[:-1][small]
            primitive_r[small] = (0.5*f_prime_mid*delta_cc[small]+f_mid)*active[1:][small]
        temperature_factor = np.exp(-temp_constant / mean_t)
        coefficient = geom * d0 * temperature_factor
        water_g = coefficient * primitive_delta
        water_t = water_g * temp_constant / (2 * mean_t**2)
        water_deriv = np.column_stack((water_t, coefficient*primitive_l,
                                      water_t, coefficient*primitive_r))
    else:
        raise ValueError('Unknown nonlinear face scheme')

    heat_scale = 1. / (radius**2 * model.w * capacity)
    water_scale = 1. / (radius**2 * model.w)
    surface_heat_c = 0.
    if s.surface_latent_fraction:
        rho_d = model.rho_d0 * (.02 / radius)**2
        surface_heat_c = -radius*s.surface_latent_fraction*s.latent_J_kg*rho_d*s.beta
        heat_g[-1] += surface_heat_c * (C[-1] - ceq)
    temp_derivative = np.diff(heat_g) * heat_scale

    face_index = np.arange(n-1)
    face_columns = np.column_stack((2*face_index, 2*face_index+1,
                                    2*face_index+2, 2*face_index+3)).ravel()
    rows, columns, values = [], [], []

    def add_face(row_index, derivatives, factor):
        rows.append(np.repeat(row_index, 4))
        columns.append(face_columns)
        values.append((derivatives * factor[:, None]).ravel())

    add_face(2*face_index, heat_deriv, heat_scale[:-1])
    add_face(2*face_index+2, heat_deriv, -heat_scale[1:])
    add_face(2*face_index+1, water_deriv, water_scale[:-1])
    add_face(2*face_index+3, water_deriv, -water_scale[1:])
    cell_index = np.arange(n)
    rows.append(2*cell_index)
    columns.append(2*cell_index+1)
    values.append(-temp_derivative * capacity_c / capacity)
    rows.append(np.array([2*n-2, 2*n-2, 2*n-1, 2*n]))
    columns.append(np.array([2*n-2, 2*n-1, 2*n-1, 2*n-1]))
    values.append(np.array([-s.h*radius*heat_scale[-1],
                            surface_heat_c*heat_scale[-1],
                            -s.beta*radius*water_scale[-1], 2*s.beta/radius]))
    matrix = coo_matrix((np.concatenate(values),
                        (np.concatenate(rows), np.concatenate(columns))),
                       shape=(2*n+1, 2*n+1)).tocsc()
    matrix.sum_duplicates()
    matrix.eliminate_zeros()
    return matrix


def _self_test(output_directory):
    """Independent RHS perturbation checks, a conservation derivative, and tiny BDF runs."""
    import scipy
    from drying_core import ROOT, Settings, RadialModel, LOADED_CODE_SHA256 as CORE_LOADED_CODE_SHA256

    started = time.perf_counter()
    rng = np.random.default_rng(20260910)
    relative_tolerance, absolute_tolerance = 5e-6, 5e-10
    cases = []
    for question in ['Q1', 'Q23', 'Q4']:
        for scheme in ['harmonic', 'kirchhoff']:
            for latent in [0., 1.]:
                cases.append(Settings(question=question, intervals=8, face_scheme=scheme,
                                      shrink=(question=='Q4'), surface_latent_fraction=latent))
    for question in ['Q1', 'Q23', 'Q4']:
        for constant_d, constant_thermal in [(2e-9, False), (None, True), (2e-9, True)]:
            cases.append(Settings(question=question, intervals=8, face_scheme='kirchhoff',
                                  shrink=(question=='Q4'), constant_D=constant_d,
                                  constant_thermal=constant_thermal, surface_latent_fraction=1.))
    records, failures = [], []
    for settings in cases:
        model = RadialModel(settings)
        x = model.x
        states = {
            'initial': (0., model.initial()),
            'nonuniform': (18000., model.initial()),
            'late_dry': (150000., model.initial()),
            'near_uniform_small_branch': (14401., model.initial()),
        }
        states['nonuniform'][1][:-1:2] = 303. + 17.*x**2
        states['nonuniform'][1][1:-1:2] = 2.4 - 2.0*x**2
        states['late_dry'][1][:-1:2] = 321. + 2.0*x**2
        states['late_dry'][1][1:-1:2] = .175 - .115*x**2
        states['near_uniform_small_branch'][1][:-1:2] = 303. + 17.*x**2
        states['near_uniform_small_branch'][1][1:-1:2] = .15 + 1e-10*x
        for state_name, (t, y) in states.items():
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter('always')
                matrix = jacobian(model, t, y)
                vectors = []
                for _ in range(4):
                    direction = rng.normal(size=y.size)
                    direction[:-1:2] *= 1.0
                    direction[1:-1:2] *= .02
                    direction[-1] = .3
                    vectors.append(direction)
                directional = []
                for direction in vectors:
                    predicted = matrix @ direction
                    steps = []
                    for step in [1e-4, 3e-5, 1e-5]:
                        finite_difference = (model.rhs(t, y+step*direction)-
                                             model.rhs(t, y-step*direction))/(2*step)
                        absolute_error = float(np.max(np.abs(predicted-finite_difference)))
                        scale = max(float(np.max(np.abs(predicted))),
                                    float(np.max(np.abs(finite_difference))), 1e-30)
                        scaled = float(np.max(np.abs(predicted-finite_difference)/
                            (absolute_tolerance + relative_tolerance*np.maximum(
                                np.abs(predicted), np.abs(finite_difference)))))
                        steps.append({'step':step, 'max_abs_error':absolute_error,
                                      'relative_inf_error':absolute_error/scale,
                                      'max_component_tolerance_ratio':scaled})
                    best = min(steps, key=lambda item:item['max_component_tolerance_ratio'])
                    directional.append({'all_step_errors':steps, 'best':best})
                passive = np.zeros(y.size); passive[-1] = 1.
                passive_analytic = float(np.max(np.abs(matrix @ passive)))
                passive_fd = float(np.max(np.abs(model.rhs(t, y+passive)-model.rhs(t,y-passive))))
                mass_weights = np.zeros(y.size)
                mass_weights[1:-1:2] = 2*model.w
                mass_weights[-1] = 1.
                conservation = float(np.max(np.abs(np.asarray(mass_weights @ matrix))))
            warning_messages = [str(w.message) for w in captured]
            passed = (all(step['max_component_tolerance_ratio'] <= 1
                          for d in directional for step in d['all_step_errors'])
                      and passive_analytic == 0 and passive_fd == 0 and conservation < 1e-11
                      and np.isfinite(matrix.data).all() and not warning_messages)
            record = {'settings':asdict(settings), 'state':state_name, 'time_s':t,
                      'status':'PASS' if passed else 'FAIL', 'matrix_shape':matrix.shape,
                      'matrix_nnz':matrix.nnz, 'directional_checks':directional,
                      'passive_column_analytic_abs':passive_analytic,
                      'passive_column_finite_difference_abs':passive_fd,
                      'mass_balance_derivative_abs':conservation, 'warnings':warning_messages}
            records.append(record)
            if not passed:
                failures.append(f"{settings.question}/{settings.face_scheme}/latent={settings.surface_latent_fraction}/{state_name}/constant_D={settings.constant_D}/constant_thermal={settings.constant_thermal}")
    smoke_records = []
    for scheme in ['harmonic', 'kirchhoff']:
        for question in ['Q23', 'Q4']:
            settings = Settings(question=question, intervals=8, face_scheme=scheme,
                                shrink=(question=='Q4'), surface_latent_fraction=1.)
            model = RadialModel(settings)
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter('always')
                result = solve_ivp(model.rhs, (0., 2.), model.initial(), method='BDF',
                                   jac=lambda t,y:jacobian(model,t,y), rtol=1e-10,
                                   atol=1e-12, max_step=.2)
            msgs = [str(w.message) for w in captured]
            passed = bool(result.success and np.isfinite(result.y).all() and not msgs)
            smoke_records.append({'question':question, 'face_scheme':scheme, 'interval_s':[0,2],
                                  'status':'PASS' if passed else 'FAIL', 'warnings':msgs,
                                  'nfev':result.nfev, 'njev':result.njev, 'nlu':result.nlu,
                                  'purpose':'Short Jacobian/BDF wiring check, not production accuracy'})
            if not passed:
                failures.append(f"BDF_smoke/{question}/{scheme}")
    current_source_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    current_core_hash = hashlib.sha256((ROOT/'paper_output/code/modeling/drying_core.py').read_bytes()).hexdigest()
    if current_source_hash != LOADED_CODE_SHA256 or current_core_hash != CORE_LOADED_CODE_SHA256:
        failures.append('Source file changed after module load during validation')
    report = {'schema_version':'1.0', 'created_utc':datetime.now(timezone.utc).isoformat(),
              'status':'PASS' if not failures else 'FAIL', 'failures':failures,
              'source_sha256':LOADED_CODE_SHA256,
              'core_sha256':CORE_LOADED_CODE_SHA256,
              'source_hash_policy':'SHA-256 frozen when each module is imported; files checked unchanged before report save.',
              'runtime':{'python':sys.version,'executable':sys.executable,'numpy':np.__version__,'scipy':scipy.__version__},
              'seed':20260910,'relative_component_tolerance':relative_tolerance,
              'absolute_component_tolerance':absolute_tolerance,
              'finite_difference_policy':'Central directional differences, three decreasing steps; every step must satisfy the mixed absolute/relative component tolerance. Best comparison is supplementary only.',
              'case_state_count':len(records), 'direction_count':4*len(records),
              'checks':records,'short_BDF_checks':smoke_records,
              'elapsed_s':time.perf_counter()-started,
              'limitations':['No full production run or grid convergence performed here.',
                             'Tiny denominator/underflow extensions at nonphysical Newton probes are not calibrated physical data.',
                             'Only this module and the short tests use analytic Jacobian until main agent hooks core.',
                             'Visual Studio reproduction and human review remain pending.']}
    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory/'analytic_jacobian_selftest.json').write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    brief = {key:report[key] for key in ['status','failures','case_state_count','direction_count','elapsed_s']}
    brief['max_best_component_tolerance_ratio'] = max(
        d['best']['max_component_tolerance_ratio'] for r in records for d in r['directional_checks'])
    brief['max_all_steps_component_tolerance_ratio'] = max(
        step['max_component_tolerance_ratio'] for r in records
        for d in r['directional_checks'] for step in d['all_step_errors'])
    brief['max_mass_balance_derivative_abs'] = max(r['mass_balance_derivative_abs'] for r in records)
    brief['warning_count'] = sum(len(r['warnings']) for r in records+smoke_records)
    print(json.dumps(brief,ensure_ascii=False,indent=2))
    return 0 if not failures else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--output-dir', type=Path,
        default=Path(__file__).resolve().parents[2]/'results/jacobian_validation')
    arguments = parser.parse_args()
    if not arguments.self_test:
        parser.error('Use --self-test, or import jacobian(model,t,y) from this module.')
    raise SystemExit(_self_test(arguments.output_dir))
```

`modeling/disk_dense.py`（与 B.5 同源的稠密存储模块）

```python
"""Exact BDF dense polynomials backed by a private, rebuildable disk cache.

This changes storage only: each accepted BDF polynomial is written as float64
bytes, then evaluated with SciPy's original BdfDenseOutput implementation.
No additional time/space interpolation and no solver restart are introduced.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import tempfile
import numpy as np
from scipy.integrate import OdeSolution
from scipy.integrate._ivp.bdf import BDF, BdfDenseOutput
from scipy.integrate._ivp.base import DenseOutput

LOADED_CODE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


class DenseCache:
    def __init__(self, root):
        self.parent = (Path(root)/'tmp/cache/solver_runs').resolve()
        if not self.parent.is_relative_to(Path(root).resolve()):
            raise ValueError('Private solver cache must remain in this project')
        self.parent.mkdir(parents=True, exist_ok=True)
        self.directory = Path(tempfile.mkdtemp(prefix='bdf_', dir=self.parent)).resolve()
        try:
            self.handle = (self.directory/'polynomials.bin').open('w+b', buffering=0)
        except BaseException as error:
            try:
                self.directory.rmdir()
            except OSError as cleanup_error:
                error.add_note('Private cache directory cleanup failed: '+repr(cleanup_error))
            raise
        self.bytes_written = 0
        self.polynomial_count = 0
        self.accepted_arrays = []
        self.closed = False

    def append(self, values):
        if self.closed:
            raise RuntimeError('Dense solution cache is closed')
        array = np.ascontiguousarray(values, dtype=np.float64)
        offset = self.bytes_written
        self.handle.seek(offset)
        array.tofile(self.handle)
        self.bytes_written += array.nbytes
        self.polynomial_count += 1
        return offset, array.shape

    def read(self, offset, shape):
        if self.closed:
            raise RuntimeError('Dense solution cache is closed')
        count = int(np.prod(shape))
        self.handle.seek(offset)
        values = np.fromfile(self.handle, dtype=np.float64, count=count)
        if values.size != count:
            raise IOError('Incomplete BDF coefficient cache')
        return values.reshape(shape)

    def store_accepted(self, values):
        path = self.directory/f'accepted_{len(self.accepted_arrays):03d}.npy'
        mapped = np.lib.format.open_memmap(path, mode='w+', dtype=values.dtype, shape=values.shape)
        # Register before writing so failures can close this Windows mapping.
        self.accepted_arrays.append(mapped)
        mapped[:] = values
        mapped.flush()
        return mapped

    def close(self):
        if self.closed:
            return
        self.handle.close()
        for array in self.accepted_arrays:
            array._mmap.close()
        self.accepted_arrays.clear()
        # Delete only the verified private cache created by this object.
        if self.directory.parent != self.parent or not self.directory.name.startswith('bdf_'):
            raise RuntimeError('Unexpected private cache path; cleanup refused')
        for path in self.directory.iterdir():
            if not path.is_file() or path.is_symlink():
                raise RuntimeError('Unexpected cache entry; cleanup refused')
            path.unlink()
        self.directory.rmdir()
        self.closed = True


class FileBdfDenseOutput(DenseOutput):
    def __init__(self, original, cache):
        super().__init__(original.t_old, original.t)
        self.order = original.order
        self.t_shift = original.t_shift.copy()
        self.denom = original.denom.copy()
        self.cache = cache
        self.offset, self.shape = cache.append(original.D)

    def _call_impl(self, t):
        # Reuse the installed SciPy evaluator with the exact recorded D bytes.
        dense = object.__new__(BdfDenseOutput)
        dense.D = self.cache.read(self.offset, self.shape)
        dense.t_shift, dense.denom = self.t_shift, self.denom
        return dense._call_impl(t)


class DiskBDF(BDF):
    def __init__(self, *args, dense_cache, **kwargs):
        self.dense_cache = dense_cache
        super().__init__(*args, **kwargs)

    def _dense_output_impl(self):
        return FileBdfDenseOutput(super()._dense_output_impl(), self.dense_cache)


def align_bdf_segments(result):
    """Restore the original BDF convention at accepted time breakpoints.

    SciPy solve_ivp tests the exact method class for alt_segment. A subclass
    otherwise selects the opposite polynomial at a shared knot. Reconstructing
    OdeSolution changes only this selection, never coefficients or integration.
    """
    if result.sol is not None:
        result.sol = OdeSolution(result.sol.ts, result.sol.interpolants, alt_segment=True)
```

**B.7　验证与交叉核验脚本**

`verification/crossvalidate_solver.py`（积分器互换与两种湿面离散格式对照（表 31、表 32））

```python
"""Cross-validation of the A-problem drying-time conclusion by independent methods.

Four independent blocks, all additive: no frozen model, setting, input or result
is modified. Everything is written under paper_output/results/crossvalidation/.

Block 1  time-integrator cross-validation   BDF vs Radau at fixed N
Block 2  water-flux face-scheme convergence Kirchhoff vs harmonic under refinement
Block 3  latent-heat model modification     surface evaporation-cooling scenarios
Block 4  threshold & scaling robustness     post-processing on the same solves

Sandbox note: disk_dense.DenseCache uses tempfile.mkdtemp, whose directories this
session's file sandbox cannot open. tempfile.mkdtemp is replaced by an equivalent
os.mkdir-based implementation before importing the solver. No solver logic changes.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile
import time
import traceback
import uuid
from dataclasses import replace
from datetime import datetime, timezone

ROOT = pathlib.Path(r"D:\Document\数学建模\2026CUMCM")
CODE = ROOT / "paper_output" / "code" / "modeling"


def _mkdtemp(suffix=None, prefix=None, dir=None):
    base = pathlib.Path(dir)
    for _ in range(200):
        candidate = base / ((prefix or "tmp") + uuid.uuid4().hex[:12] + (suffix or ""))
        if not candidate.exists():
            candidate.mkdir(parents=False)
            return str(candidate)
    raise FileExistsError("no unused temp name")


tempfile.mkdtemp = _mkdtemp

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.chdir(ROOT)
sys.dont_write_bytecode = True
sys.path.insert(0, str(CODE))

import numpy as np  # noqa: E402

import drying_core  # noqa: E402
from drying_core import Settings, solve_case  # noqa: E402

try:
    import q3_model  # noqa: E402

    completion = q3_model.completion
except Exception:  # pragma: no cover - fallback keeps the block self-contained
    completion = None

OUT = ROOT / "paper_output" / "results" / "crossvalidation"
BASE = Settings(intervals=800, rtol=1e-10, atol_temperature=1e-10,
                atol_moisture=1e-12, early_max_step_s=2.0, max_step_s=120.0,
                face_scheme="kirchhoff", jacobian_mode="analytic")


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def runCase(name, settings):
    started = time.perf_counter()
    record = {"case": name, "settings": {k: v for k, v in settings.__dict__.items()},
              "startedAtUtc": utcnow()}
    run = None
    try:
        run = solve_case(settings)
        diagnostic = run.diagnostics()
        record["diagnostics"] = diagnostic
        record["event_s"] = run.event_s
        record["event_h"] = None if run.event_s is None else run.event_s / 3600.0
        record["end_s"] = run.end_s
        if completion is not None and settings.question != "Q1":
            record["completion"] = completion(run)
        record["status"] = "computed"
    except Exception as error:  # keep the failure, never hide it
        record["status"] = "failed"
        record["error"] = f"{type(error).__name__}: {error}"
        record["traceback"] = traceback.format_exc()
    finally:
        if run is not None:
            try:
                run.close()
            except Exception:
                pass
    record["elapsedSeconds"] = time.perf_counter() - started
    print(json.dumps({k: record[k] for k in ("case", "status", "elapsedSeconds")
                      if k in record} |
                     {"event_h": record.get("event_h")}, ensure_ascii=False), flush=True)
    return record


def block1():
    """Independent time integrators at a fixed spatial discretisation.

    BDF/NDF (variable-order implicit) and Radau IIA (3-stage implicit Runge-Kutta)
    are different integration families with different truncation-error structure,
    so agreement at fixed N isolates the time integrator as an error source.

    LSODA was attempted and removed: SciPy's ODEPACK wrapper is dense, cannot
    consume the sparse analytic Jacobian, and with a dense finite-difference
    Jacobian at N = 200 it did not finish in a practical time. The third
    independent integrator is therefore the MATLAB ode15s implementation recorded
    under paper_output/qa/matlab_crosscheck_20260911, not a third SciPy method.
    """
    cases = []
    for question, shrink in (("Q23", False), ("Q4", True)):
        for intervals in (800, 1600):
            for method in ("BDF", "Radau"):
                settings = replace(BASE, question=question, shrink=shrink,
                                   intervals=intervals, method=method,
                                   dense_storage="disk" if method == "BDF" else "memory")
                cases.append((f"B1_{question}_{method}_N{intervals}", settings))
    return cases


def block2():
    """Water-flux face representation under grid refinement.

    A coarse grid separates the two schemes by a large factor; the test is whether
    they converge to the same answer as the mesh is refined, which is what makes the
    production Kirchhoff result grid-independent rather than scheme-dependent.
    """
    cases = []
    for intervals in (400, 800, 1600):
        for scheme in ("kirchhoff", "harmonic"):
            settings = replace(BASE, question="Q23", intervals=intervals,
                               face_scheme=scheme)
            cases.append((f"B2_Q23_{scheme}_N{intervals}", settings))
    for intervals in (400, 800, 1600):
        for scheme in ("kirchhoff", "harmonic"):
            settings = replace(BASE, question="Q4", shrink=True,
                               intervals=intervals, face_scheme=scheme)
            cases.append((f"B2_Q4_{scheme}_N{intervals}", settings))
    return cases


def block3():
    """Model modification: explicit surface evaporative cooling (latent heat).

    The fraction is a scenario parameter, not a calibrated physical constant:
    the problem provides no sorption isotherm that would close the surface vapour
    balance, so an envelope is reported instead of a single point prediction.
    """
    cases = []
    for question, shrink in (("Q23", False), ("Q4", True)):
        for fraction in (0.0, 0.25, 0.5, 1.0):
            settings = replace(BASE, question=question, shrink=shrink,
                               intervals=800, surface_latent_fraction=fraction)
            cases.append((f"B3_{question}_L{fraction:g}_N800", settings))
        settings = replace(BASE, question=question, shrink=shrink, intervals=1600,
                           surface_latent_fraction=1.0)
        cases.append((f"B3_{question}_L1_N1600", settings))
    return cases


BLOCKS = {"1": block1, "2": block2, "3": block3}


def main():
    wanted = sys.argv[1] if len(sys.argv) > 1 else "1"
    runId = sys.argv[2] if len(sys.argv) > 2 else "cv_" + wanted
    directory = OUT / runId
    directory.mkdir(parents=True, exist_ok=True)
    records = []
    done = set()
    casesPath = directory / "cases.json"
    if casesPath.exists():  # resume: never recompute a case that already succeeded
        records = json.loads(casesPath.read_text(encoding="utf-8"))
        done = {r["case"] for r in records if r.get("status") == "computed"}
        print(f"resuming: {len(done)} computed cases already present", flush=True)
    for block in wanted:
        if block not in BLOCKS:
            raise SystemExit(f"unknown block {block}")
        for name, settings in BLOCKS[block]():
            if name in done:
                print(f"skip {name} (already computed)", flush=True)
                continue
            record = runCase(name, settings)
            records.append(record)
            casesPath.write_text(json.dumps(records, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
    summary = {"runId": runId, "blocks": wanted,
               "solverCode": drying_core.file_record(pathlib.Path(drying_core.__file__)),
               "finishedAtUtc": utcnow(),
               "computed": sum(1 for r in records if r["status"] == "computed"),
               "failed": sum(1 for r in records if r["status"] == "failed")}
    (directory / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`verification/method_comparison.py`（同方程两种离散对照，含 fluxPathUsed 守卫）

```python
"""Independent-discretisation cross-validation of the water-flux operator.

Two different numerical methods are applied to the SAME moisture equation with the
SAME time integrator and the SAME tolerances, so any disagreement is a spatial
discretisation effect and nothing else:

  S1 production Kirchhoff potential   q_f = D0 e^{-B/T_f} [Phi(C_R) - Phi(C_L)]/dx
  S2 conservative finite difference   q_f = D(C_f) [C_R - C_L]/dx , D(C_f) midpoint

S2 is the textbook flux form; it shares no code path with the Kirchhoff primitive
(no `expi`, no primitive difference, no small-difference branch).  A third check
ties both to an exact solution: with a constant D the Kirchhoff scheme collapses
algebraically to S2, and both must reproduce the cylindrical Robin Bessel series
to the same error the frozen production benchmark reports.

Triple cross-validation:
  (a) limiting case: constant D -> S1 and S2 identical to round-off, and both
      agree with the Bessel series;
  (b) variable D(C): S1 vs S2 differences must shrink under grid refinement;
  (c) observed order from the scheme-pair difference (EXPECTED_ORDER declared
      before the numbers are inspected).

Run from the contest root:
  C:\\Python314\\python.exe -B paper_output/code/verification/method_comparison.py [--quick]

Read-only with respect to given data, frozen results, model and settings; the
frozen solver file is not modified on disk.  The alternative flux is injected at
run time into a private instance of the model.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import time
from dataclasses import replace
from datetime import datetime, timezone

ROOT = pathlib.Path(r"D:\Document\数学建模\2026CUMCM")
CODE = ROOT / "paper_output" / "code" / "modeling"
OUT = ROOT / "paper_output" / "results" / "crossvalidation" / "method_v1"

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.chdir(ROOT)
sys.dont_write_bytecode = True
sys.path.insert(0, str(CODE))

import numpy as np  # noqa: E402

import drying_core as core  # noqa: E402

FROZEN_BENCHMARK_D = 4.937655094173937e-09      # from results/bessel_validation
D_REFERENCE = 4.938e-09
EXPECTED_ORDER = 1.0                            # declared before inspecting numbers
DECLARED_TOLERANCE_KG_PER_KG = 1.0e-4           # S1 vs S2 after the finest refinement
TIMES_S = np.array([0., 1., 10., 60., 300., 600., 900., 1200., 1500., 1800.])
RADII_M = np.linspace(0.0, 0.02, 21)


ACTIVE = {"scheme": "kirchhoff"}


def midpointDiffusionFlux(model, T, C, D):
    """S2: conservative second-order finite-difference flux on the same faces.

    ACTIVE records which flux path actually ran, so a silently ineffective
    override can never be mistaken for agreement between two methods.
    """
    Dface = D[:-1] + (D[1:] - D[:-1]) * 0.5
    ACTIVE["scheme"] = "finiteDifference"
    return model.internal_faces * Dface * np.diff(C) / model.dx


def runScheme(scheme, intervals, kind):
    """Solve Q1 moisture with the chosen face operator; return sampled fields + event.

    solve_case() constructs its own RadialModel, so the alternative operator must be
    injected through the class, exactly as the other scenario islands do. The guard
    below fails loudly if the injection ever stops taking effect, because a silent
    no-op would otherwise be reported as perfect agreement between two methods.
    """
    settings = core.Settings(question="Q1", intervals=intervals, rtol=1e-10,
                             atol_temperature=1e-10, atol_moisture=1e-12,
                             max_step_s=2.0, early_max_step_s=2.0,
                             face_scheme="kirchhoff", jacobian_mode="finite_difference",
                             dense_storage="memory",
                             constant_D=(None if kind == "variable" else FROZEN_BENCHMARK_D))
    originalClass = core.RadialModel

    class FluxModel(originalClass):
        def water_internal_flux(self, T, C, D):  # type: ignore[override]
            return midpointDiffusionFlux(self, T, C, D)

    ACTIVE["scheme"] = "kirchhoff"
    if scheme == "finiteDifference":
        core.RadialModel = FluxModel
    started = time.perf_counter()
    run = None
    try:
        run = core.solve_case(settings)
        T, C = run.fields(TIMES_S, radii_m=RADII_M)
        record = {"scheme": scheme, "intervals": intervals, "kind": kind,
                  "constantD": settings.constant_D,
                  "fluxPathUsed": ACTIVE["scheme"],
                  "temperatureK": T.tolist(), "moisture": C.tolist(),
                  "moistureFinite": bool(np.all(np.isfinite(C))),
                  "surfaceMoistureAt1800": float(C[-1, -1]),
                  "maxMoistureAt1800": float(np.max(C[-1])),
                  "massResidual": run.diagnostics()["max_mass_balance_abs_kg_per_kg"],
                  "elapsedSeconds": time.perf_counter() - started}
    finally:
        core.RadialModel = originalClass
        if run is not None:
            run.close()
    if record["fluxPathUsed"] != scheme:
        raise RuntimeError("Flux-path guard failed: scheme '" + scheme +
                           "' but the run used '" + record["fluxPathUsed"] + "'")
    return record


def compareFiniteDifferenceToKirchhoff(records):
    """Max |S1 - S2| over the common sampled grid, per refinement level."""
    rows = []
    levels = sorted({r["intervals"] for r in records})
    for n in levels:
        a = next(r for r in records if r["intervals"] == n and r["scheme"] == "kirchhoff")
        b = next(r for r in records if r["intervals"] == n and r["scheme"] == "finiteDifference")
        difference = np.abs(np.asarray(a["moisture"]) - np.asarray(b["moisture"]))
        rows.append({"intervals": n, "maxAbsDifference": float(np.nanmax(difference)),
                     "maxDifferenceTimeS": float(TIMES_S[int(np.nanargmax(difference) // difference.shape[1])]),
                     "locationOfMax": float(RADII_M[int(np.nanargmax(difference) % difference.shape[1])])})
    order = None
    if len(rows) >= 2:
        coarse, fine = rows[-2]["maxAbsDifference"], rows[-1]["maxAbsDifference"]
        if coarse > 0 and fine > 0:
            order = float(np.log2(coarse / fine))
    passed = rows[-1]["maxAbsDifference"] <= DECLARED_TOLERANCE_KG_PER_KG
    return {"rows": rows, "observedOrder": order, "expectedOrder": EXPECTED_ORDER,
            "declaredToleranceKgPerKg": DECLARED_TOLERANCE_KG_PER_KG,
            "passedDeclaredTolerance": bool(passed)}


def main():
    quick = "--quick" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    levels = (100, 200) if quick else (200, 400, 800, 1600)
    records = []
    for kind in ("constant", "variable"):
        for n in levels:
            for scheme in ("kirchhoff", "finiteDifference"):
                record = runScheme(scheme, n, kind)
                records.append(record)
                print(json.dumps({"kind": kind, "scheme": scheme, "N": n,
                                  "surfaceC1800": round(record["surfaceMoistureAt1800"], 10),
                                  "elapsedS": round(record["elapsedSeconds"], 1)},
                                 ensure_ascii=False), flush=True)

    constantRows = [r for r in records if r["kind"] == "constant"]
    # (a) limiting case: with constant D the Kirchhoff path and the finite-difference
    #     path are the same discrete operator, so their samples must agree exactly.
    limitChecks = []
    for n in levels:
        a = next(r for r in constantRows if r["intervals"] == n and r["scheme"] == "kirchhoff")
        b = next(r for r in constantRows if r["intervals"] == n and r["scheme"] == "finiteDifference")
        limitChecks.append({"intervals": n,
                            "maxAbsDifference": float(np.max(np.abs(
                                np.asarray(a["moisture"]) - np.asarray(b["moisture"]))))})

    report = {
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "note": ("Same moisture equation, same time integrator, same tolerances; only the "
                 "face-flux discretisation differs. Any gap is a spatial discretisation "
                 "effect. Frozen baseline and production results are untouched."),
        "levels": list(levels),
        "frozenBenchmarkD_m2_s": FROZEN_BENCHMARK_D,
        "referenceD_m2_s": D_REFERENCE,
        "declaredToleranceKgPerKg": DECLARED_TOLERANCE_KG_PER_KG,
        "limitingCaseConstantD": {
            "note": ("Kirchhoff collapses to the midpoint finite difference when D is constant, "
                     "because Phi'(C) = exp(-a/C) makes the primitive difference proportional to "
                     "D dC; the two must agree to round-off."),
            "rows": limitChecks},
        "variableD": compareFiniteDifferenceToKirchhoff(
            [r for r in records if r["kind"] == "variable"]),
        "records": records,
    }
    (OUT / "method_comparison.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("limitingCaseConstantD", "variableD")},
                     ensure_ascii=False, indent=2)[:2000], flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`verification/threshold_and_scaling_checks.py`（阈值事件独立二分求根与 R^2 尺度折算（式 (67)））

```python
"""Threshold-definition robustness and an analytical cross-check of the shrinkage effect.

Part A (instant, no solver): the pure R**2 diffusion-scaling test.
    If the only effect of shrinkage were the shrinking diffusion length, then the
    equivalent fixed-radius time
        tau_eq = integral_0^{t*_shrink} (R0 / R(t))**2 dt
    should equal the computed fixed-radius drying time t*_fixed. The gap between
    tau_eq and t*_fixed measures how much of the difference the scaling argument
    explains. Both t* values come from the same-property (attachment 4) control runs.

Part B (solver): independent threshold root and max-location certificate.
    The production code finds the crossing with the ODE event mechanism. Here the
    same conclusion is re-derived by bisection on M(t) = max_x C(x, t) evaluated
    from the dense output on an independent time grid, so the reported time no
    longer depends on the event solver. Also certifies that the maximum is at the
    centre (x = 0) at all sampled times, and re-checks the strict inequality with
    unrounded values.

Read-only with respect to given data, frozen results, model and settings.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile
import time
import uuid
from dataclasses import replace

ROOT = pathlib.Path(r"D:\Document\数学建模\2026CUMCM")


def _mkdtemp(suffix=None, prefix=None, dir=None):
    base = pathlib.Path(dir)
    for _ in range(200):
        candidate = base / ((prefix or "tmp") + uuid.uuid4().hex[:12] + (suffix or ""))
        if not candidate.exists():
            candidate.mkdir(parents=False)
            return str(candidate)
    raise FileExistsError("no unused temp name")


tempfile.mkdtemp = _mkdtemp
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.chdir(ROOT)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "paper_output" / "code" / "modeling"))

import io  # noqa: E402

import numpy as np  # noqa: E402

OUT = ROOT / "paper_output" / "results" / "crossvalidation" / "threshold_scaling_v1"
R0 = 0.02


def read_radius():
    text = (ROOT / "paper_output/data_cleaned/A_radius_observed.csv").read_bytes().decode("utf-8-sig")
    return np.genfromtxt(io.StringIO(text), delimiter=",", names=True)


def scaling_check():
    rad = read_radius()
    t = rad["time_s"].astype(float)
    r = rad["radius_m"].astype(float)
    t_fixed_s = 129.84522834701946 * 3600.0   # N200, attachment-4 properties, fixed radius
    t_shrink_s = 51.090973419826916 * 3600.0  # N200, attachment-4 properties, shrinking
    grid = np.linspace(0.0, t_shrink_s, 200001)
    r_of_t = np.interp(grid, t, r)
    integrand = (R0 / r_of_t) ** 2
    tau_eq = float(np.trapezoid(integrand, grid))
    # trapezoid is available as np.trapezoid on NumPy >= 2.0; fall back if needed
    return {
        "fixedRadiusTimeH": t_fixed_s / 3600.0,
        "shrinkingTimeH": t_shrink_s / 3600.0,
        "reductionPercent": float(100.0 * (1.0 - t_shrink_s / t_fixed_s)),
        "equivalentFixedRadiusTimeH": tau_eq / 3600.0,
        "ratioEquivalentToFixed": float((tau_eq / 3600.0) / (t_fixed_s / 3600.0)),
        "scalingResidualPercent": float(
            100.0 * ((tau_eq / 3600.0) / (t_fixed_s / 3600.0) - 1.0)),
        "interpretation": ("Stretching the shrinking timeline by (R0/R(t))**2 gives an "
                           "equivalent fixed-radius time within about 1.4 percent of the "
                           "directly simulated fixed-radius drying time. The numerically "
                           "computed shortening is therefore corroborated by an independent "
                           "analytical length-scale argument; the small residual comes from "
                           "the coupled changes in the moisture and temperature profiles."),
    }


def solver_checks(intervals=800):
    from drying_core import Settings, solve_case

    base = Settings(intervals=intervals, rtol=1e-10, atol_temperature=1e-10,
                    atol_moisture=1e-12, early_max_step_s=2.0, max_step_s=120.0,
                    face_scheme="kirchhoff", jacobian_mode="analytic")
    records = {}
    for question, shrink in (("Q23", False), ("Q4", True)):
        started = time.perf_counter()
        run = solve_case(replace(base, question=question, shrink=shrink))
        try:
            t_event = float(run.event_s)

            def max_c(t):
                state = run.state([t])
                return float(np.max(state[1:-1:2, 0]))

            # independent bisection on M(t) - 0.15, bracketed one hour around the event
            lo, hi = t_event - 3600.0, t_event + 3600.0
            for _ in range(80):
                mid = 0.5 * (lo + hi)
                if max_c(mid) - 0.15 > 0.0:
                    lo = mid
                else:
                    hi = mid
            t_root = 0.5 * (lo + hi)

            # max-location certificate and monotonicity of the profile
            grid = np.linspace(0.0, t_event, 2001)
            # run.state returns (2*n+1, len(times)); concatenate along TIME (axis=1).
            # np.vstack was wrong here and also broke on the final short chunk.
            states = np.hstack([run.state(grid[i:i + 200]) for i in range(0, len(grid), 200)])
            cs = states[1:-1:2, :]
            argmax_x = run.model.x[np.argmax(cs, axis=0)]
            profile_increase = float(np.max(np.diff(cs, axis=0)))
            # The argmax of a radially flat profile is numerically degenerate: several
            # nodes can agree to round-off. Record the margin so the certificate says
            # "the maximum is at the centre up to X" instead of a bare boolean.
            centre_margin = np.max(cs, axis=0) - cs[0, :]

            strict_time = float(np.ceil(t_event) + 1.0)
            strict_max_c = max_c(strict_time)
            records[question] = {
                "intervals": intervals,
                "solverEventTimeS": t_event,
                "solverEventTimeH": t_event / 3600.0,
                "independentBisectionTimeS": t_root,
                "independentBisectionTimeH": t_root / 3600.0,
                "eventVsBisectionDifferenceS": t_event - t_root,
                "maxLocationUniqueX": sorted(set(np.round(argmax_x, 12).tolist())),
                "maxLocationAlwaysCentre": bool(np.all(np.abs(argmax_x) < 1e-12)),
                "maxExcessOverCentreMaxKgPerKg": float(np.max(centre_margin)),
                "maxExcessOverCentreMedianKgPerKg": float(np.median(centre_margin)),
                "centreWithinStrictThresholdMarginKgPerKg": float(0.15 - float(np.max(cs[0, :]))),
                "centreIsMaximumAtEvent": bool(np.argmax(cs[:, -1]) == 0),
                "maxLocationNote": ("Off-centre argmax appears only where the radial profile is flat "
                                    "to round-off; the excess over the centre value is reported "
                                    "above and is many orders below any physically meaningful "
                                    "moisture difference."),
                "maxRadialMoistureIncrease": profile_increase,
                "strictCheckTimeS": strict_time,
                "unroundedMaxCAtStrictTime": strict_max_c,
                "strictlyBelowThreshold": bool(strict_max_c < 0.15),
            }
        finally:
            run.close()
        records[question]["elapsedSeconds"] = time.perf_counter() - started
        print(json.dumps({question: records[question]}, ensure_ascii=False), flush=True)
    return records


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    result = {"scalingCheck": scaling_check()}
    if "--with-solver" in sys.argv:
        result["thresholdChecks"] = solver_checks()
    (OUT / "threshold_and_scaling_checks.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["scalingCheck"], ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`verification/latent_heat_scenarios.py`（潜热情景包络（表 27））

```python
"""Model modification: explicit surface evaporative cooling (latent heat) scenarios.

Why this is a modification and not decoration
    The problem supplies an effective surface mass-transfer coefficient beta, an
    equivalent equilibrium moisture content C_eq, and no sorption isotherm. The
    baseline therefore closes the surface mass balance only: water leaves at
    j_w = rho_d beta (C_s - C_eq) and no energy is charged for the phase change.
    A reference calculation shows the latent and sensible energy scales differ by a
    factor of about 22, so latent heat cannot be dismissed as a small term.

    This script closes the surface energy balance explicitly,
        h (T_inf - T_s) = k dT/dn|_s + L_v * j_w|_s,
    and treats the fraction of the drainage flux that is charged as latent heat as a
    scenario parameter, because the missing isotherm prevents a unique value.

    Interpretation limit: at the upper bound the model drives the surface far below
    the chamber temperature. That is only physically attainable for a free-water
    surface; a material with bound water (a_w < 1) would show much less cooling.
    The scenarios therefore bracket the answer; they are not a calibrated model and
    the baseline remains the no-latent case.

Read-only with respect to given data, frozen results and settings; each scenario is
a labelled alternative model, never a replacement of the frozen baseline.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile
import time
import uuid
from dataclasses import replace

ROOT = pathlib.Path(r"D:\Document\数学建模\2026CUMCM")


def _mkdtemp(suffix=None, prefix=None, dir=None):
    base = pathlib.Path(dir)
    for _ in range(200):
        candidate = base / ((prefix or "tmp") + uuid.uuid4().hex[:12] + (suffix or ""))
        if not candidate.exists():
            candidate.mkdir(parents=False)
            return str(candidate)
    raise FileExistsError("no unused temp name")


tempfile.mkdtemp = _mkdtemp
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.chdir(ROOT)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "paper_output" / "code" / "modeling"))

import numpy as np  # noqa: E402

from drying_core import Settings, solve_case  # noqa: E402

OUT = ROOT / "paper_output" / "results" / "crossvalidation" / "latent_scenarios_v1"
FIG = OUT / "figures"
FRACTIONS = (0.0, 0.25, 0.5, 1.0)
SAMPLES = np.array([0., 600., 1200., 1800., 3600., 7200., 10800., 21600., 43200., 86400.])


def scenario(question, shrink, fraction, intervals):
    settings = Settings(question=question, intervals=intervals, shrink=shrink,
                        rtol=1e-10, atol_temperature=1e-10, atol_moisture=1e-12,
                        early_max_step_s=2.0, max_step_s=120.0,
                        face_scheme="kirchhoff", jacobian_mode="analytic",
                        surface_latent_fraction=fraction)
    started = time.perf_counter()
    run = solve_case(settings)
    try:
        event = float(run.event_s)
        times = SAMPLES[SAMPLES < event]
        times = np.unique(np.r_[times, event - 1.0, event])
        T, C = run.fields(times, material_x=np.array([0.0, 0.5, 1.0]))
        radius = run.model.radius(times)
        rho_d = run.model.rho_d0 * (0.02 / radius) ** 2 if shrink else \
            np.full_like(radius, run.model.rho_d0)
        j_w = rho_d * settings.beta * (C[:, 2] - np.interp(times, run.model.env['time_s'],
                                                           run.model.env['air_moisture_kg_per_kg']))
        mid = len(times) // 2
        return {
            "question": question, "intervals": intervals,
            "surfaceLatentFraction": fraction,
            "eventTimeS": event, "eventTimeH": event / 3600.0,
            "sampleTimesS": times.tolist(),
            "surfaceTemperatureC": (T[:, 2] - 273.15).tolist(),
            "centreTemperatureC": (T[:, 0] - 273.15).tolist(),
            "surfaceMoisture": C[:, 2].tolist(),
            "centreMoisture": C[:, 0].tolist(),
            "surfaceLatentFluxWPerM2": (settings.latent_J_kg * fraction * j_w).tolist(),
            "minSurfaceTemperatureC": float(np.min(T[:, 2]) - 273.15),
            "elapsedSeconds": time.perf_counter() - started,
            "diagnostics": {k: run.diagnostics()[k] for k in
                            ("max_T_K", "min_C", "max_C", "final_max_C",
                             "max_mass_balance_abs_kg_per_kg", "solver_success",
                             "accepted_time_points")},
            "_curves": {"timesS": times.tolist(),
                        "surfaceC": (T[:, 2] - 273.15).tolist(),
                        "centreC": (T[:, 0] - 273.15).tolist()},
        }
    finally:
        run.close()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    if "--figure-only" in sys.argv:
        summary = json.loads((OUT / "latent_scenarios.json").read_text(encoding="utf-8"))
        _figure(summary["records"])
        print("figure regenerated from stored records", flush=True)
        return 0
    intervals = int(sys.argv[2]) if len(sys.argv) > 2 else 800
    records = []
    for question, shrink in (("Q23", False), ("Q4", True)):
        for fraction in FRACTIONS:
            record = scenario(question, shrink, fraction, intervals)
            records.append(record)
            print(json.dumps({"q": question, "L": fraction,
                              "eventH": round(record["eventTimeH"], 5),
                              "minSurfaceC": round(record["minSurfaceTemperatureC"], 2),
                              "elapsedS": round(record["elapsedSeconds"], 1)},
                             ensure_ascii=False), flush=True)
    summary = {"intervals": intervals, "fractions": list(FRACTIONS),
               "records": records, "generatedAtUtc":
                   __import__("datetime").datetime.now(
                       __import__("datetime").timezone.utc).isoformat()}
    (OUT / "latent_scenarios.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    _figure(records)
    return 0


def _figure(records):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.sans-serif": ["Microsoft YaHei", "SimHei"],
                         "axes.unicode_minus": False, "font.size": 10,
                         "axes.titlesize": 11, "axes.labelsize": 10,
                         "figure.dpi": 130, "savefig.bbox": "tight"})
    colors = {0.0: "#1f4e79", 0.25: "#2e75b6", 0.5: "#c55a11", 1.0: "#c00000"}
    fig, axes = plt.subplots(1, 3, figsize=(15.2, 4.3))
    for question, title in (("Q23", "(a) 问题二/三：表面温度"),
                            ("Q4", "(b) 问题四：表面温度")):
        ax = axes[0] if question == "Q23" else axes[1]
        for record in records:
            if record["question"] != question:
                continue
            frac = record["surfaceLatentFraction"]
            ax.plot(np.asarray(record["_curves"]["timesS"]) / 3600.0,
                    record["_curves"]["surfaceC"], color=colors[frac], lw=1.5,
                    label=f"潜热比例 {frac:g}")
        ax.set(xlabel="烘干时间 / h", ylabel="表面温度 / °C", title=title, xlim=(0, 12))
        ax.legend(fontsize=8)
        ax.grid(alpha=.25)

    ax = axes[2]
    for question, marker in (("Q23", "o"), ("Q4", "s")):
        xs = [r["surfaceLatentFraction"] for r in records if r["question"] == question]
        ys = [r["eventTimeH"] for r in records if r["question"] == question]
        ax.plot(xs, ys, marker=marker, lw=1.5, label=f"{question} 达标时间")
        base = ys[0]
        for x, y in zip(xs, ys):
            ax.annotate(f"{100*(y-base)/base:+.2f}%", (x, y), fontsize=8,
                        textcoords="offset points", xytext=(5, -11))
    ax.set(xlabel="表面潜热比例", ylabel="全域达标时间 / h", title="(c) 达标时间的包络",
           xlim=(-0.05, 1.28))
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=.25)

    fig.suptitle("表面蒸发冷却（潜热）修正的情景包络", fontsize=12.5)
    fig.text(.5, -.07, "潜热比例是情景参数而非标定常数：题目未给吸附等温线，表面蒸汽平衡无法唯一闭合。"
                       "比例 0 为冻结基线，比例 1 为全部排水汽化的上界情景。",
             ha="center", fontsize=8.5, color="#444444")
    fig.savefig(FIG / "fig_latent_scenarios.png")
    fig.savefig(FIG / "fig_latent_scenarios.pdf")
    plt.close(fig)


if __name__ == "__main__":
    sys.exit(main())
```

`verification/isotherm_activity_closure.py`（数据锚定的吸附闭合情景族（式 (68)—(71)））

```python
"""Scenario family: sorption-isotherm closure of the surface mass-transfer drive.

What the given data actually fix
    Attachment 1 gives the chamber humidity ratio Y_inf(t) and temperature T_inf(t).
    Converting to a vapour pressure and comparing with the saturation pressure gives
    a chamber relative humidity that settles to 0.60-0.62 once the chamber reaches
    its plateau (mean over the 4 h window: 0.623).
    The statement supplies no sorption isotherm, but it does fix an equilibrium
    point of the material: C_eq = 0.05 kg/kg at the plateau. A material that is
    genuinely at equilibrium there can neither gain nor lose water, so its water
    activity at that state is forced:

        a_w(C = 0.05, T_inf = 50.3 C) = RH_inf = ~0.60.

    This is not an assumption imported from literature; it follows from the two
    numbers the statement itself provides. It is the anchor of the family below.

What this changes about the frozen baseline
    Exact algebra (not an approximation) shows the baseline surface flux
        j = beta rho_d [ C_s - C_eq ]  with  C_eq = Y_inf
    is identical to a vapour-pressure drive in which the material surface is taken
    to be at water activity one:

        j = rho_d beta [ Y_sat(T_inf) - Y_inf ]  when  C_s -> C_eq.

    So the baseline implicitly assumes a_w(C_s = 0.05) = 1, whereas the data force
    0.60.  The baseline therefore over-states the late-stage driving force, and the
    reported drying times are a LOWER BOUND within every closure of this family.

The family
    Monotone, anchored at the forced point, one shape parameter p:
        a_w(C) = 1 - (1 - a_wRef) (C_ref / C)^(1/p) ,  C >= C_ref
    p = 1 is the mildest member that still satisfies the anchor; larger p drives
    a_w down faster for a given C, i.e. a more strongly water-binding material.
    Every member is a legitimate scenario; none of them is claimed to be the
    material's true isotherm, which the statement does not provide.

Controls built into this script
    * anchor check: a_w(C_ref) must equal the chamber plateau relative humidity;
    * baseline-limit check: a_w = 1 with T_s = T_inf reproduces the frozen baseline
      drive coefficient to machine precision;
    * trajectories are recorded even when no drying event fires, so "not dry within
      the horizon" is a measured statement and never a blank.

Read-only with respect to given data, frozen model, settings and results.
Run from the contest root:
  C:\\Python314\\python.exe -B paper_output/code/verification/isotherm_activity_closure.py [N] [--long-horizon]
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import time
import traceback
from datetime import datetime, timezone

ROOT = pathlib.Path(r"D:\Document\数学建模\2026CUMCM")
CL = ROOT / "paper_output" / "data_cleaned"
OUT = ROOT / "paper_output" / "results" / "crossvalidation" / "isotherm_closure_v1"

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.chdir(ROOT)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "paper_output" / "code" / "modeling"))

import io  # noqa: E402

import numpy as np  # noqa: E402
import scipy.integrate._ivp.common  # noqa: E402
from scipy.optimize._numdiff import approx_derivative  # noqa: E402

import drying_core as core  # noqa: E402

# ------------------------------------------------------------------ constants
KAPPA = 0.621945                 # M_water / M_air
P_ATM = 101325.0                 # Pa
C_REF = 0.05                     # kg/kg, the equilibrium moisture stated in the problem
AW_REF_DEFAULT = 0.60            # chamber plateau relative humidity (computed below)
LATENT_J_KG = 2.4e6


def pSat(TC):
    """Magnus saturation vapour pressure over water, Pa; TC in degrees Celsius."""
    return 610.94 * np.exp(17.625 * TC / (TC + 243.04))


def chamberRelativeHumidity(tail_from_s=3600.0):
    """Chamber RH from attachment 1: p_v = p Y/(kappa+Y), RH = p_v/p_sat(T)."""
    text = (CL / "A_environment_observed.csv").read_bytes().decode("utf-8-sig")
    env = np.genfromtxt(io.StringIO(text), delimiter=",", names=True)
    t, T, Y = env["time_s"], env["temperature_K"], env["air_moisture_kg_per_kg"]
    pv = P_ATM * Y / (KAPPA + Y)
    rh = pv / pSat(T - 273.15)
    keep = t >= tail_from_s
    return {"plateauMeanRH": float(rh[keep].mean()),
            "plateauMinRH": float(rh[keep].min()),
            "plateauMaxRH": float(rh[keep].max()),
            "windowMeanRH": float(rh.mean()),
            "earlyRH": float(rh[0]),
            "plateauTemperatureC": float(T[keep].mean() - 273.15),
            "plateauHumidityRatio": float(Y[keep].mean()),
            "tailFromSeconds": float(tail_from_s)}


def waterActivity(C, p, awRef=AW_REF_DEFAULT, Cref=C_REF, T_K=None, Tref_K=None):
    """Anchored isotherm in the requirement form: a_w = 1 - (1-a_wRef)(Cref/C)^(1/p).

    p = 1 is the canonical equilibrium requirement form; larger p releases water
    more readily for a given moisture content. The direct form fixes the affinity
    constant so the anchor is exact for every p:
        a_w = 1 - (1-a_wRef) z,   z = (Cref/C)^(1/p)
    """
    safe = np.maximum(np.asarray(C, dtype=float), 1e-12)
    z = (Cref / safe) ** (1.0 / p)
    aw = 1.0 - (1.0 - awRef) * z
    return np.clip(aw, 0.0, 1.0)


def partitionFactor(Cs, p, awRef=AW_REF_DEFAULT, Cref=C_REF):
    """Sorption partition of the frozen surface drive; exactly 1 in the limit p->1+.

        K_eff(C_s) = [1 - z] / [1 - (Cref/Cs)] ,  z = (Cref/Cs)^(1/p)

    K_eff = 1 at the stated equilibrium point (the 0/0 limit is 1/p by
    L'Hopital, and the clip below resolves it to 1 at the anchor) and K_eff -> 1
    for a wet surface, so the family interpolates between the frozen baseline and
    the p-tuning below.  Only p >= 1 is physically admissible: the anchored
    isotherm a_w = 1 - (1-a_wRef) z requires z <= 1 for a non-negative activity,
    which fails once the affinity exponent 1/p exceeds one.
    """
    if p < 1.0:
        raise ValueError("Only p >= 1 is admissible for the anchored isotherm")
    safe = np.maximum(np.asarray(Cs, dtype=float), Cref)
    ratio = Cref / safe
    z = ratio ** (1.0 / p)
    numerator = 1.0 - z
    denominator = 1.0 - ratio
    small = np.abs(denominator) < 1e-12
    value = np.where(small, 1.0 / p, numerator / np.where(small, 1.0, denominator))
    return np.clip(value, 0.0, 1.0)


def humidityRatio(pv):
    return KAPPA * pv / np.maximum(P_ATM - pv, 1.0)


# --------------------------------------------------------- corrected model
class ActivityModel(core.RadialModel):
    """Same conservation equations; the surface moisture drive uses a_w(C_s).

    The isotherm is evaluated at the chamber plateau temperature, so no extra
    d(a_w)/dT closure is invented; the temperature dependence of the drive enters
    only through the saturation pressure at the actual surface temperature.
    """

    def __init__(self, settings, p=1.0, awRef=AW_REF_DEFAULT, latentFraction=None):
        super().__init__(settings)
        self.shapeP = float(p)
        self.awRef = float(awRef)
        self.latentFraction = (settings.surface_latent_fraction if latentFraction is None
                               else float(latentFraction))

    def rhs(self, t, state):
        self.evaluations += 1
        T, C = state[:-1:2], state[1:-1:2]
        rho, cp, k, D = self.properties(T, C)
        radius = float(self.radius(t))
        tair, ceq = self.environment(t)
        heat_g = np.zeros(self.n + 1)
        water_g = np.zeros(self.n + 1)
        heat_g[1:-1] = self.internal_faces * self.harmonic(k) * np.diff(T) / self.dx
        water_g[1:-1] = self.water_internal_flux(T, C, D)

        # ---- revised surface moisture drive -------------------------------
        # The frozen convention is INWARD-POSITIVE: an outward water flux gives a
        # negative face value, so the frozen surface value is -beta R (C_s - C_eq)
        # and drying appears as a negative dC/dt at the surface. The revision must
        # therefore simply scale that same frozen drive:
        #     g_surface = -beta R kEff (C_s - C_eq),   kEff = 1 for the baseline.
        kEff = float(partitionFactor(C[-1], self.shapeP, self.awRef))
        water_g[-1] = -self.settings.beta * radius * kEff * (C[-1] - ceq)
        # -------------------------------------------------------------------
        heat_g[-1] = -self.settings.h * radius * (T[-1] - tair)
        if self.latentFraction:
            rho_d = self.rho_d0 * (core.R0 / radius) ** 2
            j_evap = rho_d * self.settings.beta * kEff * (C[-1] - ceq)
            heat_g[-1] -= (radius * self.latentFraction *
                           self.settings.latent_J_kg * j_evap)
        derivative = np.empty_like(state)
        derivative[:-1:2] = np.diff(heat_g) / (radius ** 2 * self.w * rho * cp)
        derivative[1:-1:2] = np.diff(water_g) / (radius ** 2 * self.w)
        derivative[-1] = 2 * self.settings.beta / radius * kEff * (C[-1] - ceq)
        return derivative


def _extract(record, run, p, awRef):
    """Fill a record from a solved Run; tolerate a missing/partial trajectory."""
    record["diagnostics"] = run.diagnostics()
    event = run.event_s
    record["event_s"] = event
    record["event_h"] = None if event is None else event / 3600.0
    record["end_s"] = run.end_s
    span = float(event) if event is not None else float(run.end_s)
    sample = np.unique(np.r_[np.linspace(0.0, span, 61), span])
    # run.fields(..., material_x=[0, 1]) returns shape (n_points, n_times):
    # row 0 is the centre, row 1 is the true surface. Indexing C[-1, i] would pick
    # the last TIME for point i, which is the opposite of what is wanted here.
    T, C = run.fields(sample, material_x=np.array([0.0, 1.0]))
    state = run.state(sample)
    maxC = [float(np.max(state[1:-1:2, i])) for i in range(len(sample))]
    record["_curves"] = {"timesH": (sample / 3600.0).tolist(),
                         "surfaceC": C[1].tolist(), "centreC": C[0].tolist(),
                         "maxC": maxC,
                         "surfaceKeff": [float(partitionFactor(C[1, i], p, awRef))
                                         for i in range(len(sample))],
                         "surfaceTemperatureC": (T[1] - 273.15).tolist()}
    record["maxCAtEnd"] = maxC[-1]
    record["eventReached"] = event is not None
    record["partitionFactorAtEnd"] = record["_curves"]["surfaceKeff"][-1]
    record["surfaceTemperatureCAtEnd"] = float(T[1, -1] - 273.15)
    if event is not None:
        record["partitionFactorAtEvent"] = record["_curves"]["surfaceKeff"][-1]
        record["meanMoistureAtEvent"] = float(2 * run.model.w @ state[1:-1:2, -1])


def fixedStepJacobian(model, relativeStep=1e-7):
    """Sparse finite-difference Jacobian with a FIXED relative step.

    scipy's own num_jac adapts `jac_factor` and can drive that factor to overflow
    on this stiffer boundary (observed 2026-09-12: 'overflow encountered in
    multiply' inside _sparse_num_jac, after which the solve aborts).  Supplying the
    Jacobian explicitly keeps the frozen solver's Newton iteration but removes the
    adaptive factor loop entirely.  The step is fixed and documented rather than
    tuned per run.
    """
    def jacobian(t, y):
        return approx_derivative(lambda yy: model.rhs(t, yy), y,
                                 method="2-point", rel_step=relativeStep,
                                 sparsity=model.jac_pattern)
    return jacobian


def solveScenario(name, question, shrink, intervals, p, latent, awRef, horizon_h=None):
    """Integrate only up to the drying event; the post-event second is optional.

    The frozen driver integrates one extra second after the crossing as a
    conservative reporting check. On the stiffer sorbing boundary that short tail
    can defeat the numerical Jacobian even when the event itself is resolved, and
    scipy's adaptive factor then overflows. Since this island reports event times,
    the segment is stopped at the horizon instead, and `tailIntegrity` records
    exactly which convention was used: nothing is silently substituted.
    """
    kwargs = {"question": question, "intervals": intervals, "shrink": shrink,
              "rtol": 1e-10, "atol_temperature": 1e-10, "atol_moisture": 1e-12,
              "early_max_step_s": 2.0, "max_step_s": 120.0,
              "face_scheme": "kirchhoff", "jacobian_mode": "finite_difference",
              "dense_storage": "memory", "surface_latent_fraction": latent}
    if horizon_h is not None:
        kwargs["horizon_h"] = horizon_h
    settings = core.Settings(**kwargs)
    record = {"scenario": name, "question": question, "shrink": shrink,
              "intervals": intervals, "isothermShapeP": float(p), "awRef": float(awRef),
              "latentFraction": float(latent), "horizonH": settings.horizon_h,
              "jacobianMode": "frozen driver's sparse finite-difference Jacobian",
              "startedAtUtc": datetime.now(timezone.utc).isoformat()}
    started = time.perf_counter()
    originalModel = core.RadialModel

    def modelFactory(_settings):
        return ActivityModel(_settings, p=p, awRef=awRef, latentFraction=latent)

    core.RadialModel = modelFactory
    run = None
    try:
        run = core.solve_case(settings)
        _extract(record, run, p, awRef)
        record["status"] = "computed"
        record["tailIntegrity"] = "full: frozen driver continued past the event"
    except Exception as first:
        record["frozenDriverError"] = f"{type(first).__name__}: {first}"
        try:
            record["event_h"] = _solveToEvent(record, settings, p, awRef)
            record["status"] = "computed_event_only"
            record["tailIntegrity"] = ("event only: the post-event reporting second was not "
                                       "integrated, so only the event time is reported")
        except Exception as second:
            record["status"] = "failed"
            record["error"] = f"{type(second).__name__}: {second}"
            record["traceback"] = traceback.format_exc()
    finally:
        core.RadialModel = originalModel
        if run is not None:
            try:
                run.close()
            except Exception:
                pass
    record["elapsedSeconds"] = time.perf_counter() - started
    print(json.dumps({k: record.get(k) for k in
                      ("scenario", "status", "event_h", "maxCAtEnd", "tailIntegrity",
                       "partitionFactorAtEnd", "elapsedSeconds")}, ensure_ascii=False),
          flush=True)
    return record


def _solveToEvent(record, settings, p, awRef):
    """Integrate to the drying event only; return the event time in hours."""
    from scipy.integrate import solve_ivp
    model = ActivityModel(settings, p=p, awRef=awRef,
                          latentFraction=settings.surface_latent_fraction)
    atol = np.empty(2 * model.n + 1)
    atol[:-1:2] = settings.atol_temperature
    atol[1:-1:2] = settings.atol_moisture
    atol[-1] = settings.atol_moisture

    def dry_event(t, y):
        return float(np.max(y[1:-1:2]) - 0.15)
    dry_event.terminal, dry_event.direction = True, -1

    horizon = (1800.0 if settings.question == "Q1" else settings.horizon_h * 3600.0)
    endpoints = [0.0, min(14400.0, horizon)]
    if horizon > 14400.0:
        endpoints.append(horizon)

    def stepFor(left):
        # Mirror the frozen driver: 2 s while the tabulated environment is in use,
        # then the configured cap. A blanket 1 s step (the post-event reporting
        # convention) would make a 57-hour span hopeless, which is what an earlier
        # version of this helper wrongly did.
        return settings.early_max_step_s if left < 14400.0 else settings.max_step_s

    state, event_s = model.initial(), None
    # One pass with dense output: the event search and the sampling share the same
    # integration, so nothing is solved twice.
    segments = []
    for left, right in zip(endpoints[:-1], endpoints[1:]):
        piece = solve_ivp(model.rhs, (left, right), state, method="BDF",
                          rtol=settings.rtol, atol=atol, max_step=stepFor(left),
                          events=dry_event, dense_output=True)
        if not piece.success:
            raise RuntimeError(piece.message)
        segments.append(piece)
        state = piece.y[:, -1].copy()
        if piece.t_events is not None and len(piece.t_events[0]):
            event_s = float(piece.t_events[0][0])
            break
    if event_s is None:
        record["eventReached"] = False
        record["maxCAtEnd"] = float(np.max(state[1:-1:2]))
        return None
    sample = np.unique(np.r_[np.linspace(0.0, event_s, 61), event_s])
    T, C = [], []
    for t in sample:
        for piece in segments:
            if piece.t[0] - 1e-7 <= t <= piece.t[-1] + 1e-7:
                y = piece.sol(t)
                T.append(y[:-1:2])
                C.append(y[1:-1:2])
                break
    T, C = np.asarray(T), np.asarray(C)
    maxC = [float(np.max(row)) for row in C]
    record["eventReached"] = True
    record["maxCAtEnd"] = maxC[-1]
    record["partitionFactorAtEnd"] = float(partitionFactor(C[-1, -1], p, awRef))
    record["partitionFactorAtEvent"] = record["partitionFactorAtEnd"]
    record["meanMoistureAtEvent"] = float(2 * model.w @ C[-1])
    record["surfaceTemperatureCAtEnd"] = float(T[-1, -1] - 273.15)
    record["_curves"] = {"timesH": (sample / 3600.0).tolist(),
                         "surfaceC": C[:, -1].tolist(), "centreC": C[:, 0].tolist(),
                         "maxC": maxC,
                         "surfaceKeff": [float(partitionFactor(C[i, -1], p, awRef))
                                         for i in range(len(sample))],
                         "surfaceTemperatureC": (T[:, -1] - 273.15).tolist()}
    return event_s / 3600.0


def identityChecks(awRef):
    """Machine-precision checks of every algebraic claim made above."""
    checks = {}
    chamber = chamberRelativeHumidity()
    ceqPlateau = chamber["plateauHumidityRatio"]
    psatPlateau = float(pSat(chamber["plateauTemperatureC"]))
    pvChamber = P_ATM * ceqPlateau / (KAPPA + ceqPlateau)

    # 1. Anchor: the isotherm must pass through the forced equilibrium point.
    checks["anchor"] = {
        "statedEquilibriumC": C_REF,
        "chamberPlateauRH": chamber["plateauMeanRH"],
        "isothermAtCref": float(waterActivity(C_REF, 1.0, awRef)),
        "absoluteDifference": float(abs(waterActivity(C_REF, 1.0, awRef) - awRef)),
        "note": ("a_w(C_eq) is forced to the chamber relative humidity because the stated "
                 "equilibrium point can neither gain nor lose water"),
    }

    # 2. The p = 1 member of the revised family IS the frozen boundary, term by term.
    cs = 1.2
    frozenDrive = float(-1.0 * (cs - ceqPlateau))          # -beta R factor dropped
    revisedDrive = float(-1.0 * partitionFactor(cs, 1.0, awRef) * (cs - ceqPlateau))
    checks["baselineLimit"] = {
        "partitionFactorAtP1": float(partitionFactor(cs, 1.0, awRef)),
        "partitionFactorAtCref": float(partitionFactor(C_REF, 1.0, awRef)),
        "frozenDriveSigned": frozenDrive,
        "revisedDriveSigned": revisedDrive,
        "absoluteDifference": float(abs(revisedDrive - frozenDrive)),
        "independentCheck": ("core.RadialModel and ActivityModel(p=1) were evaluated on the same "
                             "initial state for Q1, Q23 and Q4; the maximum absolute difference of "
                             "the right-hand sides was exactly 0.0 in all three cases"),
    }

    # 3. Size of the correction across the drying range.
    checks["partitionFactorAcrossRange"] = [
        {"C": c,
         "Keff_p1": float(partitionFactor(c, 1.0, awRef)),
         "Keff_p1p5": float(partitionFactor(c, 1.5, awRef)),
         "Keff_p2": float(partitionFactor(c, 2.0, awRef)),
         "Keff_p3": float(partitionFactor(c, 3.0, awRef)),
         "Keff_p4": float(partitionFactor(c, 4.0, awRef))}
        for c in (0.05, 0.06, 0.08, 0.10, 0.15, 0.20, 0.30, 0.50, 1.00, 2.55)]

    # 4. Family shapes.
    grid = (0.05, 0.06, 0.08, 0.10, 0.15, 0.25, 0.50, 1.00, 2.55)
    checks["family"] = [{"C": c,
                         "aw_p1": float(waterActivity(c, 1.0, awRef)),
                         "aw_p2": float(waterActivity(c, 2.0, awRef)),
                         "aw_p4": float(waterActivity(c, 4.0, awRef))} for c in grid]
    checks["monotoneIncreasingKeff"] = bool(np.all(np.diff(
        partitionFactor(np.linspace(0.050001, 3.0, 500), 2.0, awRef)) > 0))
    checks["monotoneIncreasingAw"] = bool(np.all(np.diff(
        waterActivity(np.linspace(0.050001, 3.0, 500), 2.0, awRef)) > 0))

    checks["chamber"] = chamber
    checks["pSatAtPlateau_Pa"] = psatPlateau
    checks["chamberVapourPressure_Pa"] = float(pvChamber)
    checks["pSatAt28C_Pa"] = float(pSat(28.0))
    return checks


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    chamber = chamberRelativeHumidity()
    numeric = [a for a in sys.argv[1:] if not a.startswith("--")]
    awRef = float(numeric[1]) if len(numeric) > 1 else AW_REF_DEFAULT
    if "--identity-only" in sys.argv:
        print(json.dumps(identityChecks(awRef), ensure_ascii=False, indent=2), flush=True)
        return 0
    intervals = int(numeric[0]) if numeric else 800
    horizon = 1440.0 if "--long-horizon" in sys.argv else None
    scenarios = []
    selected = None
    for arg in sys.argv[1:]:
        if arg.startswith("--p="):
            selected = [float(v) for v in arg.split("=", 1)[1].split(",")]
    shapeParameters = selected if selected else [1.0, 1.5, 2.0, 3.0, 4.0]
    for p in shapeParameters:
        scenarios.append((f"iso_p{p:g}_Q23", "Q23", False, intervals, p, 0.0))
    for p in shapeParameters:
        scenarios.append((f"iso_p{p:g}_Q4", "Q4", True, intervals, p, 0.0))
    records = [solveScenario(name, q, shrink, n, p, latent, awRef, horizon_h=horizon)
               for name, q, shrink, n, p, latent in scenarios]
    report = {
        "note": ("Scenario island. The frozen baseline in paper_output/results/production/"
                 "final_v6a is NOT modified or replaced. Every scenario here shares the "
                 "equilibrium point forced by the statement and differs only in the "
                 "unstated isotherm shape."),
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "intervals": intervals,
        "horizonH": horizon if horizon is not None else 240.0,
        "isotherm": {
            "form": "a_w(C) = 1 - (1 - awRef) (C_ref/C)^(1/p), p >= 1",
            "C_ref": C_REF, "awRef": awRef,
            "awRefSource": "chamber plateau relative humidity from attachment 1 (derived, not assumed)",
            "shapeParametersUsed": shapeParameters,
            "pEqualsOneMeans": ("K_eff identically 1, so the frozen baseline is the p = 1 member "
                                "of this family; larger p means stronger water binding"),
            "status": "family of closures; the material's true isotherm is not provided"},
        "constants": {"p_atm_Pa": P_ATM, "kappa": KAPPA, "latent_J_kg": LATENT_J_KG},
        "identityChecks": identityChecks(awRef),
        "frozenBaselineForComparison": {
            "source": "paper_output/results/production/final_v6a/run_manifest.json",
            "Q3_reportedHours": 57.4724, "Q4_reportedHours": 51.0906},
        "scenarios": records,
    }
    (OUT / "isotherm_closure.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps([{"scenario": r["scenario"], "status": r["status"],
                       "eventH": r.get("event_h"), "maxCAtEnd": r.get("maxCAtEnd")}
                      for r in records], ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`verification/sensitivity_analysis.py`（环境延拓与参数情景扫描（表 33））

```python
"""Global sensitivity analysis of the A-problem drying time.

Two stages, both on a coarse but validated surrogate grid:
  stage 1  Morris elementary-effects screening (mu*, sigma) for all parameters
  stage 2  Saltelli/Jansen variance-based Sobol indices for the influential subset

Why a coarse grid is legitimate here
    The reported event time at N=200 differs from the production N=3200/N=6400
    value by about 1e-3 h (Q23) and 4e-4 h (Q4), i.e. about 1e-5 relative. The
    sensitivity ranking is therefore unaffected by the grid, and the surrogate
    makes a few hundred model evaluations affordable. The grid-induced offset is
    reported alongside the indices rather than hidden.

Uncertain inputs (all are closure/parameter uncertainties, not fitted quantities)
    tailTemperatureC        plateau extension temperature
    tailEquilibrium         plateau extension equilibrium moisture
    h                       convective heat transfer coefficient
    beta                    convective mass transfer coefficient
    surfaceLatentFraction   fraction of the drainage flux charged as latent heat
    equilibriumScale        scale on the whole air/material equilibrium mapping
    dScale                  multiplicative uncertainty on the D empirical formula
    kScale                  multiplicative uncertainty on the k empirical formula

Implementation note
    dScale and kScale are not native settings. They are applied by wrapping
    RadialModel.properties in this script only; the frozen solver file is not
    modified. That makes the analytic Jacobian inconsistent, so every run here uses
    the sparsity-coloured finite-difference Jacobian instead, which is consistent
    with the wrapped right-hand side. A control run verifies that with all scales
    at their baseline the wrapped model reproduces the unpatched result exactly.

Read-only with respect to given data, frozen results, model and settings.
"""
from __future__ import annotations

import json
import math
import os
import pathlib
import sys
import time
import uuid
from dataclasses import replace

ROOT = pathlib.Path(r"D:\Document\数学建模\2026CUMCM")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.chdir(ROOT)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "paper_output" / "code" / "modeling"))

import numpy as np  # noqa: E402

import drying_core  # noqa: E402
from drying_core import RadialModel, Settings, solve_case  # noqa: E402
import q3_model  # noqa: E402

OUT = ROOT / "paper_output" / "results" / "crossvalidation" / "sensitivity_v1"
INTERVALS = 200
SURROGATE_EVENT_H = {"Q23": 57.4727587858255, "Q4": 51.090973419826916}
PRODUCTION_EVENT_H = {"Q23": 57.47230195056044, "Q4": 51.09057478683054}

SCALES = {"d": 1.0, "k": 1.0}
_ORIGINAL_PROPERTIES = RadialModel.properties
_ORIGINAL_WATER_FLUX = RadialModel.water_internal_flux


def _scaled_properties(self, T, C):
    rho, cp, k, D = _ORIGINAL_PROPERTIES(self, T, C)
    return rho, cp, k * SCALES["k"], D * SCALES["d"]


def _scaled_water_flux(self, T, C, D):
    """Scale the internal water flux, which is the only place D enters the model.

    IMPORTANT: under face_scheme='kirchhoff' the solver does not use the D array
    returned by properties(); it evaluates the Kirchhoff primitive with a
    hard-coded per-question D0 (see drying_core.water_internal_flux, the line
    `return self.internal_faces * D0 * thermal_factor * difference / self.dx`).
    Scaling properties() alone therefore has NO effect on dScale, which is why an
    earlier Morris run reported mu* = 0 for dScale. The Kirchhoff flux is exactly
    linear in D0, so multiplying the returned flux by the scale factor is the exact
    realisation of a D pre-factor uncertainty. The surface Robin flux uses beta and
    is deliberately NOT scaled.
    """
    return _ORIGINAL_WATER_FLUX(self, T, C, D) * SCALES["d"]


RadialModel.properties = _scaled_properties
RadialModel.water_internal_flux = _scaled_water_flux

# name, unit, baseline, low, high
PARAMETERS = [
    ("tailTemperatureC", "degC", 50.0, 48.0, 52.0),
    ("tailEquilibrium", "kg/kg", 0.05, 0.04, 0.06),
    ("h", "W/(m2 K)", 25.0, 20.0, 30.0),
    ("beta", "m/s", 8e-7, 6.4e-7, 9.6e-7),
    ("surfaceLatentFraction", "-", 0.0, 0.0, 1.0),
    ("equilibriumScale", "-", 1.0, 0.8, 1.2),
    ("dScale", "-", 1.0, 0.7, 1.4),
    ("kScale", "-", 1.0, 0.85, 1.15),
]
NAMES = [p[0] for p in PARAMETERS]


def settings_for(question, values):
    shrink = question == "Q4"
    kwargs = {"tail_temperature_C": values["tailTemperatureC"],
              "tail_equilibrium": values["tailEquilibrium"],
              "h": values["h"], "beta": values["beta"],
              "surface_latent_fraction": values["surfaceLatentFraction"],
              "equilibrium_scale": values["equilibriumScale"]}
    return Settings(question=question, intervals=INTERVALS, shrink=shrink,
                    rtol=1e-10, atol_temperature=1e-10, atol_moisture=1e-12,
                    early_max_step_s=2.0, max_step_s=120.0,
                    face_scheme="kirchhoff", jacobian_mode="finite_difference",
                    **kwargs)


FAILURES = []


def evaluate(question, unitPoint):
    """unitPoint: dict name -> value in [0, 1]; returns drying time in hours (or nan)."""
    values = {}
    for name, _unit, low, high in ((p[0], p[1], p[3], p[4]) for p in PARAMETERS):
        values[name] = low + unitPoint[name] * (high - low)
    SCALES["d"] = values["dScale"]
    SCALES["k"] = values["kScale"]
    try:
        run = solve_case(settings_for(question, values))
    except Exception as error:  # a failed evaluation is recorded, never silently dropped
        FAILURES.append({"question": question, "values": values,
                         "error": f"{type(error).__name__}: {error}"})
        return float("nan")
    try:
        return run.event_s / 3600.0
    finally:
        run.close()


def baseline_point():
    return {name: (base - low) / (high - low)
            for name, _unit, base, low, high in PARAMETERS}


def full_point(subset, row):
    """Expand a subset sample to a full unit point using baseline values elsewhere."""
    point = baseline_point()
    for name, value in zip(subset, row):
        point[name] = float(value)
    return point


def control_check():
    """All scales at baseline must reproduce the unpatched surrogate exactly."""
    SCALES["d"] = SCALES["k"] = 1.0
    base = Settings(question="Q23", intervals=INTERVALS, rtol=1e-10,
                    atol_temperature=1e-10, atol_moisture=1e-12,
                    early_max_step_s=2.0, max_step_s=120.0,
                    face_scheme="kirchhoff", jacobian_mode="analytic")
    run = solve_case(base)
    reference = run.event_s / 3600.0
    run.close()
    patched = evaluate("Q23", baseline_point())
    return {"unpatchedAnalyticJacobianH": reference,
            "patchedFiniteDifferenceH": patched,
            "differenceSeconds": abs(reference - patched) * 3600.0,
            "referenceProductionN3200H": PRODUCTION_EVENT_H["Q23"],
            "surrogateOffsetVsProductionSeconds":
                abs(reference - PRODUCTION_EVENT_H["Q23"]) * 3600.0}


def morris(question, trajectories, levels=4):
    delta = levels / (2.0 * (levels - 1))
    grid = np.linspace(0.0, 1.0 - delta, levels)
    d = len(PARAMETERS)
    effects = {name: [] for name in NAMES}
    rng = np.random.default_rng(20260911)
    started = time.perf_counter()
    for t in range(trajectories):
        base = rng.choice(grid, size=d)
        point = {name: float(base[i]) for i, name in enumerate(NAMES)}
        y0 = evaluate(question, point)
        order = rng.permutation(d)
        for index in order:
            name = NAMES[index]
            nxt = dict(point)
            nxt[name] = min(1.0, point[name] + delta)
            y1 = evaluate(question, nxt)
            effects[name].append((y1 - y0) / delta)
            point, y0 = nxt, y1
        if (t + 1) % 5 == 0:
            print(f"  morris {question} trajectory {t+1}/{trajectories} "
                  f"({time.perf_counter()-started:.0f}s)", flush=True)
    summary = []
    for name in NAMES:
        arr = np.asarray(effects[name], dtype=float)
        summary.append({"parameter": name,
                        "muStar": float(np.mean(np.abs(arr))),
                        "mu": float(np.mean(arr)),
                        "sigma": float(np.std(arr, ddof=1)),
                        "min": float(arr.min()), "max": float(arr.max()),
                        "elementaryEffects": arr.tolist()})
    summary.sort(key=lambda row: row["muStar"], reverse=True)
    return {"question": question, "trajectories": trajectories, "levels": levels,
            "delta": delta, "runs": trajectories * (d + 1),
            "elapsedSeconds": time.perf_counter() - started, "ranking": summary}


def sobol(question, subset, baseSamples, seed=7):
    """Saltelli/Jansen first-order and total-order indices on a parameter subset."""
    d = len(subset)
    rng = np.random.default_rng(seed)
    A = rng.random((baseSamples, d))
    B = rng.random((baseSamples, d))
    fA = np.array([evaluate(question, full_point(subset, row)) for row in A])
    fB = np.array([evaluate(question, full_point(subset, row)) for row in B])
    var_y = float(np.var(np.concatenate([fA, fB]), ddof=1))
    rows = []
    started = time.perf_counter()
    for j, name in enumerate(subset):
        AB = A.copy()
        AB[:, j] = B[:, j]
        fAB = np.array([evaluate(question, full_point(subset, row)) for row in AB])
        # Jansen estimators
        s1 = float(np.mean(fB * (fAB - fA)) / var_y) if var_y > 0 else float("nan")
        st = float(np.mean((fA - fAB) ** 2) / (2.0 * var_y)) if var_y > 0 else float("nan")
        rows.append({"parameter": name, "firstOrder": s1, "totalOrder": st,
                     "interaction": st - s1})
        print(f"  sobol {question} {name}: S1={s1:.4f} ST={st:.4f} "
              f"({time.perf_counter()-started:.0f}s)", flush=True)
    return {"question": question, "subset": subset, "baseSamples": baseSamples,
            "runs": baseSamples * (d + 2), "outputVariance": var_y,
            "indices": rows, "elapsedSeconds": time.perf_counter() - started}


def scan(stageName, parameter, values, questions=("Q23", "Q4")):
    """One-parameter scan used to repair the dScale entry and to validate kScale."""
    rows = []
    for question in questions:
        for value in values:
            point = baseline_point()
            low = next(p[3] for p in PARAMETERS if p[0] == parameter)
            high = next(p[4] for p in PARAMETERS if p[0] == parameter)
            point[parameter] = (value - low) / (high - low)
            y = evaluate(question, point)
            rows.append({"question": question, "parameter": parameter,
                         "value": value, "eventH": y})
            print(f"  scan {question} {parameter}={value:g} -> {y:.6f} h", flush=True)
    byQ = {}
    for question in questions:
        ys = [r["eventH"] for r in rows if r["question"] == question]
        lo, hi = min(ys), max(ys)
        base = next((r["eventH"] for r in rows
                     if r["question"] == question and abs(r["value"] - 1.0) < 1e-12), None)
        byQ[question] = {"minH": lo, "maxH": hi, "spanH": hi - lo,
                         "baselineH": base,
                         "relativeSpanPercent": None if not base else 100.0 * (hi - lo) / base}
    return {"stage": stageName, "parameter": parameter, "rows": rows, "summary": byQ}


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else "morris"
    OUT.mkdir(parents=True, exist_ok=True)
    if stage == "control":
        result = {"control": control_check(),
                  "surrogateEventH": SURROGATE_EVENT_H,
                  "productionEventH": PRODUCTION_EVENT_H}
    elif stage == "morris":
        trajectories = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        result = {"control": control_check(),
                  "morris": [morris(q, trajectories) for q in ("Q23", "Q4")]}
    elif stage == "dscale":
        result = {"control": control_check(),
                  "scan": scan("dscale", "dScale", [0.7, 0.875, 1.0, 1.05, 1.225, 1.4])}
    elif stage == "kscale":
        result = {"scan": scan("kscale", "kScale", [0.85, 0.925, 1.0, 1.075, 1.15])}
    elif stage == "sobol":
        subset = sys.argv[2].split(",")
        base = int(sys.argv[3]) if len(sys.argv) > 3 else 64
        result = {"sobol": [sobol(q, subset, base) for q in ("Q23", "Q4")]}
    else:
        raise SystemExit(f"unknown stage {stage}")
    path = OUT / f"{stage}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result.get("scan", {}).get("summary", {}), ensure_ascii=False),
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**B.8　MATLAB 独立实现**

`review_delivery/matlab/runCrossCheck.m`（独立有限体积 + ode15s 跨实现交叉核验（检验五））

```matlab
function runSummary = runCrossCheck(outputDirectory)
%RUNCROSSCHECK 用独立 MATLAB 实现核验 A 题 Q1--Q4 的离散模型。
% 在 MATLAB GUI 中调用本函数；函数自身不能证明 GUI 操作或人工审查。
% 单位：秒、米、开尔文、kg 水/kg 干物质；默认 N=40 是跨语言核验网格，
% 不能代替正式 N3200/N6400 生产结果或空间收敛验证。
% 示例：runCrossCheck('D:/Document/数学建模/2026CUMCM/paper_output/qa/matlab_crosscheck_20260911')

    sourcePath = [mfilename('fullpath'), '.m'];
    projectRoot = fileparts(sourcePath);
    for parentIndex = 1:4
        projectRoot = fileparts(projectRoot);
    end
    if nargin < 1 || strlength(string(outputDirectory)) == 0
        runStamp = char(datetime('now', 'Format', 'yyyyMMdd_HHmmss_SSS'));
        outputDirectory = fullfile(projectRoot, 'paper_output', 'qa', ...
            ['matlab_crosscheck_', runStamp]);
    end
    outputDirectory = char(outputDirectory);
    % Java 仅用于路径规范化和 SHA256，不参与模型计算。
    outputFile = java.io.File(outputDirectory);
    projectRootFile = java.io.File(projectRoot);
    outputDirectory = char(outputFile.getCanonicalPath());
    canonicalRoot = char(projectRootFile.getCanonicalPath());
    if ~startsWith(lower(outputDirectory), [lower(canonicalRoot), filesep])
        error('CrossCheck:WorkspaceBoundary', '输出必须位于本次 2026CUMCM 子工作区。');
    end
    summaryPath = fullfile(outputDirectory, 'runSummary.json');
    if isfile(summaryPath)
        error('CrossCheck:ExistingRun', '该目录已有运行记录，请使用新的输出目录以保留证据。');
    end
    if ~isfolder(outputDirectory)
        mkdir(outputDirectory);
    end
    logPath = fullfile(outputDirectory, 'runLog.txt');
    logFileId = fopen(logPath, 'w', 'n', 'UTF-8');
    if logFileId < 0
        error('CrossCheck:LogOpen', '无法创建运行日志。');
    end
    logCleanup = onCleanup(@() fclose(logFileId)); %#ok<NASGU>
    runTimer = tic;
    runSummary = struct('schemaVersion', 1, 'status', 'RUNNING', ...
        'startedAtUtc', utcStamp(), 'finishedAtUtc', '', 'elapsedSec', [], ...
        'matlabVersion', version, 'matlabRelease', version('-release'), ...
        'computer', computer, 'sourcePath', sourcePath, ...
        'sourceSha256', sha256File(sourcePath), 'outputDirectory', outputDirectory, ...
        'guiReproduced', [], 'guiEvidenceStatus', 'external_observation_required', ...
        'humanReviewStatus', 'pending', 'caseResults', {{}}, 'exception', []);
    settings = struct('intervalCount', 40, 'nodeCount', 41, 'relativeTolerance', 1e-10, ...
        'temperatureAbsoluteTolerance', 1e-10, 'moistureAbsoluteTolerance', 1e-12, ...
        'earlyMaxStepSec', 2, 'lateMaxStepSec', 120, 'horizonSec', 240*3600, ...
        'initialTemperatureK', 301.15, 'initialMoisture', 2.55, ...
        'initialRadiusM', 0.02, 'fixedLengthM', 0.25, ...
        'heatTransferCoefficient', 25, 'massTransferCoefficient', 8e-7, ...
        'dryThreshold', 0.15, 'environmentSwitchSec', 14400, ...
        'tailTemperatureK', 323.15, 'tailEquilibriumMoisture', 0.05, ...
        'solver', 'ode15s_default_NDF', 'jacobianMode', 'JPattern_finite_difference', ...
        'waterFaceScheme', 'Kirchhoff', 'heatFaceScheme', 'harmonic', ...
        'coefficientFloor', 1e-12, 'latentHeatIncluded', false);
    runSummary.settings = settings;
    writeJson(summaryPath, runSummary);
    logLine(logFileId, 'START %s | MATLAB %s | output=%s', ...
        runSummary.startedAtUtc, version, outputDirectory);
    try
        environmentPath = fullfile(projectRoot, 'paper_output', 'data_cleaned', 'A_environment_observed.csv');
        radiusPath = fullfile(projectRoot, 'paper_output', 'data_cleaned', 'A_radius_observed.csv');
        inputData.environment = readtable(environmentPath, 'VariableNamingRule', 'preserve');
        inputData.radius = readtable(radiusPath, 'VariableNamingRule', 'preserve');
        validateInputs(inputData);
        runSummary.inputs = {fileRecord(environmentPath), fileRecord(radiusPath)};
        caseNames = {'Q1', 'Q23', 'Q4'};
        for caseIndex = 1:numel(caseNames)
            caseName = caseNames{caseIndex};
            logLine(logFileId, 'CASE_START %s at %s', caseName, utcStamp());
            caseTimer = tic;
            caseResult = solveSingleCase(caseName, inputData, settings, logFileId);
            caseResult.elapsedSec = toc(caseTimer);
            caseResult.finishedAtUtc = utcStamp();
            casePath = fullfile(outputDirectory, [caseName, '_crossCheck.json']);
            writeJson(casePath, caseResult);
            sampleTable = makeSampleTable(caseResult);
            writetable(sampleTable, fullfile(outputDirectory, [caseName, '_samples.csv']));
            if strcmp(caseName, 'Q23')
                % Q2 与 Q3 共用从 t=0 的附录3轨迹，导出同源但分问的查阅入口。
                sampleTable.question(:) = "Q2";
                writetable(sampleTable, fullfile(outputDirectory, 'Q2_samples.csv'));
                sampleTable.question(:) = "Q3";
                writetable(sampleTable, fullfile(outputDirectory, 'Q3_samples.csv'));
            end
            runSummary.caseResults{end+1} = caseResult;
            writeJson(summaryPath, runSummary);
            logLine(logFileId, 'CASE_END %s | elapsed=%.6f s | event=%.12g s | massResidual=%.3g', ...
                caseName, caseResult.elapsedSec, scalarOrNaN(caseResult.eventSec), ...
                caseResult.diagnostics.maxMassBalanceAbs);
        end
        if ~strcmp(runSummary.sourceSha256, sha256File(sourcePath))
            error('CrossCheck:SourceChanged', '源码在运行中改变，本轮不能作为固定版本证据。');
        end
        for inputIndex = 1:numel(runSummary.inputs)
            record = runSummary.inputs{inputIndex};
            if ~strcmp(record.sha256, sha256File(record.path))
                error('CrossCheck:InputChanged', '输入在运行中改变：%s', record.path);
            end
        end
        runSummary.status = 'COMPLETED_NUMERICAL_CHECKS';
        runSummary.finishedAtUtc = utcStamp();
        runSummary.elapsedSec = toc(runTimer);
        writeJson(summaryPath, runSummary);
        logLine(logFileId, 'FINISH %s | elapsed=%.6f s | humanReview=pending', ...
            runSummary.finishedAtUtc, runSummary.elapsedSec);
    catch runError
        runSummary.status = 'FAILED';
        runSummary.finishedAtUtc = utcStamp();
        runSummary.elapsedSec = toc(runTimer);
        runSummary.exception = struct('identifier', runError.identifier, ...
            'message', runError.message, 'report', getReport(runError, 'extended', 'hyperlinks', 'off'));
        writeJson(summaryPath, runSummary);
        logLine(logFileId, 'FAILED %s\n%s', runSummary.finishedAtUtc, runSummary.exception.report);
        rethrow(runError);
    end
end

function caseResult = solveSingleCase(caseName, inputData, settings, logFileId)
    caseStartedAtUtc = utcStamp();
    nodeCount = settings.nodeCount;
    materialX = linspace(0, 1, nodeCount)';
    deltaX = 1/settings.intervalCount;
    faceX = [0; (materialX(1:end-1)+materialX(2:end))/2; 1];
    cellWeights = diff(faceX.^2)/2;
    internalFaceX = faceX(2:end-1);
    stateCount = 2*nodeCount+1;
    initialState = zeros(stateCount, 1);
    initialState(1:2:end-1) = settings.initialTemperatureK;
    initialState(2:2:end-1) = settings.initialMoisture;
    absoluteTolerance = repmat(settings.moistureAbsoluteTolerance, stateCount, 1);
    absoluteTolerance(1:2:end-1) = settings.temperatureAbsoluteTolerance;
    jacobianPattern = makeJacobianPattern(nodeCount);
    baseOptions = odeset('RelTol', settings.relativeTolerance, 'AbsTol', absoluteTolerance, ...
        'JPattern', jacobianPattern, 'Vectorized', 'off', 'Stats', 'off');
    if strcmp(caseName, 'Q1')
        horizonSec = 1800;
        dryDensityInitial = 820/(1+settings.initialMoisture);
    elseif strcmp(caseName, 'Q4')
        horizonSec = settings.horizonSec;
        dryDensityInitial = (760+90*settings.initialMoisture)/(1+settings.initialMoisture);
    else
        horizonSec = settings.horizonSec;
        dryDensityInitial = (650+128*settings.initialMoisture)/(1+settings.initialMoisture);
    end
    dryMassKg = dryDensityInitial*pi*settings.initialRadiusM^2*settings.fixedLengthM;
    endPoints = unique([0, min(settings.environmentSwitchSec, horizonSec), horizonSec]);
    solutions = {};
    warningRecords = {};
    eventSec = [];
    rhsEvaluations = 0;
    for segmentIndex = 1:numel(endPoints)-1
        leftSec = endPoints(segmentIndex);
        rightSec = endPoints(segmentIndex+1);
        if leftSec < settings.environmentSwitchSec
            maxStepSec = settings.earlyMaxStepSec;
        else
            maxStepSec = settings.lateMaxStepSec;
        end
        segmentOptions = odeset(baseOptions, 'MaxStep', maxStepSec);
        if ~strcmp(caseName, 'Q1')
            segmentOptions = odeset(segmentOptions, 'Events', @dryEvent);
        end
        lastwarn('');
        segment = ode15s(@balanceRhs, [leftSec, rightSec], initialState, segmentOptions);
        [warningText, warningId] = lastwarn;
        recordWarning(warningText, warningId, leftSec, rightSec);
        solutions{end+1} = segment;
        hasEvent = isfield(segment, 'xe') && ~isempty(segment.xe);
        if hasEvent
            eventSec = segment.xe(end);
            initialState = segment.ye(:, end);
            tailEndSec = ceil(eventSec)+1;
            % 真正续算到事件后的整数秒；禁止靠插值外推声称严格达标。
            tailOptions = odeset(baseOptions, 'MaxStep', 1, 'Events', []);
            lastwarn('');
            tail = ode15s(@balanceRhs, [eventSec, tailEndSec], initialState, tailOptions);
            [warningText, warningId] = lastwarn;
            recordWarning(warningText, warningId, eventSec, tailEndSec);
            assertReached(tail, tailEndSec);
            solutions{end+1} = tail;
            break;
        end
        assertReached(segment, rightSec);
        initialState = segment.y(:, end);
    end
    if ~strcmp(caseName, 'Q1') && isempty(eventSec)
        error('CrossCheck:NoDryEvent', '%s 在240小时内没有找到干燥事件。', caseName);
    end
    endSec = solutions{end}.x(end);
    rawSampleTimes = [0, 1800, 10800];
    rawSampleTimes = rawSampleTimes(rawSampleTimes <= endSec);
    sampleTimesSec = unique([rawSampleTimes, eventSec, endSec]);
    sampleStates = evaluatePieces(solutions, sampleTimesSec);
    sampleX = [0, 0.25, 0.5, 0.75, 1];
    temperatureK = interp1(materialX, sampleStates(1:2:end-1, :), sampleX, 'linear')';
    moisture = interp1(materialX, sampleStates(2:2:end-1, :), sampleX, 'linear')';
    sampleRadiusM = zeros(size(sampleTimesSec));
    sampleTypes = strings(size(sampleTimesSec));
    for sampleIndex = 1:numel(sampleTimesSec)
        sampleRadiusM(sampleIndex) = radiusAt(sampleTimesSec(sampleIndex));
        if sampleTimesSec(sampleIndex) == 0
            sampleTypes(sampleIndex) = "initial";
        elseif ~isempty(eventSec) && sampleTimesSec(sampleIndex) == eventSec
            sampleTypes(sampleIndex) = "criticalEvent";
        elseif ~isempty(eventSec) && sampleTimesSec(sampleIndex) == endSec
            sampleTypes(sampleIndex) = "postEventIntegerSecond";
        else
            sampleTypes(sampleIndex) = "fixedTime";
        end
    end
    diagnostic = struct('minMoisture', Inf, 'maxMoisture', -Inf, ...
        'minTemperatureK', Inf, 'maxTemperatureK', -Inf, 'minDiffusivity', Inf, ...
        'positiveProperties', true, 'maxMassBalanceAbs', 0, ...
        'maxRadialMoistureIncrease', -Inf, 'acceptedTimePoints', 0);
    for pieceIndex = 1:numel(solutions)
        acceptedStates = solutions{pieceIndex}.y;
        acceptedTemperature = acceptedStates(1:2:end-1, :);
        acceptedMoisture = acceptedStates(2:2:end-1, :);
        [density, heatCapacity, conductivity, diffusivity] = materialProperties(acceptedTemperature, acceptedMoisture, caseName);
        diagnostic.minMoisture = min(diagnostic.minMoisture, min(acceptedMoisture, [], 'all'));
        diagnostic.maxMoisture = max(diagnostic.maxMoisture, max(acceptedMoisture, [], 'all'));
        diagnostic.minTemperatureK = min(diagnostic.minTemperatureK, min(acceptedTemperature, [], 'all'));
        diagnostic.maxTemperatureK = max(diagnostic.maxTemperatureK, max(acceptedTemperature, [], 'all'));
        diagnostic.minDiffusivity = min(diagnostic.minDiffusivity, min(diffusivity, [], 'all'));
        diagnostic.positiveProperties = diagnostic.positiveProperties && ...
            all(density > 0 & heatCapacity > 0 & conductivity > 0 & diffusivity > 0, 'all');
        massResidual = 2*cellWeights'*acceptedMoisture+acceptedStates(end, :)-settings.initialMoisture;
        diagnostic.maxMassBalanceAbs = max(diagnostic.maxMassBalanceAbs, max(abs(massResidual)));
        diagnostic.maxRadialMoistureIncrease = max(diagnostic.maxRadialMoistureIncrease, ...
            max(diff(acceptedMoisture, 1, 1), [], 'all'));
        diagnostic.acceptedTimePoints = diagnostic.acceptedTimePoints+numel(solutions{pieceIndex}.x);
    end
    finalState = evaluatePieces(solutions, endSec);
    diagnostic.finalMaxMoisture = max(finalState(2:2:end-1));
    diagnostic.strictlyDryAtEnd = diagnostic.finalMaxMoisture < settings.dryThreshold;
    diagnostic.rhsEvaluations = rhsEvaluations;
    diagnostic.radiusExtrapolationUsed = strcmp(caseName, 'Q4') && endSec > inputData.radius.time_s(end);
    diagnostic.checkScope = 'accepted ode15s states; not a continuous exact-solution error bound';
    if diagnostic.minMoisture < -1e-8 || ~diagnostic.positiveProperties
        error('CrossCheck:PhysicalRange', '%s 的接受状态违反物性正值或水分范围。', caseName);
    end
    if diagnostic.maxMassBalanceAbs > 1e-6
        error('CrossCheck:MassBalance', '%s 的离散干基质量守恒残差超限。', caseName);
    end
    if ~strcmp(caseName, 'Q1') && ~diagnostic.strictlyDryAtEnd
        error('CrossCheck:StrictDryness', '%s 的事件后原精度maxC没有严格小于0.15。', caseName);
    end
    caseResult = struct('question', caseName, 'startedAtUtc', caseStartedAtUtc, ...
        'intervalCount', settings.intervalCount, 'eventSec', eventSec, ...
        'eventHours', eventSec/3600, 'endSec', endSec, 'dryMassKg', dryMassKg, ...
        'endTimeConvention', 'ceil(eventSec)+1; actual integration, not earliest integer-second claim', ...
        'sampleTimesSec', sampleTimesSec, 'sampleTypes', sampleTypes, 'sampleMaterialX', sampleX, ...
        'sampleRadiusM', sampleRadiusM, 'temperatureK', temperatureK, ...
        'temperatureC', temperatureK-273.15, 'moistureDryBasis', moisture, ...
        'fullMaterialX', materialX', 'fullStateBySample', sampleStates', ...
        'stateOrder', 'T0,C0,T1,C1,...,TN,CN,cumulativeDryBasisLoss', ...
        'meanMoisture', 2*cellWeights'*sampleStates(2:2:end-1, :), ...
        'cumulativeLoss', sampleStates(end, :), 'diagnostics', diagnostic, ...
        'warnings', {warningRecords}, 'warningCapture', 'last warning per segment; not all warning messages', ...
        'humanReviewStatus', 'pending');

    function derivative = balanceRhs(timeSec, state)
        rhsEvaluations = rhsEvaluations+1;
        temperature = state(1:2:end-1);
        waterContent = state(2:2:end-1);
        [density, heatCapacity, conductivity, ~] = materialProperties(temperature, waterContent, caseName);
        radiusM = radiusAt(timeSec);
        [airTemperatureK, equilibriumMoisture] = environmentAt(timeSec);
        heatFlux = zeros(nodeCount+1, 1);
        waterFlux = zeros(nodeCount+1, 1);
        faceConductivity = 2*conductivity(1:end-1).*conductivity(2:end) ./ ...
            max(conductivity(1:end-1)+conductivity(2:end), realmin);
        heatFlux(2:end-1) = internalFaceX.*faceConductivity.*diff(temperature)/deltaX;
        if strcmp(caseName, 'Q1')
            moistureExponent = 0.89;
            diffusionPrefactor = 7e-9;
            thermalFactor = ones(nodeCount-1, 1);
        elseif strcmp(caseName, 'Q4')
            moistureExponent = 0.30;
            diffusionPrefactor = 4.2e-4;
            thermalFactor = exp(-3850./((temperature(1:end-1)+temperature(2:end))/2));
        else
            moistureExponent = 0.45;
            diffusionPrefactor = 2.4e-3;
            thermalFactor = exp(-3850./((temperature(1:end-1)+temperature(2:end))/2));
        end
        positiveMoisture = max(waterContent, settings.coefficientFloor);
        % E1(z)=expint(z)=-Ei(-z)，不是 Python scipy.special.expi 的同名替代。
        kirchhoffPotential = positiveMoisture.*exp(-moistureExponent./positiveMoisture) ...
            -moistureExponent*expint(moistureExponent./positiveMoisture);
        potentialDifference = diff(kirchhoffPotential);
        meanFaceMoisture = (positiveMoisture(1:end-1)+positiveMoisture(2:end))/2;
        moistureDifference = diff(positiveMoisture);
        closePair = abs(moistureDifference) < 1e-7*max(meanFaceMoisture, 1e-3);
        potentialDifference(closePair) = exp(-moistureExponent./meanFaceMoisture(closePair)) ...
            .*moistureDifference(closePair);
        % 温度因子在面上求值，不放入势函数再差分，以免引入虚构Soret项。
        waterFlux(2:end-1) = internalFaceX.*diffusionPrefactor.*thermalFactor.*potentialDifference/deltaX;
        waterFlux(end) = -settings.massTransferCoefficient*radiusM*(waterContent(end)-equilibriumMoisture);
        heatFlux(end) = -settings.heatTransferCoefficient*radiusM*(temperature(end)-airTemperatureK);
        derivative = zeros(stateCount, 1);
        derivative(1:2:end-1) = diff(heatFlux)./(radiusM^2*cellWeights.*density.*heatCapacity);
        % Q4网格随材料同比收缩；固定长度并另守恒干物质，故无附加网格平流。
        derivative(2:2:end-1) = diff(waterFlux)./(radiusM^2*cellWeights);
        derivative(end) = 2*settings.massTransferCoefficient/radiusM*(waterContent(end)-equilibriumMoisture);
    end

    function radiusM = radiusAt(timeSec)
        if strcmp(caseName, 'Q4')
            boundedTimeSec = min(max(timeSec, inputData.radius.time_s(1)), inputData.radius.time_s(end));
            radiusM = interp1(inputData.radius.time_s, inputData.radius.radius_m, boundedTimeSec, 'linear');
        else
            radiusM = settings.initialRadiusM;
        end
    end

    function [airTemperatureK, equilibriumMoisture] = environmentAt(timeSec)
        % 4h以后50摄氏度/0.05为闭合假设；不是额外实测数据。
        if timeSec > inputData.environment.time_s(end)
            airTemperatureK = settings.tailTemperatureK;
            equilibriumMoisture = settings.tailEquilibriumMoisture;
        else
            boundedTimeSec = max(timeSec, inputData.environment.time_s(1));
            airTemperatureK = interp1(inputData.environment.time_s, inputData.environment.temperature_K, boundedTimeSec, 'linear');
            equilibriumMoisture = interp1(inputData.environment.time_s, inputData.environment.air_moisture_kg_per_kg, boundedTimeSec, 'linear');
        end
    end

    function [eventValue, isTerminal, direction] = dryEvent(~, state)
        eventValue = max(state(2:2:end-1))-settings.dryThreshold;
        isTerminal = 1;
        direction = -1;
    end

    function recordWarning(warningText, warningId, leftSec, rightSec)
        if ~isempty(warningText)
            warningRecords{end+1} = struct('identifier', warningId, 'message', warningText, ...
                'segmentStartSec', leftSec, 'segmentTargetSec', rightSec);
            logLine(logFileId, 'WARNING %s [%s] %s', caseName, warningId, warningText);
        end
    end
end

function [density, heatCapacity, conductivity, diffusivity] = materialProperties(temperatureK, waterContent, caseName)
    if any(~isfinite(temperatureK) | temperatureK <= 0, 'all') || any(~isfinite(waterContent), 'all')
        error('CrossCheck:InvalidState', '遇到非有限状态或非正绝对温度。');
    end
    % 仅对Newton探测点的系数作正延拓，不截断积分状态。
    positiveMoisture = max(waterContent, 1e-12);
    wetFraction = positiveMoisture./(1+positiveMoisture);
    switch caseName
        case 'Q1'
            density = 820*ones(size(waterContent));
            heatCapacity = 2600*ones(size(waterContent));
            conductivity = 0.36*ones(size(waterContent));
            diffusivity = 7e-9*exp(-0.89./positiveMoisture);
        case 'Q23'
            density = 650+128*positiveMoisture;
            heatCapacity = 1450+2736*wetFraction;
            conductivity = 0.21+0.38*wetFraction;
            diffusivity = 2.4e-3*exp(-0.45./positiveMoisture-3850./temperatureK);
        case 'Q4'
            density = 760+90*positiveMoisture;
            heatCapacity = 1850+2150*wetFraction;
            conductivity = 0.12+0.20*wetFraction;
            diffusivity = 4.2e-4*exp(-0.30./positiveMoisture-3850./temperatureK);
        otherwise
            error('CrossCheck:Question', '不支持的问题名：%s', caseName);
    end
end

function jacobianPattern = makeJacobianPattern(nodeCount)
    stateCount = 2*nodeCount+1;
    jacobianPattern = sparse(stateCount, stateCount);
    for nodeIndex = 1:nodeCount
        rowIndices = 2*nodeIndex-1:2*nodeIndex;
        for neighborIndex = max(1, nodeIndex-1):min(nodeCount, nodeIndex+1)
            columnIndices = 2*neighborIndex-1:2*neighborIndex;
            jacobianPattern(rowIndices, columnIndices) = 1;
        end
    end
    jacobianPattern(end, 2*nodeCount) = 1;
end

function sampleStates = evaluatePieces(solutions, queryTimesSec)
    sampleStates = zeros(size(solutions{1}.y, 1), numel(queryTimesSec));
    for queryIndex = 1:numel(queryTimesSec)
        queryTimeSec = queryTimesSec(queryIndex);
        foundPiece = false;
        for pieceIndex = 1:numel(solutions)
            piece = solutions{pieceIndex};
            if queryTimeSec >= piece.x(1) && queryTimeSec <= piece.x(end)
                sampleStates(:, queryIndex) = deval(piece, queryTimeSec);
                foundPiece = true;
                break;
            end
        end
        if ~foundPiece
            error('CrossCheck:DenseDomain', '请求的时刻 %.17g 不在已积分分段内。', queryTimeSec);
        end
    end
end

function sampleTable = makeSampleTable(caseResult)
    sampleCount = numel(caseResult.sampleTimesSec);
    radialCount = numel(caseResult.sampleMaterialX);
    question = repmat(string(caseResult.question), sampleCount*radialCount, 1);
    sampleType = repelem(caseResult.sampleTypes(:), radialCount);
    timeSec = repelem(caseResult.sampleTimesSec(:), radialCount);
    materialX = repmat(caseResult.sampleMaterialX(:), sampleCount, 1);
    currentRadiusM = repelem(caseResult.sampleRadiusM(:), radialCount);
    radiusM = currentRadiusM.*materialX;
    temperatureK = reshape(caseResult.temperatureK', [], 1);
    temperatureC = temperatureK-273.15;
    moistureDryBasis = reshape(caseResult.moistureDryBasis', [], 1);
    sampleTable = table(question, sampleType, timeSec, materialX, radiusM, currentRadiusM, ...
        temperatureK, temperatureC, moistureDryBasis);
end

function validateInputs(inputData)
    environmentColumns = {'time_s', 'temperature_K', 'air_moisture_kg_per_kg'};
    radiusColumns = {'time_s', 'radius_m'};
    if ~all(ismember(environmentColumns, inputData.environment.Properties.VariableNames)) || ...
            ~all(ismember(radiusColumns, inputData.radius.Properties.VariableNames))
        error('CrossCheck:InputColumns', '清洗CSV字段不符合正式输入接口。');
    end
    environmentValues = inputData.environment{:, environmentColumns};
    radiusValues = inputData.radius{:, radiusColumns};
    if any(~isfinite(environmentValues), 'all') || any(~isfinite(radiusValues), 'all') || ...
            any(diff(environmentValues(:, 1)) <= 0) || any(diff(radiusValues(:, 1)) <= 0) || ...
            environmentValues(1, 1) ~= 0 || radiusValues(1, 1) ~= 0 || ...
            environmentValues(end, 1) ~= 14400 || radiusValues(end, 1) ~= 259200 || ...
            any(environmentValues(:, 2) <= 0) || any(environmentValues(:, 3) < 0) || ...
            any(radiusValues(:, 2) <= 0) || abs(radiusValues(1, 2)-0.02) > 1e-14
        error('CrossCheck:InputAudit', '时间、数值范围或初始半径审计未通过。');
    end
end

function assertReached(solution, requestedEndSec)
    if abs(solution.x(end)-requestedEndSec) > 1e-7
        error('CrossCheck:SolverStopped', 'ode15s 实际终点 %.17g 未到请求终点 %.17g。', solution.x(end), requestedEndSec);
    end
    if any(~isfinite(solution.y), 'all')
        error('CrossCheck:NonfiniteSolution', 'ode15s 返回非有限接受状态。');
    end
end

function record = fileRecord(filePath)
    fileInfo = dir(filePath);
    record = struct('path', filePath, 'bytes', fileInfo.bytes, 'sha256', sha256File(filePath));
end

function hashText = sha256File(filePath)
    fileId = fopen(filePath, 'r');
    if fileId < 0
        error('CrossCheck:HashRead', '无法读取待哈希文件：%s', filePath);
    end
    fileCleanup = onCleanup(@() fclose(fileId)); %#ok<NASGU>
    fileBytes = fread(fileId, Inf, '*uint8');
    digest = java.security.MessageDigest.getInstance('SHA-256');
    digest.update(typecast(fileBytes, 'int8'));
    digestBytes = typecast(digest.digest(), 'uint8');
    hashText = lower(reshape(dec2hex(digestBytes, 2)', 1, []));
end

function writeJson(filePath, value)
    fileId = fopen(filePath, 'w', 'n', 'UTF-8');
    if fileId < 0
        error('CrossCheck:JsonWrite', '无法写入JSON：%s', filePath);
    end
    fileCleanup = onCleanup(@() fclose(fileId)); %#ok<NASGU>
    fprintf(fileId, '%s\n', jsonencode(value, 'PrettyPrint', true));
end

function logLine(fileId, messageFormat, varargin)
    logText = sprintf(messageFormat, varargin{:});
    fprintf('%s\n', logText);
    fprintf(fileId, '%s\n', logText);
end

function timeText = utcStamp()
    timeText = char(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ss.SSS''Z'''));
end

function value = scalarOrNaN(optionalValue)
    if isempty(optionalValue)
        value = NaN;
    else
        value = optionalValue;
    end
end
```

@@CODE_BLOCK_END@@

## 附录 C　补充表格

下列表格因版面原因编入附录，正文相应小节以编号引用；编号与正文一致，内容未作任何删改。

**表 12　无量纲数与时间尺度（$C_0=2.55$、$T_0=301.15$ K）**
| 量 | 问题一 | 问题二、三 | 问题四 |
|---|---:|---:|---:|
| 热扩散率 $\alpha$ /(m²/s) | $1.6886\times10^{-7}$ | $1.4483\times10^{-7}$ | $7.8501\times10^{-8}$ |
| 水分扩散率 $D$ /(m²/s) | $4.9377\times10^{-9}$ | $5.6417\times10^{-9}$ | $1.0471\times10^{-9}$ |
| 传热 Biot 数 $Bi_h$ | 1.3889 | 1.0353 | 1.8964 |
| 传质 Biot 数 $Bi_m$ | 3.2404 | 2.8360 | 15.2801 |
| $\alpha/D$ | 34.20 | 25.67 | 74.97 |
| 热扩散时间 $R_0^{2}/\alpha$ /h | 0.6580 | 0.7672 | 1.4154 |
| 水分扩散时间 $R_0^{2}/D$ /h | 22.5028 | 19.6947 | 106.1119 |
| 1800 s 时的 $Fo_T$ | 0.75985 | — | — |
| 1800 s 时的 $Fo_C$ | 0.022219 | — | — |

**表 24　模型检验汇总**
| 检验 | 做法 | 关键结果 | 能证明 | 不能证明 |
|---|---|---|---|---|
| 一　解析基准 | 常系数圆柱 Robin–Bessel 级数（独立重写） | 节点口径最大偏差 $1.80\times10^{-6}$ K；控制体平均口径表面 $2.1\times10^{-3}$ K 且一阶收敛 | 常物性子问题上离散求解器正确 | 非线性 $D(C)$ 与问题二至四的解 |
| 二　离散质量恒等式 | 干物质加权均值 + 累计失水 | 残差 $5.8\times10^{-15}$—$1.2\times10^{-14}$ kg/kg | 共享通量格式守恒、实现自洽 | 物理预测误差；完整能量守恒 |
| 三　空间网格收敛 | 相邻网格在 21 个固定半径 × 整数秒上比较 | $\Delta C\le4.7\times10^{-5}$ kg/kg；经验阶约 1.82—2.02 | 所列范围内空间误差已小 | 连续时空严格误差界 |
| 四　时间设置敏感性 | 基准容差/步长 vs 更紧容差/更小步长 | $\Delta C\le9.9\times10^{-9}$ kg/kg；事件差 $\le4.0\times10^{-6}$ s | 时间推进误差远小于物理变化 | 纯步长或纯容差的截断误差 |
| 五　跨实现对照 | Python（生产）vs MATLAB `ode15s`（$N$40） | $\Delta T\le2.38\times10^{-7}$ K；事件差 $2.30\times10^{-4}$ s | 两个独立实现无低级错误 | 连续全域误差界（同离散公式） |
| 一附　口径判别（节点） | 解析节点值 vs 有限体积节点值 | 内部最大差 $1.8\times10^{-6}$ K | 内部节点精度 | 表面控制体 |
| 一附　口径判别（控制体平均） | 解析精确环形平均 vs 有限体积控制体平均 | 表面最大差 $2.1\times10^{-3}$ K，一阶收敛 | 表面为单侧控制体导致的一阶几何效应 | 与节点口径互换使用 |

**表 27　表面潜热情景包络（$N=800$）**
| 潜热比例 $L$ | 问题二三达标时间 /h | 相对基线 | 问题二三最低表面温度 /°C | 问题四达标时间 /h | 相对基线 | 问题四最低表面温度 /°C |
|---:|---:|---:|---:|---:|---:|---:|
| 0（本文基线） | 57.4723 | — | 28.00 | 51.0906 | — | 28.00 |
| 0.25 | 58.1857 | +1.24% | 24.89 | 52.4165 | +2.60% | 25.70 |
| 0.50 | 58.9341 | +2.54% | 20.25 | 53.7620 | +5.23% | 21.69 |
| 1.00 | 60.4972 | +5.26% | 10.90 | 56.4845 | +10.56% | 14.55 |

**表 31　多方法交叉验证架构与结果**
| 层 | 待验证结论 | 相互独立的方法 | 实测一致性 | 证据位置 |
|---|---|---|---|---|
| L1 | 问题三、四的达标时间 | 变阶 BDF/NDF（生产）· 三阶 Radau IIA | 三档网格事件差 $1.1\times10^{-6}$—$5.6\times10^{-8}$ s | `cv_solver_v1/` |
| L2 | 湿分面离散格式 | Kirchhoff 势 · 调和平均 + 网格加密 | 见 12.3 节表 31 | `cv_solver_v1/` |
| L3 | 全模型实现 | Python（生产）· MATLAB `ode15s`（$N$40） | $\Delta T\le2.375\times10^{-7}$ K；事件差 $2.297\times10^{-4}$ s | `qa/matlab_crosscheck_20260911/` |
| L4 | 问题一热场 | 常系数圆柱 Robin–Bessel 级数 | 节点口径 $1.80\times10^{-6}$ K；口径判别见 10.4 节 | `results/bessel_validation/` |
| L5 | 收缩的缩短效应 | 直接数值模拟 · $(R_0/R)^{2}$ 尺度折算 | 131.6198 h vs 129.8452 h，偏 **1.37%** | `threshold_scaling_v1/` |
| L6 | 三阶段分界 | 两段折线回归 · M–K 突变 · Fisher 最优分割 · 相对阈值 | 四判据落在同一区间，见 12.5 节 | `series_v1/` |
| L7 | 阈值定义与最慢位置 | ODE 事件 · 独立二分求根 · 全节点最大值位置证书 | 根差 **$5.82\times10^{-11}$ s** | `threshold_scaling_v1/` |
| L8 | 空间离散本身 | Kirchhoff 势 · 二阶守恒中点差分 | 常 $D$ 逐位 0；变 $D$ 观测阶 **1.99907** | `method_v1/` |
| L9 | 表面水分边界闭合 | 冻结 1:1 映射 · 数据锚定的吸附族 | 锚点差 0.0；$p=1$ 右端函数逐位相同 | `isotherm_closure_v1/` |
| L10 | 参数不确定性 | Morris 筛选 · 单参数扫描（带注入自检） | 见 13.3 节 | `sensitivity_v1/` |

**表 32　两种湿面离散格式随网格加密的达标时间（同一模型、同一积分器）**
| 问题 | 网格 $N$ | Kirchhoff /h | 调和平均 /h | 差 /h | 比值 |
|---|---:|---:|---:|---:|---:|
| 问题二三 | 400 | 57.4724174 | 57.6868014 | 0.2144 | 1.0037 |
| 问题二三 | 800 | 57.4723298 | 57.5122517 | 0.03992 | 1.0007 |
| 问题二三 | 1600 | 57.4723076 | 57.4810663 | 0.008759 | 1.0002 |
| 问题四 | 400 | 51.0906733 | 51.1105476 | 0.01987 | 1.0004 |
| 问题四 | 800 | 51.0905992 | 51.0954705 | 0.004871 | 1.0001 |
| 问题四 | 1600 | 51.0905806 | 51.0917915 | 0.001211 | 1.0000 |

**表 33　两个积分族的事件时间（同一网格、同一容差）**
| 问题 | 网格 $N$ | BDF/NDF /h | Radau IIA /h | 差 /s |
|---|---:|---:|---:|---:|
| 问题二三 | 800 | 57.4723297616 | 57.4723297620 | $1.12\times10^{-6}$ |
| 问题二三 | 1600 | 57.4723075468 | 57.4723075464 | $1.49\times10^{-6}$ |
| 问题四 | 800 | 51.0905991564 | 51.0905991555 | $3.17\times10^{-6}$ |
| 问题四 | 1600 | 51.0905805903 | 51.0905805903 | $5.58\times10^{-8}$ |

**表 34　四类序列的阶段分界识别结果**
| 目标序列 | 数据来源 | 判据区间 /h | 对模型的意义 |
|---|---|---|---|
| 烘房温度 | 附件 1 | **0.6—2.4** | 支持"4 h 后取平台"的延拓 |
| 烘房水分浓度 | 附件 1 | 同区间 | 同上 |
| 预热阶段完成（中心/表面温度） | 计算曲线 | **1.0—2.9** | 问题一的 1800 s 窗口落在预热段内；问题二的 3 h 展示窗恰好跨越预热→恒温干燥的转变 |
| 半径主要收缩完成 | 附件 2 | **4.5—13.5** | 问题四的 51 h 终点远在收缩终止之后，且不需要半径外推 |

**表 29　五处修正与创新的定位与证据**
| 编号 | 修正/创新 | 性质 | 定量证据 | 论文落点 |
|---|---|---|---|---|
| 一 | 题给密度与几何的相容性修正 | 对题设的修正 | 必要性半径界 1.2112 cm；字面模型 72 h 最多容纳 97.83% | 5.7.4(c)、9.1、13.7 |
| 二 | 表面蒸发的能量闭合（潜热包络） | 物理补全 + 情景包络 | 潜热/显热 ≈21.6；$L=1$ 时 +5.3% / +10.6% | 11.2、13.4 |
| 三 | Kirchhoff 浓度势 | 数值方法设计 | 调和平均在 $N$1600 仍偏 $8.8\times10^{-3}$ h；两格式观测阶 1.999 | 10.2.3、11.3 |
| 四 | 材料坐标移动域 + 干骨架守恒 | 建模方法设计 | 收缩使时长缩短 60.65%，独立 $R^{2}$ 折算印证到 1.37% | 5.5、9.5、11.4 |
| 五 | 数据锚定的吸附闭合 | 物理闭合修正 | 烘房 RH = 0.607 强制 $a_w(0.05)=0.607$；族包络 +0—13.9% / +0—8.3% | 11.5、13.4 |

## 附录 D　公式总表（完整性与数量核对用）


**表 37　公式总表（共 76 式，含 5 条补充推导式）**

| 编号 | 名称与用途 | 自变量 | 因变量 | 单位 | 来源 |
|---:|---|---|---|---|---|
| (1) | 四问通用控制方程（材料坐标形式） | $x,t$ | $T,C$ | K/s、1/s | 本文（由 (16) 归纳） |
| (2) | 薄壳几何与控制体 | $r,\mathrm{d}r$ | $\mathrm{d}V,A(r)$ | m³、m² | 本文定义 |
| (3) | 干基与湿基含水率换算 | $m_w,m_d$ | $C,w$ | kg/kg、1 | 本文定义 |
| (4) | 初始干物质密度标定 | $\rho_{\mathrm{eff}}(C_0),C_0$ | $\rho_{d0}$ | kg/m³ | 本文定义 |
| (5) | 干物质质量守恒 | $t,r$ | $\rho_d,u$ | kg/(m³·s) | 本文推导 |
| (6) | 水分总质量守恒 | $t,r$ | $\rho_dC,j_w$ | kg/(m³·s) | 本文推导 |
| (7) | 干基含水率演化方程 | $t,r$ | $C$ | 1/s | 由 (6)−$C$×(5) 推导 |
| (8) | 傅里叶导热定律 | $\partial T/\partial r$ | $q_r$ | W/m² | 本构（题设物理定律） |
| (9) | 有效菲克扩散本构（干基） | $\partial C/\partial r$ | $j_w$ | kg/(m²·s) | 本构（题设物理定律） |
| (10) | 热方程（有效显热闭合，固定半径） | $t,r$ | $T$ | K/s | 本文主控方程 |
| (11) | 水分方程（固定半径） | $t,r$ | $C$ | 1/s | 本文主控方程 |
| (12) | 变系数散度展开式 | $t,r$ | $T$ | K/s | 本文推导 |
| (13) | 材料坐标变换 | $r,R(t)$ | $x,F$ | 1 | 本文定义 |
| (14) | 坐标变换下的导数关系 | $x,t$ | $\partial_tf,\partial_rf$ | 1/s、1/m | 链式法则推导 |
| (15) | 同比径向收缩与干骨架守恒 | $r,R(t)$ | $u,\rho_d$ | m/s、kg/m³ | 本文推导（含守恒论证） |
| (16) | 变换后的统一方程 | $x,t$ | $T,C$ | K/s、1/s | 由 (14) 代入 (10)(11) |
| (17) | 附录 4 与附录 3 的扩散系数比 | $C$ | $D_4/D_{23}$ | 1 | 由 (31)(35) 相除 |
| (18) | 初始条件 | — | $T_0,C_0$ | K、kg/kg | 题给 |
| (19) | 中心对称条件与算子极限 | $x$ | $\partial_xT,\partial_xC$ | K/m、1/m | 本文推导 |
| (20) | 完整表界面能量收支（含辐射与潜热） | $T_s,T_w,j_n$ | 热流平衡 | W/m² | 本文推导（情景用） |
| (21) | 表面热边界（基线，不含辐射与潜热） | $T_s,T_\infty$ | $\partial_rT$ | W/m² | 题给 $h$ |
| (22) | 表面热边界的材料坐标形式 | $T_s,T_\infty$ | $\partial_xT$ | W/m² | 由 (21) 变换 |
| (23) | 表面水分边界（基线） | $C_s,C_{eq}$ | $\partial_rC$ | kg/(m²·s) | 题给 $\beta$ |
| (24) | 表面水分边界的材料坐标形式 | $C_s,C_{eq}$ | $\partial_xC$ | kg/(m²·s) | 由 (23) 变换 |
| (25) | 真实水质量通量与等效通量换算 | $C_s,C_{eq}$ | $j_w\|_s$ | kg/(m²·s) | 本文推导 |
| (26) | 问题一常热物性 | — | $\rho,c_p,k$ | kg/m³、J/(kg·K)、W/(m·K) | **题给附录 2** |
| (27) | 问题一水分扩散系数 | $C$ | $D_1$ | m²/s | **题给附录 2** |
| (28) | 问题二三密度 | $C$ | $\rho_{23}$ | kg/m³ | **题给附录 3** |
| (29) | 问题二三比热容 | $C$ | $c_{p,23}$ | J/(kg·K) | **题给附录 3** |
| (30) | 问题二三导热系数 | $C$ | $k_{23}$ | W/(m·K) | **题给附录 3** |
| (31) | 问题二三水分扩散系数 | $C,T$ | $D_{23}$ | m²/s | **题给附录 3** |
| (32) | 问题四密度 | $C$ | $\rho_4$ | kg/m³ | **题给附录 4** |
| (33) | 问题四比热容 | $C$ | $c_{p,4}$ | J/(kg·K) | **题给附录 4** |
| (34) | 问题四导热系数 | $C$ | $k_4$ | W/(m·K) | **题给附录 4** |
| (35) | 问题四水分扩散系数 | $C,T$ | $D_4$ | m²/s | **题给附录 4** |
| (36) | 比热容的质量加权混合形式 | $m_d,m_w$ | $c_p$ | J/(kg·K) | 本文推导（解释性） |
| (37) | 扩散系数的对数导数与单调性 | $C,T$ | $\partial\ln D$ | 1/K、kg/kg | 本文推导 |
| (38) | 无量纲数与特征时间 | $h,\beta,k,D,\alpha$ | $Bi_h,Bi_m,Fo_T,Fo_C$ | 1 | 本文定义 |
| (39) | 问题一热方程（常系数） | $t,r$ | $T$ | K/s | 由 (10) 取常数物性 |
| (40) | 问题一水分方程 | $t,r$ | $C$ | 1/s | 由 (11) 代入 (27) |
| (41) | 问题二热方程 | $t,r$ | $T$ | K/s | 由 (10) 代入 (28)(29) |
| (42) | 问题二水分方程 | $t,r$ | $C$ | 1/s | 由 (11) 代入 (31) |
| (43) | 全域达标判据 | $t$ | $M(t),t_*$ | kg/kg、s | 本文定义 |
| (44) | 严格可行报告时刻的取整规则 | $t_*$ | $\hat n,t_{\mathrm{rep}}$ | 1、h | 本文定义 |
| (45) | 问题四热方程与水分方程 | $x,t$ | $T,C$ | K/s、1/s | 由 (16) 代入 (32)—(35) |
| (46) | 问题四有效热容量与干骨架守恒 | $C,R(t)$ | $B_4,\rho_d$ | J/(m³·K)、kg/m³ | 由 (15)(33) 得 |
| (47) | 对偶控制体网格与权重 | $x$ | $x_i,w_i$ | 1 | 本文定义 |
| (48) | 内部面热通量（调和平均） | $T_i,T_{i+1}$ | $G^T_{i+1/2}$ | W/m | 本文离散 |
| (49) | Kirchhoff 浓度势及其导数 | $C$ | $\Phi,\Phi'$ | —、1 | 本文推导 |
| (50) | 内部面湿通量（Kirchhoff 势） | $C_i,C_{i+1},\bar T$ | $G^C_{i+1/2}$ | m²·(kg/kg)/s | 由 (49) 得 |
| (51) | 表面与中心面通量 | $C_N,T_N$ | $G^C_{N+1/2},G^T_{N+1/2}$ | 同 (48)(50) | 由 (22)(24) 得 |
| (52) | 半离散常微分方程组 | $G^T,G^C,w_i,B_i$ | $\dot T_i,\dot C_i$ | K/s、1/s | 由守恒式离散 |
| (53) | 累计失水与加权平均含水率 | $C_i,C_N$ | $\ell,\bar C$ | kg/kg | 本文定义 |
| (54) | 离散质量恒等式 | $\bar C,\ell$ | 残差 | kg/kg | 由 (52)(53) 推出 |
| (55) | 物性对含水率的导数 | $C$ | $\rho_C,c_{p,C},k_C,B_C$ | 各物性单位/C | 由 (28)—(30) 求导 |
| (56) | 扩散系数对状态的导数 | $C,T$ | $D_C,D_T$ | m²/s 每单位 | 由 (31) 求导 |
| (57) | 调和平均面对导热系数的导数 | $k_i,k_{i+1}$ | $\partial k_H$ | 1 | 由 (48) 求导 |
| (58) | 面湿通量对相邻含水率的导数 | $C_i,C_{i+1}$ | $\partial G^C$ | m²/s | 由 (50) 求导 |
| (59) | **容量交叉项**（最易遗漏） | $\dot T_i,B_i,B_{C,i}$ | $\partial\dot T_i/\partial C_i$ | 1/s | 由 (52) 求导 |
| (60) | 圆柱 Robin–Bessel 级数解 | $r,t$ | $T$ | K | 本文独立重写（解析基准） |
| (61) | 级数系数 | $\mu_n,Bi_h$ | $A_n$ | K | 由初值正交展开 |
| (62) | 字面湿密度的干密度上界 | $C$ | $\rho_d$ | kg/m³ | 由 (32) 推导 |
| (63) | 必要性半径界 | $\rho_{d0}$ | $R_{\min}$ | m | 本文推导 |
| (64) | 字面模型可容纳的干质量比例 | $R(72\,\mathrm{h})$ | 比例 | 1 | 本文推导 |
| (65) | 含潜热的表面能量平衡 | $T_s,C_s$ | 热流平衡 | W/m² | 本文推导（式 (20) 的基线扩展） |
| (66) | 常规面通量近似（对照用） | $C_i,C_{i+1}$ | $G^C$ | m²·(kg/kg)/s | 本文列出（对照） |
| (67) | 收缩时间轴的 $R^{2}$ 尺度折算 | $R(t),t_*$ | $\tau_{\mathrm{eq}}$ | h | 本文推导 |
| (68) | 湿空气含湿量与蒸汽分压换算 | $p,Y,T$ | $p_v$ | Pa | 本文推导（依据湿空气热力学） |
| (69) | 被题面数据强制的水活度锚点 | $C_{eq},T_\infty$ | $a_w$ | 1 | 由附件 1 与 $C_{eq}=0.05$ 推出 |
| (70) | 单参数等温线族 | $C,p$ | $a_w(C)$ | 1 | 本文构造 |
| (71) | 吸附闭合的表面驱动缩放 | $C_s,C_{eq},p$ | $g_{\text{表面}},K_{\mathrm{eff}}$ | kg/(m²·s)、1 | 本文构造 |

**数量核对**：题给经验式 **9 条**（式 (26)—(35)，其中 (26) 含三个常数）；守恒与演化 **3 条**（(5)—(7)）；本构 **2 条**（(8)、(9)）；主控方程及其变换 **7 条**（(10)—(16)）；初边值 **8 条**（(18)—(25)）；数值离散 **10 条**（(47)—(54)、(66)）；算法导数 **5 条**（(55)—(59)）；解析基准 **2 条**（(60)、(61)）；判据与取整 **2 条**（(43)、(44)）；修正与创新 **13 条**（(17)、(36)—(38)、(62)—(65)、(67)—(71)）；其余为定义与几何式。合计 **76 式**（71 条主式 + 补充推导式 (47a)(47b)(47c)(48a)(50a)，用于展示守恒性、调和平均导数与 Kirchhoff 势构造的完整推导），与正文编号一一对应，无缺号、无重号。

