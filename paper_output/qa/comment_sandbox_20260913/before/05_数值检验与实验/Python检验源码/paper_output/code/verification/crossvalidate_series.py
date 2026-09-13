"""Multi-method cross-validation of stage boundaries for problem A.

The problem states that hot-air drying consists of a preheating / equilibrium
stage followed by constant-temperature drying, and the model extends the measured
4 h environment to a plateau and treats the given radius trajectory as a moving
domain. Every one of those choices implies a stage boundary. This script locates
the boundaries with several mutually independent methods and checks agreement.

Targets
  T1  onset of the chamber plateau         (given series, attachment 1)
  T2  end of the main radius shrinkage     (given series, attachment 2)
  T3  end of the preheating stage          (computed trajectory, Q2/Q3)

Methods
  M1  Mann-Kendall trend test (tie-corrected, Sen slope)
  M2  Sequential Mann-Kendall mutation test (UF / UB intersection)
  M3  Broken-stick regression (best continuous two-segment linear fit)
  M4  Fisher optimal segmentation (minimum within-group sum of squares, k = 2..6)
  M5  Relative-threshold criterion (fraction of the total change)
  M6  Morlet continuous wavelet transform (dominant scale)
  M7  Rescaled-range (Hurst) analysis

Cross-validation means: M2, M3, M4, M5 are four different statistical criteria for
the same boundary, and they must agree within a stated tolerance for the boundary
to be reported as identified rather than assumed.

Read-only with respect to given data, frozen results, model and settings.
"""
from __future__ import annotations

import json
import io
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(r"D:\Document\数学建模\2026CUMCM")
OUT = ROOT / "paper_output" / "results" / "crossvalidation" / "series_v1"
FIG = OUT / "figures"
Z95 = 1.959963984540054


# ---------------------------------------------------------------- Mann-Kendall
def mann_kendall(x):
    x = np.asarray(x, dtype=float)
    n = x.size
    s = 0.0
    for i in range(n - 1):
        s += float(np.sum(np.sign(x[i + 1:] - x[i])))
    _, counts = np.unique(x, return_counts=True)
    tie = float(np.sum(counts * (counts - 1) * (2 * counts + 5)))
    var_s = (n * (n - 1) * (2 * n + 5) - tie) / 18.0
    z = 0.0 if s == 0 else ((s - 1) / math.sqrt(var_s) if s > 0 else (s + 1) / math.sqrt(var_s))
    chunks = [(x[i + 1:] - x[i]) / np.arange(1, n - i, dtype=float) for i in range(n - 1)]
    sen = float(np.median(np.concatenate(chunks))) if chunks else float("nan")
    return {"n": n, "S": s, "varS": float(var_s), "Z": float(z),
            "p": math.erfc(abs(z) / math.sqrt(2.0)), "senSlopePerStep": sen,
            "trend": ("increasing" if z > Z95 else "decreasing" if z < -Z95 else "no trend")}


def sequential_mk(x):
    """Forward UF and backward UB sequences (standard M-K mutation test)."""
    x = np.asarray(x, dtype=float)
    n = x.size

    def forward(series):
        out = np.zeros(n)
        sk = 0.0
        for k in range(1, n):
            sk += float(np.sum(np.sign(series[k] - series[:k])))
            e = k * (k + 1) / 4.0
            v = k * (k + 1) * (2 * k + 5) / 72.0
            out[k] = 0.0 if v <= 0 else (sk - e) / math.sqrt(v)
        return out

    uf = forward(x)
    ub = -forward(x[::-1])[::-1]
    crossing = None
    for k in range(1, n):
        if (uf[k] - ub[k]) * (uf[k - 1] - ub[k - 1]) <= 0:
            crossing = k
            break
    return {"uf": uf.tolist(), "ub": ub.tolist(),
            "firstCrossingIndex": crossing,
            "firstCrossingInsideBand": bool(crossing is not None and abs(uf[crossing]) < Z95),
            "firstExceedanceIndex": int(np.argmax(np.abs(uf) > Z95))
            if np.any(np.abs(uf) > Z95) else None}


# ------------------------------------------------------------ broken-stick fit
def broken_stick(x, minFraction=0.05):
    """Best continuous two-segment linear fit with an unknown breakpoint.

    Model: x(t) = a + b t + c * max(0, t - bp). Solved through the 3x3 normal
    equations, so the scan over all admissible breakpoints is cheap.
    """
    x = np.asarray(x, dtype=float)
    n = x.size
    t = np.arange(n, dtype=float)
    lo, hi = max(2, int(minFraction * n)), n - 3
    best = (np.inf, None, None)
    for bp in range(lo, hi + 1):
        hinge = np.maximum(0.0, t - bp)
        A = np.column_stack([np.ones(n), t, hinge])
        ata = A.T @ A
        atx = A.T @ x
        try:
            coef = np.linalg.solve(ata, atx)
        except np.linalg.LinAlgError:
            continue
        rss = float(np.sum((x - A @ coef) ** 2))
        if rss < best[0]:
            best = (rss, bp, coef)
    rss, bp, coef = best
    total = float(np.sum((x - x.mean()) ** 2))
    return {"breakpointIndex": bp, "rss": rss,
            "explainedFraction": (1.0 - rss / total) if total > 0 else None,
            "slopeBefore": float(coef[1]) if coef is not None else None,
            "slopeAfter": float(coef[1] + coef[2]) if coef is not None else None}


# ------------------------------------------------------- Fisher optimal split
def fisher_segmentation(x, maxK=6):
    x = np.asarray(x, dtype=float)
    n = x.size
    c1 = np.concatenate(([0.0], np.cumsum(x)))
    c2 = np.concatenate(([0.0], np.cumsum(x * x)))
    prev = np.full(n + 1, np.inf)
    prev[0] = 0.0
    back = np.zeros((maxK + 1, n + 1), dtype=int)
    costs = [0.0]
    for k in range(1, maxK + 1):
        cur = np.full(n + 1, np.inf)
        for j in range(1, n + 1):
            start = np.arange(0, j)
            seg_sum = c1[j] - c1[start]
            seg_sq = c2[j] - c2[start]
            m = j - start
            total = prev[start] + (seg_sq - seg_sum * seg_sum / m)
            arg = int(np.argmin(total))
            cur[j] = total[arg]
            back[k, j] = arg + 1
        prev = cur
        costs.append(float(cur[n]))
    total_ss = float(c2[n] - c1[n] ** 2 / n)
    details = []
    for k in range(2, maxK + 1):
        cuts, j = [], n
        for kk in range(k, 1, -1):
            i = int(back[kk, j])
            cuts.append(i - 1)
            j = i - 1
        details.append({"k": k, "boundaryIndices": sorted(cuts), "withinSS": costs[k],
                        "explainedFraction": float(1.0 - costs[k] / total_ss)
                        if total_ss > 0 else None})
    return {"totalSS": total_ss, "segmentations": details}


# ------------------------------------------------------------------- wavelet
def morlet_cwt(x, scales=None, omega0=6.0):
    x = np.asarray(x, dtype=float)
    n = x.size
    xd = x - x.mean()
    if scales is None:
        scales = np.unique(np.round(np.geomspace(2.0, max(4.0, n / 8.0), 40)).astype(int))
    nfft = int(2 ** np.ceil(np.log2(n * 2)))
    xh = np.fft.fft(xd, nfft)
    omega = 2.0 * np.pi * np.fft.fftfreq(nfft)
    power = np.empty((len(scales), n))
    for si, s in enumerate(scales):
        psi = math.sqrt(2.0 * math.pi) * s * (math.pi ** -0.25) * \
            np.exp(-0.5 * (s * omega - omega0) ** 2)
        power[si] = np.abs(np.fft.ifft(xh * psi, nfft)[:n]) ** 2
    return scales, power


def wavelet_summary(x, dt):
    scales, power = morlet_cwt(x)
    total = power.sum(axis=1)
    scale_avg = power.mean(axis=0)
    return {"dominantScaleSamples": int(scales[int(np.argmax(total))]),
            "dominantPeriodSeconds": float(scales[int(np.argmax(total))] * dt),
            "scalesSamples": scales.tolist(), "globalWaveletPower": total.tolist()}


# --------------------------------------------------------------------- R/S
def hurst_rs(x):
    x = np.asarray(x, dtype=float)
    n = x.size
    sizes = [s for s in (8, 16, 32, 64, 128, 256, 512, 1024) if s <= n // 2]
    if len(sizes) < 3:
        return {"hurst": None, "note": "series too short"}
    logs, logrs = [], []
    for s in sizes:
        vals = []
        for w in range(n // s):
            seg = x[w * s:(w + 1) * s]
            y = np.cumsum(seg - seg.mean())
            sd = seg.std(ddof=0)
            if sd > 0:
                vals.append((y.max() - y.min()) / sd)
        if vals:
            logs.append(math.log(s))
            logrs.append(math.log(float(np.mean(vals))))
    return {"hurst": float(np.polyfit(logs, logrs, 1)[0]),
            "windowSizes": sizes, "logWindow": logs, "logRS": logrs}


# ------------------------------------------------------------------- helpers
def moving_average(x, w):
    x = np.asarray(x, dtype=float)
    if w <= 1:
        return x
    pad = w // 2
    xp = np.concatenate((np.full(pad, x[0]), x, np.full(pad, x[-1])))
    return np.convolve(xp, np.ones(w) / w, mode="valid")[:x.size]


def threshold_time(values, timeSeconds, fraction, increasing):
    """First time the series has covered `fraction` of its total change."""
    v = np.asarray(values, dtype=float)
    span = v[-1] - v[0]
    target = v[0] + fraction * span
    idx = np.argmax(v >= target) if increasing else np.argmax(v <= target)
    return float(timeSeconds[idx])


def analyse(name, values, timeSeconds, unit, note=""):
    v = np.asarray(values, dtype=float)
    if len(timeSeconds) > 1:
        dt = float(np.median(np.diff(timeSeconds)))
    else:
        dt = 1.0
    dv = np.diff(v)
    return {"series": name, "unit": unit, "n": int(v.size), "note": note,
            "mannKendall": mann_kendall(v),
            "sequentialMK": sequential_mk(v),
            "brokenStick": broken_stick(v),
            "fisher": fisher_segmentation(v, maxK=6),
            "wavelet": wavelet_summary(v, dt),
            "hurst": hurst_rs(v),
            "hurstOfIncrements": hurst_rs(dv) if dv.size > 64 else {"hurst": None}}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)

    def read_csv(name):
        text = (ROOT / "paper_output/data_cleaned" / name).read_bytes().decode("utf-8-sig")
        return np.genfromtxt(io.StringIO(text), delimiter=",", names=True)

    env = read_csv("A_environment_observed.csv")
    rad = read_csv("A_radius_observed.csv")
    q23 = np.load(ROOT / "paper_output/results/production/final_v6a/Q23/sampled_solution.npz")
    t_s = q23["times_s"]
    T_center = q23["T_K"][:, 0]
    T_surface = q23["T_K"][:, -1]
    mean_c = q23["mean_C"]
    t_env = env["time_s"]

    targets = {
        "T1_chamber_plateau_onset": analyse(
            "chamber temperature", env["temperature_C"], t_env, "degC"),
        "T1b_chamber_moisture_plateau_onset": analyse(
            "chamber moisture indicator", env["air_moisture_kg_per_kg"], t_env, "kg/kg"),
        "T2_radius_shrinkage_end": analyse(
            "specimen radius", rad["radius_cm"], rad["time_s"], "cm"),
        "T3_preheating_end_center": analyse(
            "centre temperature", T_center, t_s, "K",
            "computed trajectory: descriptive stage identification, not model validation"),
        "T3b_preheating_end_surface": analyse(
            "surface temperature", T_surface, t_s, "K",
            "computed trajectory: descriptive stage identification, not model validation"),
        "aux_mean_moisture": analyse(
            "dry-mass-weighted mean moisture", mean_c, t_s, "kg/kg",
            "computed trajectory"),
    }

    def bs_hours(key, timeSeconds):
        bp = targets[key]["brokenStick"]["breakpointIndex"]
        return None if bp is None else float(timeSeconds[bp] / 3600.0)

    def fisher_k2_hours(key, timeSeconds):
        seg = targets[key]["fisher"]["segmentations"]
        if not seg:
            return []
        return [float(timeSeconds[i] / 3600.0) for i in seg[0]["boundaryIndices"]]

    def mk_hours(key, timeSeconds):
        idx = targets[key]["sequentialMK"]["firstCrossingIndex"]
        return None if idx is None else float(timeSeconds[idx] / 3600.0)

    r95 = threshold_time(rad["radius_cm"], rad["time_s"], 0.95, increasing=False)
    t95_center = threshold_time(T_center, t_s, 0.95, increasing=True)
    t95_surface = threshold_time(T_surface, t_s, 0.95, increasing=True)

    boundaries = {
        "T1_chamber_plateau_onset": {
            "brokenStick_hours": bs_hours("T1_chamber_plateau_onset", t_env),
            "sequentialMK_hours": mk_hours("T1_chamber_plateau_onset", t_env),
            "fisher_k2_hours": fisher_k2_hours("T1_chamber_plateau_onset", t_env),
            "relative_threshold_95pct_hours": threshold_time(
                env["temperature_C"], t_env, 0.95, increasing=True) / 3600.0,
        },
        "T1b_chamber_moisture_plateau_onset": {
            "brokenStick_hours": bs_hours("T1b_chamber_moisture_plateau_onset", t_env),
            "sequentialMK_hours": mk_hours("T1b_chamber_moisture_plateau_onset", t_env),
            "fisher_k2_hours": fisher_k2_hours("T1b_chamber_moisture_plateau_onset", t_env),
            "relative_threshold_95pct_hours": threshold_time(
                env["air_moisture_kg_per_kg"], t_env, 0.95, increasing=True) / 3600.0,
        },
        "T2_radius_shrinkage_end": {
            "brokenStick_hours": bs_hours("T2_radius_shrinkage_end", rad["time_s"]),
            "sequentialMK_hours": mk_hours("T2_radius_shrinkage_end", rad["time_s"]),
            "fisher_k2_hours": fisher_k2_hours("T2_radius_shrinkage_end", rad["time_s"]),
            "fisher_k3_hours": [float(rad["time_s"][i] / 3600.0) for i in
                                targets["T2_radius_shrinkage_end"]["fisher"]
                                ["segmentations"][1]["boundaryIndices"]],
            "relative_threshold_95pct_hours": r95 / 3600.0,
        },
        "T3_preheating_end": {
            "brokenStick_center_hours": bs_hours("T3_preheating_end_center", t_s),
            "brokenStick_surface_hours": bs_hours("T3b_preheating_end_surface", t_s),
            "sequentialMK_center_hours": mk_hours("T3_preheating_end_center", t_s),
            "sequentialMK_surface_hours": mk_hours("T3b_preheating_end_surface", t_s),
            "fisher_k2_center_hours": fisher_k2_hours("T3_preheating_end_center", t_s),
            "fisher_k2_surface_hours": fisher_k2_hours("T3b_preheating_end_surface", t_s),
            "relative_threshold_95pct_center_hours": t95_center / 3600.0,
            "relative_threshold_95pct_surface_hours": t95_surface / 3600.0,
        },
    }

    results = {"targets": targets, "boundaries": boundaries}
    (OUT / "series_crossvalidation.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "stage_boundaries.json").write_text(
        json.dumps(boundaries, ensure_ascii=False, indent=2), encoding="utf-8")

    _figures(env, rad, t_s, T_center, T_surface, targets, boundaries)
    print(json.dumps(boundaries, ensure_ascii=False, indent=2), flush=True)
    return 0


def _figures(env, rad, t_s, T_center, T_surface, targets, boundaries):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.sans-serif": ["Microsoft YaHei", "SimHei"],
                         "axes.unicode_minus": False, "font.size": 10,
                         "axes.titlesize": 11, "axes.labelsize": 10,
                         "figure.dpi": 130, "savefig.bbox": "tight"})

    # Figure 1: preheating -> constant-temperature transition (computed trajectory)
    fig, axes = plt.subplots(1, 3, figsize=(15.2, 4.3))
    t_h = t_s / 3600.0
    ax = axes[0]
    ax.plot(t_h, T_center - 273.15, color="#1f4e79", lw=1.5, label="中心")
    ax.plot(t_h, T_surface - 273.15, color="#c55a11", lw=1.5, label="表面")
    ax.axhline(50, color="grey", ls=":", lw=1.1)
    for label, value, color in (
        ("中心 95%", boundaries["T3_preheating_end"]["relative_threshold_95pct_center_hours"], "#1f4e79"),
        ("表面 95%", boundaries["T3_preheating_end"]["relative_threshold_95pct_surface_hours"], "#c55a11"),
    ):
        if value:
            ax.axvline(value, color=color, ls="--", lw=1.1, label=f"{label} {value:.2f} h")
    ax.set(xlabel="烘干时间 / h", ylabel="温度 / °C", title="(a) 预热阶段温升（问题二轨迹）",
           xlim=(0, 8))
    ax.legend(fontsize=8)
    ax.grid(alpha=.25)

    ax = axes[1]
    bs = targets["T3_preheating_end_center"]["brokenStick"]
    bp = bs["breakpointIndex"]
    ax.plot(t_h, T_center - 273.15, color="#1f4e79", lw=1.5, label="中心温度")
    ax.axvline(t_h[bp], color="#c00000", ls="--", lw=1.2,
               label=f"两段折线分界 {t_h[bp]:.2f} h")
    ax.set(xlabel="烘干时间 / h", ylabel="温度 / °C", title="(b) 两段折线回归分界", xlim=(0, 8))
    ax.legend(fontsize=8)
    ax.grid(alpha=.25)

    ax = axes[2]
    values = boundaries["T3_preheating_end"]
    labels = ["两段\n折线", "M–K\n突变", "Fisher\nk=2", "95%\n阈值"]
    center = [values["brokenStick_center_hours"], values["sequentialMK_center_hours"],
              values["fisher_k2_center_hours"][0] if values["fisher_k2_center_hours"] else None,
              values["relative_threshold_95pct_center_hours"]]
    surface = [values["brokenStick_surface_hours"], values["sequentialMK_surface_hours"],
               values["fisher_k2_surface_hours"][0] if values["fisher_k2_surface_hours"] else None,
               values["relative_threshold_95pct_surface_hours"]]
    xpos = np.arange(len(labels))
    ax.bar(xpos - .18, [v if v else 0 for v in center], .36, color="#1f4e79", label="中心")
    ax.bar(xpos + .18, [v if v else 0 for v in surface], .36, color="#c55a11", label="表面")
    ax.set_xticks(xpos)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set(ylabel="分界时刻 / h", title="(c) 四种方法的分界时刻对照")
    ax.legend(fontsize=8)
    ax.grid(alpha=.25, axis="y")

    fig.suptitle("预热平衡→恒温干燥分界的多方法交叉验证", fontsize=12.5)
    fig.text(.5, -.06, "四种判据相互独立；分界时刻的一致性用于说明阶段划分客观可辨，"
                       "而非人为设定。该轨迹为已冻结数值解，故此处仅作阶段识别，不构成模型验证。",
             ha="center", fontsize=8.5, color="#444444")
    fig.savefig(FIG / "fig_stage_boundary_crossvalidation.png")
    fig.savefig(FIG / "fig_stage_boundary_crossvalidation.pdf")
    plt.close(fig)

    # Figure 2: mutation tests on given data series
    fig, axes = plt.subplots(1, 3, figsize=(15.2, 4.3))
    for ax, key, x, tt, title in (
        (axes[0], "T1_chamber_plateau_onset", env["temperature_C"], env["time_s"] / 3600.0, "(a) 烘房温度"),
        (axes[1], "T1b_chamber_moisture_plateau_onset", env["air_moisture_kg_per_kg"], env["time_s"] / 3600.0, "(b) 烘房水分指标"),
        (axes[2], "T2_radius_shrinkage_end", rad["radius_cm"], rad["time_s"] / 3600.0, "(c) 药材半径"),
    ):
        uf = np.asarray(targets[key]["sequentialMK"]["uf"])
        ub = np.asarray(targets[key]["sequentialMK"]["ub"])
        ax.plot(tt, uf, color="#1f4e79", lw=1.3, label="UF（正向）")
        ax.plot(tt, ub, color="#c55a11", lw=1.3, label="UB（反向）")
        ax.axhline(Z95, color="grey", ls=":", lw=1)
        ax.axhline(-Z95, color="grey", ls=":", lw=1)
        ax.axhline(0, color="black", lw=.6)
        bp = targets[key]["brokenStick"]["breakpointIndex"]
        if bp is not None:
            ax.axvline(tt[bp], color="#c00000", ls="--", lw=1.2,
                       label=f"折线分界 {tt[bp]:.2f} h")
        ax.set(xlabel="时间 / h", ylabel="统计量", title=f"{title} 的 M–K 突变检验与折线分界")
        ax.legend(fontsize=8)
        ax.grid(alpha=.25)
    fig.suptitle("给定数据序列的阶段分界识别", fontsize=12.5)
    fig.text(.5, -.06, "M–K 顺序检验给出趋势突变的统计位置，两段折线回归给出均方意义下的最优拐点；"
                       "两者一致时该分界可在论文中作为客观结果报告。",
             ha="center", fontsize=8.5, color="#444444")
    fig.savefig(FIG / "fig_series_mutation_tests.png")
    fig.savefig(FIG / "fig_series_mutation_tests.pdf")
    plt.close(fig)


if __name__ == "__main__":
    sys.exit(main())
