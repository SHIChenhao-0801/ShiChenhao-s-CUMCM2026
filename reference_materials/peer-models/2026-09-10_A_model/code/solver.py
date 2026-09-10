# -*- coding: utf-8 -*-
"""
solver.py —— CUMCM2026 A 题四问统一的有限体积求解器（纯标准库实现）

===========================================================================
统一数学模型   材料坐标  x = r/R(t)，仿射收缩假设
===========================================================================
令 F(x,t) = C(R(t)x, t)，Theta(x,t) = T(R(t)x, t)。热风烘干过程中药材为
一维轴对称、忽略端面与轴向变化，守恒形式为

  能量：  X_j * d/dt( rho*cp*T * R^2 )      = d/dx( x * k * dT/dx )       ... (E)
  水分：  R^2 * X_j * dC/dt                 = d/dx( x * D * dC/dx )       ... (M)
  其中    X_j = ∫_{CV_j} x dx

  R=const 时 (E)(M) 严格退化为标准圆柱方程
      d_t(rho cp T) = (1/r) d_r( r k d_r T ),   d_t C = (1/r) d_r( r D d_r C )

边界条件 (x=1)：
      k * dT/dx |_1 =  R * h    * ( T_inf(t) - T_s )
     -D * dC/dx |_1 =  R * beta * ( C_s - C_eq(t) )
  中心 (x=0)：dT/dx = dC/dx = 0（对称，x_{-1/2}=0 使该面通量恒为 0）

初值：T(r,0)=28 °C，C(r,0)=2.55 kg/kg

===========================================================================
数值方法
===========================================================================
空间：节点中心有限体积，节点 x_j = j/N 恰为题目要求的取样位置（0,0.1,...,2 cm）
      界面系数取调和平均（串联等效），保证界面通量守恒、二阶精度
时间：θ 方法（θ=1 后向欧拉 / θ=0.5 Crank-Nicolson），
      首步采用 Rannacher 启动（两个后向欧拉半步）抑制初值瞬变振荡
非线性：逐时步 Picard 迭代（rho,cp,k 依赖 C；D 依赖 C 与 T）
线性求解：Thomas 追赶法，O(N)
"""
import math
from physics import R0, C_INIT, T_INIT_C, H_CONV, BETA


# ----------------------------------------------------------------------
# 三对角求解（Thomas 追赶法）
# ----------------------------------------------------------------------
def thomas(a, b, c, d, n):
    """解 a[i]x[i-1] + b[i]x[i] + c[i]x[i+1] = d[i]（a[0]=c[n-1]=0）。"""
    cp = [0.0] * n
    dp = [0.0] * n
    cp[0] = c[0] / b[0]
    dp[0] = d[0] / b[0]
    for i in range(1, n):
        m = b[i] - a[i] * cp[i - 1]
        cp[i] = c[i] / m
        dp[i] = (d[i] - a[i] * dp[i - 1]) / m
    x = [0.0] * n
    x[n - 1] = dp[n - 1]
    for i in range(n - 2, -1, -1):
        x[i] = dp[i] - cp[i] * x[i + 1]
    return x


# ----------------------------------------------------------------------
# 网格
# ----------------------------------------------------------------------
class Grid(object):
    """节点中心有限体积网格，节点 x_j = j/N（j = 0..N），恰含结果要求的取样点。"""

    def __init__(self, N):
        self.N = N
        self.n = N + 1
        dx = 1.0 / N
        self.dx = dx
        self.x = [j * dx for j in range(self.n)]
        self.xf = [(j + 0.5) * dx for j in range(-1, self.n + 1)]   # 面 x_{j+1/2}
        X = []
        for j in range(self.n):
            if j == 0:
                X.append(0.5 * (dx / 2.0) ** 2)
            elif j == self.n - 1:
                a = 1.0 - dx / 2.0
                X.append(0.5 * (1.0 - a * a))
            else:
                X.append(j * dx * dx)
        self.X = X

    def xface(self, jp):
        """x_{jp}，jp = -1 .. N（面编号，面 jp 位于节点 jp 与 jp+1 之间）。"""
        return self.xf[jp + 1]


# ----------------------------------------------------------------------
# 结果容器
# ----------------------------------------------------------------------
class SimResult(object):
    def __init__(self):
        self.times = []
        self.T = []            # 摄氏
        self.C = []
        self.R = []
        self.Cmax = []
        self.Cmin = []
        self.Tmax = []
        self.Tmin = []
        self.mass = []         # 无量纲含水量 2∫C x dx
        self.energy = []       # 无量纲显热焓 2∫rho cp T x dx
        self.flux_T = []       # 表面热通量，指向药材内部为正 [W/m^2]
        self.flux_C = []       # 表面水通量，指向外部为正 [kg/(m^2·s)]
        self.x = None
        self.N = None
        self.meta = {}
        self.picard_iters = []

    def __len__(self):
        return len(self.times)

    def interp_T(self, k, xq):
        return interp_uniform(self.x, self.T[k], xq)

    def interp_C(self, k, xq):
        return interp_uniform(self.x, self.C[k], xq)

    def value_at_radius_cm(self, k, r_cm, which='C'):
        """第 k 个快照、物理半径 r_cm (cm) 处的值；超出当前材料表面返回 None。"""
        Rk = self.R[k]
        r = r_cm * 1e-2
        if r > Rk + 1e-12:
            return None
        xq = r / Rk
        return self.interp_C(k, xq) if which == 'C' else self.interp_T(k, xq)


def interp_uniform(x, y, xq):
    """均匀节点网格上的线性插值。"""
    n = len(y)
    if xq <= 0.0:
        return y[0]
    if xq >= x[n - 1]:
        return y[n - 1]
    h = x[1] - x[0]
    i = int(xq / h)
    if i >= n - 1:
        return y[n - 1]
    w = (xq - x[i]) / h
    return y[i] * (1.0 - w) + y[i + 1] * w


# ----------------------------------------------------------------------
# 时间步序列（含 Rannacher 启动）
# ----------------------------------------------------------------------
def build_steps(out_times, sub, theta, rannacher):
    steps = []
    t = 0.0
    for k, t_out in enumerate(out_times):
        if t_out <= t:
            continue
        dt = (t_out - t) / sub
        for s in range(sub):
            a = t + s * dt
            b = a + dt
            if rannacher and k == 0 and s == 0:
                steps.append((a, a + dt * 0.5, 1.0))
                steps.append((a + dt * 0.5, b, 1.0))
            else:
                steps.append((a, b, theta))
        t = t_out
    return steps


# ----------------------------------------------------------------------
# 主求解器
# ----------------------------------------------------------------------
def simulate(props,
             out_times,
             N=200,
             sub=4,
             theta=0.5,
             rannacher=True,
             R_func=None,
             Rprime_func=None,
             Tinf_func=None,
             Ceq_func=None,
             T_init_c=T_INIT_C,
             C_init=C_INIT,
             picard_tol=1e-10,
             picard_max=25,
             stop_cmax=None,
             keep_nodes=None,
             h_scale=1.0,
             beta_scale=1.0,
             verbose=False):
    """
    props      : physics.Props，一组物性经验公式
    out_times  : 结果输出时刻列表（升序，均 > 0）
    N          : 径向节点数（N 取 20 的倍数可保证 0.1 cm 取样点恰为节点）
    sub        : 每个输出间隔的细分步数，实际 dt = 间隔/sub
    theta      : 1.0 后向欧拉 / 0.5 Crank-Nicolson
    R_func     : R(t) -> m；None 表示恒为 R0（问题1—3）
    stop_cmax  : 给定则全域最大 C 低于该值时提前结束
    """
    g = Grid(N)
    n = g.n
    dx = g.dx
    X = g.X

    if R_func is None:
        Rf = lambda t: R0
        Rp = lambda t: 0.0
    else:
        Rf = R_func
        Rp = Rprime_func if Rprime_func is not None else (lambda t: 0.0)

    rho_f, cp_f, k_f, D_f = props.rho, props.cp, props.k, props.D
    Tinf_f, Ceq_f = Tinf_func, Ceq_func
    h = H_CONV * h_scale
    beta = BETA * beta_scale

    def face_harm(fv):
        out = [0.0] * (n - 1)
        for j in range(n - 1):
            a, b = fv[j], fv[j + 1]
            s = a + b
            out[j] = 2.0 * a * b / s if s > 0.0 else 0.0
        return out

    def face_coefs(kv, Dv, Rv):
        kh = face_harm(kv)
        Dh = face_harm(Dv)
        aL = [0.0] * n
        aR = [0.0] * n
        bL = [0.0] * n
        bR = [0.0] * n
        for j in range(n):
            if j > 0:
                xf = g.xface(j - 1)
                aL[j] = xf * kh[j - 1] / dx
                bL[j] = xf * Dh[j - 1] / dx
            if j < n - 1:
                xf = g.xface(j)
                aR[j] = xf * kh[j] / dx
                bR[j] = xf * Dh[j] / dx
            else:
                aR[j] = Rv * h            # x=1 面：k dT/dx = R h (T_inf - T_s)
                bR[j] = Rv * beta         # x=1 面：-D dC/dx = R beta (C_s - C_eq)
        return aL, aR, bL, bR

    def resid_T(Tv, aLv, aRv, Tinf):
        r = [0.0] * n
        for j in range(n):
            v = 0.0
            if j > 0:
                v -= aLv[j] * (Tv[j] - Tv[j - 1])
            if j < n - 1:
                v += aRv[j] * (Tv[j + 1] - Tv[j])
            else:
                v += aRv[j] * (Tinf - Tv[j])
            r[j] = v
        return r

    def resid_C(Cv, bLv, bRv, Ceq):
        r = [0.0] * n
        for j in range(n):
            v = 0.0
            if j > 0:
                v -= bLv[j] * (Cv[j] - Cv[j - 1])
            if j < n - 1:
                v += bRv[j] * (Cv[j + 1] - Cv[j])
            else:
                v += bRv[j] * (Ceq - Cv[j])
            r[j] = v
        return r

    # ---- 初值 ----
    T = [T_init_c] * n
    C = [C_init] * n
    rcp = [rho_f(c) * cp_f(c) for c in C]
    kv = [k_f(c) for c in C]
    Dv = [D_f(c, T[j] + 273.15) for j, c in enumerate(C)]
    Tinf_old, Ceq_old = Tinf_f(0.0), Ceq_f(0.0)
    aL, aR, bL, bR = face_coefs(kv, Dv, Rf(0.0))
    resT_old = resid_T(T, aL, aR, Tinf_old)
    resC_old = resid_C(C, bL, bR, Ceq_old)

    res = SimResult()
    res.N = N
    idx = list(range(n)) if keep_nodes is None else list(keep_nodes)
    res.x = [g.x[j] for j in idx]
    res.meta.update(props=props.tag, theta=theta, sub=sub, N=N)

    def record(t):
        res.times.append(t)
        res.T.append([T[j] for j in idx])
        res.C.append([C[j] for j in idx])
        res.R.append(Rf(t))
        res.Cmax.append(max(C))
        res.Cmin.append(min(C))
        res.Tmax.append(max(T))
        res.Tmin.append(min(T))
        mC = 0.0
        eE = 0.0
        for j in range(n):
            mC += C[j] * X[j]
            eE += rcp[j] * (T[j] + 273.15) * X[j]
        res.mass.append(2.0 * mC)
        res.energy.append(2.0 * eE)
        res.flux_T.append(h * (Tinf_f(t) - T[n - 1]))
        res.flux_C.append(beta * (C[n - 1] - Ceq_f(t)))

    record(0.0)

    steps = build_steps(out_times, sub, theta, rannacher)
    out_set = {round(t, 9): i for i, t in enumerate(out_times)}
    stopped_at = None
    oi = 0

    for (t0, t1, th) in steps:
        dt = t1 - t0
        if dt <= 0.0:
            continue
        R0v, R1v = Rf(t0), Rf(t1)
        Tinf1, Ceq1 = Tinf_f(t1), Ceq_f(t1)
        R0sq, R1sq = R0v * R0v, R1v * R1v
        Rth2 = th * R1sq + (1.0 - th) * R0sq

        Told = list(T)
        Cold = list(C)
        rcp_old = list(rcp)
        Tn = list(T)
        Cn = list(C)
        iters = 0

        for it in range(picard_max):
            iters = it + 1
            rcp_n = [rho_f(c) * cp_f(c) for c in Cn]
            kv_n = [k_f(c) for c in Cn]
            Dv_n = [D_f(c, Tn[j] + 273.15) for j, c in enumerate(Cn)]
            aLn, aRn, bLn, bRn = face_coefs(kv_n, Dv_n, R1v)

            la = [0.0] * n
            lb = [0.0] * n
            lc = [0.0] * n
            ld = [0.0] * n
            ma = [0.0] * n
            mb = [0.0] * n
            mc = [0.0] * n
            md = [0.0] * n
            for j in range(n):
                Xj = X[j]
                # 能量方程（材料导数形式，见模块文档的严格推导）：
                #   rho*cp * dT/dt = (1/(R^2 x)) d_x( x k d_x T )
                # theta 加权： rcp_th = th*rcp^{n+1} + (1-th)*rcp^n , Rth2 同理
                rcp_th = th * rcp_n[j] + (1.0 - th) * rcp_old[j]
                cap = Xj * rcp_th * Rth2 / dt
                lb[j] = cap + th * (aLn[j] + aRn[j])
                la[j] = -th * aLn[j]
                lc[j] = -th * aRn[j]
                rhs = cap * Told[j] + (1.0 - th) * resT_old[j]
                if j == n - 1:
                    rhs += th * aRn[j] * Tinf1
                ld[j] = rhs

                mb[j] = R1sq * Xj / dt + th * (bLn[j] + bRn[j])
                ma[j] = -th * bLn[j]
                mc[j] = -th * bRn[j]
                rhs2 = R1sq * Xj * Cold[j] / dt + (1.0 - th) * resC_old[j]
                if j == n - 1:
                    rhs2 += th * bRn[j] * Ceq1
                md[j] = rhs2

            Tnew = thomas(la, lb, lc, ld, n)
            Cnew = thomas(ma, mb, mc, md, n)

            eT = 0.0
            eC = 0.0
            for j in range(n):
                if Cnew[j] < 0.0:
                    Cnew[j] = 0.0
                dT = Tnew[j] - Tn[j]
                if dT < 0.0:
                    dT = -dT
                if dT > eT:
                    eT = dT
                dC = Cnew[j] - Cn[j]
                if dC < 0.0:
                    dC = -dC
                if dC > eC:
                    eC = dC
            Tn, Cn = Tnew, Cnew
            if eT < picard_tol and eC < picard_tol:
                break

        res.picard_iters.append(iters)

        rcp = [rho_f(c) * cp_f(c) for c in Cn]
        kv = [k_f(c) for c in Cn]
        Dv = [D_f(c, Tn[j] + 273.15) for j, c in enumerate(Cn)]
        aL, aR, bL, bR = face_coefs(kv, Dv, R1v)
        resT_old = resid_T(Tn, aL, aR, Tinf1)
        resC_old = resid_C(Cn, bL, bR, Ceq1)
        T, C = Tn, Cn

        # 抵达某个输出时刻则记录
        key = round(t1, 9)
        if key in out_set and out_set[key] == oi:
            record(t1)
            oi += 1
            if stop_cmax is not None and res.Cmax[-1] < stop_cmax:
                stopped_at = t1
                break

    res.meta['stopped_at'] = stopped_at
    if verbose:
        print('  %-12s N=%-4d sub=%-3d theta=%.2f  snaps=%-6d  Cmax=%.6f  iters~%.1f'
              % (props.tag, N, sub, theta, len(res.times), res.Cmax[-1],
                 sum(res.picard_iters) / max(1, len(res.picard_iters))))
    return res


def find_crossing(res, level):
    """在输出时刻序列上线性插值，求全域最大 C 首次降到 level 之下（不含）的时刻。"""
    ts, cm = res.times, res.Cmax
    for i in range(1, len(ts)):
        if cm[i] < level:
            c0, c1 = cm[i - 1], cm[i]
            if c0 == c1:
                return ts[i]
            w = (c0 - level) / (c0 - c1)
            return ts[i - 1] + w * (ts[i] - ts[i - 1])
    return None
