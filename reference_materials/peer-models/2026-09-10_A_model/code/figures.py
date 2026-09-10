# -*- coding: utf-8 -*-
"""
figures.py —— 生成全部论文插图（矢量 SVG）

依赖 svgplot.py，数据来自 out/pkl/*.pkl
"""
import os
import pickle
import math
import sys

from physics import (OUT_DIR, FIG_DIR, C_TARGET, C_INIT, R0, L_CYL, H_CONV, BETA,
                     PROPS_Q1, PROPS_Q23, PROPS_Q4, T_INF_TAB, C_EQ_TAB,
                     ATT1_T, ATT1_TC, ATT1_CEQ, T_inf, C_eq, R_TAB,
                     T_CHAMBER_PLATEAU_C, C_EQ_PLATEAU, dry_to_wet)
from solver import find_crossing
from svgplot import Plot, heatmap_svg, PALETTE

PKL_DIR = os.path.join(OUT_DIR, 'pkl')
RAD_CM = [round(i * 0.1, 10) for i in range(21)]
MADE = []


def load(q, N=400, sub=None):
    if sub is None:
        sub = {1: 4, 2: 2, 3: 12, 4: 12}[q]
    p = os.path.join(PKL_DIR, 'q%d_N%d_sub%d.pkl' % (q, N, sub))
    if not os.path.exists(p):
        N = 200
        p = os.path.join(PKL_DIR, 'q%d_N%d_sub%d.pkl' % (q, N, sub))
    with open(p, 'rb') as f:
        return pickle.load(f), N


def save(p, name):
    d = os.path.dirname(os.path.abspath(p))
    os.makedirs(d, exist_ok=True)
    MADE.append((name, p))
    return p


def prof(res, k, which='T', rmax_cm=2.0):
    """把快照 k 映射到物理半径 r(cm) 上的剖面（考虑收缩）。"""
    Rk = res.R[k]
    n = len(res.x)
    xs, ys = [], []
    for j in range(n):
        r_cm = res.x[j] * Rk * 100.0
        if r_cm > rmax_cm + 1e-9:
            break
        xs.append(r_cm)
        ys.append(res.T[k][j] if which == 'T' else res.C[k][j])
    return xs, ys


# ======================================================================
def fig01_conditions():
    """附件1 烘房条件 + 两阶段划分"""
    p = Plot(820, 470, title='图1  烘房温度与空气水分浓度（附件1）',
             xlabel='时间 t / h', ylabel='烘房温度 T∞ / °C',
             ylabel2='空气水分浓度 C_eq / (kg/kg)', xlim=(0, 4.6))
    ts = [t / 3600.0 for t in ATT1_T]
    p.add(ts, ATT1_TC, label='烘房温度 T∞(t)', color='#c0392b', width=2.2)
    p.add(ts, ATT1_CEQ, label='空气水分浓度 C_eq(t)', color='#1f4e9c', width=2.2, axis=2)
    p.vline(10800 / 3600.0, color='#777', label='10800 s 起进入恒温段')
    p.hline(T_CHAMBER_PLATEAU_C, color='#c0392b', dash='6,4', axis=1, label='50.00 °C')
    p.hline(C_EQ_PLATEAU, color='#1f4e9c', dash='6,4', axis=2, label='0.0500')
    p.text(0.35, 30.5, '预热平衡阶段', color='#333', size=13)
    p.text(3.05, 30.5, '恒温干燥阶段', color='#333', size=13)
    return save(p.save(os.path.join(FIG_DIR, 'fig01_chamber_conditions.svg')), '图1 烘房条件')


def fig02_q1_T_profiles(res):
    ts = [100, 300, 600, 900, 1200, 1500, 1800]
    p = Plot(800, 480, title='图2  问题1 药材温度径向剖面（预热平衡阶段）',
             xlabel='到药材中心的距离 r / cm', ylabel='温度 T / °C', xlim=(0, 2.0))
    idx = {int(round(t)): k for k, t in enumerate(res.times)}
    for i, t in enumerate(ts):
        xs, ys = prof(res, idx[t], 'T')
        p.add(xs, ys, label='t = %d s' % t, color=PALETTE[i % len(PALETTE)], width=2.0)
    return save(p.save(os.path.join(FIG_DIR, 'fig02_q1_T_profiles.svg')), '图2 Q1温度剖面')


def fig03_q1_C_profiles(res):
    ts = [100, 300, 600, 900, 1200, 1500, 1800]
    p = Plot(800, 480, title='图3  问题1 药材水分浓度径向剖面（预热平衡阶段）',
             xlabel='到药材中心的距离 r / cm', ylabel='干基含水率 C / (kg/kg)', xlim=(0, 2.0))
    idx = {int(round(t)): k for k, t in enumerate(res.times)}
    for i, t in enumerate(ts):
        xs, ys = prof(res, idx[t], 'C')
        p.add(xs, ys, label='t = %d s' % t, color=PALETTE[i % len(PALETTE)], width=2.0)
    p.hline(C_INIT, color='#999', dash='4,3', label='初始 2.55')
    return save(p.save(os.path.join(FIG_DIR, 'fig03_q1_C_profiles.svg')), '图3 Q1水分剖面')


def fig04_q1_history(res):
    p = Plot(820, 470, title='图4  问题1 中心与表面的温度、水分随时间变化',
             xlabel='时间 t / s', ylabel='温度 T / °C',
             ylabel2='干基含水率 C / (kg/kg)', xlim=(0, 1800))
    ts = res.times
    Tc = [res.T[k][0] for k in range(len(ts))]
    Ts = [res.T[k][-1] for k in range(len(ts))]
    Cc = [res.C[k][0] for k in range(len(ts))]
    Cs = [res.C[k][-1] for k in range(len(ts))]
    p.add(ts, Tc, label='中心温度 T(r=0)', color='#1f4e9c', width=2.2)
    p.add(ts, Ts, label='表面温度 T(r=2cm)', color='#c0392b', width=2.2)
    p.add(ts, Cc, label='中心含水率 C(r=0)', color='#1e8449', width=2.0, dash='7,4', axis=2)
    p.add(ts, Cs, label='表面含水率 C(r=2cm)', color='#b7791f', width=2.0, dash='7,4', axis=2)
    return save(p.save(os.path.join(FIG_DIR, 'fig04_q1_history.svg')), '图4 Q1时间演化')


def fig05_verification():
    """数值解 vs Duhamel-Bessel 解析解 + 误差"""
    from analytic import CylinderConduction, piecewise_linear_derivative
    from physics import T_INIT_C
    from verify import _delta_prime_table
    q1, _ = load(1)
    alpha = PROPS_Q1.k(0) / (PROPS_Q1.rho(0) * PROPS_Q1.cp(0))
    Bi = H_CONV * R0 / PROPS_Q1.k(0)
    ana = CylinderConduction(alpha, R0, Bi, n_terms=40, z_max=100.0)
    dts, slopes = _delta_prime_table()
    idx = {int(round(t)): k for k, t in enumerate(q1.times)}

    check_t = list(range(20, 1801, 20))
    errs = {r: [] for r in (0.0, 1.0, 2.0)}
    for t in check_t:
        k = idx[t]
        for r_cm in (0.0, 1.0, 2.0):
            x = r_cm * 1e-2 / R0
            Ta = T_INIT_C + ana.duhamel(x, t, dts, slopes)
            Tn = q1.interp_T(k, min(x, 1.0))
            errs[r_cm].append(abs(Ta - Tn))

    p = Plot(800, 430, title='图5  问题1 数值解与解析解的偏差（Duhamel–Bessel 级数）',
             xlabel='时间 t / s', ylabel='绝对偏差 |T_数值 − T_解析| / °C',
             ylim=(1e-7, 1e-2), logy=True)
    for i, r in enumerate((0.0, 1.0, 2.0)):
        p.add(check_t, errs[r], label='r = %g cm' % r, color=PALETTE[i], width=1.9)
    p.hline(1e-4, color='#c0392b', dash='5,4', label='四位小数报告精度 1e-4')
    return save(p.save(os.path.join(FIG_DIR, 'fig05_verification.svg')), '图5 解析校核')


def fig06_q2_T_profiles(res):
    ts = [300, 900, 1800, 3600, 5400, 7200, 9000, 10800]
    p = Plot(800, 480, title='图6  问题2 药材温度径向剖面（0—3 h）',
             xlabel='到药材中心的距离 r / cm', ylabel='温度 T / °C', xlim=(0, 2.0))
    idx = {int(round(t)): k for k, t in enumerate(res.times)}
    for i, t in enumerate(ts):
        xs, ys = prof(res, idx[t], 'T')
        p.add(xs, ys, label='%g h' % (t / 3600.0), color=PALETTE[i % len(PALETTE)], width=2.0)
    return save(p.save(os.path.join(FIG_DIR, 'fig06_q2_T_profiles.svg')), '图6 Q2温度剖面')


def fig07_q2_C_profiles(res):
    ts = [300, 900, 1800, 3600, 5400, 7200, 9000, 10800]
    p = Plot(800, 480, title='图7  问题2 药材水分浓度径向剖面（0—3 h）',
             xlabel='到药材中心的距离 r / cm', ylabel='干基含水率 C / (kg/kg)', xlim=(0, 2.0))
    idx = {int(round(t)): k for k, t in enumerate(res.times)}
    for i, t in enumerate(ts):
        xs, ys = prof(res, idx[t], 'C')
        p.add(xs, ys, label='%g h' % (t / 3600.0), color=PALETTE[i % len(PALETTE)], width=2.0)
    return save(p.save(os.path.join(FIG_DIR, 'fig07_q2_C_profiles.svg')), '图7 Q2水分剖面')


def fig08_q2_history(res):
    p = Plot(820, 470, title='图8  问题2 中心与表面的温度、水分随时间变化（0—3 h）',
             xlabel='时间 t / h', ylabel='温度 T / °C',
             ylabel2='干基含水率 C / (kg/kg)', xlim=(0, 3.0))
    th = [t / 3600.0 for t in res.times]
    p.add(th, [res.T[k][0] for k in range(len(th))], label='中心温度', color='#1f4e9c', width=2.2)
    p.add(th, [res.T[k][-1] for k in range(len(th))], label='表面温度', color='#c0392b', width=2.2)
    p.add(th, [res.C[k][0] for k in range(len(th))], label='中心含水率', color='#1e8449',
          width=2.0, dash='7,4', axis=2)
    p.add(th, [res.C[k][-1] for k in range(len(th))], label='表面含水率', color='#b7791f',
          width=2.0, dash='7,4', axis=2)
    return save(p.save(os.path.join(FIG_DIR, 'fig08_q2_history.svg')), '图8 Q2时间演化')


def fig09_drying_rate(res, tag, fname, tmax_h=None):
    """干燥速率 - 平均含水率 特征曲线 + 表面通量时间曲线"""
    idx_end = len(res.times) - 1
    mean = [res.mass[k] / 2.0 for k in range(len(res.times))]
    th = [t / 3600.0 for t in res.times]
    # 数值微分求干燥速率 dM/dt（每单位外表面积，kg/(m^2 s)）
    rate = []
    for k in range(len(res.times)):
        k0 = max(0, k - 1)
        k1 = min(len(res.times) - 1, k + 1)
        dt = res.times[k1] - res.times[k0]
        if dt <= 0:
            rate.append(None)
            continue
        # 单位长度水质量 = pi rho_d R^2 * M ; 面积 = 2 pi R
        rho_d = PROPS_Q23.rho(mean[k]) / (1.0 + mean[k])
        dM = (mean[k1] - mean[k0]) / dt
        Rk = res.R[k]
        rate.append(dM * rho_d * Rk / 2.0)
    p = Plot(800, 450, title='图9  %s 干燥速率特征曲线' % tag,
             xlabel='平均干基含水率 C_avg / (kg/kg)',
             ylabel='干燥速率 (−dM_w/dt)/A / (kg/(m²·s))',
             xlim=(0, 2.6), logy=False)
    xs = [mean[k] for k in range(len(mean)) if rate[k] is not None]
    ys = [rate[k] for k in range(len(rate)) if rate[k] is not None]
    p.add(xs, ys, label='干燥速率', color='#1f4e9c', width=2.2)
    p.vline(dry_to_wet(0.15) * 0 + 0.15, color='#c0392b', label='C = 0.15 判据')
    return save(p.save(os.path.join(FIG_DIR, fname)), '图9 ' + tag + '干燥速率')


def fig10_q3_cmax(res):
    tc = find_crossing(res, C_TARGET)
    p = Plot(820, 470, title='图10  问题3 全域含水率指标随时间变化',
             xlabel='时间 t / h', ylabel='干基含水率 C / (kg/kg)',
             xlim=(0, res.times[-1] / 3600.0))
    th = [t / 3600.0 for t in res.times]
    p.add(th, res.Cmax, label='全域最大值 C_max', color='#c0392b', width=2.3)
    p.add(th, res.Cmin, label='全域最小值 C_min', color='#1f4e9c', width=1.8)
    p.add(th, [v / 2.0 for v in res.mass], label='截面平均 C_avg', color='#1e8449', width=2.0, dash='6,3')
    p.hline(C_TARGET, color='#333', dash='5,4', label='烘干判据 0.15')
    if tc:
        p.vline(tc / 3600.0, color='#6c3483', label='T* = %.2f h' % (tc / 3600.0))
    return save(p.save(os.path.join(FIG_DIR, 'fig10_q3_cmax.svg')), '图10 Q3含水率指标')


def fig11_field(res, which, fname, title, cblabel, tmax_h=None, nlev=9, rmax_cm=2.0):
    """r–t 等值线图（考虑收缩：r > R(t) 处留白）"""
    nT = 160
    nr = 41
    Rmax = max(res.R)
    ts = [res.times[0] + (res.times[-1] - res.times[0]) * i / float(nT - 1) for i in range(nT)]
    rs_cm = [rmax_cm * i / float(nr - 1) for i in range(nr)]
    zs = []
    import bisect
    for r_cm in rs_cm:
        row = []
        r = r_cm * 1e-2
        for t in ts:
            k = bisect.bisect_left(res.times, t)
            k = min(max(k, 0), len(res.times) - 1)
            Rk = res.R[k]
            if r > Rk + 1e-12:
                row.append(None)
            else:
                xq = r / Rk
                row.append(res.interp_T(k, xq) if which == 'T' else res.interp_C(k, xq))
        zs.append(row)
    vmin = min(v for row in zs for v in row if v is not None)
    vmax = max(v for row in zs for v in row if v is not None)
    levels = [vmin + (vmax - vmin) * (i + 1) / (nlev + 1) for i in range(nlev)]
    path = os.path.join(FIG_DIR, fname)
    heatmap_svg(path, [t / 3600.0 for t in ts], rs_cm, zs, title=title,
                xlabel='时间 t / h', ylabel='到药材中心的距离 r / cm',
                cblabel=cblabel, levels=levels)
    return save(path, title)


def fig14_R(res):
    from physics import ATT2_T, ATT2_R
    tmax_h = ATT2_T[-1] / 3600.0
    t4 = find_crossing(res, C_TARGET)
    p = Plot(780, 420, title='图14  附件2 药材半径随时间的变化（收缩规律）',
             xlabel='时间 t / h', ylabel='药材半径 R / cm', xlim=(0, tmax_h))
    p.add([t / 3600.0 for t in ATT2_T], [v * 100.0 for v in ATT2_R],
          label='附件2 实测半径 R(t)', color='#c0392b', width=2.2, marker='o')
    p.add([t / 3600.0 for t in res.times], [R * 100.0 for R in res.R],
          label='模型采用 R(t)（线性插值）', color='#1f4e9c', width=1.6, dash='5,3')
    p.hline(1.198, color='#777', dash='4,3', label='终值 1.198 cm')
    if t4:
        p.vline(t4 / 3600.0, color='#6c3483', label='T*₄ = %.2f h' % (t4 / 3600.0))
    return save(p.save(os.path.join(FIG_DIR, 'fig14_R_shrinkage.svg')), '图14 收缩曲线')


ATT2_CACHE = {}


def ATT2_T_global():
    from physics import ATT2_T
    return ATT2_T


def ATT2_R_global():
    from physics import ATT2_R
    return ATT2_R


def fig16_compare(q3, q4):
    t3 = find_crossing(q3, C_TARGET)
    t4 = find_crossing(q4, C_TARGET)
    p = Plot(820, 470, title='图16  问题3 与问题4 全域最大含水率对比',
             xlabel='时间 t / h', ylabel='全域最大干基含水率 C_max / (kg/kg)',
             xlim=(0, max(q3.times[-1], q4.times[-1]) / 3600.0))
    p.add([t / 3600.0 for t in q3.times], q3.Cmax, label='问题3 无收缩', color='#1f4e9c', width=2.2)
    p.add([t / 3600.0 for t in q4.times], q4.Cmax, label='问题4 含收缩', color='#c0392b', width=2.2)
    p.hline(C_TARGET, color='#333', dash='5,4', label='判据 0.15')
    if t3:
        p.vline(t3 / 3600.0, color='#1f4e9c', label='T*₃ = %.2f h' % (t3 / 3600.0))
    if t4:
        p.vline(t4 / 3600.0, color='#c0392b', label='T*₄ = %.2f h' % (t4 / 3600.0))
    return save(p.save(os.path.join(FIG_DIR, 'fig16_q3_vs_q4.svg')), '图16 Q3/Q4对比')


def main():
    os.makedirs(FIG_DIR, exist_ok=True)
    q1, n1 = load(1)
    q2, n2 = load(2)
    q3, n3 = load(3)
    q4, n4 = load(4)
    print('载入: Q1 N=%d  Q2 N=%d  Q3 N=%d  Q4 N=%d' % (n1, n2, n3, n4))

    fig01_conditions()
    fig02_q1_T_profiles(q1)
    fig03_q1_C_profiles(q1)
    fig04_q1_history(q1)
    fig05_verification()
    fig06_q2_T_profiles(q2)
    fig07_q2_C_profiles(q2)
    fig08_q2_history(q2)
    fig09_drying_rate(q3, '问题3', 'fig09_q3_drying_rate.svg')
    fig10_q3_cmax(q3)
    fig11_field(q2, 'T', 'fig11_q2_field_T.svg', '图11  问题2 温度场 r–t 等值线图', 'T / °C')
    fig11_field(q2, 'C', 'fig12_q2_field_C.svg', '图12  问题2 水分场 r–t 等值线图', 'C / (kg/kg)')
    fig11_field(q3, 'C', 'fig13_q3_field_C.svg', '图13  问题3 水分场 r–t 等值线图（全过程）', 'C / (kg/kg)')
    fig14_R(q4)
    fig11_field(q4, 'C', 'fig15_q4_field_C.svg',
                '图15  问题4 水分场 r–t 等值线图（含收缩，空白处已无材料）', 'C / (kg/kg)')
    fig16_compare(q3, q4)

    print()
    print('共生成 %d 张插图：' % len(MADE))
    for name, p in MADE:
        print('  %-28s %s' % (name, os.path.basename(p)))


if __name__ == '__main__':
    main()
