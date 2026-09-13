"""Independent axisymmetric end-face check for the Q23 effective drying model.

Same constitutive laws, measured environment, and Kirchhoff face flux as
drying_core.py. Fixed radius and length, no latent heat. r=0 and z=0 are
symmetry planes; outer radius and optionally z=L/2 have Robin exchange.
Python execution is numerical evidence only: VS GUI and human review pending.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import traceback

# Limit BLAS worker threads before importing numpy/scipy, within this process.
for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_name, "1")

import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import coo_matrix
from scipy.special import expi

from drying_core import ROOT, C0, T0, R0, LENGTH, RadialModel, Settings, solve_case

CODE_PATH = Path(__file__).resolve()
CORE_PATH = CODE_PATH.with_name("drying_core.py")
CODE_HASH = hashlib.sha256(CODE_PATH.read_bytes()).hexdigest()
CORE_HASH = hashlib.sha256(CORE_PATH.read_bytes()).hexdigest()


def harmonic_pair(a, b):
    return 2 * a * b / np.maximum(a + b, np.finfo(float).tiny)


def concentration_potential(c):
    cc = np.maximum(c, 1e-12)  # Newton coefficient continuation, never clip state.
    return cc * np.exp(-0.45 / cc) + 0.45 * expi(-0.45 / cc)


class AxisymmetricModel:
    def __init__(self, nr=30, nz=30, end_faces=True):
        self.nr, self.nz = nr, nz
        self.shape = (nr + 1, nz + 1)
        self.nodes = (nr + 1) * (nz + 1)
        self.settings = Settings(question="Q23", intervals=nr,
                                 face_scheme="kirchhoff", horizon_h=100.)
        self.reference = RadialModel(self.settings)
        self.x, self.wr = self.reference.x, self.reference.w
        self.xr_faces = self.reference.internal_faces
        self.y = np.linspace(0., 1., nz + 1)
        faces_z = np.r_[0., (self.y[:-1] + self.y[1:]) / 2., 1.]
        self.wz = np.diff(faces_z)
        self.dx, self.dy = 1. / nr, 1. / nz
        self.half_length = LENGTH / 2.
        self.end_faces = bool(end_faces)
        self.mean_weights = 2 * self.wr[:, None] * self.wz[None, :]
        self.calls = 0
        self.started = 0.
        self.budget_s = 900.
        self.jac_pattern = self._sparsity()

    def _sparsity(self):
        idx = np.arange(self.nodes).reshape(self.shape)
        pairs = [(idx.ravel(), idx.ravel())]
        for a, b in [(idx[:-1], idx[1:]), (idx[:, :-1], idx[:, 1:])]:
            pairs += [(a.ravel(), b.ravel()), (b.ravel(), a.ravel())]
        rows, cols = [], []
        for a, b in pairs:
            for i in (0, 1):
                for j in (0, 1):
                    rows.extend((2 * a + i).tolist())
                    cols.extend((2 * b + j).tolist())
        surface = np.unique(np.r_[idx[-1, :], idx[:, -1]])
        rows.extend([2 * self.nodes] * len(surface))
        cols.extend((2 * surface + 1).tolist())
        size = 2 * self.nodes + 1
        return coo_matrix((np.ones(len(rows)), (rows, cols)),
                          shape=(size, size)).tocsr()

    def initial(self):
        out = np.empty(2 * self.nodes + 1)
        out[:-1:2], out[1:-1:2], out[-1] = T0, C0, 0.
        return out

    def fields(self, state):
        return state[:-1:2].reshape(self.shape), state[1:-1:2].reshape(self.shape)

    @staticmethod
    def face_water(Ta, Tb, Ca, Cb, Fa, Fb):
        cc_a, cc_b = np.maximum(Ca, 1e-12), np.maximum(Cb, 1e-12)
        dc = cc_b - cc_a
        dc_potential = Fb - Fa
        small = np.abs(dc) < 1e-7 * np.maximum((cc_a + cc_b) / 2, 1e-3)
        dc_potential = np.where(small, np.exp(-.45 / ((cc_a + cc_b) / 2)) * dc,
                                dc_potential)
        return 2.4e-3 * np.exp(-3850 / ((Ta + Tb) / 2)) * dc_potential

    def rhs(self, t, state):
        self.calls += 1
        if self.calls % 50 == 0 and time.perf_counter() - self.started > self.budget_s:
            raise TimeoutError("Axisymmetric per-run CPU/wall budget reached")
        T, C = self.fields(state)
        rho, cp, k, _ = self.reference.properties(T, C)
        tair, ceq = self.reference.environment(t)
        F = concentration_potential(C)
        gr_t = np.zeros((self.nr + 2, self.nz + 1))
        gr_c = np.zeros_like(gr_t)
        gz_t = np.zeros((self.nr + 1, self.nz + 2))
        gz_c = np.zeros_like(gz_t)
        gr_t[1:-1] = (self.xr_faces[:, None] *
            harmonic_pair(k[:-1], k[1:]) * np.diff(T, axis=0) / self.dx)
        gr_c[1:-1] = (self.xr_faces[:, None] *
            self.face_water(T[:-1], T[1:], C[:-1], C[1:], F[:-1], F[1:]) / self.dx)
        gz_t[:, 1:-1] = harmonic_pair(k[:, :-1], k[:, 1:]) * np.diff(T, axis=1) / self.dy
        gz_c[:, 1:-1] = self.face_water(T[:, :-1], T[:, 1:], C[:, :-1], C[:, 1:],
                                       F[:, :-1], F[:, 1:]) / self.dy
        gr_t[-1] = -self.settings.h * R0 * (T[-1] - tair)
        gr_c[-1] = -self.settings.beta * R0 * (C[-1] - ceq)
        if self.end_faces:
            gz_t[:, -1] = -self.settings.h * self.half_length * (T[:, -1] - tair)
            gz_c[:, -1] = -self.settings.beta * self.half_length * (C[:, -1] - ceq)
        heat_div = (np.diff(gr_t, axis=0) / (R0**2 * self.wr[:, None]) +
                    np.diff(gz_t, axis=1) / (self.half_length**2 * self.wz[None, :]))
        mass_div = (np.diff(gr_c, axis=0) / (R0**2 * self.wr[:, None]) +
                    np.diff(gz_c, axis=1) / (self.half_length**2 * self.wz[None, :]))
        derivative = np.empty_like(state)
        derivative[:-1:2] = (heat_div / (rho * cp)).ravel()
        derivative[1:-1:2] = mass_div.ravel()
        lateral_loss = 2 * self.settings.beta / R0 * (self.wz @ (C[-1] - ceq))
        end_loss = (self.settings.beta / self.half_length *
                    (2 * self.wr @ (C[:, -1] - ceq))) if self.end_faces else 0.
        derivative[-1] = lateral_loss + end_loss
        return derivative


class AxisymmetricRun:
    def __init__(self, model, pieces, elapsed, event):
        self.model, self.pieces, self.elapsed_s, self.event_s = model, pieces, elapsed, event
        self.end_s = float(pieces[-1].t[-1])

    def state(self, times):
        tt = np.atleast_1d(np.asarray(times, float))
        result = np.empty((2 * self.model.nodes + 1, len(tt)))
        pending = np.ones(len(tt), bool)
        for p in self.pieces:
            take = pending & (tt >= p.t[0] - 1e-8) & (tt <= p.t[-1] + 1e-8)
            if np.any(take):
                result[:, take] = p.sol(tt[take])
                pending[take] = False
        if pending.any():
            raise ValueError("Requested time outside computed axisymmetric solution")
        return result

    def diagnostics(self):
        m = self.model
        mass_error, cmin, cmax, tmin, tmax, axial_spread = 0., C0, C0, T0, T0, 0.
        for p in self.pieces:
            T, C = p.y[:-1:2], p.y[1:-1:2]
            means = m.mean_weights.ravel() @ C
            mass_error = max(mass_error, float(np.max(np.abs(means + p.y[-1] - C0))))
            cmin, cmax = min(cmin, float(C.min())), max(cmax, float(C.max()))
            tmin, tmax = min(tmin, float(T.min())), max(tmax, float(T.max()))
            CC = C.reshape(*m.shape, -1)
            axial_spread = max(axial_spread, float(np.max(np.ptp(CC, axis=1))))
        event_state = self.state([self.event_s if self.event_s is not None else self.end_s])[:, 0]
        _, finalC = m.fields(event_state)
        index = np.unravel_index(np.argmax(finalC), m.shape)
        result = {"event_s":self.event_s,
            "event_h":None if self.event_s is None else self.event_s/3600.,
            "end_s":self.end_s, "elapsed_s":self.elapsed_s,
            "max_mass_residual_kg_per_kg":mass_error, "min_C":cmin, "max_C":cmax,
            "min_T_K":tmin, "max_T_K":tmax, "max_axial_C_spread":axial_spread,
            "slowest_point_at_event_m":{"r":float(m.x[index[0]]*R0),
                                       "z_from_midplane":float(m.y[index[1]]*m.half_length)},
            "max_C_at_event":float(finalC.max()),
            "mean_C_at_event":float(np.sum(m.mean_weights*finalC)),
            "nfev":sum(p.nfev for p in self.pieces), "njev":sum(p.njev for p in self.pieces),
            "nlu":sum(p.nlu for p in self.pieces),
            "rhs_calls_including_jacobian":m.calls,
            "accepted_time_points":sum(len(p.t) for p in self.pieces),
            "solver_success":all(p.success for p in self.pieces)}
        if mass_error > 1e-6 or cmin < -1e-8:
            raise FloatingPointError(f"Axisymmetric physical check failed: {result}")
        return result


def solve_axisymmetric(nr=30, nz=30, end_faces=True, budget_s=600.):
    started = time.perf_counter()
    model = AxisymmetricModel(nr, nz, end_faces)
    model.started, model.budget_s = started, budget_s
    def event(t, y):
        return np.max(y[1:-1:2]) - .15
    event.terminal, event.direction = True, -1
    atol = np.empty(2*model.nodes+1)
    atol[:-1:2], atol[1:-1:2], atol[-1] = 1e-7, 1e-9, 1e-9
    pieces, initial, event_s = [], model.initial(), None
    for left, right in [(0.,14400.), (14400.,360000.)]:
        p = solve_ivp(model.rhs, (left,right), initial, method="BDF",
            rtol=1e-7, atol=atol, max_step=30. if left==0 else 600.,
            jac_sparsity=model.jac_pattern, events=event, dense_output=True)
        pieces.append(p)
        if not p.success:
            raise RuntimeError(p.message)
        initial = p.y[:,-1]
        if len(p.t_events[0]):
            event_s = float(p.t_events[0][0])
            break
    return AxisymmetricRun(model,pieces,time.perf_counter()-started,event_s)


def compare(run, radial):
    end=min(run.end_s,radial.end_s)
    times=np.unique(np.r_[np.arange(0.,end,21600.),1800.,10800.,end])
    times=times[times<=end]
    state2=run.state(times)
    T2=state2[:-1:2].reshape(*run.model.shape,-1)
    C2=state2[1:-1:2].reshape(*run.model.shape,-1)
    state1=radial.state(times)
    T1,C1=state1[:-1:2],state1[1:-1:2]
    mean2=run.model.mean_weights.ravel()@state2[1:-1:2]
    mean1=2*radial.model.w@C1
    delta_t=None if run.event_s is None or radial.event_s is None else (run.event_s-radial.event_s)/3600
    comparison={"same_radial_intervals":run.model.nr,
        "one_dimensional_event_h":None if radial.event_s is None else radial.event_s/3600,
        "axisymmetric_event_h":None if run.event_s is None else run.event_s/3600,
        "event_difference_h_2d_minus_1d":delta_t,
        "event_relative_difference":None if delta_t is None else delta_t/(radial.event_s/3600),
        "max_midplane_C_difference":float(np.max(np.abs(C2[:,0,:]-C1))),
        "max_midplane_T_difference_K":float(np.max(np.abs(T2[:,0,:]-T1))),
        "max_mean_C_difference":float(np.max(np.abs(mean2-mean1))),
        "times_s":times.tolist(),
        "mean_C_2d":mean2.tolist(),"mean_C_1d":mean1.tolist(),
        "center_C_2d":C2[0,0].tolist(),"center_C_1d":C1[0].tolist(),
        "center_T_K_2d":T2[0,0].tolist(),"center_T_K_1d":T1[0].tolist()}
    sample={"times_s":times,"x":run.model.x,"y":run.model.y,
        "T_K_2d":T2,"C_2d":C2,"T_K_1d":T1,"C_1d":C1,
        "mean_C_2d":mean2,"mean_C_1d":mean1}
    return comparison,sample


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--nr",type=int,default=30)
    p.add_argument("--nz",type=int,default=30)
    p.add_argument("--end-faces",choices=["on","off"],default="on")
    p.add_argument("--budget-s",type=float,default=600.)
    p.add_argument("--tag",default="")
    a=p.parse_args()
    folder=ROOT/"paper_output/results/axisymmetric_check"/f"Nr{a.nr}_Nz{a.nz}_end_{a.end_faces}{a.tag}"
    if folder.exists():
        raise FileExistsError(f"Refusing to overwrite {folder}")
    folder.mkdir(parents=True)
    start=datetime.now(timezone.utc).isoformat()
    print(f"START axisymmetric {folder.name} {start}",flush=True)
    try:
        run=solve_axisymmetric(a.nr,a.nz,a.end_faces=="on",a.budget_s)
        diagnostic=run.diagnostics()
        print(json.dumps({"axisymmetric_complete":diagnostic}),flush=True)
        radial=solve_case(Settings(question="Q23",intervals=a.nr,face_scheme="kirchhoff",horizon_h=100.))
        comparison,samples=compare(run,radial)
        np.savez_compressed(folder/"comparison_fields.npz",**samples)
        if hashlib.sha256(CODE_PATH.read_bytes()).hexdigest()!=CODE_HASH:
            raise RuntimeError("axisymmetric source changed during execution")
        if hashlib.sha256(CORE_PATH.read_bytes()).hexdigest()!=CORE_HASH:
            raise RuntimeError("shared core source changed during execution")
        summary={"started_at_utc":start,"finished_at_utc":datetime.now(timezone.utc).isoformat(),
            "settings":{"nr":a.nr,"nz":a.nz,"end_faces":a.end_faces=="on",
                        "R_m":R0,"half_length_m":LENGTH/2,
                        "reference":asdict(run.model.settings)},
            "diagnostics":diagnostic,"one_dimensional_diagnostics":radial.diagnostics(),
            "comparison":comparison,
            "provenance":{"axisymmetric_sha256":CODE_HASH,"core_sha256":CORE_HASH,
                          "inputs":run.model.reference.input_records},
            "gui_reproduced":False,"human_review_status":"pending",
            "limits":"Same-physics numerical comparison, not experimental validation. Grid/time convergence evaluated separately."}
        (folder/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
        print(json.dumps({"folder":str(folder),"comparison":comparison}),flush=True)
    except Exception:
        (folder/"failure.txt").write_text(traceback.format_exc(),encoding="utf-8")
        raise


if __name__=="__main__":
    main()
