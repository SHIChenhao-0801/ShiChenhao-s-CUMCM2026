# -*- coding: utf-8 -*-
"""
sensitivity.py —— 敏感度分析与模型对比

A. 关键参数敏感度（问题3 烘干时间 T*）
     beta 对流传质系数  x {0.5, 0.75, 1.25, 2.0}
     h    对流换热系数  x {0.5, 0.75, 1.25, 2.0}
     D    水分扩散系数  x {0.5, 0.75, 1.25, 2.0}
     C_eq 空气水分浓度  x {0.8, 1.2}
B. 边界延拓口径对比（平台值 / 数据末端均值 / 指数平滑拟合）
C. 空气水分浓度基准（干基直接使用 / 由湿基换算）
D. 问题4 收缩口径对比（仿射收缩 / 忽略收缩 / 固定等效终半径）
E. 数值参数敏感度（网格 N、时间子步 sub）
"""
import os
import math
import sys
import json
import pickle

from physics import (PROPS_Q23, PROPS_Q4, OUT_DIR, C_TARGET, R0, T_inf, C_eq,
                     R_TAB, ATT1_T, ATT1_TC, ATT1_CEQ,
                     T_CHAMBER_PLATEAU_C, C_EQ_PLATEAU)
from solver import simulate, find_crossing

PKL_DIR = os.path.join(OUT_DIR, 'pkl')
OUT_JSON = os.path.join(OUT_DIR, 'sensitivity.json')

N_SENS = 200
SUB_SENS = 12
T_LIM = 600000.0
STOP = C_TARGET - 2.0e-4


def out_grid():
    return [60.0 * i for i in range(1, int(T_LIM / 60.0) + 1)]


def run_q3(props=None, N=N_SENS, sub=SUB_SENS, R_func=None, Rprime=None,
           Tinf=None, Ceq=None, h_scale=1.0, beta_scale=1.0):
    res = simulate(props or PROPS_Q23, out_grid(), N=N, sub=sub, theta=0.5,
                   R_func=R_func, Rprime_func=Rprime,
                   Tinf_func=Tinf or T_inf, Ceq_func=Ceq or C_eq,
                   stop_cmax=STOP, h_scale=h_scale, beta_scale=beta_scale)
    t = find_crossing(res, C_TARGET)
    return res, t


def scaled_props(base, dscale=1.0):
    if dscale == 1.0:
        return base
    P = type('P', (), {})()
    P.tag = '%s(D x%.2f)' % (base.tag, dscale)
    P.rho, P.cp, P.k = base.rho, base.cp, base.k
    P.D = lambda C, T: base.D(C, T) * dscale
    return P


# ----------------------------------------------------------------------
def main():
    base_res, base_t = run_q3()
    out = {'baseline': {'T_star_s': base_t, 'T_star_h': base_t / 3600.0}}
    print('基准：T* = %.2f s = %.4f h' % (base_t, base_t / 3600.0))

    rows = []

    def add(cat, name, t, note=''):
        if t is None:
            return
        rows.append(dict(cat=cat, name=name, T_star_s=t, T_star_h=t / 3600.0,
                         delta_pct=(t - base_t) / base_t * 100.0, note=note))
        print('  %-34s T*=%9.2f s (%8.4f h)  %+7.2f%% %s'
              % (name, t, t / 3600.0, (t - base_t) / base_t * 100.0, note))

    # A. 参数敏感度
    print('\n[A] 参数敏感度')
    for f in (0.5, 0.75, 1.25, 2.0):
        _, t = run_q3(beta_scale=f)
        add('beta', 'beta x%.2f' % f, t)
    for f in (0.5, 0.75, 1.25, 2.0):
        _, t = run_q3(h_scale=f)
        add('h', 'h x%.2f' % f, t)
    for f in (0.5, 0.75, 1.25, 2.0):
        _, t = run_q3(props=scaled_props(PROPS_Q23, f))
        add('D', 'D x%.2f' % f, t)
    for f in (0.8, 1.2):
        _, t = run_q3(Ceq=lambda t, f=f: C_eq(t) * f)
        add('Ceq', 'C_eq x%.2f' % f, t)

    # B. 边界延拓口径
    print('\n[B] 边界延拓口径')
    tmean = sum(ATT1_TC[-61:]) / 61.0
    cmean = sum(ATT1_CEQ[-61:]) / 61.0
    _, t = run_q3(Tinf=lambda t: _plateau(ATT1_T, ATT1_TC, t, tmean),
                  Ceq=lambda t: _plateau(ATT1_T, ATT1_CEQ, t, cmean))
    add('BC', '数据末端平台均值(%.4f C, %.5f)' % (tmean, cmean), t)

    tau_t, tau_c = 1900.0, 3100.0
    _, t = run_q3(Tinf=lambda t: 50.0 - 22.0 * math.exp(-t / tau_t),
                  Ceq=lambda t: 0.05 - 0.03037 * math.exp(-t / tau_c))
    add('BC', '指数平滑拟合', t)

    # C. 空气水分浓度基准
    print('\n[C] C_eq 基准口径')
    _, t = run_q3(Ceq=lambda t: _wet_to_dry(C_eq(t)))
    add('units', 'C_eq 由湿基换算为干基', t)

    # D. 问题4 收缩口径
    print('\n[D] 问题4 收缩口径')
    _, t4a = run_q3(props=PROPS_Q4, R_func=R_TAB)
    add('shrink', '仿射收缩（主模型）', t4a)
    _, t4b = run_q3(props=PROPS_Q4)
    add('shrink', '忽略收缩 R≡2 cm', t4b)
    Rend = R_TAB(259200.0)
    _, t4c = run_q3(props=PROPS_Q4, R_func=lambda t: Rend)
    add('shrink', '固定等效终半径 R≡%.3f cm' % (Rend * 100), t4c)
    _, t4d = run_q3(props=PROPS_Q23, R_func=R_TAB)
    add('shrink', '仅收缩、物性取附录3', t4d)

    # E. 数值参数
    print('\n[E] 数值参数敏感度（问题3）')
    for N in (100, 200, 400):
        _, t = run_q3(N=N)
        add('num', '网格 N=%d' % N, t)
    for s in (6, 12, 24):
        _, t = run_q3(sub=s)
        add('num', '时间子步 sub=%d (dt=%.1f s)' % (s, 60.0 / s), t)

    out['rows'] = rows
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('\n保存 -> %s' % OUT_JSON)

    with open(os.path.join(PKL_DIR, 'sens_base.pkl'), 'wb') as f:
        pickle.dump(base_res, f, protocol=4)


def _plateau(ts, ys, t, tail):
    import bisect
    if t >= ts[-1]:
        return tail
    i = bisect.bisect_right(ts, t) - 1
    t0, t1 = ts[i], ts[i + 1]
    w = (t - t0) / (t1 - t0)
    return ys[i] * (1 - w) + ys[i + 1] * w


def _wet_to_dry(w):
    w = min(max(w, 0.0), 0.9)
    return w / (1.0 - w)


if __name__ == '__main__':
    main()
