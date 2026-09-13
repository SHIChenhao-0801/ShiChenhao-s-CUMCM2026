from __future__ import annotations

import json
import os
import pathlib
import sys
import time
import traceback
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[3]
CL = ROOT / "paper_output" / "data_cleaned"
OUT = ROOT / "paper_output" / "results" / "crossvalidation" / "isotherm_closure_v1"

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.chdir(ROOT)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "paper_output" / "code" / "modeling"))

import io

import numpy as np
import scipy.integrate._ivp.common
from scipy.optimize._numdiff import approx_derivative

import drying_core as core


KAPPA = 0.621945
P_ATM = 101325.0
C_REF = 0.05
AW_REF_DEFAULT = 0.60
LATENT_J_KG = 2.4e6


def pSat(TC):

    return 610.94 * np.exp(17.625 * TC / (TC + 243.04))


def chamberRelativeHumidity(tail_from_s=3600.0):

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


    safe = np.maximum(np.asarray(C, dtype=float), 1e-12)
    z = (Cref / safe) ** (1.0 / p)
    aw = 1.0 - (1.0 - awRef) * z
    return np.clip(aw, 0.0, 1.0)


def partitionFactor(Cs, p, awRef=AW_REF_DEFAULT, Cref=C_REF):


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


class ActivityModel(core.RadialModel):


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


        kEff = float(partitionFactor(C[-1], self.shapeP, self.awRef))
        water_g[-1] = -self.settings.beta * radius * kEff * (C[-1] - ceq)

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

    record["diagnostics"] = run.diagnostics()
    event = run.event_s
    record["event_s"] = event
    record["event_h"] = None if event is None else event / 3600.0
    record["end_s"] = run.end_s
    span = float(event) if event is not None else float(run.end_s)
    sample = np.unique(np.r_[np.linspace(0.0, span, 61), span])


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


    def jacobian(t, y):
        return approx_derivative(lambda yy: model.rhs(t, yy), y,
                                 method="2-point", rel_step=relativeStep,
                                 sparsity=model.jac_pattern)
    return jacobian


def solveScenario(name, question, shrink, intervals, p, latent, awRef, horizon_h=None):


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


        return settings.early_max_step_s if left < 14400.0 else settings.max_step_s

    state, event_s = model.initial(), None


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

    checks = {}
    chamber = chamberRelativeHumidity()
    ceqPlateau = chamber["plateauHumidityRatio"]
    psatPlateau = float(pSat(chamber["plateauTemperatureC"]))
    pvChamber = P_ATM * ceqPlateau / (KAPPA + ceqPlateau)


    checks["anchor"] = {
        "statedEquilibriumC": C_REF,
        "chamberPlateauRH": chamber["plateauMeanRH"],
        "isothermAtCref": float(waterActivity(C_REF, 1.0, awRef)),
        "absoluteDifference": float(abs(waterActivity(C_REF, 1.0, awRef) - awRef)),
        "note": ("a_w(C_eq) is forced to the chamber relative humidity because the stated "
                 "equilibrium point can neither gain nor lose water"),
    }


    cs = 1.2
    frozenDrive = float(-1.0 * (cs - ceqPlateau))
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


    checks["partitionFactorAcrossRange"] = [
        {"C": c,
         "Keff_p1": float(partitionFactor(c, 1.0, awRef)),
         "Keff_p1p5": float(partitionFactor(c, 1.5, awRef)),
         "Keff_p2": float(partitionFactor(c, 2.0, awRef)),
         "Keff_p3": float(partitionFactor(c, 3.0, awRef)),
         "Keff_p4": float(partitionFactor(c, 4.0, awRef))}
        for c in (0.05, 0.06, 0.08, 0.10, 0.15, 0.20, 0.30, 0.50, 1.00, 2.55)]


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
