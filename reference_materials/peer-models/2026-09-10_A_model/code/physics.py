# -*- coding: utf-8 -*-
"""
physics.py —— CUMCM 2026 A 题「药材的烘干问题」：数据加载、物性经验公式、题设参数

单位约定（全文统一）
    时间 t : s          半径/径向坐标 r : m        长度 L : m
    温度 T : K（摄氏换算 T-273.15）    干基含水率 C : kg/kg(干物质)
    密度 rho : kg/m^3   比热 cp : J/(kg·K)          导热 k : W/(m·K)
    扩散系数 D : m^2/s  对流换热 h : W/(m^2·K)      对流传质 beta : m/s
"""
import os
import bisect
import math

from xlsxio import read_workbook

# ----------------------------------------------------------------------
# 路径
# ----------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(_HERE)                       # ...\A题_model
MATH_ROOT = os.path.dirname(PROJ)                   # ...\数学建模
ATT_DIR = os.path.join(MATH_ROOT, 'A题')            # 赛题附件目录
OUT_DIR = os.path.join(PROJ, 'out')
FIG_DIR = os.path.join(PROJ, 'out', 'figures')
TAB_DIR = os.path.join(PROJ, 'out', 'tables')

# ----------------------------------------------------------------------
# 题设固定参数
# ----------------------------------------------------------------------
R0 = 0.02                 # m  药材初始半径 2 cm
L_CYL = 0.25              # m  药材长度 25 cm
T_INIT_C = 28.0           # °C 初始温度
T_INIT = 273.15 + T_INIT_C
C_INIT = 2.55             # kg/kg 初始干基含水率
C_TARGET = 0.15           # kg/kg 烘干判据（全域最大值低于此值）
H_CONV = 25.0             # W/(m^2·K) 对流换热系数
BETA = 8.0e-7             # m/s 对流传质系数
T_CHAMBER_PLATEAU_C = 50.0    # °C 恒温干燥段烘房温度（附件1平台值）
C_EQ_PLATEAU = 0.05           # kg/kg 恒温干燥段空气水分浓度（附件1平台值）
T_CHAMBER_END = 14400.0   # s  附件1 数据终止时刻
T_RADIUS_END = 259200.0   # s  附件2 数据终止时刻

# 物理常数（仅用于模型推广中的相变潜热讨论）
L_VAP = 2.4e6             # J/kg 水在 ~50°C 的汽化潜热（量级估计）


# ----------------------------------------------------------------------
# 一维表格插值（线性，数据区间外按给定的平台值延拓）
# ----------------------------------------------------------------------
class Table(object):
    """给定 (t_i, y_i) 的线性插值表；t 超出右端时返回 tail 值。"""

    def __init__(self, ts, ys, tail=None, extrapolate='const'):
        self.ts = list(ts)
        self.ys = list(ys)
        self.tail = ys[-1] if tail is None else tail
        self.extrapolate = extrapolate

    def __call__(self, t):
        ts, ys = self.ts, self.ys
        if t <= ts[0]:
            return ys[0]
        if t >= ts[-1]:
            return self.tail
        i = bisect.bisect_right(ts, t) - 1
        t0, t1 = ts[i], ts[i + 1]
        if t1 == t0:
            return ys[i]
        w = (t - t0) / (t1 - t0)
        return ys[i] * (1.0 - w) + ys[i + 1] * w

    def values(self, n):
        return [self(self.ts[0] + (self.ts[-1] - self.ts[0]) * i / (n - 1)) for i in range(n)]


# ----------------------------------------------------------------------
# 附件数据加载
# ----------------------------------------------------------------------
def _load_att1(path=None):
    """附件1：烘房温度 T_inf(t)[°C] 与空气水分浓度 C_eq(t)[kg/kg]。241 点, 0~14400 s。"""
    path = path or os.path.join(ATT_DIR, '附件1(1).xlsx')
    rows = read_workbook(path)['Sheet1']
    ts, Tc, Ceq = [], [], []
    for r in rows[1:]:
        if len(r) >= 3 and isinstance(r[0], float):
            ts.append(float(r[0]))
            Tc.append(float(r[1]))
            Ceq.append(float(r[2]))
    ws = [T_CHAMBER_PLATEAU_C]   # 恒温段平台温度
    we = [C_EQ_PLATEAU]          # 恒温段平台水分浓度
    return Table(ts, Tc, tail=T_CHAMBER_PLATEAU_C), Table(ts, Ceq, tail=C_EQ_PLATEAU), ts, Tc, Ceq


def _load_att2(path=None):
    """附件2：药材半径 R(t)[cm]。146 点, 0~259200 s。"""
    path = path or os.path.join(ATT_DIR, '附件2(1).xlsx')
    rows = read_workbook(path)['Sheet1']
    ts, Rs = [], []
    for r in rows[1:]:
        if len(r) >= 2 and isinstance(r[0], float):
            ts.append(float(r[0]))
            Rs.append(float(r[1]) * 1e-2)      # cm -> m
    return Table(ts, Rs, tail=Rs[-1]), ts, Rs


T_INF_TAB, C_EQ_TAB, ATT1_T, ATT1_TC, ATT1_CEQ = _load_att1()
R_TAB, ATT2_T, ATT2_R = _load_att2()


def T_inf(t):
    """烘房温度 [°C]。求解器内部统一使用摄氏度（纯导热方程对温度平移不变，
    且边界换热只依赖温差，故用摄氏度与开尔文完全等价，可避免单位混用）。"""
    return T_INF_TAB(t)


def T_inf_K(t):
    """烘房温度 [K]（仅用于物性公式中需要绝对温度处）。"""
    return 273.15 + T_INF_TAB(t)


def C_eq(t):
    """烘房空气水分浓度（等效平衡含水率）[kg/kg]。"""
    return C_EQ_TAB(t)


def R_of(t):
    """药材半径 [m]（问题1—3 恒为 R0）。"""
    return R_TAB(t)


def R_prime(t, dt=1.0):
    """dR/dt [m/s]，中心差分。"""
    t0 = max(0.0, t - dt)
    t1 = min(T_RADIUS_END, t + dt)
    if t1 <= t0:
        return 0.0
    return (R_TAB(t1) - R_TAB(t0)) / (t1 - t0)


# ----------------------------------------------------------------------
# 经验物性公式（严格照抄赛题附录）
# ----------------------------------------------------------------------
def rho_q1(C):
    """问题1 密度 [kg/m^3]（附录2，常数）。"""
    return 820.0


def cp_q1(C):
    """问题1 比热容 [J/(kg·K)]（附录2，常数）。"""
    return 2600.0


def k_q1(C):
    """问题1 导热系数 [W/(m·K)]（附录2，常数）。"""
    return 0.36


def D_q1(C, T):
    """问题1 水分扩散系数 [m^2/s]：D = 7e-9 · exp(-0.89/C)。"""
    return 7.0e-9 * math.exp(-0.89 / max(C, 1e-9))


def rho_q23(C):
    """问题2/3 密度：rho = 650 + 128 C。"""
    return 650.0 + 128.0 * C


def cp_q23(C):
    """问题2/3 比热容：cp = 1450 + 2736·C/(1+C)。"""
    return 1450.0 + 2736.0 * C / (1.0 + C)


def k_q23(C):
    """问题2/3 导热系数：k = 0.21 + 0.38·C/(1+C)。"""
    return 0.21 + 0.38 * C / (1.0 + C)


def D_q23(C, T):
    """问题2/3 扩散系数：D = 2.4e-3 · exp(-0.45/C) · exp(-3850/T)。"""
    return 2.4e-3 * math.exp(-0.45 / max(C, 1e-9)) * math.exp(-3850.0 / T)


def rho_q4(C):
    """问题4 密度：rho = 760 + 90 C。"""
    return 760.0 + 90.0 * C


def cp_q4(C):
    """问题4 比热容：cp = 1850 + 2150·C/(1+C)。"""
    return 1850.0 + 2150.0 * C / (1.0 + C)


def k_q4(C):
    """问题4 导热系数：k = 0.12 + 0.20·C/(1+C)。"""
    return 0.12 + 0.20 * C / (1.0 + C)


def D_q4(C, T):
    """问题4 扩散系数：D = 4.2e-4 · exp(-0.30/C) · exp(-3850/T)。"""
    return 4.2e-4 * math.exp(-0.30 / max(C, 1e-9)) * math.exp(-3850.0 / T)


class Props(object):
    """一组物性关系。"""

    def __init__(self, tag, rho, cp, k, D):
        self.tag = tag
        self.rho, self.cp, self.k, self.D = rho, cp, k, D

    def __repr__(self):
        return 'Props(%s)' % self.tag


PROPS_Q1 = Props('Q1-附录2', rho_q1, cp_q1, k_q1, D_q1)
PROPS_Q23 = Props('Q2Q3-附录3', rho_q23, cp_q23, k_q23, D_q23)
PROPS_Q4 = Props('Q4-附录4', rho_q4, cp_q4, k_q4, D_q4)


# ----------------------------------------------------------------------
# 干基 / 湿基换算与派生量
# ----------------------------------------------------------------------
def dry_to_wet(C):
    """干基 C = m_w/m_d  ->  湿基质量分数 w = m_w/(m_d+m_w)。"""
    return C / (1.0 + C)


def wet_to_dry(w):
    """湿基质量分数 w -> 干基含水率 C。"""
    return w / (1.0 - w)


def rho_dry(C, rho_func):
    """干物质表观密度 rho_d = rho(C)/(1+C) [kg/m^3]（rho 为总质量/总体积）。"""
    return rho_func(C) / (1.0 + C)


def alpha(k, rho, cp):
    """热扩散率 [m^2/s]。"""
    return k / (rho * cp)


if __name__ == '__main__':
    print('附件1: %d 点, t=%.0f..%.0f s' % (len(ATT1_T), ATT1_T[0], ATT1_T[-1]))
    print('附件2: %d 点, t=%.0f..%.0f s, R=%.5f..%.5f m'
          % (len(ATT2_T), ATT2_T[0], ATT2_T[-1], ATT2_R[0], ATT2_R[-1]))
    print('C0=%.2f -> w0=%.4f ;  C_target=0.15 -> w=%.4f' % (C_INIT, dry_to_wet(C_INIT), dry_to_wet(0.15)))
    print('T_inf(0)=%.3f K, T_inf(1e5)=%.3f K, C_eq(1e5)=%.5f' % (T_inf(0), T_inf(1e5), C_eq(1e5)))
    print('D_q1(C0,301.15)=%.4e  D_q23(C0,301.15)=%.4e  D_q4(C0,301.15)=%.4e'
          % (D_q1(C_INIT, T_INIT), D_q23(C_INIT, T_INIT), D_q4(C_INIT, T_INIT)))
