# -*- coding: utf-8 -*-
"""smoke.py —— 求解器冒烟测试：跑问题1 与 问题2 的开头，检查物理合理性。"""
import time
from physics import (PROPS_Q1, PROPS_Q23, R0, C_INIT, T_INIT_C, T_inf, C_eq,
                     R_TAB, R0 as R_INIT, dry_to_wet)
from solver import simulate, find_crossing

t0 = time.time()

print('===== 问题1：预热平衡阶段，0-1800 s，附录2 物性 =====')
out1 = [float(i) for i in range(1, 1801)]
r1 = simulate(PROPS_Q1, out1, N=200, sub=4, theta=0.5,
              Tinf_func=T_inf, Ceq_func=C_eq, verbose=True)
print('  壁时 %.1f s' % (time.time() - t0))
last = -1
for k in (0, 59, 299, 599, 899, 1199, 1499, 1799):
    print('  t=%5.0f s  T[中心]=%9.4f  T[表面]=%9.4f  C[中心]=%9.6f  C[表面]=%9.6f  Cmax=%.6f'
          % (r1.times[k], r1.T[k][0], r1.T[k][-1], r1.C[k][0], r1.C[k][-1], r1.Cmax[k]))

t1 = time.time()
print()
print('===== 问题2：整个烘干过程，0-10800 s，附录3 物性 =====')
out2 = [float(i) for i in range(1, 10801)]
r2 = simulate(PROPS_Q23, out2, N=200, sub=2, theta=0.5,
              Tinf_func=T_inf, Ceq_func=C_eq, verbose=True)
print('  壁时 %.1f s' % (time.time() - t1))
for k in (0, 299, 899, 1799, 3599, 5399, 7199, 8999, 10799):
    print('  t=%6.0f s  T[中心]=%9.4f  T[表面]=%9.4f  C[中心]=%9.6f  C[表面]=%9.6f  Cmax=%.6f'
          % (r2.times[k], r2.T[k][0], r2.T[k][-1], r2.C[k][0], r2.C[k][-1], r2.Cmax[k]))

print()
print('  质量守恒检验（无量纲含水量 2∫C x dx，应单调下降）：')
print('   Q1: %.8f -> %.8f' % (r1.mass[0], r1.mass[-1]))
print('   Q2: %.8f -> %.8f' % (r2.mass[0], r2.mass[-1]))
print()
print('总壁时 %.1f s' % (time.time() - t0))
