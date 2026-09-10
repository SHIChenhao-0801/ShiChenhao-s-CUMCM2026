# -*- coding: utf-8 -*-
"""
analytic.py —— 解析解参考：无限长圆柱 + 对流边界 的 Bessel 级数解

用途
----
1. 独立校核数值求解器（空间离散、边界条件、时间积分、追赶法）是否正确；
2. 为论文提供"数值解 vs 解析解"的误差表与误差图（国赛 A 题极重要的加分项）。

数学
----
无量纲变量  x = r/R，Fo = a*t/R^2，Bi = hR/k（传质时 Bi_m = beta*R/D）

归一化响应（初值 0，环境阶跃到 1）：
    phi(x,Fo) = 1 - Sum_n C_n J0(zeta_n x) exp(-zeta_n^2 Fo)
    C_n = 2*Bi / [ (zeta_n^2 + Bi^2) J0(zeta_n) ]
    zeta_n 为  zeta*J1(zeta) = Bi*J0(zeta)  的正根

时变环境 T_inf(t) 由 **Duhamel 卷积** 给出（线性问题）：
    T(r,t) - T_i = Int_0^t phi(r, t-tau) * Delta'(tau) dtau,  Delta = T_inf - T_i
对分段线性环境，Delta' 分段常数，积分可逐段解析处理，精度仅受 Bessel 级数截断限制。

Bessel 函数采用 Miller 向后递推（数值稳定、大自变量亦精确），
不依赖 scipy。
"""


# ----------------------------------------------------------------------
# Bessel 函数：Miller 向后递推
# ----------------------------------------------------------------------
def bessel_j0_j1(x):
    """返回 (J0(x), J1(x))，用 Miller 算法（向后递推 + 归一化），全程稳定。"""
    if x <= 0.0:
        return 1.0, 0.0
    if x < 1e-8:
        return 1.0, 0.5 * x
    N = int(x) + int(20 + 1.6 * x) + 30
    j = [0.0] * (N + 2)
    j[N] = 1.0
    j[N + 1] = 0.0
    inv = 1.0 / x
    for n in range(N, 0, -1):
        j[n - 1] = (2.0 * n * inv) * j[n] - j[n + 1]
    s = j[0]
    for n in range(2, N + 1, 2):
        s += 2.0 * j[n]
    return j[0] / s, j[1] / s


_J0CACHE = {}


def bessel_j0(x):
    """带缓存的 J0（级数求值中 (zeta_n * x_j) 会大量重复）。"""
    v = _J0CACHE.get(x)
    if v is None:
        v = bessel_j0_j1(x)[0]
        _J0CACHE[x] = v
    return v


# ----------------------------------------------------------------------
# 特征根
# ----------------------------------------------------------------------
def bessel_roots(Bi, z_max=100.0, step=0.02):
    """求 zeta*J1(zeta) = Bi*J0(zeta) 在 (0, z_max] 内的全部正根。"""
    roots = []

    def f(z):
        j0, j1 = bessel_j0_j1(z)
        return z * j1 - Bi * j0

    z = 1e-6
    fz = f(z)
    while z < z_max:
        zn = z + step
        fn = f(zn)
        if fz == 0.0:
            roots.append(z)
        elif fz * fn < 0.0:
            a, b, fa = z, zn, fz
            for _ in range(80):
                m = 0.5 * (a + b)
                fm = f(m)
                if fa * fm <= 0.0:
                    b = m
                else:
                    a, fa = m, fm
            roots.append(0.5 * (a + b))
        z, fz = zn, fn
    return roots


def make_series(Bi, n_terms=60, z_max=100.0):
    """
    预计算级数系数。
    返回 (zetas, Cns, J0_at_zetas)
    """
    zetas = bessel_roots(Bi, z_max=z_max)[:n_terms]
    Cns = []
    J0s = []
    for z in zetas:
        j0 = bessel_j0(z)
        Cns.append(2.0 * Bi / ((z * z + Bi * Bi) * j0))
        J0s.append(j0)
    return zetas, Cns, J0s


# ----------------------------------------------------------------------
# 阶跃响应与 Duhamel 卷积
# ----------------------------------------------------------------------
class CylinderConduction(object):
    """
    无限长圆柱 + 对流边界的线性响应。

    alpha : 热扩散率 a [m^2/s]（传质时填 D）
    R     : 半径 [m]
    Bi    : Biot 数（传质时 beta*R/D）
    """

    def __init__(self, alpha, R, Bi, n_terms=60, z_max=100.0):
        self.alpha, self.R, self.Bi = alpha, R, Bi
        self.zetas, self.Cns, self.J0s = make_series(Bi, n_terms, z_max)
        self.lam = [(z * z) * alpha / (R * R) for z in self.zetas]   # 特征衰减率

    def phi(self, x, Fo):
        """归一化阶跃响应 phi(x,Fo)：初值 0，环境阶跃至 1。"""
        s = 1.0
        for z, C in zip(self.zetas, self.Cns):
            e = (z * z) * Fo
            if e > 60.0:
                continue
            s -= C * bessel_j0(z * x) * _exp(-e)
        return s

    def F(self, x, s):
        """F(x,s) = Int_0^s phi(x,u) du —— Duhamel 卷积核。"""
        tot = s
        for z, C, lam in zip(self.zetas, self.Cns, self.lam):
            e = lam * s
            if e > 700.0:
                continue
            tot -= C * bessel_j0(z * x) * (1.0 - _exp(-e)) / lam
        return tot

    def duhamel(self, x, t, dprime_times, dprime_vals):
        """
        时变环境 Delta(t)（分段线性）下的响应。
        dprime_times[t_k] / dprime_vals[dk] 描述 Delta' 在各区间的常值。
        返回 theta = T - T_i。
        """
        tot = 0.0
        for k, dk in enumerate(dprime_vals):
            tk = dprime_times[k]
            if tk >= t:
                break
            tk1 = dprime_times[k + 1]
            s_hi = t - tk
            s_lo = t - tk1
            if s_lo < 0.0:
                s_lo = 0.0
            if s_hi <= 0.0:
                continue
            tot += dk * (self.F(x, s_hi) - self.F(x, s_lo))
        return tot


_EXPCACHE = {}


def _exp(v):
    """带缓存的 math.exp(v)。"""
    e = _EXPCACHE.get(v)
    if e is None:
        e = __import__('math').exp(v)
        if len(_EXPCACHE) < 400000:
            _EXPCACHE[v] = e
    return e


# ----------------------------------------------------------------------
# 由附件表格构造分段常值 Delta'
# ----------------------------------------------------------------------
def piecewise_linear_derivative(ts, ys):
    """给定 (t_k, y_k) 线性插值表，返回 (左端点序列, 各段斜率)。"""
    dts = list(ts[:-1])
    slopes = []
    for k in range(len(ts) - 1):
        dt = ts[k + 1] - ts[k]
        slopes.append((ys[k + 1] - ys[k]) / dt if dt > 0 else 0.0)
    return dts, slopes


if __name__ == '__main__':
    import math
    # 已知值自检
    checks = [(0.0, 1.0, 0.0), (1.0, 0.7651976866, 0.4400505857),
              (2.0, 0.2238907791, 0.5767248078),
              (5.0, -0.1775967713, -0.3275791376),
              (10.0, -0.2459357645, 0.0434727462),
              (20.0, 0.1670246643, 0.0668331242),
              (50.0, 0.0558123277, -0.0975118281),
              (100.0, 0.0199858503, -0.0771453520)]
    print('J0/J1 自检（Miller 递推 vs 标准值）：')
    for x, j0e, j1e in checks:
        j0, j1 = bessel_j0_j1(x)
        print('  x=%6.1f  J0 err=%.2e   J1 err=%.2e' % (x, abs(j0 - j0e), abs(j1 - j1e)))

    print()
    print('特征根自检 Bi=1.3888889:')
    Bi = 25.0 * 0.02 / 0.36
    zs = bessel_roots(Bi, z_max=30.0)[:6]
    for i, z in enumerate(zs, 1):
        j0, j1 = bessel_j0_j1(z)
        print('  zeta_%d = %.10f  残差 z*J1-Bi*J0 = %.3e' % (i, z, z * j1 - Bi * j0))
