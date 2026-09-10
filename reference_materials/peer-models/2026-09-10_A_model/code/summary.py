# -*- coding: utf-8 -*-
"""summary.py —— 汇总全部关键数值结果，供撰写论文正文引用。"""
import os
import pickle
import math
import json

from physics import (OUT_DIR, C_TARGET, C_INIT, R0, L_CYL, H_CONV, BETA,
                     PROPS_Q1, PROPS_Q23, PROPS_Q4, T_inf, C_eq, R_TAB,
                     ATT1_T, ATT1_TC, ATT1_CEQ, ATT2_T, ATT2_R,
                     T_CHAMBER_PLATEAU_C, C_EQ_PLATEAU, dry_to_wet, rho_dry)
from solver import find_crossing

PKL = os.path.join(OUT_DIR, 'pkl')


def load(tag):
    with open(os.path.join(PKL, tag + '.pkl'), 'rb') as f:
        return pickle.load(f)


def at(res, t, r_cm, which='C'):
    idx = min(range(len(res.times)), key=lambda k: abs(res.times[k] - t))
    Rk = res.R[idx]
    r = r_cm * 1e-2
    if r > Rk + 1e-12:
        return None
    return res.interp_C(idx, r / Rk) if which == 'C' else res.interp_T(idx, r / Rk)


def main():
    S = {}
    q1 = load('q1_N400_sub4')
    q2 = load('q2_N400_sub2')
    q3 = load('q3_N400_sub12')
    q4 = load('q4_N400_sub12')

    t3 = find_crossing(q3, C_TARGET)
    t4 = find_crossing(q4, C_TARGET)

    S['params'] = dict(
        R0_cm=R0 * 100, L_cm=L_CYL * 100, C0=C_INIT, C_target=C_TARGET,
        w0=dry_to_wet(C_INIT), w_target=dry_to_wet(C_TARGET),
        h=H_CONV, beta=BETA,
        alpha_q1=PROPS_Q1.k(0) / (PROPS_Q1.rho(0) * PROPS_Q1.cp(0)),
        Bi_q1=H_CONV * R0 / PROPS_Q1.k(0),
        Bi_m_q1=BETA * R0 / PROPS_Q1.D(C_INIT, 301.15),
        D_q1_C0=PROPS_Q1.D(C_INIT, 301.15),
        D_q23_C0=PROPS_Q23.D(C_INIT, 301.15),
        D_q4_C0=PROPS_Q4.D(C_INIT, 301.15),
        D_q23_C015=PROPS_Q23.D(0.15, 323.15),
        tau_q1_s=R0 * R0 / (PROPS_Q1.k(0) / (PROPS_Q1.rho(0) * PROPS_Q1.cp(0))),
        tau_q23_C0_s=R0 * R0 / PROPS_Q23.D(C_INIT, 301.15),
        tau_q23_C015_s=R0 * R0 / PROPS_Q23.D(0.15, 323.15),
    )

    S['att1'] = dict(n=len(ATT1_T), t_end=ATT1_T[-1],
                     T0=ATT1_TC[0], Tend=ATT1_TC[-1], Tmax=max(ATT1_TC),
                     Ceq0=ATT1_CEQ[0], Ceqend=ATT1_CEQ[-1],
                     plateau_T=sum(ATT1_TC[-61:]) / 61.0,
                     plateau_Ceq=sum(ATT1_CEQ[-61:]) / 61.0)
    S['att2'] = dict(n=len(ATT2_T), t_end=ATT2_T[-1],
                     R0=ATT2_R[0] * 100, Rend=ATT2_R[-1] * 100,
                     ratio=ATT2_R[-1] / ATT2_R[0])

    # ---- 问题1 ----
    S['q1'] = dict(
        end_T_center=q1.T[-1][0], end_T_surface=q1.T[-1][-1],
        end_C_center=q1.C[-1][0], end_C_surface=q1.C[-1][-1],
        Cmax_end=q1.Cmax[-1],
        mass_drop=q1.mass[0] - q1.mass[-1],
        flux_C_end=q1.flux_C[-1], flux_T_end=q1.flux_T[-1],
        tbl_T=[[100, 300, 600, 900, 1200, 1500, 1800]],
    )
    S['q1']['tbl'] = {str(t): {str(rc): at(q1, t, rc, 'T') for rc in (0, 0.5, 1, 1.5, 2)}
                      for t in (100, 300, 600, 900, 1200, 1500, 1800)}
    S['q1']['tblC'] = {str(t): {str(rc): at(q1, t, rc, 'C') for rc in (0, 0.5, 1, 1.5, 2)}
                       for t in (100, 300, 600, 900, 1200, 1500, 1800)}

    # ---- 问题2 ----
    S['q2'] = dict(Cmax_end=q2.Cmax[-1],
                   end_T_center=q2.T[-1][0], end_T_surface=q2.T[-1][-1],
                   end_C_center=q2.C[-1][0], end_C_surface=q2.C[-1][-1],
                   mass_end=q2.mass[-1] / 2.0,
                   flux_C_end=q2.flux_C[-1])
    S['q2']['tbl'] = {str(h): {str(rc): at(q2, h * 3600, rc, 'T') for rc in (0, 0.5, 1, 1.5, 2)}
                      for h in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0)}
    S['q2']['tblC'] = {str(h): {str(rc): at(q2, h * 3600, rc, 'C') for rc in (0, 0.5, 1, 1.5, 2)}
                       for h in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0)}

    # ---- 问题3 ----
    S['q3'] = dict(T_star_s=t3, T_star_h=t3 / 3600.0, T_star_d=t3 / 86400.0,
                   n_snap=len(q3), t_last=q3.times[-1],
                   Cmax_end=q3.Cmax[-1],
                   rate_end=(q3.Cmax[-1] - q3.Cmax[-7]) / (q3.times[-1] - q3.times[-7]),
                   T_end_center=q3.T[-1][0], T_end_surface=q3.T[-1][-1])
    # 若干时刻的 Cmax
    S['q3']['Cmax_at'] = {str(int(t / 3600.0)): at(q3, t, 0.0, 'C') for t in
                          (3600, 21600, 43200, 86400, 129600, 172800, 216000)}
    S['q3']['tbl'] = {str(int(h)): {str(rc): at(q3, h * 3600, rc, 'C') for rc in (0, 0.5, 1, 1.5, 2)}
                      for h in range(6, int(t3 / 3600.0), 6)}
    # 干燥速率分阶段特征（按平均含水率）
    mean = [m / 2.0 for m in q3.mass]
    S['q3']['mean_C_at'] = {str(int(t / 3600.0)): mean[min(range(len(q3.times)),
                          key=lambda k: abs(q3.times[k] - t))] for t in
                          (60, 3600, 21600, 86400, t3)}

    # ---- 问题4 ----
    S['q4'] = dict(T_star_s=t4, T_star_h=t4 / 3600.0, T_star_d=t4 / 86400.0,
                   n_snap=len(q4), t_last=q4.times[-1],
                   Cmax_end=q4.Cmax[-1],
                   R_end_cm=q4.R[-1] * 100,
                   R_at_Tstar_cm=q4.R[min(range(len(q4.times)),
                                          key=lambda k: abs(q4.times[k] - t4))] * 100,
                   T_end_center=q4.T[-1][0], T_end_surface=q4.T[-1][-1])
    S['q4']['tbl'] = {str(int(h)): {str(rc): at(q4, h * 3600, rc, 'C') for rc in (0, 0.5, 1, 1.5, 2)}
                      for h in range(6, int(t4 / 3600.0), 6)}
    S['compare'] = dict(
        ratio_pct=(t3 - t4) / t3 * 100.0,
        D_ratio_at_C015=PROPS_Q4.D(0.15, 323.15) / PROPS_Q23.D(0.15, 323.15),
        R2_ratio=(ATT2_R[-1] / ATT2_R[0]) ** 2,
    )

    # ---- 收敛性（若已算完）----
    for tag in ('q1', 'q2'):
        try:
            a = load('%s_N200_%s' % (tag, 'sub4' if tag == 'q1' else 'sub2'))
            b = load('%s_N400_%s' % (tag, 'sub4' if tag == 'q1' else 'sub2'))
            S.setdefault('conv', {})[tag] = dict(
                N200=[a.T[-1][0], a.T[-1][-1], a.C[-1][0], a.C[-1][-1]],
                N400=[b.T[-1][0], b.T[-1][-1], b.C[-1][0], b.C[-1][-1]])
        except Exception:
            pass

    path = os.path.join(OUT_DIR, 'summary.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(S, f, ensure_ascii=False, indent=1, default=str)

    def p(k, v):
        print('%-34s %s' % (k, v))

    print('=' * 74)
    print('参数与派生量')
    for k, v in S['params'].items():
        p(k, ('%.6g' % v) if isinstance(v, float) else v)
    print('-' * 74)
    print('附件1');  [p(k, v) for k, v in S['att1'].items()]
    print('附件2');  [p(k, v) for k, v in S['att2'].items()]
    print('-' * 74)
    print('问题1 (t=1800 s)')
    for k in ('end_T_center', 'end_T_surface', 'end_C_center', 'end_C_surface',
              'Cmax_end', 'mass_drop', 'flux_C_end'):
        p(k, '%.6g' % S['q1'][k])
    print('-' * 74)
    print('问题2 (t=10800 s)')
    for k in ('end_T_center', 'end_T_surface', 'end_C_center', 'end_C_surface',
              'Cmax_end', 'mass_end', 'flux_C_end'):
        p(k, '%.6g' % S['q2'][k])
    print('-' * 74)
    print('问题3')
    for k in ('T_star_s', 'T_star_h', 'T_star_d', 't_last', 'Cmax_end', 'rate_end'):
        p(k, '%.6g' % S['q3'][k])
    print('-' * 74)
    print('问题4')
    for k in ('T_star_s', 'T_star_h', 'T_star_d', 't_last', 'Cmax_end',
              'R_end_cm', 'R_at_Tstar_cm'):
        p(k, '%.6g' % S['q4'][k])
    print('-' * 74)
    print('对比')
    for k, v in S['compare'].items():
        p(k, '%.6g' % v)
    print('=' * 74)
    print('保存 ->', path)


if __name__ == '__main__':
    main()
