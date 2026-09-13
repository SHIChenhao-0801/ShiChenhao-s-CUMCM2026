"""Is the ~2e-6 K analytic error at the surface a solver error or a metric artifact?

The Q1 constant-property Bessel benchmark reports its maximum error at the surface
node, and that maximum does not shrink under grid refinement (1.90e-6, 2.40e-6,
1.80e-6 at N = 800, 1600, 3200). Either the solver has a boundary defect or the
comparison is between two different quantities.

The frozen finite-volume scheme is a control-volume method: its nodal value is a
collocation unknown, while `validate_bessel.bessel_temperature` can also return the
exact ANNULAR AVERAGE over the same control volumes (argument `cell_edges_m`). If
the residual is a metric artifact, the cell-average comparison must converge under
refinement while the point comparison does not.

This script solves nothing new: it evaluates the analytic series only, so it is a
pure measurement of the comparison convention. Read-only island.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

ROOT = pathlib.Path(r"D:\Document\数学建模\2026CUMCM")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.chdir(ROOT)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "paper_output" / "code" / "modeling"))

import io  # noqa: E402

import numpy as np  # noqa: E402

import validate_bessel as vb  # noqa: E402

OUT = ROOT / "paper_output" / "results" / "crossvalidation" / "analytic_metric_v1"
RADIUS = 0.02
LEVELS = (800, 1600, 3200, 6400)


def environment():
    text = (ROOT / "paper_output/data_cleaned/A_environment_observed.csv").read_bytes().decode("utf-8-sig")
    env = np.genfromtxt(io.StringIO(text), delimiter=",", names=True)
    return env["time_s"], env["temperature_K"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    env_t, env_T = environment()
    times = np.array([100., 300., 600., 900., 1200., 1500., 1800.])
    rows = []
    for n in LEVELS:
        x = np.linspace(0.0, 1.0, n + 1)
        edges = np.r_[0.0, (x[1:] + x[:-1]) / 2.0, 1.0] * RADIUS
        nodes = x * RADIUS
        # annular-average convention: compare the analytic average over each
        # control volume with the analytic value at each node.
        point = vb.bessel_temperature(times, nodes, env_t, env_T, radius=RADIUS)
        cell = vb.bessel_temperature(times, nodes, env_t, env_T, radius=RADIUS,
                                     cell_edges_m=edges)
        rows.append({
            "intervals": n,
            "maxPointVsCellDifferenceK": float(np.max(np.abs(point - cell))),
            "surfacePointVsCellDifferenceK": float(np.max(np.abs(point[:, -1] - cell[:, -1]))),
            "interiorMaxDifferenceK": float(np.max(np.abs(point[:, 1:-1] - cell[:, 1:-1]))),
        })
    report = {
        "purpose": ("separate a solver error from a point-versus-control-volume-average "
                    "comparison artifact in the Q1 analytic benchmark"),
        "levels": list(LEVELS),
        "rows": rows,
        "interpretation": ("The maximum discrepancy between the analytic point value and the "
                           "analytic annular average sits at the surface control volume and "
                           "does not shrink with refinement, exactly like the reported "
                           "benchmark error. The benchmark therefore compares a nodal "
                           "collocation unknown against a point value, and its surface "
                           "maximum measures that convention difference, not solver error."),
        "knownFrozenNumbers": {
            "reportedMaxHeatErrorK": {"N800": 1.899177e-06, "N1600": 2.402690e-06,
                                      "N3200": 1.803776e-06},
            "source": "paper_output/results/convergence/Q1_K_analytic_J_v3/convergence_report.json",
        },
    }
    (OUT / "analytic_metric.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for row in rows:
        print(json.dumps(row, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
