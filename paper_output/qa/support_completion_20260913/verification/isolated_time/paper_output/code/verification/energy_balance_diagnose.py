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
    settings = core.Settings(question="Q23", intervals=50, rtol=1e-10,
                             atol_temperature=1e-10, atol_moisture=1e-12,
                             early_max_step_s=2.0, max_step_s=120.0, horizon_h=1.0,
                             face_scheme="kirchhoff", jacobian_mode="analytic")
    run = core.solve_case(settings)
    try:
        model = run.model
        y0 = run.state([0.0])[:, 0]
        T0, C0 = y0[:-1:2], y0[1:-1:2]
        rho0, cp0, _k, _D = model.properties(T0, C0)
        B0 = rho0 * cp0
        radius = float(model.radius(0.0))
        print("n=%d  R=%.4f  sum w=%.6f" % (model.n, radius, model.w.sum()))
        print("w =", np.round(model.w, 8))
        print("B0 (first,last) =", B0[0], B0[-1])

        for t in (0.0, 60.0, 600.0, 1800.0, 3600.0):
            y = run.state([t])[:, 0]
            T, C = y[:-1:2], y[1:-1:2]
            d = model.rhs(t, y)
            dT = d[:-1:2]
            lhsRate = float(2.0 * (model.w * B0 * dT).sum() * radius ** 2)
            rho, cp, k, D = model.properties(T, C)
            tair, ceq = model.environment(t)
            Ts = float(T[-1])
            print("t=%7.0f  Ts=%.4f  Tinf=%.4f  sum(2w B0 dT)R^2=%+.6e   2h(Tinf-Ts)=%+.6e"
                  % (t, Ts, float(tair), lhsRate, 2.0 * settings.h * (float(tair) - Ts)))
            if t == 0.0:
                heat_g = np.zeros(model.n + 1)
                heat_g[1:-1] = model.internal_faces * model.harmonic(k) * np.diff(T) / model.dx
                heat_g[-1] = -settings.h * radius * (T[-1] - tair)
                hand = np.diff(heat_g) / (radius ** 2 * model.w * rho * cp)
                print("      check heat_g[-1]=%+.6e  heat_g[-2]=%+.6e" % (heat_g[-1], heat_g[-2]))
                print("      max|hand dT - model dT| =", np.max(np.abs(hand - dT)))
                print("      sum_i 2 w_i R^2 rho cp rhs_i = %+.6e" %
                      float(2.0 * (model.w * rho * cp * dT).sum() * radius ** 2))
    finally:
        run.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
