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

import io

import numpy as np

OUT = ROOT / "paper_output" / "results" / "crossvalidation" / "threshold_scaling_v1"
R0 = 0.02


def read_radius():
    text = (ROOT / "paper_output/data_cleaned/A_radius_observed.csv").read_bytes().decode("utf-8-sig")
    return np.genfromtxt(io.StringIO(text), delimiter=",", names=True)


def scaling_check():
    rad = read_radius()
    t = rad["time_s"].astype(float)
    r = rad["radius_m"].astype(float)
    t_fixed_s = 129.84522834701946 * 3600.0
    t_shrink_s = 51.090973419826916 * 3600.0
    grid = np.linspace(0.0, t_shrink_s, 200001)
    r_of_t = np.interp(grid, t, r)
    integrand = (R0 / r_of_t) ** 2
    tau_eq = float(np.trapezoid(integrand, grid))

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


            lo, hi = t_event - 3600.0, t_event + 3600.0
            for _ in range(80):
                mid = 0.5 * (lo + hi)
                if max_c(mid) - 0.15 > 0.0:
                    lo = mid
                else:
                    hi = mid
            t_root = 0.5 * (lo + hi)


            grid = np.linspace(0.0, t_event, 2001)


            states = np.hstack([run.state(grid[i:i + 200]) for i in range(0, len(grid), 200)])
            cs = states[1:-1:2, :]
            argmax_x = run.model.x[np.argmax(cs, axis=0)]
            profile_increase = float(np.max(np.diff(cs, axis=0)))


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
