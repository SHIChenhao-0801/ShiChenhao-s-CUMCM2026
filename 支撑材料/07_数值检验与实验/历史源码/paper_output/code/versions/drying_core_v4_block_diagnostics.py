"""2026 A: radial heat and dry-basis moisture transport on a material mesh.

Units: s, m, K, kg water / kg dry matter. See numerical_design.md for derivation.
The supplied empirical rho*cp is an effective thermal capacity. Dry-solid mass
is conserved separately on uniformly shrinking material control volumes.
No latent heat in the baseline; optional surface-latent scenario is labelled.
No clipping of solution values. Coefficients use a positive continuation only
for integrator Newton probes; all accepted states are checked independently.
"""
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
import analytic_jacobian

ROOT = Path(__file__).resolve().parents[3]
LOADED_CODE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
C0, T0, R0, LENGTH = 2.55, 301.15, 0.02, 0.25


def load_inputs(with_records=False):
    arrays, records = [], []
    for name in ['A_environment_observed.csv', 'A_radius_observed.csv']:
        path = ROOT / 'paper_output/data_cleaned' / name
        content = path.read_bytes()
        arrays.append(np.genfromtxt(io.StringIO(content.decode('utf-8-sig')),
                                    delimiter=',', names=True))
        records.append({'path':path.relative_to(ROOT).as_posix(), 'bytes':len(content),
                        'sha256':hashlib.sha256(content).hexdigest(), 'exists':True})
    return (*arrays, records) if with_records else tuple(arrays)


@dataclass(frozen=True)
class Settings:
    question: str = 'Q23'
    intervals: int = 100
    rtol: float = 1e-7
    atol_temperature: float = 1e-7
    atol_moisture: float = 1e-9
    max_step_s: float = 600.0
    early_max_step_s: float = 30.0
    horizon_h: float = 240.0
    shrink: bool = False
    boundary_extension: str = 'nominal'
    tail_temperature_C: float = 50.0
    tail_equilibrium: float = 0.05
    h: float = 25.0
    beta: float = 8e-7
    equilibrium_scale: float = 1.0
    surface_latent_fraction: float = 0.0
    latent_J_kg: float = 2.4e6
    constant_D: float | None = None
    constant_thermal: bool = False
    method: str = 'BDF'
    face_scheme: str = 'harmonic'
    jacobian_mode: str = 'analytic'


class RadialModel:
    def __init__(self, settings: Settings):
        self.settings = settings
        if settings.intervals < 2 or settings.jacobian_mode not in ('analytic', 'finite_difference'):
            raise ValueError('At least two intervals and a supported Jacobian mode are required')
        self.env, self.rad, self.input_records = load_inputs(with_records=True)
        self.x = np.linspace(0., 1., settings.intervals + 1)
        self.dx = 1. / settings.intervals
        faces = np.r_[0., (self.x[1:] + self.x[:-1]) / 2., 1.]
        self.w = np.diff(faces ** 2) / 2.
        self.internal_faces = faces[1:-1]
        self.n = len(self.x)
        self.rho_d0 = (760 + 90 * C0) / (1 + C0) if settings.question == 'Q4' else (
            820. / (1 + C0) if settings.question == 'Q1' else (650 + 128 * C0) / (1 + C0))
        self.evaluations = 0
        self.jac_pattern = self._sparsity()

    def radius(self, t):
        if self.settings.shrink:
            return np.interp(t, self.rad['time_s'], self.rad['radius_m'])
        return np.asarray(t) * 0. + R0

    def environment(self, t):
        s = self.settings
        tair = np.interp(t, self.env['time_s'], self.env['temperature_K'])
        ceq = np.interp(t, self.env['time_s'], self.env['air_moisture_kg_per_kg'])
        after = np.asarray(t) > self.env['time_s'][-1]
        if s.boundary_extension == 'nominal':
            tair = np.where(after, s.tail_temperature_C + 273.15, tair)
            ceq = np.where(after, s.tail_equilibrium, ceq)
        elif s.boundary_extension == 'tail_mean':
            tail = self.env['time_s'] >= 10800
            tair = np.where(after, self.env['temperature_K'][tail].mean(), tair)
            ceq = np.where(after, self.env['air_moisture_kg_per_kg'][tail].mean(), ceq)
        elif s.boundary_extension != 'last':
            raise ValueError('Unknown boundary extension')
        return tair, ceq * s.equilibrium_scale

    def properties(self, T, C):
        s = self.settings
        positive_C = np.maximum(C, 1e-12)  # coefficient continuation, never state clipping
        if np.any(T <= 0):
            raise FloatingPointError('Nonpositive absolute temperature')
        wet = positive_C / (1. + positive_C)
        if s.question == 'Q1':
            rho = np.full_like(C, 820.)
            cp = np.full_like(C, 2600.)
            k = np.full_like(C, .36)
            D = 7e-9 * np.exp(-.89 / positive_C)
        elif s.question in ('Q2', 'Q3', 'Q23'):
            rho, cp, k = 650 + 128 * positive_C, 1450 + 2736 * wet, .21 + .38 * wet
            D = 2.4e-3 * np.exp(-.45 / positive_C - 3850 / T)
        elif s.question == 'Q4':
            rho, cp, k = 760 + 90 * positive_C, 1850 + 2150 * wet, .12 + .20 * wet
            D = 4.2e-4 * np.exp(-.30 / positive_C - 3850 / T)
        else:
            raise ValueError(s.question)
        if s.constant_D is not None:
            D = np.full_like(C, s.constant_D)
        if s.constant_thermal:
            rho, cp, k = np.full_like(C, 820.), np.full_like(C, 2600.), np.full_like(C, .36)
        return rho, cp, k, D

    @staticmethod
    def harmonic(a):
        return 2 * a[:-1] * a[1:] / np.maximum(a[:-1] + a[1:], np.finfo(float).tiny)

    def _sparsity(self):
        p = lil_matrix((2 * self.n + 1, 2 * self.n + 1), dtype=int)
        for i in range(self.n):
            for j in range(max(0, i - 1), min(self.n, i + 2)):
                p[2*i:2*i+2, 2*j:2*j+2] = 1
        p[-1, 2 * (self.n - 1) + 1] = 1
        return p.tocsr()

    def water_internal_flux(self, T, C, D):
        if self.settings.face_scheme == 'harmonic' or self.settings.constant_D is not None:
            return self.internal_faces * self.harmonic(D) * np.diff(C) / self.dx
        if self.settings.face_scheme != 'kirchhoff':
            raise ValueError('Unknown nonlinear face scheme')
        a, D0 = {'Q1':(.89,7e-9), 'Q23':(.45,2.4e-3), 'Q2':(.45,2.4e-3),
                  'Q3':(.45,2.4e-3), 'Q4':(.30,4.2e-4)}[self.settings.question]
        cc = np.maximum(C, 1e-12)
        potential = cc * np.exp(-a/cc) + a * expi(-a/cc)
        difference = np.diff(potential)
        small = np.abs(np.diff(cc)) < 1e-7 * np.maximum((cc[:-1]+cc[1:])/2, 1e-3)
        difference[small] = (np.exp(-a/((cc[:-1][small]+cc[1:][small])/2)) * np.diff(cc)[small])
        thermal_factor = 1. if self.settings.question == 'Q1' else np.exp(-3850/((T[:-1]+T[1:])/2))
        # Do not difference thermal_factor*potential: that would add a false Soret flux.
        return self.internal_faces * D0 * thermal_factor * difference / self.dx

    def rhs(self, t, state):
        """REVIEW: actual material-control-volume balance, no extra mesh advection."""
        self.evaluations += 1
        T, C = state[:-1:2], state[1:-1:2]
        rho, cp, k, D = self.properties(T, C)
        radius = float(self.radius(t))
        tair, ceq = self.environment(t)
        heat_g = np.zeros(self.n + 1)
        water_g = np.zeros(self.n + 1)
        heat_g[1:-1] = self.internal_faces * self.harmonic(k) * np.diff(T) / self.dx
        water_g[1:-1] = self.water_internal_flux(T, C, D)
        water_g[-1] = -self.settings.beta * radius * (C[-1] - ceq)
        heat_g[-1] = -self.settings.h * radius * (T[-1] - tair)
        if self.settings.surface_latent_fraction:
            # Scenario: all selected outgoing water vaporizes at the surface.
            rho_d = self.rho_d0 * (R0 / radius) ** 2
            j_evap = rho_d * self.settings.beta * (C[-1] - ceq)
            heat_g[-1] -= (radius * self.settings.surface_latent_fraction *
                            self.settings.latent_J_kg * j_evap)
        derivative = np.empty_like(state)
        derivative[:-1:2] = np.diff(heat_g) / (radius ** 2 * self.w * rho * cp)
        derivative[1:-1:2] = np.diff(water_g) / (radius ** 2 * self.w)
        derivative[-1] = 2 * self.settings.beta / radius * (C[-1] - ceq)
        return derivative

    def initial(self):
        state = np.empty(2 * self.n + 1)
        state[:-1:2], state[1:-1:2], state[-1] = T0, C0, 0.
        return state


class Run:
    def __init__(self, model, pieces, elapsed, event_s):
        self.model, self.pieces = model, pieces
        self.elapsed_s, self.event_s = elapsed, event_s
        self.end_s = float(pieces[-1].t[-1])

    def state(self, times):
        tt = np.atleast_1d(np.asarray(times, dtype=float))
        if np.min(tt) < -1e-10 or np.max(tt) > self.end_s + 1e-7:
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

    def fields(self, times, radii_m=None, material_x=None):
        tt = np.atleast_1d(np.asarray(times, dtype=float))
        state = self.state(tt)
        Ts, Cs = state[:-1:2].T, state[1:-1:2].T
        if material_x is not None:
            points = np.asarray(material_x, dtype=float)
            if np.any(~np.isfinite(points)) or np.any((points < 0.) | (points > 1.)):
                raise ValueError('Material coordinates must be finite and within [0,1]')
            return np.array([np.interp(points, self.model.x, row) for row in Ts]), np.array([
                np.interp(points, self.model.x, row) for row in Cs])
        if radii_m is None:
            return Ts, Cs
        radial = np.asarray(radii_m)
        Tout, Cout = [], []
        for i, t in enumerate(tt):
            xx = radial / self.model.radius(t)
            Tout.append(np.interp(xx, self.model.x, Ts[i], left=np.nan, right=np.nan))
            Cout.append(np.interp(xx, self.model.x, Cs[i], left=np.nan, right=np.nan))
        return np.asarray(Tout), np.asarray(Cout)

    def diagnostics(self):
        # Reduce in bounded blocks: a fine full-domain run may contain tens of
        # millions of accepted state values. Diagnostics must not duplicate all
        # of them and four property arrays at the same time.
        minimum_C = minimum_T = minimum_D = minimum_property = np.inf
        maximum_C = maximum_T = maximum_D = maximum_radial_increase = -np.inf
        maximum_mass_residual = 0.
        for piece in self.pieces:
            for first in range(0, len(piece.t), 256):
                raw = piece.y[:, first:first+256]
                T, C = raw[:-1:2], raw[1:-1:2]
                residual = 2*self.model.w@C + raw[-1] - C0
                rho, cp, k, D = self.model.properties(T.ravel(), C.ravel())
                minimum_C, maximum_C = min(minimum_C,C.min()), max(maximum_C,C.max())
                minimum_T, maximum_T = min(minimum_T,T.min()), max(maximum_T,T.max())
                minimum_D = min(minimum_D,D.min())
                maximum_D = max(maximum_D,D.max())
                minimum_property = min(minimum_property,rho.min(),cp.min(),k.min(),D.min())
                maximum_radial_increase = max(maximum_radial_increase,np.max(np.diff(C,axis=0)))
                maximum_mass_residual = max(maximum_mass_residual,np.max(np.abs(residual)))
        final = self.state([self.end_s])[:, 0]
        finalC = final[1:-1:2]
        return {
            'event_s': self.event_s, 'event_h': None if self.event_s is None else self.event_s/3600,
            'end_s': self.end_s, 'elapsed_s': self.elapsed_s,
            'end_time_convention': 'ceil(critical_event_s)+1: conservative post-crossing verification second; not claimed earliest integer second',
            'max_mass_balance_abs_kg_per_kg': float(maximum_mass_residual),
            'min_C': float(minimum_C), 'max_C': float(maximum_C),
            'min_T_K': float(minimum_T), 'max_T_K': float(maximum_T),
            'min_D': float(minimum_D), 'max_D': float(maximum_D),
            'positive_properties': bool(minimum_property > 0),
            'max_radial_C_increase': float(maximum_radial_increase),
            'final_max_C': float(finalC.max()), 'final_surface_C': float(finalC[-1]),
            'strictly_dry_at_end': bool(finalC.max() < .15),
            'radius_end_m': float(self.model.radius(self.end_s)),
            'radius_extrapolation_used': bool(self.model.settings.shrink and self.end_s > 259200),
            'rhs_evaluations': self.model.evaluations,
            'accepted_time_points': sum(len(p.t) for p in self.pieces),
            'nfev': sum(p.nfev for p in self.pieces),
            'njev': sum(p.njev for p in self.pieces), 'nlu': sum(p.nlu for p in self.pieces),
            'solver_success': all(p.success for p in self.pieces),
        }


def solve_case(settings: Settings) -> Run:
    started = time.perf_counter()
    model = RadialModel(settings)
    jacobian_options = ({'jac': lambda t, y: analytic_jacobian.jacobian(model, t, y)}
        if settings.jacobian_mode == 'analytic' else {'jac_sparsity': model.jac_pattern})
    def dry_event(t, y):
        return float(np.max(y[1:-1:2]) - .15)
    dry_event.terminal, dry_event.direction = True, -1
    atol = np.empty(2 * model.n + 1)
    atol[:-1:2], atol[1:-1:2], atol[-1] = settings.atol_temperature, settings.atol_moisture, settings.atol_moisture
    horizon = 1800. if settings.question == 'Q1' else settings.horizon_h * 3600.
    pieces, initial, event_s = [], model.initial(), None
    # A separate segment at 4 h makes the modelling extension explicit.
    endpoints = [0., min(14400., horizon)]
    if horizon > 14400.:
        endpoints.append(horizon)
    for left, right in zip(endpoints[:-1], endpoints[1:]):
        piece = solve_ivp(model.rhs, (left, right), initial, method=settings.method,
            rtol=settings.rtol, atol=atol, **jacobian_options,
            max_step=settings.early_max_step_s if left < 14400. else settings.max_step_s,
            events=None if settings.question == 'Q1' else dry_event, dense_output=True)
        pieces.append(piece)
        if not piece.success:
            raise RuntimeError(piece.message)
        initial = piece.y[:, -1]
        if piece.t_events is not None and len(piece.t_events[0]):
            event_s = float(piece.t_events[0][0])
            # Continue to a genuine post-crossing integer second, not an extrapolation.
            end = float(np.ceil(event_s) + 1)
            tail = solve_ivp(model.rhs, (event_s, end), initial, method=settings.method,
                rtol=settings.rtol, atol=atol, **jacobian_options,
                max_step=1., dense_output=True)
            if not tail.success:
                raise RuntimeError(tail.message)
            pieces.append(tail)
            break
    run = Run(model, pieces, time.perf_counter() - started, event_s)
    diagnostic = run.diagnostics()
    if diagnostic['min_C'] < -1e-8 or not diagnostic['positive_properties']:
        raise FloatingPointError('Physical range/positive property check failed')
    if diagnostic['max_mass_balance_abs_kg_per_kg'] > 1e-6:
        raise FloatingPointError('Dry-basis mass balance failed')
    return run


def file_record(path):
    p = Path(path)
    return {'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size,
            'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'exists': True}


def save_run(run: Run, directory: Path):
    code_record = file_record(Path(__file__))
    if code_record['sha256'] != LOADED_CODE_SHA256:
        raise RuntimeError('Solver file changed after import; restart to obtain valid provenance')
    jacobian_record = file_record(Path(analytic_jacobian.__file__))
    if jacobian_record['sha256'] != analytic_jacobian.LOADED_CODE_SHA256:
        raise RuntimeError('Jacobian file changed after import; restart to obtain valid provenance')
    for record in run.model.input_records:
        if file_record(ROOT/record['path'])['sha256'] != record['sha256']:
            raise RuntimeError('Input changed after being loaded; retain failure and rerun')
    directory.mkdir(parents=True, exist_ok=True)
    times = np.unique(np.r_[np.arange(0., run.end_s, 60.),
                [t for t in [100., 300., 600., 900., 1200., 1500., 1800., 3600., 5400., 7200., 9000., 10800.] if t <= run.end_s],
                run.end_s, [] if run.event_s is None else [run.event_s]])
    x = np.linspace(0., 1., 21)
    T, C = run.fields(times, material_x=x)
    state = run.state(times)
    np.savez_compressed(directory/'sampled_solution.npz', times_s=times, material_x=x,
        T_K=T, C=C, radius_m=run.model.radius(times), mean_C=2*run.model.w@state[1:-1:2],
        cumulative_loss=state[-1])
    summary = {'settings': asdict(run.model.settings), 'diagnostics': run.diagnostics(),
               'code': code_record,
               'jacobian_code': jacobian_record,
               'inputs': run.model.input_records,
               'human_review_status': 'pending', 'gui_reproduced': False}
    (directory/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return summary
