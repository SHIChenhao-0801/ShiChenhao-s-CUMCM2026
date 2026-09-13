from __future__ import annotations

import os
import pathlib
import sys
from dataclasses import replace

ROOT = pathlib.Path(r"D:\Document\数学建模\2026CUMCM")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.chdir(ROOT)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "paper_output" / "code" / "modeling"))
sys.path.insert(0, str(ROOT / "paper_output" / "code" / "verification"))

import numpy as np

import drying_core as core
import isotherm_activity_closure as iso


def describe(model, label, state):
    rhs = model.rhs(0.0, state)
    T, C = state[:-1:2], state[1:-1:2]
    print(f"--- {label}")
    print(f"    C_s={C[-1]:.6f}  T_s={T[-1]:.4f} K  aw={float(iso.waterActivity(C[-1], T[-1])):.6f}")
    print(f"    |rhs|_inf={np.max(np.abs(rhs)):.6e}  rhs[C_s]={rhs[2*model.n-1]:.6e}"
          f"  rhs[T_s]={rhs[2*model.n-2]:.6e}  rhs[A]={rhs[-1]:.6e}")
    print(f"    finite rhs: {bool(np.all(np.isfinite(rhs)))}")


    d = 1e-9
    for name, delta in (("C_s", np.zeros_like(state)), ("T_s", np.zeros_like(state))):
        perturbed = state.copy()
        idx = 2 * model.n - 1 if name == "C_s" else 2 * model.n - 2
        perturbed[idx] += d
        other = model.rhs(0.0, perturbed)
        print(f"    d(rhs[C_s])/d{name} = {(other[2*model.n-1] - rhs[2*model.n-1]) / d:.6e}")
    return rhs


def main():
    settings = core.Settings(question="Q23", intervals=200, rtol=1e-10,
                             atol_temperature=1e-10, atol_moisture=1e-12,
                             early_max_step_s=2.0, max_step_s=120.0,
                             face_scheme="kirchhoff", jacobian_mode="finite_difference")
    baseline = core.RadialModel(settings)
    state = baseline.initial()
    describe(baseline, "frozen baseline model at t=0", state)

    scenario = iso.ActivityModel(settings, B=4.2, latentFraction=0.0)
    describe(scenario, "isotherm scenario at t=0", state)


    run = core.solve_case(replace(settings, intervals=200))
    try:
        for t in (60.0, 600.0, 3600.0, 14400.0):
            walk = run.state([t])[:, 0]
            describe(baseline, f"baseline model at t={t}s", walk)
            describe(scenario, f"isotherm scenario at t={t}s (same state)", walk)
    finally:
        run.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
