from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile
import time
import uuid
from dataclasses import replace

ROOT = pathlib.Path(r"D:\Document\数学建模\2026CUMCM")


def _mkdtemp(suffix=None, prefix=None, dir=None):
    base = pathlib.Path(dir)
    for _ in range(200):
        candidate = base / ((prefix or "tmp") + uuid.uuid4().hex[:12] + (suffix or ""))
        if not candidate.exists():
            candidate.mkdir(parents=False)
            return str(candidate)
    raise FileExistsError("no unused temp name")


tempfile.mkdtemp = _mkdtemp
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.chdir(ROOT)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "paper_output" / "code" / "modeling"))

import numpy as np

from drying_core import Settings, solve_case

OUT = ROOT / "paper_output" / "results" / "crossvalidation" / "latent_scenarios_v1"
FIG = OUT / "figures"
FRACTIONS = (0.0, 0.25, 0.5, 1.0)
SAMPLES = np.array([0., 600., 1200., 1800., 3600., 7200., 10800., 21600., 43200., 86400.])


def scenario(question, shrink, fraction, intervals):
    settings = Settings(question=question, intervals=intervals, shrink=shrink,
                        rtol=1e-10, atol_temperature=1e-10, atol_moisture=1e-12,
                        early_max_step_s=2.0, max_step_s=120.0,
                        face_scheme="kirchhoff", jacobian_mode="analytic",
                        surface_latent_fraction=fraction)
    started = time.perf_counter()
    run = solve_case(settings)
    try:
        event = float(run.event_s)
        times = SAMPLES[SAMPLES < event]
        times = np.unique(np.r_[times, event - 1.0, event])
        T, C = run.fields(times, material_x=np.array([0.0, 0.5, 1.0]))
        radius = run.model.radius(times)
        rho_d = run.model.rho_d0 * (0.02 / radius) ** 2 if shrink else \
            np.full_like(radius, run.model.rho_d0)
        j_w = rho_d * settings.beta * (C[:, 2] - np.interp(times, run.model.env['time_s'],
                                                           run.model.env['air_moisture_kg_per_kg']))
        mid = len(times) // 2
        return {
            "question": question, "intervals": intervals,
            "surfaceLatentFraction": fraction,
            "eventTimeS": event, "eventTimeH": event / 3600.0,
            "sampleTimesS": times.tolist(),
            "surfaceTemperatureC": (T[:, 2] - 273.15).tolist(),
            "centreTemperatureC": (T[:, 0] - 273.15).tolist(),
            "surfaceMoisture": C[:, 2].tolist(),
            "centreMoisture": C[:, 0].tolist(),
            "surfaceLatentFluxWPerM2": (settings.latent_J_kg * fraction * j_w).tolist(),
            "minSurfaceTemperatureC": float(np.min(T[:, 2]) - 273.15),
            "elapsedSeconds": time.perf_counter() - started,
            "diagnostics": {k: run.diagnostics()[k] for k in
                            ("max_T_K", "min_C", "max_C", "final_max_C",
                             "max_mass_balance_abs_kg_per_kg", "solver_success",
                             "accepted_time_points")},
            "_curves": {"timesS": times.tolist(),
                        "surfaceC": (T[:, 2] - 273.15).tolist(),
                        "centreC": (T[:, 0] - 273.15).tolist()},
        }
    finally:
        run.close()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    if "--figure-only" in sys.argv:
        summary = json.loads((OUT / "latent_scenarios.json").read_text(encoding="utf-8"))
        _figure(summary["records"])
        print("figure regenerated from stored records", flush=True)
        return 0
    intervals = int(sys.argv[2]) if len(sys.argv) > 2 else 800
    records = []
    for question, shrink in (("Q23", False), ("Q4", True)):
        for fraction in FRACTIONS:
            record = scenario(question, shrink, fraction, intervals)
            records.append(record)
            print(json.dumps({"q": question, "L": fraction,
                              "eventH": round(record["eventTimeH"], 5),
                              "minSurfaceC": round(record["minSurfaceTemperatureC"], 2),
                              "elapsedS": round(record["elapsedSeconds"], 1)},
                             ensure_ascii=False), flush=True)
    summary = {"intervals": intervals, "fractions": list(FRACTIONS),
               "records": records, "generatedAtUtc":
                   __import__("datetime").datetime.now(
                       __import__("datetime").timezone.utc).isoformat()}
    (OUT / "latent_scenarios.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    _figure(records)
    return 0


def _figure(records):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.sans-serif": ["Microsoft YaHei", "SimHei"],
                         "axes.unicode_minus": False, "font.size": 10,
                         "axes.titlesize": 11, "axes.labelsize": 10,
                         "figure.dpi": 130, "savefig.bbox": "tight"})
    colors = {0.0: "#1f4e79", 0.25: "#2e75b6", 0.5: "#c55a11", 1.0: "#c00000"}
    fig, axes = plt.subplots(1, 3, figsize=(15.2, 4.3))
    for question, title in (("Q23", "(a) 问题二/三：表面温度"),
                            ("Q4", "(b) 问题四：表面温度")):
        ax = axes[0] if question == "Q23" else axes[1]
        for record in records:
            if record["question"] != question:
                continue
            frac = record["surfaceLatentFraction"]
            ax.plot(np.asarray(record["_curves"]["timesS"]) / 3600.0,
                    record["_curves"]["surfaceC"], color=colors[frac], lw=1.5,
                    label=f"潜热比例 {frac:g}")
        ax.set(xlabel="烘干时间 / h", ylabel="表面温度 / °C", title=title, xlim=(0, 12))
        ax.legend(fontsize=8)
        ax.grid(alpha=.25)

    ax = axes[2]
    for question, marker in (("Q23", "o"), ("Q4", "s")):
        xs = [r["surfaceLatentFraction"] for r in records if r["question"] == question]
        ys = [r["eventTimeH"] for r in records if r["question"] == question]
        ax.plot(xs, ys, marker=marker, lw=1.5, label=f"{question} 达标时间")
        base = ys[0]
        for x, y in zip(xs, ys):
            ax.annotate(f"{100*(y-base)/base:+.2f}%", (x, y), fontsize=8,
                        textcoords="offset points", xytext=(5, -11))
    ax.set(xlabel="表面潜热比例", ylabel="全域达标时间 / h", title="(c) 达标时间的包络",
           xlim=(-0.05, 1.28))
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=.25)

    fig.suptitle("表面蒸发冷却（潜热）修正的情景包络", fontsize=12.5)
    fig.text(.5, -.07, "潜热比例是情景参数而非标定常数：题目未给吸附等温线，表面蒸汽平衡无法唯一闭合。"
                       "比例 0 为冻结基线，比例 1 为全部排水汽化的上界情景。",
             ha="center", fontsize=8.5, color="#444444")
    fig.savefig(FIG / "fig_latent_scenarios.png")
    fig.savefig(FIG / "fig_latent_scenarios.pdf")
    plt.close(fig)


if __name__ == "__main__":
    sys.exit(main())
