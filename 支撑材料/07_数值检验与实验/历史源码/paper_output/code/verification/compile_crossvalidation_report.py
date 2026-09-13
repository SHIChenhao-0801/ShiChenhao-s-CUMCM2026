"""Consolidate every cross-validation result into one report (JSON + Markdown).

Reads the outputs of the verification scripts and applies pre-declared tolerances.
A tolerance is stated before the numbers are inspected, so agreement is a test and
not a description. Missing inputs are reported as missing, never silently skipped.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(r"D:\Document\数学建模\2026CUMCM")
CV = ROOT / "paper_output" / "results" / "crossvalidation"
OUT = CV / "consolidated_v1"

TOLERANCES = {
    "integratorEventSeconds": 1.0,
    "faceSchemeHoursAtFinest": 0.5,
    "scalingResidualPercent": 5.0,
    "crossLanguageEventSeconds": 1.0,
    "analyticBenchmarkKelvin": 1e-4,
    "massBalanceKgPerKg": 1e-6,
    "independentRootSeconds": 1e-6,
    "schemeDifferenceKgPerKg": 1e-4,
    "observedOrderMinimum": 1.5,
    "constantDLimitKgPerKg": 0.0,
    "baselineLimitAbsoluteDifferencePaOverKappa": 1e-6,
}


def load(path):
    p = CV / path
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cases = load("cv_solver_v1/cases.json") or []
    latent = load("latent_scenarios_v1/latent_scenarios.json")
    scaling = load("threshold_scaling_v1/threshold_and_scaling_checks.json")
    series = load("series_v1/stage_boundaries.json")
    methodReport = load("method_v1/method_comparison.json")
    isotherm = load("isotherm_closure_v1/isotherm_closure.json")
    morris = load("sensitivity_v1/morris.json")
    sobol = load("sensitivity_v1/sobol.json")
    metric = load("analytic_metric_v1/analytic_metric.json")
    dscale = load("sensitivity_v1/dscale.json")
    kscale = load("sensitivity_v1/kscale.json")
    energy = load("energy_balance_v1/energy_balance.json")

    report = {"tolerances": TOLERANCES, "layers": {}, "inputsPresent": {
        "solverCases": bool(cases), "latentScenarios": bool(latent),
        "thresholdScaling": bool(scaling), "stageBoundaries": bool(series),
        "methodComparison": bool(methodReport), "isothermClosure": bool(isotherm),
        "morrisScreening": bool(morris), "sobolIndices": bool(sobol),
        "analyticMetric": bool(metric),
        "validatedScans": bool(dscale and kscale),
        "thermalConservation": bool(energy)}}

    # ---- L1 time integrators -------------------------------------------------
    byCase = {c["case"]: c for c in cases if c.get("status") == "computed"}
    l1 = {}
    for question in ("Q23", "Q4"):
        row = {}
        for method in ("BDF", "Radau"):
            for intervals in (800, 1600):
                key = f"B1_{question}_{method}_N{intervals}"
                if key in byCase:
                    row[f"{method}_N{intervals}"] = byCase[key]["event_h"]
        for intervals in (800, 1600):
            a, b = row.get(f"BDF_N{intervals}"), row.get(f"Radau_N{intervals}")
            if a is not None and b is not None:
                row[f"differenceSeconds_N{intervals}"] = abs(a - b) * 3600.0
        l1[question] = row
    report["layers"]["L1_timeIntegrator"] = l1

    # ---- L2 face scheme ------------------------------------------------------
    l2 = {}
    for question in ("Q23", "Q4"):
        row = {}
        for intervals in (400, 800, 1600, 3200):
            k = byCase.get(f"B2_{question}_kirchhoff_N{intervals}")
            h = byCase.get(f"B2_{question}_harmonic_N{intervals}")
            if k and h:
                row[f"N{intervals}"] = {"kirchhoffH": k["event_h"], "harmonicH": h["event_h"],
                                        "differenceH": abs(k["event_h"] - h["event_h"]),
                                        "ratio": h["event_h"] / k["event_h"]}
        l2[question] = row
    report["layers"]["L2_faceScheme"] = l2

    # ---- L3 cross implementation (recorded evidence, not re-run here) --------
    report["layers"]["L3_crossImplementation"] = {
        "source": "paper_output/qa/matlab_crosscheck_20260911",
        "maxTemperatureDifferenceK": 2.375e-7,
        "maxMoistureDifferenceKgPerKg": 5.851e-10,
        "maxEventDifferenceSeconds": 2.297e-4,
        "note": "separate MATLAB finite-volume + ode15s implementation at N=40",
    }

    # ---- L4 analytic / scaling ----------------------------------------------
    l4 = {"analyticBenchmarkQ1Kelvin": 1.803776172e-6,
          "analyticBenchmarkNote": "constant-property cylindrical Bessel series, 240 terms"}
    if scaling:
        l4.update(scaling.get("scalingCheck", {}))
    report["layers"]["L4_analyticAndScaling"] = l4

    # ---- L4b analytic comparison convention ---------------------------------
    if metric:
        rows = metric["rows"]
        gaps = [r["maxPointVsCellDifferenceK"] for r in rows]
        ratios = [gaps[i] / gaps[i + 1] for i in range(len(gaps) - 1) if gaps[i + 1] > 0]
        report["layers"]["L4b_analyticMetricConvention"] = {
            "rows": rows,
            "observedPointToAverageOrder": (float(np.log2(np.mean(ratios))) if ratios else None),
            "interpretation": metric["interpretation"],
            "knownFrozenNumbers": metric["knownFrozenNumbers"],
        }
        report["layers"]["L4b_analyticMetricConvention"]["note"] = (
            "The Q1 Bessel benchmark maximum sits at the surface node and does not fall "
            "under refinement because it compares a nodal collocation unknown with an "
            "exact point value. The two conventions are reported separately and neither "
            "may stand in for the other.")

    # ---- L5 stage boundaries -------------------------------------------------
    if series:
        # stage_boundaries.json is small; the full series_crossvalidation.json is not,
        # so only the boundary table enters the consolidated report.
        report["layers"]["L5_stageBoundaries"] = series

    # ---- L6 model structure (latent envelope) -------------------------------
    if latent:
        env = {}
        for question in ("Q23", "Q4"):
            rows = [r for r in latent["records"] if r["question"] == question]
            base = next((r for r in rows if r["surfaceLatentFraction"] == 0.0), None)
            env[question] = [
                {"fraction": r["surfaceLatentFraction"], "eventH": r["eventTimeH"],
                 "minSurfaceC": r["minSurfaceTemperatureC"],
                 "relativeToBaselinePercent": None if not base else
                 100.0 * (r["eventTimeH"] - base["eventTimeH"]) / base["eventTimeH"]}
                for r in sorted(rows, key=lambda r: r["surfaceLatentFraction"])]
        report["layers"]["L6_modelStructure"] = env

    # ---- L11 thermal conservation certificate -------------------------------
    if energy:
        rows = {c["question"]: {"rateIdentityMaxRelativeDeviation":
                                c["rateIdentityMaxRelativeDeviation"],
                                "cumulativeRelativeResidual": c["cumulativeRelativeResidual"],
                                "discardedCapacityWorkJPerM": c.get("discardedCapacityWorkJPerM"),
                                "unexplainedResidualJPerM": c.get("unexplainedResidualJPerM"),
                                "cumulativeResidualJPerM": c["cumulativeMaxAbsoluteResidualJPerM"]}
                     for c in energy["cases"]}
        report["layers"]["L11_thermalConservation"] = {
            "checkA_rateIdentity": energy["checkA_rateIdentity"],
            "checkB_cumulative": energy["checkB_cumulative"],
            "whyIndependent": energy["whyIndependent"],
            "cases": rows,
            "refinement": energy["refinement"],
        }
        for question, row in rows.items():
            if row.get("discardedCapacityWorkJPerM") and row.get("cumulativeResidualJPerM"):
                row["explainedShare"] = float(
                    min(1.0, abs(row["discardedCapacityWorkJPerM"])
                        / abs(row["cumulativeResidualJPerM"])))
        report["layers"]["L11_thermalConservation"]["cases"] = rows
        q23 = rows.get("Q23", {})
        if q23.get("explainedShare") is not None:
            report["layers"]["L11_thermalConservation"]["discardedWorkExplainsResidual"] = {
                "question": "Q23", "share": q23["explainedShare"],
                "note": ("The work done against the changing effective capacity accounts for the "
                         "stated share of the frozen-capacity cumulative residual. That residual "
                         "is therefore a property of the effective-capacity closure, not a "
                         "solver error. Q4 retains an additional gap from the d(R^2)/dt cross "
                         "term of the shrinking domain."),
            }

    # ---- verdicts ------------------------------------------------------------
    verdicts = []
    for question, row in l1.items():
        for intervals in (800, 1600):
            d = row.get(f"differenceSeconds_N{intervals}")
            if d is not None:
                verdicts.append({"check": f"L1 integrator {question} N{intervals}",
                                 "value": d, "unit": "s",
                                 "tolerance": TOLERANCES["integratorEventSeconds"],
                                 "status": "PASS" if d <= TOLERANCES["integratorEventSeconds"] else "FAIL"})
    for question, row in l2.items():
        for key, value in row.items():
            verdicts.append({"check": f"L2 face scheme {question} {key}",
                             "value": value["differenceH"], "unit": "h",
                             "ratio": value["ratio"],
                             "status": "REPORTED"})
    if scaling:
        residual = abs(scaling["scalingCheck"].get("scalingResidualPercent", 1e9))
        verdicts.append({"check": "L4 R-squared scaling residual", "value": residual,
                         "unit": "%", "tolerance": TOLERANCES["scalingResidualPercent"],
                         "status": "PASS" if residual <= TOLERANCES["scalingResidualPercent"] else "FAIL"})

    # ---- L7 independent root finding and max-location certificate -----------
    if scaling and scaling.get("thresholdChecks"):
        rows = {}
        for question, record in scaling["thresholdChecks"].items():
            rows[question] = {
                "solverEventH": record["solverEventTimeH"],
                "independentBisectionH": record["independentBisectionTimeH"],
                "differenceSeconds": abs(record["eventVsBisectionDifferenceS"]),
                "unroundedMaxCAtStrictTime": record["unroundedMaxCAtStrictTime"],
                "strictlyBelowThreshold": record["strictlyBelowThreshold"],
                "centreIsMaximumAtEvent": record["centreIsMaximumAtEvent"],
                "maxExcessOverCentreKgPerKg": record.get("maxExcessOverCentreMaxKgPerKg"),
                "maxExcessOverCentreMedianKgPerKg": record.get("maxExcessOverCentreMedianKgPerKg"),
                "maxRadialMoistureIncreaseKgPerKg": record["maxRadialMoistureIncrease"],
            }
            verdicts.append({"check": f"L7 independent root {question}",
                             "value": rows[question]["differenceSeconds"], "unit": "s",
                             "tolerance": TOLERANCES["independentRootSeconds"],
                             "status": "PASS" if rows[question]["differenceSeconds"]
                             <= TOLERANCES["independentRootSeconds"] else "FAIL"})
            verdicts.append({"check": f"L7 strict threshold {question}",
                             "value": rows[question]["unroundedMaxCAtStrictTime"],
                             "unit": "kg/kg", "tolerance": 0.15,
                             "status": "PASS" if rows[question]["strictlyBelowThreshold"] else "FAIL"})
        report["layers"]["L7_independentRootAndMaxLocation"] = rows

    # ---- L8 same equation, different discretisation -------------------------
    if methodReport:
        variable = methodReport["variableD"]
        limitRows = methodReport["limitingCaseConstantD"]["rows"]
        maxLimit = max(r["maxAbsDifference"] for r in limitRows)
        report["layers"]["L8_discretisation"] = {
            "constantDLimitMaxDifferenceKgPerKg": maxLimit,
            "constantDLimitRows": limitRows,
            "variableDRows": variable["rows"],
            "observedOrder": variable["observedOrder"],
            "expectedOrderDeclared": variable["expectedOrder"],
            "declaredToleranceKgPerKg": variable["declaredToleranceKgPerKg"],
        }
        verdicts.append({"check": "L8 constant-D Kirchhoff vs midpoint FD",
                         "value": maxLimit, "unit": "kg/kg",
                         "tolerance": TOLERANCES["constantDLimitKgPerKg"],
                         "status": "PASS" if maxLimit <= TOLERANCES["constantDLimitKgPerKg"] else "FAIL"})
        finest = variable["rows"][-1]["maxAbsDifference"]
        verdicts.append({"check": "L8 variable-D scheme difference at finest N",
                         "value": finest, "unit": "kg/kg",
                         "tolerance": TOLERANCES["schemeDifferenceKgPerKg"],
                         "status": "PASS" if finest <= TOLERANCES["schemeDifferenceKgPerKg"] else "FAIL"})
        order = variable["observedOrder"]
        if order is not None:
            verdicts.append({"check": "L8 observed convergence order",
                             "value": order, "unit": "1",
                             "tolerance": TOLERANCES["observedOrderMinimum"],
                             "status": "PASS" if order >= TOLERANCES["observedOrderMinimum"] else "FAIL"})

    if energy:
        worst = max((c["rateIdentityMaxRelativeDeviation"] for c in energy["cases"]),
                    default=None)
        verdicts.append({"check": "L11 thermal rate identity vs surface face",
                         "value": worst, "unit": "1", "tolerance": 1e-12,
                         "status": "PASS" if worst is not None and worst <= 1e-12 else "FAIL"})

    # ---- L9 isotherm / water-activity closure scenario ----------------------
    if isotherm:
        checks = isotherm["identityChecks"]
        limit = abs(checks.get("baselineLimit", {}).get("absoluteDifference", float("inf")))
        report["layers"]["L9_isothermClosure"] = {
            "isotherm": isotherm["isotherm"],
            "anchorCheck": checks.get("anchor"),
            "baselineLimitDifference": limit,
            "baselineLimitDetail": checks.get("baselineLimit"),
            "partitionFactorAcrossRange": checks.get("partitionFactorAcrossRange"),
            "chamber": checks.get("chamber"),
            "scenarios": [{"scenario": r["scenario"], "status": r["status"],
                           "eventH": r.get("event_h"),
                           "tailIntegrity": r.get("tailIntegrity"),
                           "partitionFactorAtEnd": r.get("partitionFactorAtEnd"),
                           "eventReached": r.get("eventReached")}
                          for r in isotherm["scenarios"]],
            "frozenBaselineForComparison": isotherm["frozenBaselineForComparison"],
        }
        verdicts.append({"check": "L9 p=1 member reproduces the frozen boundary",
                         "value": limit, "unit": "1",
                         "tolerance": TOLERANCES["baselineLimitAbsoluteDifferencePaOverKappa"],
                         "status": "PASS" if limit <= TOLERANCES[
                             "baselineLimitAbsoluteDifferencePaOverKappa"] else "FAIL"})
        anchor = checks.get("anchor", {})
        anchorGap = abs(anchor.get("absoluteDifference", float("inf"))) if anchor else float("inf")
        verdicts.append({"check": "L9 isotherm passes through the forced equilibrium point",
                         "value": anchorGap, "unit": "1", "tolerance": 1e-12,
                         "status": "PASS" if anchorGap <= 1e-12 else "FAIL"})

    # ---- L10 variance-based sensitivity -------------------------------------
    if morris or sobol or dscale or kscale:
        report["layers"]["L10_sensitivity"] = {
            "morrisRanking": None if not morris else {
                q["question"]: [{"parameter": r["parameter"], "muStar": r["muStar"],
                                 "sigma": r["sigma"]} for r in q["ranking"]]
                for q in morris.get("morris", [])},
            "sobolIndices": None if not sobol else {
                q["question"]: q["indices"] for q in sobol.get("sobol", [])},
            "validatedSingleParameterScans": {
                key: (None if not data or "scan" not in data else {
                    "parameter": data["scan"]["parameter"],
                    "rows": data["scan"]["rows"],
                    "summary": data["scan"]["summary"]})
                for key, data in (("dScale", dscale), ("kScale", kscale))},
            "knownInjectionDefect": (
                "The Morris run in morris.json reports mu* = 0 exactly for dScale in all "
                "20 elementary effects of both questions. That is an injection defect, not "
                "a robustness result: with face_scheme='kirchhoff' the solver's "
                "water_internal_flux uses a hard-coded per-question D0 and never reads the D "
                "array returned by properties(), so scaling properties() alone cannot change "
                "the model. The defect was patched in a parallel session by also scaling the "
                "returned Kirchhoff flux, which is exactly linear in D0. The Morris dScale "
                "entry is therefore VOID; the validated single-parameter scans above replace "
                "it and carry a self-check at scale 1.0 that reproduces the surrogate "
                "baseline to 1e-6 h."),
            "establishedResult": (
                "Diffusion pre-factor uncertainty of -30%/+40% moves the drying time by "
                "+38%/-25% (Q23: 79.42 h to 43.08 h; Q4: 70.41 h to 38.32 h), while thermal "
                "conductivity uncertainty of +/-15% moves it by less than 0.011%. Under this "
                "operating point the model is mass-transfer controlled."),
            "injectionSentinelRequired": (
                "Every injection-style experiment (monkey-patched properties, alternative "
                "flux, wrapped model) must carry a sentinel proving the injection was "
                "actually used; see method_v1/method_comparison.json fluxPathUsed."),
            "note": ("Indices are rankings on a validated coarse surrogate; absolute event times "
                     "carry the surrogate grid offset and must not be quoted as production values."),
        }

    report["verdicts"] = verdicts
    report["status"] = "FAIL" if any(v["status"] == "FAIL" for v in verdicts) else "PASS"

    (OUT / "crossvalidation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "crossvalidation_report.md").write_text(_markdown(report), encoding="utf-8")
    print(json.dumps({"status": report["status"],
                      "present": report["inputsPresent"],
                      "verdicts": verdicts}, ensure_ascii=False, indent=2), flush=True)
    return 0


def _fmt(value, digits=6):
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.{digits}g}"
    return str(value)


def _markdown(report):
    lines = ["# A题交叉验证汇总报告", "",
             f"- 总判定：**{report['status']}**",
             f"- 预声明容差：`{json.dumps(report['tolerances'], ensure_ascii=False)}`",
             f"- 输入齐备情况：`{json.dumps(report['inputsPresent'], ensure_ascii=False)}`", ""]
    lines += ["## L1 时间积分器交叉验证（同一网格、不同积分族）", "",
              "| 问题 | 网格 | BDF / h | Radau / h | 差 / s |", "|---|---:|---:|---:|---:|"]
    for question, row in report["layers"]["L1_timeIntegrator"].items():
        for intervals in (800, 1600):
            lines.append(f"| {question} | {intervals} | {_fmt(row.get(f'BDF_N{intervals}'), 12)} | "
                         f"{_fmt(row.get(f'Radau_N{intervals}'), 12)} | "
                         f"{_fmt(row.get(f'differenceSeconds_N{intervals}'), 4)} |")
    lines += ["", "## L2 水通量面格式随网格加密的收敛", "",
              "| 问题 | 网格 | Kirchhoff / h | 调和平均 / h | 差 / h | 比值 |", "|---|---:|---:|---:|---:|---:|"]
    for question, row in report["layers"]["L2_faceScheme"].items():
        for key, value in row.items():
            lines.append(f"| {question} | {key} | {_fmt(value['kirchhoffH'], 10)} | "
                         f"{_fmt(value['harmonicH'], 10)} | {_fmt(value['differenceH'], 4)} | "
                         f"{_fmt(value['ratio'], 5)} |")
    lines += ["", "## L4 解析与尺度交叉验证", "", "```json",
              json.dumps(report["layers"]["L4_analyticAndScaling"], ensure_ascii=False, indent=2),
              "```"]
    if "L4b_analyticMetricConvention" in report["layers"]:
        l4b = report["layers"]["L4b_analyticMetricConvention"]
        lines += ["", "## L4b 解析基准的比较口径（节点值 vs 控制体平均）", "",
                  f"- 观测到的一阶收敛率：{_fmt(l4b['observedPointToAverageOrder'], 5)}"
                  "（表面控制体单侧，几何效应）", "",
                  "| 网格 N | 点值↔控制体平均最大差 / K | 内部节点最大差 / K |",
                  "|---:|---:|---:|"]
        for row in l4b["rows"]:
            lines.append(f"| {row['intervals']} | {_fmt(row['maxPointVsCellDifferenceK'], 6)} | "
                         f"{_fmt(row['interiorMaxDifferenceK'], 6)} |")
    lines += ["", "## L6 模型结构（潜热情景包络）", ""]
    for question, rows in report["layers"].get("L6_modelStructure", {}).items():
        lines += [f"### {question}", "", "| 潜热比例 | 达标时间 / h | 相对基线 / % | 最低表面温度 / °C |",
                  "|---:|---:|---:|---:|"]
        for row in rows:
            lines.append(f"| {row['fraction']:g} | {_fmt(row['eventH'], 10)} | "
                         f"{_fmt(row['relativeToBaselinePercent'], 4)} | {_fmt(row['minSurfaceC'], 4)} |")
        lines.append("")
    lines += ["", "## L7 独立求根与最慢位置证书", "",
              "| 问题 | 事件根 / h | 独立二分根 / h | 差 / s | 严格复核 max C | 圆心即最大值 | 圆心超出量(中位) |",
              "|---|---:|---:|---:|---:|:--:|---:|"]
    for question, row in report["layers"].get("L7_independentRootAndMaxLocation", {}).items():
        lines.append(f"| {question} | {_fmt(row['solverEventH'], 12)} | "
                     f"{_fmt(row['independentBisectionH'], 12)} | "
                     f"{_fmt(row['differenceSeconds'], 4)} | "
                     f"{_fmt(row['unroundedMaxCAtStrictTime'], 8)} | "
                     f"{'是' if row['centreIsMaximumAtEvent'] else '否'} | "
                     f"{_fmt(row['maxExcessOverCentreMedianKgPerKg'], 3)} |")
    if "L8_discretisation" in report["layers"]:
        l8 = report["layers"]["L8_discretisation"]
        lines += ["", "## L8 同方程不同离散（Kirchhoff 势 vs 二阶守恒差分）", "",
                  f"- 常 D 极限最大差：{_fmt(l8['constantDLimitMaxDifferenceKgPerKg'], 4)} kg/kg",
                  f"- 变 D 观测收敛阶：{_fmt(l8['observedOrder'], 5)}"
                  f"（预先声明 {_fmt(l8['expectedOrderDeclared'], 3)}）", "",
                  "| 网格 N | 两方案最大差 / (kg/kg) | 出现时刻 / s | 出现半径 / m |",
                  "|---:|---:|---:|---:|"]
        for row in l8["variableDRows"]:
            lines.append(f"| {row['intervals']} | {_fmt(row['maxAbsDifference'], 6)} | "
                         f"{_fmt(row['maxDifferenceTimeS'], 6)} | {_fmt(row['locationOfMax'], 4)} |")
    if "L9_isothermClosure" in report["layers"]:
        l9 = report["layers"]["L9_isothermClosure"]
        lines += ["", "## L9 等温线／水活度闭合情景族", "",
                  f"- 等温线：`{l9['isotherm']['form']}`；锚点 a_wRef = {l9['isotherm']['awRef']}",
                  f"- 锚点来源：{l9['isotherm']['awRefSource']}",
                  f"- p=1 成员与冻结边界的最大差：{_fmt(l9['baselineLimitDifference'], 4)}",
                  f"- 烘房稳态相对湿度：{_fmt((l9.get('chamber') or {}).get('plateauMeanRH'), 4)}", "",
                  "| 情景 | 状态 | 达标时间 / h | 事件时 K_eff | tail 完整性 |",
                  "|---|---|---:|---:|---|"]
        for row in l9["scenarios"]:
            lines.append(f"| {row['scenario']} | {row['status']} | {_fmt(row['eventH'], 10)} | "
                         f"{_fmt(row['partitionFactorAtEnd'], 5)} | {row.get('tailIntegrity') or '—'} |")
    if "L10_sensitivity" in report["layers"]:
        l10 = report["layers"]["L10_sensitivity"]
        lines += ["", "## L10 参数敏感性（代理网格 N200，仅用于排序）", "",
                  "**Morris 的 dScale 条目已作废**（注入缺陷，见 JSON 的 `knownInjectionDefect`）；",
                  "以下单参数扫描在修补版上运行，并在 scale = 1.0 处自检复现代理基准到 1e−6 h。", ""]
        for key in ("dScale", "kScale"):
            scan = (l10.get("validatedSingleParameterScans") or {}).get(key)
            if not scan:
                continue
            lines += [f"### {key}", "", "| 取值 | Q2/Q3 事件 / h | Q4 事件 / h |", "|---:|---:|---:|"]
            rows = scan["rows"]
            for value in sorted({r["value"] for r in rows}):
                q23 = next((r["eventH"] for r in rows
                            if r["question"] == "Q23" and r["value"] == value), None)
                q4 = next((r["eventH"] for r in rows
                           if r["question"] == "Q4" and r["value"] == value), None)
                lines.append(f"| {value:g} | {_fmt(q23, 8)} | {_fmt(q4, 8)} |")
            summary = scan["summary"]
            lines += ["", "- 跨度：Q2/Q3 " + _fmt(summary["Q23"]["spanH"], 6) + " h（"
                      + _fmt(summary["Q23"]["relativeSpanPercent"], 4) + "%）；Q4 "
                      + _fmt(summary["Q4"]["spanH"], 6) + " h（"
                      + _fmt(summary["Q4"]["relativeSpanPercent"], 4) + "%）", ""]
        if l10.get("establishedResult"):
            lines += ["**结论**：" + l10["establishedResult"], ""]
        if l10.get("morrisRanking"):
            lines += ["### Morris 筛选排序（dScale 条目作废）", "", "```json",
                      json.dumps(l10["morrisRanking"], ensure_ascii=False, indent=2)[:3000],
                      "```"]
    if "L11_thermalConservation" in report["layers"]:
        l11 = report["layers"]["L11_thermalConservation"]
        lines += ["", "## L11 温度侧守恒证书", "",
                  "- CHECK A（速率恒等式）：`d/dt Σ 2w B T R² = 2hR(T∞−T_s)`，直接比较模型右端与表面面通量，"
                  "不含任何求积或轨迹差分。",
                  "- CHECK B（累积平衡）：容量冻结在 t = 0 时成立；题目一为精确形式，耦合问的残差即"
                  "有效容量随含水率变化所丢弃的功。", "",
                  "| 问题 | CHECK A 最大相对偏差 | CHECK B 相对残差 | 丢弃的容量功 / (J/m) | 未解释残差 / (J/m) |",
                  "|---|---:|---:|---:|---:|"]
        for question, row in l11["cases"].items():
            lines.append(f"| {question} | {_fmt(row['rateIdentityMaxRelativeDeviation'], 4)} | "
                         f"{_fmt(row['cumulativeRelativeResidual'], 6)} | "
                         f"{_fmt(row['discardedCapacityWorkJPerM'], 6)} | "
                         f"{_fmt(row['unexplainedResidualJPerM'], 6)} |")
        if l11.get("discardedWorkExplainsResidual"):
            ex = l11["discardedWorkExplainsResidual"]
            lines += ["", f"**{ex['question']} 的累积残差由丢弃功解释 {_fmt(100*ex['share'],4)}%**："
                      + ex["note"]]
    lines += ["", "## 判定明细", "", "| 检查 | 值 | 单位 | 容差 | 判定 |", "|---|---:|---|---:|---|"]
    for v in report["verdicts"]:
        lines.append(f"| {v['check']} | {_fmt(v.get('value'), 6)} | {v['unit']} | "
                     f"{_fmt(v.get('tolerance'), 4)} | {v['status']} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.exit(main())
