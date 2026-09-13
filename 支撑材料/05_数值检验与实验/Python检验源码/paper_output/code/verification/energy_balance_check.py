"""Energy-conservation certificate for the thermal side of the frozen model.

Why this layer was missing
    Mass has a discrete conservation identity (2*sum(w_i C_i) + A = C0) and it is
    checked on every run.  The thermal side had only grid refinement and an
    analytic benchmark; it had no independent invariant.  This script derives and
    tests one.

Derivation, and an honest statement of what the model conserves
    The frozen temperature equation is the EFFECTIVE-CAPACITY form
        B(C) T_t = (1/r) (r k T_r)_r ,   B = rho_eff cp ,
    not a strict enthalpy equation: B depends on the moisture field, so d(B T)/dt is
    not B dT/dt and integral B T dV is not the conserved quantity of this model.

    Summing the discrete equations with the weights 2 w_i R(t)^2 cancels the
    1/(R^2 w_i) prefactor exactly; every interior face then appears twice with
    opposite signs and cancels pairwise, leaving only the surface face.  In this
    code the surface heat face carries the radius itself,

        g_{N+1/2}^T = -h R (T_s - T_inf) ,

    so after the weighting the exchange rate is 2 h R (T_inf - T_s).  Two separate
    statements follow, and they are NOT equally strong:

    CHECK A  rate identity (the certificate).  For the capacity actually used at the
      evaluation instant,
        d/dt sum_i 2 w_i B_i T_i R^2  =  2 h R (T_inf - T_s)      exactly
      which is verified below by comparing the model's own right-hand side with the
      surface face, with no quadrature and no trajectory differencing involved.

    CHECK B  cumulative balance.  Because the rate identity involves B at the
      evaluation instant while the solver advances B(C) T_t, the cumulative form is
      exact only for a capacity frozen in time:
        H0(t) = sum_i 2 w_i B_i(0) T_i(t) R(t)^2 ,
        H0(t) - E(t) = H0(0) ,   dE/dt = 2 h R (T_inf - T_s) .
      This is reported per question, and its residual is dominated by the quadrature
      of E rather than by the spatial operator.

    History, kept because each step was a real defect and each was caught only by
    the residual refusing to shrink under refinement: the first version used the
    instantaneous B but dropped the radius factor from the surface term (a
    factor-of-fifty error at R = 0.02 m); the second used the correct radius but
    instantaneous B in the cumulative form (Q23 residual 0.428 relative).  Both
    grid-independent failures meant the identity, not the solver, was wrong.

Read-only with respect to given data, frozen results, model and settings.  Writes
only its own result directory.
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
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.chdir(ROOT)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "paper_output" / "code" / "modeling"))

import numpy as np  # noqa: E402
from scipy.integrate import solve_ivp  # noqa: E402

import drying_core as core  # noqa: E402

OUT = ROOT / "paper_output" / "results" / "crossvalidation" / "energy_balance_v1"
DECLARED_TOLERANCE_J_PER_M = 1.0e-3      # declared before the numbers are inspected


def energyResidual(model, times, states, boundaryExchange, kernel):
    """CHECK B: |H0(t) - E(t) - H0(0)| with the capacity frozen at t = 0."""
    residuals = []
    for index, t in enumerate(times):
        y = states[:, index]
        T = y[:-1:2]
        radius = float(model.radius(t))
        stored = float(2.0 * (model.w * kernel * T).sum() * radius ** 2)
        residuals.append(abs(stored - boundaryExchange[index] - INITIAL[0]))
    return np.asarray(residuals)


def rateIdentity(model, times, states, settings):
    """CHECK A: the model's own dH/dt compared with the surface face, no quadrature."""
    rows = []
    for index, t in enumerate(times):
        y = states[:, index]
        T = y[:-1:2]
        rho, cp, _k, _D = model.properties(T, y[1:-1:2])
        radius = float(model.radius(t))
        tair, _ceq = model.environment(t)
        derivative = model.rhs(t, y)
        lhs = float(2.0 * (model.w * rho * cp * derivative[:-1:2]).sum() * radius ** 2)
        rhs = 2.0 * settings.h * radius * (float(tair) - float(T[-1]))
        rows.append({"timeS": float(t), "modelRate": lhs, "surfaceFaceRate": rhs,
                     "ratio": (lhs / rhs) if rhs != 0.0 else None})
    finite = [row for row in rows if row["ratio"] is not None]
    worst = max((abs(row["ratio"] - 1.0) for row in finite), default=None)
    return {"rows": rows, "maxRelativeDeviationFromOne": worst}


INITIAL = [0.0]


def runCase(question, intervals, shrink, sampleCount=41):
    settings = core.Settings(question=question, intervals=intervals, shrink=shrink,
                             rtol=1e-10, atol_temperature=1e-10, atol_moisture=1e-12,
                             early_max_step_s=2.0, max_step_s=120.0, horizon_h=6.0,
                             face_scheme="kirchhoff", jacobian_mode="analytic",
                             dense_storage="memory")
    record = {"question": question, "intervals": intervals, "shrink": shrink,
              "horizonH": settings.horizon_h}
    started = time.perf_counter()
    run = core.solve_case(settings)
    try:
        model = run.model
        end = float(run.end_s)
        times = np.linspace(0.0, end, sampleCount)
        states = run.state(times)
        # CHECK A needs no capacity choice at all: it compares the right-hand side
        # with the surface face at the same instant.
        rate = rateIdentity(model, times, states, settings)

        # CHECK B uses the capacity frozen at t = 0, which is the only form in which
        # the cumulative balance is exact for this effective-capacity model.
        radius0 = float(model.radius(times[0]))
        T0, C0 = states[:-1:2, 0], states[1:-1:2, 0]
        rho0, cp0, _k0, _D0 = model.properties(T0, C0)
        kernel = rho0 * cp0
        INITIAL[0] = float(2.0 * (model.w * kernel * T0).sum() * radius0 ** 2)

        def exchangeRate(t, y):
            T = y[:-1:2]
            tair, _ceq = model.environment(t)
            radius = float(model.radius(t))
            # The frozen surface heat face is -h R (T_s - T_inf); after the R^2
            # weighting the exchange rate is +2 h R (T_inf - T_s). Omitting R is a
            # factor-of-fifty error at R = 0.02 m and was the first real defect
            # found in this check.
            return 2.0 * settings.h * radius * (float(tair) - float(T[-1]))

        grid = np.linspace(0.0, end, 4001)
        rates = np.array([exchangeRate(t, run.state([t])[:, 0]) for t in grid])
        cumulative = np.concatenate([[0.0], np.cumsum(
            0.5 * (rates[1:] + rates[:-1]) * np.diff(grid))])
        boundaryExchange = np.interp(times, grid, cumulative)

        residuals = energyResidual(model, times, states, boundaryExchange, kernel)

        # Quantify the energy the effective-capacity closure discards. CHECK B is
        # exact only for a capacity frozen in time; the missing piece is the work
        # done against the changing capacity, sum_i 2 w_i (dB_i/dt) T_i R^2, which
        # this effective-capacity model does not carry. Reporting it turns the
        # CHECK B residual into a physical statement instead of an unexplained gap.
        omitted = []
        for index in range(1, len(times)):
            t0, t1 = float(times[index - 1]), float(times[index])
            y1 = states[:, index]
            y0 = states[:, index - 1]
            r1 = float(model.radius(t1))
            r0 = float(model.radius(t0))
            rho1, cp1, _k1, _D1 = model.properties(y1[:-1:2], y1[1:-1:2])
            rho0s, cp0s, _k0s, _D0s = model.properties(y0[:-1:2], y0[1:-1:2])
            b1 = 2.0 * (model.w * rho1 * cp1 * y1[:-1:2]).sum() * r1 ** 2
            b0 = 2.0 * (model.w * rho0s * cp0s * y0[:-1:2]).sum() * r0 ** 2
            omitted.append(float(b1 - b0) - float(
                2.0 * (model.w * kernel * (y1[:-1:2] - y0[:-1:2])).sum() * r1 ** 2))
        omittedTotal = float(np.sum(omitted))

        record.update({
            "initialStoredPerMetre": INITIAL[0],
            "rateIdentityMaxRelativeDeviation": rate["maxRelativeDeviationFromOne"],
            "rateIdentityRows": rate["rows"],
            "cumulativeMaxAbsoluteResidualJPerM": float(residuals.max()),
            "cumulativeRelativeResidual": float(residuals.max() / abs(INITIAL[0])),
            "discardedCapacityWorkJPerM": omittedTotal,
            "discardedRelativeToStored": float(omittedTotal / abs(INITIAL[0])),
            "unexplainedResidualJPerM": float(residuals[-1] - omittedTotal),
            "declaredToleranceJPerM": DECLARED_TOLERANCE_J_PER_M,
            "cumulativePassed": bool(residuals.max() <= DECLARED_TOLERANCE_J_PER_M),
            "sampleTimesS": times.tolist(),
            "cumulativeResidualsJPerM": residuals.tolist(),
            "maxMassResidualKgPerKg": run.diagnostics()["max_mass_balance_abs_kg_per_kg"],
        })
    finally:
        run.close()
    record["elapsedSeconds"] = time.perf_counter() - started
    print(json.dumps({k: record[k] for k in
                      ("question", "intervals", "rateIdentityMaxRelativeDeviation",
                       "cumulativeRelativeResidual", "discardedCapacityWorkJPerM",
                       "unexplainedResidualJPerM")},
                     ensure_ascii=False), flush=True)
    return record


def refinementCheck(question, shrink, levels=(100, 200, 400)):
    """The cumulative residual must fall under refinement if it is discretisation error."""
    rows = []
    for n in levels:
        row = runCase(question, n, shrink)
        rows.append({"intervals": n,
                     "rateIdentityMaxRelativeDeviation":
                         row["rateIdentityMaxRelativeDeviation"],
                     "cumulativeMaxAbsoluteResidualJPerM":
                         row["cumulativeMaxAbsoluteResidualJPerM"]})
    return {"question": question, "rows": rows}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cases = [runCase("Q1", 200, False), runCase("Q23", 200, False),
             runCase("Q4", 200, True)]
    refinement = [refinementCheck("Q23", False), refinementCheck("Q4", True)]
    report = {
        "checkA_rateIdentity": (
            "d/dt sum_i 2 w_i B_i T_i R^2 = 2 h R (T_inf - T_s), verified by comparing the "
            "model's own right-hand side with the surface face at the same instant; no "
            "quadrature and no trajectory differencing are involved"),
        "checkB_cumulative": (
            "H0(t) = sum_i 2 w_i B_i(0) T_i(t) R(t)^2 with dE/dt = 2 h R (T_inf - T_s); "
            "exact for a capacity frozen in time, which is the only form available for this "
            "effective-capacity model"),
        "derivation": ("Summing the discrete temperature equations with weights 2 w_i R^2 makes "
                       "every interior face cancel pairwise, leaving only the surface face, "
                       "which in this code is -h R (T_s - T_inf)."),
        "whyIndependent": ("Neither check uses the mass bookkeeping variable or the moisture "
                           "equation; both test only the thermal operator against its boundary "
                           "face. The two conventions are reported separately and must not be "
                           "conflated."),
        "declaredToleranceJPerM": DECLARED_TOLERANCE_J_PER_M,
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "cases": cases,
        "refinement": refinement,
    }
    (OUT / "energy_balance.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
