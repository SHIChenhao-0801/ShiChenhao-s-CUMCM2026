from __future__ import annotations

import json
import os
import pathlib
import sys
import time
import warnings

ROOT = pathlib.Path(__file__).resolve().parents[3]
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.chdir(ROOT)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "paper_output" / "code" / "modeling"))
sys.path.insert(0, str(ROOT / "paper_output" / "code" / "verification"))

import numpy as np
import scipy.integrate._ivp.common as common
from scipy.optimize._numdiff import approx_derivative

import drying_core as core
import isotherm_activity_closure as iso

OUT = ROOT / "paper_output" / "results" / "crossvalidation" / "isotherm_closure_v1"


def probe(relative_step, p=1.0, intervals=100, horizon_h=72.0):
    calls = {"numJac": 0}

    def fixedNumJac(fun, t, y, f, h, factor_, y_scale, f_scale, sparsity):
        calls["numJac"] += 1
        fresh = np.asarray(fun(t, y), dtype=float)
        jacobian = approx_derivative(lambda yy: fun(t, yy), y, f0=fresh,
                                     method="2-point", rel_step=relative_step,
                                     sparsity=sparsity)
        return jacobian, 1.0

    settings = core.Settings(question="Q23", intervals=intervals, shrink=False,
                             rtol=1e-10, atol_temperature=1e-10, atol_moisture=1e-12,
                             early_max_step_s=2.0, max_step_s=120.0, horizon_h=horizon_h,
                             face_scheme="kirchhoff", jacobian_mode="finite_difference",
                             dense_storage="memory")

    def factory(_settings):
        return iso.ActivityModel(_settings, p=p, awRef=0.6, latentFraction=0.0)

    originalModel, originalNumJac = core.RadialModel, common.num_jac
    core.RadialModel = factory
    common.num_jac = fixedNumJac
    record = {"relativeStep": relative_step, "p": p, "intervals": intervals,
              "horizonH": horizon_h}
    started = time.perf_counter()
    run = None
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            run = core.solve_case(settings)
        record["warnings"] = [str(w.message) for w in caught]
        diagnostic = run.diagnostics()
        record["status"] = "computed"
        record["event_h"] = None if run.event_s is None else run.event_s / 3600.0
        record["maxMassBalance"] = diagnostic["max_mass_balance_abs_kg_per_kg"]
        record["massBalanceWithinSolverGuard"] = bool(
            diagnostic["max_mass_balance_abs_kg_per_kg"] <= 1e-6)
        record["acceptedTimePoints"] = diagnostic["accepted_time_points"]
        record["finalMaxC"] = diagnostic["final_max_C"]
        record["numJacCalls"] = calls["numJac"]
    except Exception as error:
        record["status"] = "failed"
        record["error"] = f"{type(error).__name__}: {error}"
        record["numJacCalls"] = calls["numJac"]
    finally:
        core.RadialModel, common.num_jac = originalModel, originalNumJac
        if run is not None:
            run.close()
    record["elapsedSeconds"] = time.perf_counter() - started
    print(json.dumps(record, ensure_ascii=False), flush=True)
    return record


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = [probe(step) for step in (1e-4, 1e-5, 1e-6, 1e-7)]
    (OUT / "jacobian_probe.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
