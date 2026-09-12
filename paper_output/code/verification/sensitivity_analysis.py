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


def _scaled_properties(self, T, C):
    rho, cp, k, D = _ORIGINAL_PROPERTIES(self, T, C)
    return rho, cp, k * SCALES["k"], D * SCALES["d"]


RadialModel.properties = _scaled_properties

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
    elif stage == "sobol":
        subset = sys.argv[2].split(",")
        base = int(sys.argv[3]) if len(sys.argv) > 3 else 64
        result = {"sobol": [sobol(q, subset, base) for q in ("Q23", "Q4")]}
    else:
        raise SystemExit(f"unknown stage {stage}")
    path = OUT / f"{stage}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "morris"},
                     ensure_ascii=False)[:2000], flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
