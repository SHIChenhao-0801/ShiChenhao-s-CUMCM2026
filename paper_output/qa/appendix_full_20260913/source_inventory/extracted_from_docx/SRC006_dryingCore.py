from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import hashlib
import io
import json
import time

import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import lil_matrix
from scipy.special import expi
import analyticJacobian
import diskDense

ROOT = Path(__file__).resolve().parent
LOADED_CODE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
C0, T0, R0, LENGTH = 2.55, 301.15, 0.02, 0.25


def loadInputs(withRecords=False):
    arrays, records = [], []
    for name in ['A_environment_observed.csv', 'A_radius_observed.csv']:
        path = ROOT / 'inputs/cleaned' / name
        content = path.read_bytes()
        arrays.append(np.genfromtxt(io.StringIO(content.decode('utf-8-sig')),
                                    delimiter=',', names=True))
        records.append({'path':path.relative_to(ROOT).as_posix(), 'bytes':len(content),
                        'sha256':hashlib.sha256(content).hexdigest(), 'exists':True})
    return (*arrays, records) if withRecords else tuple(arrays)


@dataclass(frozen=True)

class Settings:
    question: str = 'Q23'
    intervals: int = 100
    rtol: float = 1e-7
    atolTemperature: float = 1e-7
    atolMoisture: float = 1e-9
    maxStepS: float = 600.0
    earlyMaxStepS: float = 30.0
    horizonH: float = 240.0
    shrink: bool = False
    boundaryExtension: str = 'nominal'
    tailTemperatureC: float = 50.0
    tailEquilibrium: float = 0.05
    h: float = 25.0
    beta: float = 8e-7
    equilibriumScale: float = 1.0
    surfaceLatentFraction: float = 0.0
    latentJKg: float = 2.4e6
    constantD: float | None = None
    constantThermal: bool = False
    method: str = 'BDF'
    faceScheme: str = 'harmonic'
    jacobianMode: str = 'analytic'
    denseStorage: str = 'disk'


class RadialModel:
    def __init__(self, settings: Settings):
        self.settings = settings
        if settings.intervals < 2 or settings.jacobianMode not in ('analytic', 'finite_difference'):
            raise ValueError('At least two intervals and a supported Jacobian mode are required')
        self.env, self.rad, self.inputRecords = loadInputs(withRecords=True)

        self.x = np.linspace(0., 1., settings.intervals + 1)
        self.dx = 1. / settings.intervals
        faces = np.r_[0., (self.x[1:] + self.x[:-1]) / 2., 1.]
        self.w = np.diff(faces ** 2) / 2.
        self.internalFaces = faces[1:-1]
        self.n = len(self.x)
        self.rhoD0 = (760 + 90 * C0) / (1 + C0) if settings.question == 'Q4' else (
            820. / (1 + C0) if settings.question == 'Q1' else (650 + 128 * C0) / (1 + C0))
        self.evaluations = 0
        self.jacPattern = self.buildSparsity()

    def radius(self, t):
        if self.settings.shrink:
            return np.interp(t, self.rad['time_s'], self.rad['radius_m'])
        return np.asarray(t) * 0. + R0


    def environment(self, t):
        s = self.settings
        tair = np.interp(t, self.env['time_s'], self.env['temperature_K'])
        ceq = np.interp(t, self.env['time_s'], self.env['air_moisture_kg_per_kg'])
        after = np.asarray(t) > self.env['time_s'][-1]
        if s.boundaryExtension == 'nominal':
            tair = np.where(after, s.tailTemperatureC + 273.15, tair)
            ceq = np.where(after, s.tailEquilibrium, ceq)
        elif s.boundaryExtension == 'tail_mean':
            tail = self.env['time_s'] >= 10800
            tair = np.where(after, self.env['temperature_K'][tail].mean(), tair)
            ceq = np.where(after, self.env['air_moisture_kg_per_kg'][tail].mean(), ceq)
        elif s.boundaryExtension != 'last':
            raise ValueError('Unknown boundary extension')
        return tair, ceq * s.equilibriumScale


    def properties(self, T, C):
        s = self.settings

        positiveC = np.maximum(C, 1e-12)
        if np.any(T <= 0):
            raise FloatingPointError('Nonpositive absolute temperature')
        wet = positiveC / (1. + positiveC)
        if s.question == 'Q1':
            rho = np.full_like(C, 820.)
            cp = np.full_like(C, 2600.)
            k = np.full_like(C, .36)
            D = 7e-9 * np.exp(-.89 / positiveC)
        elif s.question in ('Q2', 'Q3', 'Q23'):
            rho, cp, k = 650 + 128 * positiveC, 1450 + 2736 * wet, .21 + .38 * wet
            D = 2.4e-3 * np.exp(-.45 / positiveC - 3850 / T)
        elif s.question == 'Q4':
            rho, cp, k = 760 + 90 * positiveC, 1850 + 2150 * wet, .12 + .20 * wet
            D = 4.2e-4 * np.exp(-.30 / positiveC - 3850 / T)
        else:
            raise ValueError(s.question)
        if s.constantD is not None:
            D = np.full_like(C, s.constantD)
        if s.constantThermal:
            rho, cp, k = np.full_like(C, 820.), np.full_like(C, 2600.), np.full_like(C, .36)
        return rho, cp, k, D

    @staticmethod
    def harmonic(a):
        return 2 * a[:-1] * a[1:] / np.maximum(a[:-1] + a[1:], np.finfo(float).tiny)

    def buildSparsity(self):
        p = lil_matrix((2 * self.n + 1, 2 * self.n + 1), dtype=int)
        for i in range(self.n):
            for j in range(max(0, i - 1), min(self.n, i + 2)):
                p[2*i:2*i+2, 2*j:2*j+2] = 1
        p[-1, 2 * (self.n - 1) + 1] = 1
        return p.tocsr()


    def waterInternalFlux(self, T, C, D):
        if self.settings.faceScheme == 'harmonic' or self.settings.constantD is not None:
            return self.internalFaces * self.harmonic(D) * np.diff(C) / self.dx
        if self.settings.faceScheme != 'kirchhoff':
            raise ValueError('Unknown nonlinear face scheme')
        a, D0 = {'Q1':(.89,7e-9), 'Q23':(.45,2.4e-3), 'Q2':(.45,2.4e-3),
                  'Q3':(.45,2.4e-3), 'Q4':(.30,4.2e-4)}[self.settings.question]
        cc = np.maximum(C, 1e-12)

        potential = cc * np.exp(-a/cc) + a * expi(-a/cc)
        difference = np.diff(potential)
        small = np.abs(np.diff(cc)) < 1e-7 * np.maximum((cc[:-1]+cc[1:])/2, 1e-3)
        difference[small] = (np.exp(-a/((cc[:-1][small]+cc[1:][small])/2)) * np.diff(cc)[small])

        thermalFactor = 1. if self.settings.question == 'Q1' else np.exp(-3850/((T[:-1]+T[1:])/2))

        return self.internalFaces * D0 * thermalFactor * difference / self.dx


    def rhs(self, t, state):

        self.evaluations += 1
        T, C = state[:-1:2], state[1:-1:2]
        rho, cp, k, D = self.properties(T, C)
        radius = float(self.radius(t))
        tair, ceq = self.environment(t)
        heatG = np.zeros(self.n + 1)
        waterG = np.zeros(self.n + 1)
        heatG[1:-1] = self.internalFaces * self.harmonic(k) * np.diff(T) / self.dx
        waterG[1:-1] = self.waterInternalFlux(T, C, D)

        waterG[-1] = -self.settings.beta * radius * (C[-1] - ceq)
        heatG[-1] = -self.settings.h * radius * (T[-1] - tair)
        if self.settings.surfaceLatentFraction:

            rhoD = self.rhoD0 * (R0 / radius) ** 2
            jEvap = rhoD * self.settings.beta * (C[-1] - ceq)
            heatG[-1] -= (radius * self.settings.surfaceLatentFraction *
                            self.settings.latentJKg * jEvap)
        derivative = np.empty_like(state)

        derivative[:-1:2] = np.diff(heatG) / (radius ** 2 * self.w * rho * cp)
        derivative[1:-1:2] = np.diff(waterG) / (radius ** 2 * self.w)
        derivative[-1] = 2 * self.settings.beta / radius * (C[-1] - ceq)
        return derivative

    def initial(self):
        state = np.empty(2 * self.n + 1)
        state[:-1:2], state[1:-1:2], state[-1] = T0, C0, 0.
        return state


class Run:
    def __init__(self, model, pieces, elapsed, eventS, cache=None):
        self.model, self.pieces = model, pieces
        self.cache = cache
        self.elapsedS, self.eventS = elapsed, eventS
        self.endS = float(pieces[-1].t[-1])

    def close(self):

        self.pieces.clear()
        if self.cache is not None:
            self.cache.close()

    def state(self, times):
        tt = np.atleast_1d(np.asarray(times, dtype=float))
        if np.min(tt) < -1e-10 or np.max(tt) > self.endS + 1e-7:
            raise ValueError('Requested time outside solved interval')
        out = np.empty((2 * self.model.n + 1, len(tt)))
        remaining = np.ones(len(tt), dtype=bool)
        for result in self.pieces:
            select = remaining & (tt >= result.t[0]-1e-7) & (tt <= result.t[-1]+1e-7)
            if np.any(select):
                out[:, select] = result.sol(tt[select])
                remaining[select] = False
        if np.any(remaining):
            raise RuntimeError('Missing dense solution segment')
        return out


    def fields(self, times, radiiM=None, materialX=None):
        tt = np.atleast_1d(np.asarray(times, dtype=float))
        state = self.state(tt)
        Ts, Cs = state[:-1:2].T, state[1:-1:2].T
        if materialX is not None:
            points = np.asarray(materialX, dtype=float)
            if np.any(~np.isfinite(points)) or np.any((points < 0.) | (points > 1.)):
                raise ValueError('Material coordinates must be finite and within [0,1]')
            return np.array([np.interp(points, self.model.x, row) for row in Ts]), np.array([
                np.interp(points, self.model.x, row) for row in Cs])
        if radiiM is None:
            return Ts, Cs
        radial = np.asarray(radiiM)
        Tout, Cout = [], []
        for i, t in enumerate(tt):
            xx = radial / self.model.radius(t)
            Tout.append(np.interp(xx, self.model.x, Ts[i], left=np.nan, right=np.nan))
            Cout.append(np.interp(xx, self.model.x, Cs[i], left=np.nan, right=np.nan))
        return np.asarray(Tout), np.asarray(Cout)


    def diagnostics(self):


        minimumC = minimumT = minimumD = minimumProperty = np.inf
        maximumC = maximumT = maximumD = maximumRadialIncrease = -np.inf
        maximumMassResidual = 0.
        for piece in self.pieces:
            for first in range(0, len(piece.t), 256):
                raw = piece.y[:, first:first+256]
                T, C = raw[:-1:2], raw[1:-1:2]
                residual = 2*self.model.w@C + raw[-1] - C0
                rho, cp, k, D = self.model.properties(T.ravel(), C.ravel())
                minimumC, maximumC = min(minimumC,C.min()), max(maximumC,C.max())
                minimumT, maximumT = min(minimumT,T.min()), max(maximumT,T.max())
                minimumD = min(minimumD,D.min())
                maximumD = max(maximumD,D.max())
                minimumProperty = min(minimumProperty,rho.min(),cp.min(),k.min(),D.min())
                maximumRadialIncrease = max(maximumRadialIncrease,np.max(np.diff(C,axis=0)))
                maximumMassResidual = max(maximumMassResidual,np.max(np.abs(residual)))
        final = self.state([self.endS])[:, 0]
        finalC = final[1:-1:2]
        return {
            'event_s': self.eventS, 'event_h': None if self.eventS is None else self.eventS/3600,
            'end_s': self.endS, 'elapsed_s': self.elapsedS,
            'end_time_convention': 'ceil(critical_event_s)+1: conservative post-crossing verification second; not claimed earliest integer second',
            'max_mass_balance_abs_kg_per_kg': float(maximumMassResidual),
            'min_C': float(minimumC), 'max_C': float(maximumC),
            'min_T_K': float(minimumT), 'max_T_K': float(maximumT),
            'min_D': float(minimumD), 'max_D': float(maximumD),
            'positive_properties': bool(minimumProperty > 0),
            'max_radial_C_increase': float(maximumRadialIncrease),
            'final_max_C': float(finalC.max()), 'final_surface_C': float(finalC[-1]),
            'strictly_dry_at_end': bool(finalC.max() < .15),
            'radius_end_m': float(self.model.radius(self.endS)),
            'radius_extrapolation_used': bool(self.model.settings.shrink and self.endS > 259200),
            'rhs_evaluations': self.model.evaluations,
            'accepted_time_points': sum(len(p.t) for p in self.pieces),
            'nfev': sum(p.nfev for p in self.pieces),
            'njev': sum(p.njev for p in self.pieces), 'nlu': sum(p.nlu for p in self.pieces),
            'solver_success': all(p.success for p in self.pieces),
            'dense_storage': self.model.settings.denseStorage,
            'dense_coefficient_bytes': 0 if self.cache is None else self.cache.bytesWritten,
            'dense_polynomial_count': 0 if self.cache is None else self.cache.polynomialCount,
        }


def solveCase(settings: Settings) -> Run:
    started = time.perf_counter()
    if settings.denseStorage not in ('memory', 'disk'):
        raise ValueError('Dense storage must be memory or disk')
    if settings.denseStorage == 'disk' and settings.method != 'BDF':
        raise ValueError('Exact disk dense storage currently supports BDF only')
    cache = diskDense.DenseCache(ROOT) if settings.denseStorage == 'disk' else None
    try:
        return solveCaseImpl(settings, cache, started)
    except BaseException as error:
        if cache is not None:
            try:
                cache.close()
            except BaseException as cleanup_error:
                error.add_note('Private cache cleanup also failed: '+repr(cleanup_error))
        raise


def solveCaseImpl(settings, cache, started):
    model = RadialModel(settings)
    method = diskDense.DiskBDF if cache is not None else settings.method
    jacobianOptions = ({'jac': lambda t, y: analyticJacobian.jacobian(model, t, y)}
        if settings.jacobianMode == 'analytic' else {'jac_sparsity': model.jacPattern})
    if cache is not None:
        jacobianOptions['dense_cache'] = cache

    def dryEvent(t, y):
        return float(np.max(y[1:-1:2]) - .15)
    dryEvent.terminal, dryEvent.direction = True, -1
    atol = np.empty(2 * model.n + 1)
    atol[:-1:2], atol[1:-1:2], atol[-1] = settings.atolTemperature, settings.atolMoisture, settings.atolMoisture
    horizon = 1800. if settings.question == 'Q1' else settings.horizonH * 3600.
    pieces, initial, eventS = [], model.initial(), None

    endpoints = [0., min(14400., horizon)]
    if horizon > 14400.:
        endpoints.append(horizon)
    for left, right in zip(endpoints[:-1], endpoints[1:]):
        piece = solve_ivp(model.rhs, (left, right), initial, method=method,
            rtol=settings.rtol, atol=atol, **jacobianOptions,
            max_step=settings.earlyMaxStepS if left < 14400. else settings.maxStepS,
            events=None if settings.question == 'Q1' else dryEvent, dense_output=True)
        if cache is not None:
            diskDense.alignBdfSegments(piece)
        pieces.append(piece)
        if not piece.success:
            raise RuntimeError(piece.message)
        initial = piece.y[:, -1].copy()
        if cache is not None:
            piece.y = cache.storeAccepted(piece.y)
        if piece.t_events is not None and len(piece.t_events[0]):
            eventS = float(piece.t_events[0][0])


            end = float(np.ceil(eventS) + 1)
            tail = solve_ivp(model.rhs, (eventS, end), initial, method=method,
                rtol=settings.rtol, atol=atol, **jacobianOptions,
                max_step=1., dense_output=True)
            if cache is not None:
                diskDense.alignBdfSegments(tail)
            if not tail.success:
                raise RuntimeError(tail.message)
            if cache is not None:
                tail.y = cache.storeAccepted(tail.y)
            pieces.append(tail)
            break
    run = Run(model, pieces, time.perf_counter() - started, eventS, cache)
    diagnostic = run.diagnostics()
    if diagnostic['min_C'] < -1e-8 or not diagnostic['positive_properties']:
        raise FloatingPointError('Physical range/positive property check failed')
    if diagnostic['max_mass_balance_abs_kg_per_kg'] > 1e-6:
        raise FloatingPointError('Dry-basis mass balance failed')
    return run


def fileRecord(path):
    p = Path(path)
    return {'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size,
            'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'exists': True}


def saveRun(run: Run, directory: Path):
    codeRecord = fileRecord(Path(__file__))
    if codeRecord['sha256'] != LOADED_CODE_SHA256:
        raise RuntimeError('Solver file changed after import; restart to obtain valid provenance')
    jacobianRecord = fileRecord(Path(analyticJacobian.__file__))
    if jacobianRecord['sha256'] != analyticJacobian.LOADED_CODE_SHA256:
        raise RuntimeError('Jacobian file changed after import; restart to obtain valid provenance')
    storageRecord = fileRecord(Path(diskDense.__file__))
    if storageRecord['sha256'] != diskDense.LOADED_CODE_SHA256:
        raise RuntimeError('Dense storage file changed after import; restart for valid provenance')
    for record in run.model.inputRecords:
        if fileRecord(ROOT/record['path'])['sha256'] != record['sha256']:
            raise RuntimeError('Input changed after being loaded; retain failure and rerun')
    directory.mkdir(parents=True, exist_ok=True)
    times = np.unique(np.r_[np.arange(0., run.endS, 60.),
                [t for t in [100., 300., 600., 900., 1200., 1500., 1800., 3600., 5400., 7200., 9000., 10800.] if t <= run.endS],
                run.endS, [] if run.eventS is None else [run.eventS]])
    x = np.linspace(0., 1., 21)
    temperature, moisture, means, losses = [], [], [], []
    for first in range(0, len(times), 128):
        blockTimes = times[first:first+128]
        Tb, Cb = run.fields(blockTimes, materialX=x)
        raw = run.state(blockTimes)
        temperature.append(Tb); moisture.append(Cb)
        means.append(2*run.model.w@raw[1:-1:2]); losses.append(raw[-1].copy())
    T, C = np.vstack(temperature), np.vstack(moisture)
    np.savez_compressed(directory/'sampled_solution.npz', times_s=times, material_x=x,
        T_K=T, C=C, radius_m=run.model.radius(times), mean_C=np.concatenate(means),
        cumulative_loss=np.concatenate(losses))
    summary = {'settings': asdict(run.model.settings), 'diagnostics': run.diagnostics(),
               'code': codeRecord,
               'jacobian_code': jacobianRecord,
               'dense_storage_code': storageRecord,
               'inputs': run.model.inputRecords,
               'human_review_status': 'pending', 'gui_reproduced': False}
    (directory/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return summary
