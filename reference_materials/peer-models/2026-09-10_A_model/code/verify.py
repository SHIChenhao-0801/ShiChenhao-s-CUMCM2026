# -*- coding: utf-8 -*-
"""
verify.py —— 数值求解器的独立验证套件

V1  问题1 温度场：数值解 vs Duhamel-Bessel 解析解（真实附件1 边界数据）
V2  常扩散系数水分问题：数值解 vs 解析解（校核水分方程与传质边界）
V3  质量守恒：全域含水量变化 vs 表面通量积分
V4  网格/时间步收敛性：Richardson 外推与收敛阶
V5  端面效应：一维径向近似 vs 有限长圆柱乘积解析解
"""
import math
import sys

from physics import (PROPS_Q1, PROPS_Q23, R0, L_CYL, H_CONV, BETA, C_INIT,
                     T_INIT_C, T_inf, C_eq, ATT1_T, ATT1_TC)
from solver import simulate
from analytic import CylinderConduction, piecewise_linear_derivative

RADII_CM = [i * 0.1 for i in range(21)]


def _delta_prime_table():
    """附件1 的 Delta(t)=T_inf(t)-T_init 分段线性导数（t>14400 后斜率 0）。"""
    ts = list(ATT1_T) + [ATT1_T[-1] + 1e6]
    ys = [v - T_INIT_C for v in ATT1_TC]
    ys.append(ys[-1])
    return piecewise_linear_derivative(ts, ys)


# ----------------------------------------------------------------------
# V1：问题1 温度场解析校核
# ----------------------------------------------------------------------
def v1(N=200, sub=4, verbose=True):
    alpha = PROPS_Q1.k(0) / (PROPS_Q1.rho(0) * PROPS_Q1.cp(0))
    Bi = H_CONV * R0 / PROPS_Q1.k(0)
    ana = CylinderConduction(alpha, R0, Bi, n_terms=40, z_max=100.0)
    dts, slopes = _delta_prime_table()

    out = [float(i) for i in range(1, 1801)]
    num = simulate(PROPS_Q1, out, N=N, sub=sub, theta=0.5,
                   Tinf_func=T_inf, Ceq_func=C_eq)

    check_t = [60.0, 120.0, 300.0, 600.0, 900.0, 1200.0, 1500.0, 1800.0]
    rows = []
    maxerr = 0.0
    for t in check_t:
        k = min(int(t) - 1, len(num.times) - 1)
        t_act = num.times[k]
        for r_cm in RADII_CM:
            x = r_cm * 1e-2 / R0
            Ta = T_INIT_C + ana.duhamel(x, t_act, dts, slopes)
            Tn = num.interp_T(k, min(x, 1.0))
            err = abs(Ta - Tn)
            maxerr = max(maxerr, err)
            rows.append((t_act, r_cm, Tn, Ta, err))
    if verbose:
        print('=== V1  问题1 温度：数值 vs Duhamel-Bessel 解析 ===')
        print('    参数  alpha=%.10e  Bi=%.8f' % (alpha, Bi))
        print('    最大绝对误差 = %.3e °C  （全部 %d 个校核点）' % (maxerr, len(rows)))
        print('    %8s %6s %14s %14s %12s' % ('t/s', 'r/cm', 'T_numeric', 'T_analytic', 'error'))
        for (t, r, Tn, Ta, e) in rows:
            if r in (0.0, 0.5, 1.0, 1.5, 2.0) and t in (300.0, 900.0, 1800.0):
                print('    %8.1f %6.1f %14.8f %14.8f %12.3e' % (t, r, Tn, Ta, e))
    return maxerr, rows


# ----------------------------------------------------------------------
# V2：常扩散系数水分问题解析校核
# ----------------------------------------------------------------------
def v2(N=200, sub=4, Dconst=4.94e-9, verbose=True):
    """把 D 固定为常数、C_eq 固定为常数，构造有解析解的线性问题。"""
    P = type('P', (), {})()
    P.tag = 'linear-mass'
    P.rho = lambda C: 820.0
    P.cp = lambda C: 2600.0
    P.k = lambda C: 0.36
    P.D = lambda C, T: Dconst

    Ceq0 = 0.05
    Bi_m = BETA * R0 / Dconst
    ana = CylinderConduction(Dconst, R0, Bi_m, n_terms=40, z_max=100.0)
    delta = Ceq0 - C_INIT

    out = [float(i) for i in range(1, 1801)]
    num = simulate(P, out, N=N, sub=sub, theta=0.5,
                   Tinf_func=lambda t: 28.0, Ceq_func=lambda t: Ceq0)

    maxerr = 0.0
    rows = []
    for t in (60.0, 300.0, 900.0, 1800.0):
        k = min(int(t) - 1, len(num.times) - 1)
        Fo = Dconst * num.times[k] / (R0 * R0)
        for r_cm in RADII_CM:
            x = r_cm * 1e-2 / R0
            Ca = C_INIT + delta * ana.phi(x, Fo)
            Cn = num.interp_C(k, min(x, 1.0))
            e = abs(Ca - Cn)
            maxerr = max(maxerr, e)
            rows.append((num.times[k], r_cm, Cn, Ca, e))
    if verbose:
        print()
        print('=== V2  线性水分问题：数值 vs 解析（D=%.4e 常数, Bi_m=%.6f） ===' % (Dconst, Bi_m))
        print('    最大绝对误差 = %.3e kg/kg' % maxerr)
        for (t, r, Cn, Ca, e) in rows:
            if r in (0.0, 1.0, 2.0):
                print('    t=%7.1f r=%4.1f  numeric=%.8f  analytic=%.8f  err=%.3e' % (t, r, Cn, Ca, e))
    return maxerr, rows


# ----------------------------------------------------------------------
# V3：质量守恒（真实非线性问题）
# ----------------------------------------------------------------------
def v3(props=PROPS_Q1, N=200, sub=4, t_end=1800.0, R_func=None, verbose=True):
    """
    离散格式守恒性：R^2 (M^{n+1}-M^n)/dt = Psi_{N+1/2} = -R beta (C_s - C_eq)
    即  dM/dt = -2 beta (C_s - C_eq)/R ，M = 2*Int C x dx。
    逐区间以梯形法累加表面通量，与实际 M 变化比较。
    """
    out = [float(i) for i in range(1, int(t_end) + 1)]
    r = simulate(props, out, N=N, sub=sub, theta=0.5,
                 Tinf_func=T_inf, Ceq_func=C_eq, R_func=R_func)
    acc = r.mass[0]
    worst = 0.0
    for k in range(1, len(r.times)):
        t0, t1 = r.times[k - 1], r.times[k]
        dt = t1 - t0
        f0 = -2.0 * BETA * (r.C[k - 1][-1] - C_eq(t0)) / r.R[k - 1]
        f1 = -2.0 * BETA * (r.C[k][-1] - C_eq(t1)) / r.R[k]
        acc += 0.5 * (f0 + f1) * dt
        worst = max(worst, abs(acc - r.mass[k]))
    if verbose:
        print()
        print('=== V3  质量守恒校验（%s） ===' % props.tag)
        print('    M(t=0)          = %.10f' % r.mass[0])
        print('    M(t=end) 数值    = %.10f' % r.mass[-1])
        print('    M(t=end) 通量积分 = %.10f' % acc)
        print('    最大偏差 = %.3e （相对 %.3e）' % (worst, worst / r.mass[0]))
    return worst, r


# ----------------------------------------------------------------------
# V4：收敛性（Richardson 外推）
# ----------------------------------------------------------------------
def v4(verbose=True):
    out = [float(i) for i in range(1, 1801)]
    ref = {}
    for N in (50, 100, 200, 400):
        r = simulate(PROPS_Q1, out, N=N, sub=4, theta=0.5,
                     Tinf_func=T_inf, Ceq_func=C_eq)
        k = len(r.times) - 1
        ref[N] = (r.T[k][0], r.T[k][-1])
    if verbose:
        print()
        print('=== V4a  空间收敛性（问题1, t=1800 s） ===')
        print('    %6s %18s %18s' % ('N', 'T(r=0)', 'T(r=2cm)'))
        for N in (50, 100, 200, 400):
            print('    %6d %18.12f %18.12f' % (N, ref[N][0], ref[N][1]))
        for a, b, c in ((50, 100, 200), (100, 200, 400)):
            for i in (0, 1):
                e1 = ref[a][i] - ref[b][i]
                e2 = ref[b][i] - ref[c][i]
                if abs(e2) > 1e-16 and e1 != 0.0:
                    p = math.log(abs(e1 / e2)) / math.log(2.0)
                    print('    节点 %-8s 收敛阶 p = %.5f' % ('r=0' if i == 0 else 'r=2cm', p))
        for i in (0, 1):
            rich = ref[400][i] + (ref[400][i] - ref[200][i]) / 3.0
            print('    Richardson 外推 %-8s = %.12f （与 N=400 相差 %.3e）'
                  % ('r=0' if i == 0 else 'r=2cm', rich, abs(rich - ref[400][i])))

    ref2 = {}
    for sub in (1, 2, 4, 8):
        r = simulate(PROPS_Q1, out, N=200, sub=sub, theta=0.5,
                     Tinf_func=T_inf, Ceq_func=C_eq)
        k = len(r.times) - 1
        ref2[sub] = (r.T[k][0], r.T[k][-1])
    if verbose:
        print()
        print('=== V4b  时间步收敛性（t=1800 s, N=200） ===')
        print('    %6s %18s %18s' % ('sub', 'T(r=0)', 'T(r=2cm)'))
        for s in (1, 2, 4, 8):
            print('    %6d %18.12f %18.12f' % (s, ref2[s][0], ref2[s][1]))
    return ref, ref2


# ----------------------------------------------------------------------
# V5：端面（轴向）效应 —— 有限长圆柱乘积解析解
# ----------------------------------------------------------------------
def v5(verbose=True):
    """
    一维径向近似忽略 25 cm 长圆柱两个端面的散热。
    对线性常物性问题，有限长圆柱解 = 无限长圆柱解 x 无限大平板解（乘积法）。
    平板（半厚 L0，两侧对流）归一化阶跃响应：
        psi(t) = Sum_m D_m exp(-mu_m^2 alpha t / L0^2)
        mu_m 为 mu*tan(mu) = Bi_s 的根，D_m = 2 sin(mu_m)/(mu_m + sin mu_m cos mu_m)
    """
    k_, rho_, cp_ = PROPS_Q1.k(0), PROPS_Q1.rho(0), PROPS_Q1.cp(0)
    alpha = k_ / (rho_ * cp_)
    L0 = L_CYL / 2.0
    Bi_s = H_CONV * L0 / k_

    roots = []
    mu = 1e-6
    step = 0.002
    f = lambda m: m * math.tan(m) - Bi_s
    fz = f(mu)
    while mu < 60.0:
        mn = mu + step
        if math.cos(mu) * math.cos(mn) < 0:
            mu, fz = mn, f(mn)
            continue
        fn = f(mn)
        if fz * fn < 0.0:
            a, b, fa = mu, mn, fz
            for _ in range(80):
                m = 0.5 * (a + b)
                fm = f(m)
                if fa * fm <= 0.0:
                    b = m
                else:
                    a, fa = m, fm
            roots.append(0.5 * (a + b))
        mu, fz = mn, fn

    def slab_phi(t):
        """无限大平板（半厚 L0，两侧对流）归一化阶跃响应：初值 0，环境阶跃到 1。"""
        Fo = alpha * t / (L0 * L0)
        s = 1.0
        for m in roots[:60]:
            D = 2.0 * math.sin(m) / (m + math.sin(m) * math.cos(m))
            e = m * m * Fo
            if e > 60.0:
                continue
            s -= D * math.exp(-e)
        return s

    dts, slopes = _delta_prime_table()
    ana = CylinderConduction(alpha, R0, H_CONV * R0 / k_, n_terms=40, z_max=100.0)

    def phi3(s):
        """有限长圆柱的归一化阶跃响应（乘积法）。
        由 1-Phi_3D = (1-Phi_cyl)(1-Phi_slab) 得
        Phi_3D = Phi_cyl + Phi_slab - Phi_cyl*Phi_slab （不是简单相乘）。"""
        pc = ana.phi(0.0, alpha * s / (R0 * R0))
        ps = slab_phi(s)
        return pc + ps - pc * ps

    def F3(s, nq=300):
        """Int_0^s Phi_3D(u) du，Simpson 积分。"""
        if s <= 0.0:
            return 0.0
        if nq % 2:
            nq += 1
        h = s / nq
        tot = phi3(0.0) + phi3(s)
        for q in range(1, nq):
            tot += (4.0 if q % 2 else 2.0) * phi3(q * h)
        return tot * h / 3.0

    if verbose:
        print()
        print('=== V5  端面效应量化（平板 Bi=%.6f, 半长 L0=%.4f m, 长径比=%.1f） ==='
              % (Bi_s, L0, L_CYL / R0))
        print('    平板热特征时间 tau_slab = L0^2/alpha = %.1f s = %.2f h' % (L0 * L0 / alpha, L0 * L0 / alpha / 3600.0))
        print('    %8s %16s %16s %14s %12s' % ('t/s', '1D径向/°C', '含端面/°C', '偏差/°C', 'Fo_平板'))
    res = []
    for t in (300.0, 600.0, 900.0, 1200.0, 1800.0, 3600.0, 7200.0, 14400.0):
        t1d = T_INIT_C + ana.duhamel(0.0, t, dts, slopes)
        tot = 0.0
        for kk, dk in enumerate(slopes):
            tk = dts[kk]
            if tk >= t:
                break
            tk1 = dts[kk + 1]
            s_hi, s_lo = t - tk, max(0.0, t - tk1)
            if s_hi <= 0.0:
                continue
            tot += dk * (F3(s_hi) - F3(s_lo))
        t2d = T_INIT_C + tot
        res.append((t, t1d, t2d, t2d - t1d))
        if verbose:
            print('    %8.1f %16.8f %16.8f %14.6f %12.5f'
                  % (t, t1d, t2d, t2d - t1d, alpha * t / (L0 * L0)))
    if verbose:
        print('    结论：端面提供额外受热面，使中心温度较一维径向近似略高；')
        print('          问题1 的 1800 s 窗口内偏差仅约 0.01 °C（平板特征时间 %.1f h），' % (L0 * L0 / alpha / 3600.0))
        print('          故一维轴对称近似成立。注意：端面使总外表面积增加约 %.1f%%，' % (
            (2 * math.pi * R0 * R0) / (2 * math.pi * R0 * L_CYL) * 100.0))
        print('          因全过程为扩散控制而非表面控制，该面积增加对烘干时间的影响更小。')
    return res


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if which in ('all', 'v1'):
        v1()
    if which in ('all', 'v2'):
        v2()
    if which in ('all', 'v3'):
        v3()
    if which in ('all', 'v4'):
        v4()
    if which in ('all', 'v5'):
        v5()
