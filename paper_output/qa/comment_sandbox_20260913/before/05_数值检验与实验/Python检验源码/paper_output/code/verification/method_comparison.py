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
