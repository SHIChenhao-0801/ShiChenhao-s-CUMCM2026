# -*- coding: utf-8 -*-
"""diag1.py —— 受控诊断：常物性 + 恒定环境温度 50°C，检验热方程求解器是否正确。
物理事实：T 必须始终落在 [28, 50] 内，且 t->inf 时趋于 50（无内热源）。"""
from physics import R0, H_CONV
from solver import simulate, Grid

P = type('P', (), {})()
P.tag = 'const'
P.rho = lambda C: 820.0
P.cp = lambda C: 2600.0
P.k = lambda C: 0.36
P.D = lambda C, T: 1e-30          # 关掉水分耦合，只看温度

Tinf = lambda t: 50.0
Ceq = lambda t: 0.0

for th, rann in ((1.0, False), (0.5, True), (0.5, False)):
    out = [float(i) for i in range(1, 301)]
    r = simulate(P, out, N=50, sub=4, theta=th, rannacher=rann,
                 Tinf_func=Tinf, Ceq_func=Ceq)
    print('theta=%.2f rannacher=%s' % (th, rann))
    for k in (0, 3, 19, 79, 199, 299):
        T = r.T[k]
        print('   t=%4.0f  Tmin=%9.4f Tmax=%9.4f  Tc=%9.4f Ts=%9.4f'
              % (r.times[k], min(T), max(T), T[0], T[-1]))
    print()

# 解析检验：无限长圆柱，恒温对流边界
print('理论解对照（Gauss 超几何级数/Bessel），Bi = hR/k = %.6f' % (H_CONV * R0 / 0.36))
