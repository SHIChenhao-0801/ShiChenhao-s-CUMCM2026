from __future__ import annotations

import json
import os
import pathlib
import sys
import time
from dataclasses import replace
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[3]
CODE = ROOT / "paper_output" / "code" / "modeling"
OUT = ROOT / "paper_output" / "results" / "crossvalidation" / "method_v1"

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.chdir(ROOT)
sys.dont_write_bytecode = True
sys.path.insert(0, str(CODE))

import numpy as np

import drying_core as core

FROZEN_BENCHMARK_D = 4.937655094173937e-09
D_REFERENCE = 4.938e-09
EXPECTED_ORDER = 1.0
DECLARED_TOLERANCE_KG_PER_KG = 1.0e-4
TIMES_S = np.array([0., 1., 10., 60., 300., 600., 900., 1200., 1500., 1800.])
RADII_M = np.linspace(0.0, 0.02, 21)


ACTIVE = {"scheme": "kirchhoff"}


def midpointDiffusionFlux(model, T, C, D):


    Dface = D[:-1] + (D[1:] - D[:-1]) * 0.5
    ACTIVE["scheme"] = "finiteDifference"
    return model.internal_faces * Dface * np.diff(C) / model.dx


def runScheme(scheme, intervals, kind):


    settings = core.Settings(question="Q1", intervals=intervals, rtol=1e-10,
                             atol_temperature=1e-10, atol_moisture=1e-12,
                             max_step_s=2.0, early_max_step_s=2.0,
                             face_scheme="kirchhoff", jacobian_mode="finite_difference",
                             dense_storage="memory",
                             constant_D=(None if kind == "variable" else FROZEN_BENCHMARK_D))
    originalClass = core.RadialModel

    class FluxModel(originalClass):
        def water_internal_flux(self, T, C, D):
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
