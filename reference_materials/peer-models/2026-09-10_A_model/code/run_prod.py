# -*- coding: utf-8 -*-
"""
run_prod.py —— 四问生产计算调度

用法：  python run_prod.py <q> [N] [sub]
        q = 1|2|3|4
结果以 pickle 存入 out/pkl/q{q}.pkl

时间步与网格设置依据（见 verify.py 的收敛性研究）：
    N 取 20 的倍数，保证结果要求的 0.1 cm 取样点恰为网格节点
    θ = 0.5（Crank-Nicolson）+ Rannacher 启动，时间二阶精度
"""
import os
import sys
import time
import pickle

from physics import (PROPS_Q1, PROPS_Q23, PROPS_Q4, T_inf, C_eq, R_TAB,
                     OUT_DIR, C_TARGET, R0)
from solver import simulate, find_crossing

PKL_DIR = os.path.join(OUT_DIR, 'pkl')

# 结果要求的取样半径：0, 0.1, ..., 2.0 cm，共 21 点。
# 取 N 为 20 的倍数时，这些点恰为网格节点，索引步长 = N/20。
KEEP_STRIDE_DIV = 20


def keep_nodes(N):
    s = N // KEEP_STRIDE_DIV
    return list(range(0, N + 1, s))


def q1(N=200, sub=4):
    out = [float(i) for i in range(1, 1801)]
    return simulate(PROPS_Q1, out, N=N, sub=sub, theta=0.5,
                    Tinf_func=T_inf, Ceq_func=C_eq, keep_nodes=keep_nodes(N))


def q2(N=200, sub=2):
    out = [float(i) for i in range(1, 10801)]
    return simulate(PROPS_Q23, out, N=N, sub=sub, theta=0.5,
                    Tinf_func=T_inf, Ceq_func=C_eq, keep_nodes=keep_nodes(N))


def q3(N=200, sub=12, t_lim=600000.0):
    out = [60.0 * i for i in range(1, int(t_lim / 60.0) + 1)]
    # 停止阈值取略严于 0.15：保证结果文件末行四位小数显示仍严格 < 0.15，
    # 真正的烘干判据时刻 T* 由 find_crossing(res, 0.15) 高精度插值给出。
    return simulate(PROPS_Q23, out, N=N, sub=sub, theta=0.5,
                    Tinf_func=T_inf, Ceq_func=C_eq,
                    stop_cmax=C_TARGET - 2.0e-4, keep_nodes=keep_nodes(N))


def q4(N=200, sub=12, t_lim=600000.0):
    out = [60.0 * i for i in range(1, int(t_lim / 60.0) + 1)]
    return simulate(PROPS_Q4, out, N=N, sub=sub, theta=0.5,
                    R_func=R_TAB, Rprime_func=None,
                    Tinf_func=T_inf, Ceq_func=C_eq,
                    stop_cmax=C_TARGET - 2.0e-4, keep_nodes=keep_nodes(N))


FUNCS = {'1': q1, '2': q2, '3': q3, '4': q4}


def main():
    q = sys.argv[1]
    N = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    sub = int(sys.argv[3]) if len(sys.argv) > 3 else None
    os.makedirs(PKL_DIR, exist_ok=True)
    t0 = time.time()
    if sub is None:
        res = FUNCS[q](N=N)
    else:
        res = FUNCS[q](N=N, sub=sub)
    el = time.time() - t0
    tag = 'q%s_N%d_sub%s' % (q, N, res.meta['sub'])
    path = os.path.join(PKL_DIR, tag + '.pkl')
    with open(path, 'wb') as f:
        pickle.dump(res, f, protocol=4)
    tc = find_crossing(res, C_TARGET)
    print('Q%s  N=%d sub=%d  snapshots=%d  用时 %.1f s' % (q, N, res.meta['sub'], len(res), el))
    print('   末态 Cmax=%.8f  烘干结束时刻 T*=%.3f s = %.4f h' %
          (res.Cmax[-1], tc if tc else float('nan'), (tc / 3600.0) if tc else float('nan')))
    print('   末态 T: 中心 %.4f 表面 %.4f   R_end=%.6f m' %
          (res.T[-1][0], res.T[-1][-1], res.R[-1]))
    print('   保存 -> %s' % path)


if __name__ == '__main__':
    main()
