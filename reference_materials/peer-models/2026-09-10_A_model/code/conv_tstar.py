# -*- coding: utf-8 -*-
"""
conv_tstar.py —— 烘干时间 T* 的收敛性研究

物理背景：判据 C_max<0.15 在干燥末期才被满足，而该阶段 dC_max/dt ~ -3e-7 /s
（特征时间 R^2/D ~ 5e5 s），因此 C_max 的微小离散误差会被放大为 T* 的显著偏差。
本脚本用多个网格 N 与时间子步 sub 量化该放大，并做 Richardson 外推。
"""
import os
import sys
import pickle

from physics import PROPS_Q23, PROPS_Q4, OUT_DIR, C_TARGET, T_inf, C_eq, R_TAB
from solver import simulate, find_crossing

PKL_DIR = os.path.join(OUT_DIR, 'pkl')
STOP = C_TARGET - 2.0e-4
T_LIM = 600000.0


def grid():
    return [60.0 * i for i in range(1, int(T_LIM / 60.0) + 1)]


def run(q, N, sub=12):
    props = PROPS_Q23 if q == 3 else PROPS_Q4
    Rf = None if q == 3 else R_TAB
    res = simulate(props, grid(), N=N, sub=sub, theta=0.5, R_func=Rf,
                   Tinf_func=T_inf, Ceq_func=C_eq, stop_cmax=STOP)
    t = find_crossing(res, C_TARGET)
    # 记录 Cmax 出现的位置（应在中心 r=0）
    jm = res.Cmax.index(max(res.Cmax))
    return t, res


def main():
    q = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    res_rows = []

    print('=== 空间收敛性（sub=12, dt=5 s, 问题%d）===' % q)
    print('   %6s %14s %14s %14s' % ('N', 'T*/s', 'T*/h', '相对 N=1600 的偏差'))
    for N in (100, 200, 400, 800):
        t, r = run(q, N)
        res_rows.append(('N', N, t))
        print('   %6d %14.2f %14.5f' % (N, t, t / 3600.0))

    ts = [r[2] for r in res_rows]
    # Richardson 外推（假定二阶）
    if len(ts) >= 3:
        t_exact = ts[-1] + (ts[-1] - ts[-2]) / 3.0
        print('   二阶 Richardson 外推 (N=800,1600)：T* = %.2f s = %.5f h'
              % (t_exact, t_exact / 3600.0))
    # 拟合收敛阶
    import math
    for i in range(len(ts) - 2):
        e1 = ts[i] - ts[i + 1]
        e2 = ts[i + 1] - ts[i + 2]
        if e2 != 0 and e1 * e2 > 0:
            print('   N=%d->%d->%d 收敛阶 p = %.4f'
                  % (res_rows[i][1], res_rows[i + 1][1], res_rows[i + 2][1],
                     math.log(abs(e1 / e2)) / math.log(2.0)))

    print()
    print('=== 时间步收敛性（N=200, 问题%d）===' % q)
    for sub in (3, 6, 12, 24):
        t, r = run(q, 200, sub=sub)
        print('   sub=%3d (dt=%5.1f s)  T* = %12.2f s = %.5f h' % (sub, 60.0 / sub, t, t / 3600.0))

    with open(os.path.join(PKL_DIR, 'conv_tstar_q%d.pkl' % q), 'wb') as f:
        pickle.dump(res_rows, f)


if __name__ == '__main__':
    main()
