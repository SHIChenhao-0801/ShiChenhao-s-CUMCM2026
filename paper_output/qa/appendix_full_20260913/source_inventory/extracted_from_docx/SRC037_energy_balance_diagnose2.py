from __future__ import annotations

import os
import pathlib
import sys

ROOT = pathlib.Path(r"D:\Document\数学建模\2026CUMCM")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.chdir(ROOT)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "paper_output" / "code" / "modeling"))

import numpy as np

import drying_core as core


def main():
    for question, shrink in (("Q23", False), ("Q4", True)):
        settings = core.Settings(question=question, intervals=100, shrink=shrink,
                                 rtol=1e-10, atol_temperature=1e-10, atol_moisture=1e-12,
                                 early_max_step_s=2.0, max_step_s=120.0, horizon_h=1.0,
                                 face_scheme="kirchhoff", jacobian_mode="analytic")
        run = core.solve_case(settings)
        try:
            model = run.model
            print("=== %s" % question)
            for t in (1.0, 10.0, 100.0, 600.0, 1800.0, 3600.0):
                y = run.state([t])[:, 0]
                T, C = y[:-1:2], y[1:-1:2]
                d = model.rhs(t, y)
                rho, cp, _k, _D = model.properties(T, C)
                radius = float(model.radius(t))
                tair, _ceq = model.environment(t)
                lhs = float(2.0 * (model.w * rho * cp * d[:-1:2]).sum() * radius ** 2)
                rhs = 2.0 * settings.h * radius * (float(tair) - float(T[-1]))
                print("  t=%7.0f  R=%.5f  Ts=%.5f  Tinf=%.5f   dH/dt=%+.6e   2hR(Tinf-Ts)=%+.6e"
                      "   ratio=%.6f" % (t, radius, T[-1], float(tair), lhs, rhs,
                                         lhs / rhs if rhs else float("nan")))

            end = float(run.end_s)
            for count in (2001, 20001, 200001):
                grid = np.linspace(0.0, end, count)
                states = run.state(grid)
                rates = []
                for i, t in enumerate(grid):
                    y = states[:, i]
                    T = y[:-1:2]
                    tair, _ceq = model.environment(t)
                    radius = float(model.radius(t))
                    rates.append(2.0 * settings.h * radius * (float(tair) - float(T[-1])))
                rates = np.asarray(rates)
                cumulative = np.concatenate([[0.0], np.cumsum(
                    0.5 * (rates[1:] + rates[:-1]) * np.diff(grid))])[-1]
                T_end, C_end = states[:-1:2, -1], states[1:-1:2, -1]
                rho_e, cp_e, _k, _D = model.properties(T_end, C_end)
                radius_end = float(model.radius(end))
                stored_end = float(2.0 * (model.w * rho_e * cp_e * T_end).sum() * radius_end ** 2)

                T_0, C_0 = states[:-1:2, 0], states[1:-1:2, 0]
                rho_0, cp_0, _k0, _D0 = model.properties(T_0, C_0)
                radius_0 = float(model.radius(grid[0]))
                stored_0 = float(2.0 * (model.w * rho_0 * cp_0 * T_0).sum() * radius_0 ** 2)
                print("  quadrature %7d: stored(end)-stored(0)=%+.6e  E=%+.6e  residual=%+.6e (%.2e rel)"
                      % (count, stored_end - stored_0, cumulative,
                         (stored_end - stored_0) - cumulative,
                         abs((stored_end - stored_0) - cumulative) / abs(stored_0)))
        finally:
            run.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
