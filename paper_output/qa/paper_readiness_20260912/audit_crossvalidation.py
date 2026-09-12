"""Read-only evidence reductions. No PDE, GUI, production writes or model changes."""
from __future__ import annotations
import ast
import hashlib
import importlib.util
import json
import math
import pathlib
import sys
from datetime import datetime, timezone
import numpy as np

ROOT = pathlib.Path(r"D:/Document/数学建模/2026CUMCM")
OUT = ROOT / "paper_output/qa/paper_readiness_20260912"
assert pathlib.Path.cwd().resolve() == ROOT.resolve()
inputs = {}
checks = []
def register(rel):
    p = ROOT / rel
    inputs[rel] = {"path": rel, "bytes": p.stat().st_size,
                   "sha256": hashlib.file_digest(p.open("rb"), "sha256").hexdigest()}
    return p
def read(rel):
    return json.loads(register(rel).read_text(encoding="utf-8-sig"))
def arrays(rel):
    with np.load(register(rel), allow_pickle=False) as data:
        return {k: data[k] for k in data.files}
def check(name, actual, expected, atol=0.):
    checks.append({"name": name, "actual": actual, "expected": expected,
                   "absoluteTolerance": atol, "passed": bool(abs(actual-expected) <= atol)})
def verify_manifest(records, scope):
    result=[]
    for r in records:
        if "path" not in r or "sha256" not in r: continue
        p=ROOT/r["path"]
        if not p.is_file():
            result.append({"path":r["path"],"scope":scope,"status":"MISSING"});continue
        register(r["path"])
        result.append({"path":r["path"],"scope":scope,"status":"MATCH" if inputs[r["path"]]["sha256"]==r["sha256"] else "MISMATCH",
                       "expectedSha256":r["sha256"]})
    return result

result={"generatedAtUtc":datetime.now(timezone.utc).isoformat(),
        "scope":"This process reads/hashes existing evidence; reduces JSON/NPZ; evaluates an existing analytic Bessel routine; integrates the given R(t) scale factor; probes a sequence statistic. It never runs a PDE, modifies production, or establishes new GUI/human review.",
        "python":sys.version,"numpy":np.__version__}
cv="paper_output/results/crossvalidation/"
production=read("paper_output/results/production/final_v6a/run_manifest.json")
run=production["runs"][0]
result["productionHashVerification"]=verify_manifest(run["input_files"]+run["output_artifacts"],"frozen production manifest")

# Independent time-integrator comparisons from original case event seconds.
cases=read(cv+"cv_solver_v1/cases.json")
solver_summary=read(cv+"cv_solver_v1/summary.json")
result["crossvalidationSolverHashVerification"]=verify_manifest([solver_summary["solverCode"]],"original crossvalidation solver")
for source in ("crossvalidate_solver.py","method_comparison.py","threshold_and_scaling_checks.py","sensitivity_analysis.py","energy_balance_check.py","isotherm_activity_closure.py"):
    register("paper_output/code/verification/"+source)
result["integrators"]=[]
for q in ("Q23","Q4"):
    for n in (400,800,1600):
        pair=[next((x for x in cases if x["case"]==f"B1_{q}_{m}_N{n}"),None) for m in ("BDF","Radau")]
        if all(pair):
            a,b=pair
            result["integrators"].append({"question":q,"N":n,"BDF_h":a["event_h"],"Radau_h":b["event_h"],"difference_s":abs(a["event_s"]-b["event_s"]),"statuses":[a["status"],b["status"]]})
result["solverCaseStatus"]={s:sum(x["status"]==s for x in cases) for s in sorted({x["status"] for x in cases})}
result["faceScheme"]=[]
for q in ("Q23","Q4"):
    for n in (400,800,1600):
        a,b=[next(x for x in cases if x["settings"]["question"]==q and x["settings"]["intervals"]==n and x["settings"]["face_scheme"]==s and x["case"].startswith("B2_")) for s in ("kirchhoff","harmonic")]
        result["faceScheme"].append({"question":q,"N":n,"kirchhoff_h":a["event_h"],"harmonic_h":b["event_h"],"difference_h":abs(a["event_h"]-b["event_h"])})

# Entire preserved temporal comparison projections, matching actual coordinates.
result["timeRefinement"]=[]
for q,d in (("Q1","final_v6"),("Q23","final_v6_Q23"),("Q4","final_v6_Q4")):
    base=f"paper_output/results/time_accuracy/{d}/"
    r=read(base+"time_accuracy_report.json")
    a,b=arrays(base+"baseline/comparison_projection.npz"),arrays(base+"tight/comparison_projection.npz")
    times,ia,ib=np.intersect1d(a["times_s"],b["times_s"],return_indices=True)
    assert np.array_equal(a["radii_m"],b["radii_m"])
    row={"question":q,"N":r["N"],"timeCount":len(times),"radiusCount":len(a["radii_m"]),"timeRange_s":[float(times[0]),float(times[-1])],"maxDifferences":{},"controls":[r["baseline_controls"],r["tight_controls"]]}
    for f in ("T_K","C"):
        value=float(np.nanmax(np.abs(a[f][ia]-b[f][ib])))
        row["maxDifferences"][f]=value
        check(f"time {q} {f}",value,r["comparison"]["max_absolute_difference"][f],1e-14)
    comp=r["comparison"]
    if comp.get("baseline_event_s") is not None:
        row["eventDifference_s"]=comp["tight_event_s"]-comp["baseline_event_s"]
        check(f"time {q} event",row["eventDifference_s"],comp["event_difference_s"],1e-12)
    result["timeRefinement"].append(row)
    if q=="Q1": q1_full=a

# Analytic Q1: reuse only the pre-existing analytic implementation, no solver import.
analytic_path=register("paper_output/code/modeling/validate_bessel.py")
spec=importlib.util.spec_from_file_location("existing_analytic_benchmark",analytic_path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
env=np.genfromtxt(register("paper_output/data_cleaned/A_environment_observed.csv"),delimiter=",",names=True,encoding="utf-8-sig")
t=q1_full["times_s"];r=q1_full["radii_m"]
exact240=module.bessel_temperature(t,r,env["time_s"],env["temperature_K"],n_terms=240)
exact480=module.bessel_temperature(t,r,env["time_s"],env["temperature_K"],n_terms=480)
diff=np.abs(q1_full["T_K"]-exact240);ii=np.unravel_index(np.argmax(diff),diff.shape)
q1_production=arrays("paper_output/results/production/final_v6a/Q1/sampled_solution.npz")
qt,ia,ib=np.intersect1d(t,q1_production["times_s"],return_indices=True)
result["bessel"]={"question":"Q1 heat only; constant thermal properties, cylindrical Robin, observed piecewise-linear chamber boundary",
    "N":3200,"timeCount":len(t),"radiusCount":len(r),"maxDifference_K":float(diff.max()),"location":{"time_s":float(t[ii[0]]),"radius_m":float(r[ii[1]])},
    "series240vs480_K":float(np.max(np.abs(exact240-exact480))),
    "preservedBaselineVsProductionSharedTimeCount":len(qt),"preservedBaselineVsProductionMax_K":float(np.max(np.abs(q1_full["T_K"][ia]-q1_production["T_K"][ib]))),
    "scope":"Full 1801x21 preserved N3200 baseline projection; production sampled values checked separately. Point-value comparison, no cell-average error attribution."}
bself=read("paper_output/results/bessel_validation/bessel_selfcheck.json")
result["besselHashVerification"]=verify_manifest(bself["execution_provenance"]["input_artifacts"]+bself["execution_provenance"]["output_artifacts"],"Bessel selfcheck")

# Space refinement: old full-grid maxima are recorded; preserved sample arrays reduced separately.
result["spaceRefinement"]=[]
for q,d in (("Q1","Q1_K_analytic_J_v3"),("Q23","Q23_final_resolution_v5"),("Q4","Q4_final_resolution_v5")):
    base=f"paper_output/results/convergence/{d}/";report=read(base+"convergence_report.json")
    c=report["comparisons"][-1];a=arrays(base+f'N{c["coarse_N"]}/sampled_solution.npz');b=arrays(base+f'N{c["fine_N"]}/sampled_solution.npz')
    times,ia,ib=np.intersect1d(a["times_s"],b["times_s"],return_indices=True)
    row={"question":q,"historicalFullGridRecord":c,"savedSampleTimeCount":len(times),"savedSampleMaximum":{}}
    for f in ("T_K","C"):row["savedSampleMaximum"][f]=float(np.nanmax(np.abs(a[f][ia]-b[f][ib])))
    row["limit"]="Full integer-second historical projection not preserved in this convergence folder; full-grid maxima are historical records, not a new complete replay. Saved samples compared at common material coordinates."
    result["spaceRefinement"].append(row)

# MATLAB independent-language scalar recomputation against raw JSON and saved Python arrays.
mat=read("paper_output/qa/matlab_crosscheck_20260911/comparison-python.json")
result["matlabHashVerification"]=verify_manifest(mat["inputRecords"],"MATLAB comparison original inputs")
result["matlab"]=[]
for row in mat["questions"]:
    q=row["question"];m=read(f"paper_output/qa/matlab_crosscheck_20260911/{q}_crossCheck.json");p=arrays(f"paper_output/results/code_delivery/camel_audit_v1/{q}/sampled_solution.npz")
    maxima={"temperatureK":0.,"moistureDryBasis":0.}
    for c in row["comparisons"]:
        # The old comparison's Python indices address its selected five-point
        # view, while the NPZ stores 21 radii. Match the raw coordinate values.
        mi=list(m["sampleTimesSec"]).index(c["timeSec"])
        mx=list(m["sampleMaterialX"]).index(c["materialX"])
        pi=int(np.flatnonzero(p["times_s"]==c["timeSec"])[0])
        px=int(np.flatnonzero(p["material_x"]==c["materialX"])[0])
        assert m["sampleTimesSec"][mi]==p["times_s"][pi]==c["timeSec"]
        assert m["sampleMaterialX"][mx]==p["material_x"][px]==c["materialX"]
        for mf,pf in (("temperatureK","T_K"),("moistureDryBasis","C")):
            value=abs(m[mf][mi][mx]-p[pf][pi,px]);maxima[mf]=max(maxima[mf],value)
            check(f"MATLAB {q} {mf} t={c['timeSec']} x={c['materialX']}",value,c[mf]["absoluteDifference"],1e-14)
    event=None
    if row["event"].get("applicable"):
        summary=read(f"paper_output/results/code_delivery/camel_audit_v1/{q}/summary.json")
        event=abs(m["eventSec"]-summary["diagnostics"]["event_s"])
        check(f"MATLAB {q} event",event,row["event"]["absoluteDifferenceSec"],1e-12)
    result["matlab"].append({"question":q,"N":40,"times_s":row["commonTimesSec"],"material_x":row["commonMaterialX"],"scalarCount":2*len(row["comparisons"]),"maxima":maxima,"eventDifference_s":event})

# Recompute two moisture-discretisation comparisons from their stored arrays.
method=read(cv+"method_v1/method_comparison.json");result["discretisation"]=[]
for kind,key in (("constant","limitingCaseConstantD"),("variable","variableD")):
    rows=[]
    for n in method["levels"]:
        a,b=[next(x for x in method["records"] if x["kind"]==kind and x["intervals"]==n and x["scheme"]==s) for s in ("kirchhoff","finiteDifference")]
        assert a["fluxPathUsed"]=="kirchhoff" and b["fluxPathUsed"]=="finiteDifference"
        value=float(np.max(np.abs(np.array(a["moisture"])-np.array(b["moisture"]))))
        check(f"discretisation {kind} N{n}",value,next(x for x in method[key]["rows"] if x["intervals"]==n)["maxAbsDifference"],1e-14)
        rows.append({"N":n,"maxDifference":value,"shape":list(np.shape(a["moisture"]))})
    result["discretisation"].append({"kind":kind,"rows":rows,"observedOrder":None if kind=="constant" else float(np.log2(rows[-2]["maxDifference"]/rows[-1]["maxDifference"]))})

threshold=read(cv+"threshold_scaling_v1/threshold_and_scaling_checks.json")
result["threshold"]=[]
for q,r in threshold["thresholdChecks"].items():
    value=abs(r["solverEventTimeS"]-r["independentBisectionTimeS"])
    check(f"threshold {q}",value,r["eventVsBisectionDifferenceS"],1e-15)
    result["threshold"].append({"question":q,"N":r["intervals"],"difference_s":value,"strictMaxC":r["unroundedMaxCAtStrictTime"],"strictTime_s":r["strictCheckTimeS"],"limit":"Both roots use the same ODE trajectory and dense output. Root-finding independence only."})
fixed=read("paper_output/results/experiments/physical_Q4_fixed_N200_K/summary.json")
shrink=read("paper_output/results/experiments/grids_Q4_N200_K/summary.json")
tf=fixed["diagnostics"]["event_h"];ts=shrink["diagnostics"]["event_h"]
rad=np.genfromtxt(register("paper_output/data_cleaned/A_radius_observed.csv"),delimiter=",",names=True,encoding="utf-8-sig")
grid=np.linspace(0.,ts*3600,200001)
tau=float(np.trapezoid((.02/np.interp(grid,rad["time_s"],rad["radius_m"]))**2,grid)/3600)
result["radiusScaling"]={"N":200,"fixed_h":tf,"shrink_h":ts,"equivalent_h":tau,"reductionPercent":100*(1-ts/tf),"residualPercent":100*(tau/tf-1),"limit":"Shared empirical radius and model outputs; dimensional/mechanistic corroboration, not an independent physical validation or an exact similarity transformation."}
check("R2 integral",tau,threshold["scalingCheck"]["equivalentFixedRadiusTimeH"],1e-11)

# Scoped sensitivity scans, old Morris defects kept explicit.
result["scans"]={}
for name in ("dscale","kscale"):
    r=read(cv+f"sensitivity_v1/{name}.json");rows=r["scan"]["rows"]
    summary=[]
    for q in ("Q23","Q4"):
        rr=[x for x in rows if x["question"]==q];base=next(x["eventH"] for x in rr if x["value"]==1.)
        vals=[x["eventH"] for x in rr]
        summary.append({"question":q,"N":200,"baseline_h":base,"span_h":max(vals)-min(vals),"spanPercent":100*(max(vals)-min(vals))/base,"rows":rr})
    result["scans"][name]=summary
morris=read(cv+"sensitivity_v1/morris.json")
result["morris"]={"dScaleInvalid":True,"reason":"Kirchhoff properties-only injection was ineffective in this historical run; other rankings are conditional on actual fixed D, not full eight-parameter screening.","invalidZeroEffects":[{"question":r["question"],"count":len(next(x for x in r["ranking"] if x["parameter"]=="dScale")["elementaryEffects"])} for r in morris["morris"]],"sobolFileExists":(ROOT/cv/"sensitivity_v1/sobol.json").exists()}

# Only execute the extracted pure statistic, no module setup/PDE side effects.
series_source=register("paper_output/code/verification/crossvalidate_series.py")
tree=ast.parse(series_source.read_text(encoding="utf-8-sig"))
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="sequential_mk")
space={"np":np,"math":math,"Z95":1.959963984540054}
exec(compile(ast.Module(body=[node],type_ignores=[]),str(series_source),"exec"),space)
probe=space["sequential_mk"](np.ones(20))
series=read(cv+"series_v1/series_crossvalidation.json")
result["stageMethods"]={"boundaries":series["boundaries"],"sequentialMK_constantSequence":{"n":20,"ufLast":probe["uf"][-1],"firstExceedanceIndex":probe["firstExceedanceIndex"],"verdict":"INVALID: sign-sum statistic subtracts positive-count expectation; a constant sequence spuriously exceeds trend threshold."},"validScope":"Other methods describe trends/segmentation/scales on shared data. They do not all estimate one stage boundary. No dependence correction in ordinary MK; wavelet boundary/cone/significance diagnostics absent; R/S on transient trends is not predictive evidence."}

result["correctionsRequired"]=["The analytic point-vs-cell difference decays ~N^-1; it cannot explain a nondecaying ~2e-6 K node benchmark mismatch by itself.","Bisection and solver events share one trajectory; do not call two independent full predictions.","R2 scaling inherits the simulated event and empirical R(t); do not call an exact independent solution.","Sequential MK is invalid. The 2023E training example is not an applicability argument for A.","Morris D entry invalid; remaining ranks are conditional on D fixed. No usable Sobol output.","Historical aggregate PASS does not certify the isotherm or cumulative energy claims identified by the handover review."]
result["arithmeticChecks"]=checks
result["arithmeticPass"]=all(x["passed"] for x in checks)
result["inputManifest"]=list(inputs.values())
result["scriptSha256"]=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()
result["humanReview"]="pending"
result["newGuiExecution"]=False
(OUT/"crossvalidation_verified.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"arithmeticPass":result["arithmeticPass"],"arithmeticChecks":len(checks),"inputsHashed":len(inputs),"hashMismatches":[x for key in ("productionHashVerification","matlabHashVerification","besselHashVerification") for x in result[key] if x["status"]!="MATCH"],"bessel":result["bessel"],"sequenceProbe":result["stageMethods"]["sequentialMK_constantSequence"]},ensure_ascii=False,indent=2))
