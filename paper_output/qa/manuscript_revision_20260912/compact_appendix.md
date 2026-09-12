# 附录

本附录补充正文方程的守恒推导、数值求解步骤和核心算法。温度、时间、长度在计算中分别采用 K、s、m；含水率为 kg 水/kg 干物质。式号续正文式(1)—(19)。完整输入、源程序和结果记录作为支撑材料保留，文末仅列实际生产程序的必要片段。

## 附录 A 物理模型的必要推导

### A.1 干基含水率守恒

记干骨架速度为 $\boldsymbol u$，当前单位体积内的干物质质量为 $\rho_d$，水相对骨架的通量为 $\boldsymbol j_w$。将正文式(13)的水质量方程减去干物质方程的 $C$ 倍，骨架压缩项消去，得到

$$
\rho_dD_tC=-\nabla\cdot\boldsymbol j_w,
\qquad D_t=\partial_t+\boldsymbol u\cdot\nabla.
\qquad\mathrm{(20)}
$$

采用 $\boldsymbol j_w=-\rho_dD\nabla C$，并以空间均匀的干骨架密度闭合，便有 $D_tC=\nabla\cdot(D\nabla C)$。固定半径时 $\boldsymbol u=0$，圆柱径向散度给出正文式(3)。初值 $C_0=2.55$ 对应湿基质量分数 $C_0/(1+C_0)=0.7183098592$；干基含水率可以大于 1。环境空气含湿量与材料干基含水率的分母不同，正文的 $C_{eq}$ 是由环境指标约定的等效边界量。

### A.2 有效热容量与密度解释

热方程采用 $B(C)D_tT=\nabla\cdot(k\nabla T)$，其中 $B=\rho_{eff}c_p$ 是题给物性构造的有效显热容量。Q1 的热物性为 $\rho_{eff}=820$、$c_p=2600$、$k=0.36$，其水扩散率仍按正文式(6)随含水率变化；Q2、Q3 从初始时刻统一使用式(8)、(9)，Q4 从初始时刻整组使用式(17)、(18)。题给经验系数直接采用，不由本次附件重新拟合。

区分 $\rho_{eff}$ 与 $\rho_d$ 有实际必要：若将第四问的 $760+90C$ 同时视作真实湿密度，则 $C\ge0$ 时 $\rho_d=(760+90C)/(1+C)\le760$。固定长度和干质量守恒又要求

$$
R(t)\ge R_0\sqrt{\frac{\rho_{d0}}{760}}
=1.2112029565\ \mathrm{cm},
\qquad \rho_{d0}=\frac{760+90\times2.55}{3.55}.
\qquad\mathrm{(21)}
$$

附件 2 在 72 h 给出 1.198 cm，说明上述字面解释不能在全时段同时成立。因此本模型保留题给 $\rho_{eff}c_p$ 为有效热容量，另行守恒干骨架质量。由于 $B(C)T_t\ne\partial_t[B(C)T]$，该闭合不包含已识别的湿分携焓、潜热和收缩功；后面的热通量检验只针对所采用的有效方程。

### A.3 收缩坐标与干物质量

第四问采用定长、同比径向收缩，令 $x=r/R(t)$、$u_r=x\dot R$。由干骨架连续性和链式法则得到

$$
\rho_d(t)=\rho_{d0}\left(\frac{R_0}{R(t)}\right)^2,
\quad \left.C_t\right|_r=\widehat C_t-\frac{x\dot R}{R}\widehat C_x,
\quad u_rC_r=\frac{x\dot R}{R}\widehat C_x.
\qquad\mathrm{(22)}
$$

两项平流相消，$D_tC=\widehat C_t$；再代入 $\partial_r=R^{-1}\partial_x$，即得正文式(14)、(15)及边界式(16)。纯收缩而无相对失水时 $D_tC=0$，所以干基比值 $C$ 不另加体积浓缩项。干物质量 $\pi LR^2\rho_d=\pi LR_0^2\rho_{d0}$ 保持不变。该变换依赖同比运动与干骨架空间均匀假设；半径按观测插值即可，方程求值无需对折线半径数值微分。

## 附录 B 守恒离散、Jacobian 与隐式方程

### B.1 节点控制体与共享面通量

取 $x_i=i\Delta x$、$\Delta x=1/N$，共 $N+1$ 个节点，包含中心与实际表面。控制体边界取相邻节点中点，在中心、表面截断。权重为

$$
w_i=\int_{a_i}^{b_i}x\,dx=\frac{b_i^2-a_i^2}{2},\quad
w_0=\frac{\Delta x^2}{8},\quad
w_i=x_i\Delta x\ (1\le i<N),\quad
w_N=\frac{\Delta x}{2}-\frac{\Delta x^2}{8}.
\qquad\mathrm{(23)}
$$

于是 $\sum_iw_i=1/2$，单位长度的物理控制体积为 $2\pi R^2w_i$。节点值乘权重近似控制体积分，未知量仍是节点值。对材料坐标方程积分，记梯度通量 $g^T=xkT_x$、$g^C=xDC_x$，得

$$
\dot T_i=\frac{g^T_{i+1/2}-g^T_{i-1/2}}{R^2w_iB_i},
\qquad
\dot C_i=\frac{g^C_{i+1/2}-g^C_{i-1/2}}{R^2w_i}.
\qquad\mathrm{(24)}
$$

梯度通量与向外物理通量方向相反。中心外侧面通量为零；表面 Robin 条件直接给出 $g^T_{N+1/2}=hR(T_\infty-T_N)$、$g^C_{N+1/2}=-\beta R(C_N-C_{eq})$。中心不会计算 $1/x_0$；常系数时其热方程为 $\dot T_0=4k(T_1-T_0)/(BR^2\Delta x^2)$。表面节点就是实际表面，不再附加半单元内阻。

热内部面采用串联导热阻对应的调和系数，共享面两侧使用同一通量：

$$
g^T_{i+1/2}=\gamma_i k_H(T_{i+1}-T_i),\quad
k_H=\frac{2k_i k_{i+1}}{k_i+k_{i+1}},\quad
\gamma_i=\frac{x_{i+1/2}}{\Delta x}.
\qquad\mathrm{(25)}
$$

### B.2 Kirchhoff 浓度势及稳定分支

三组扩散率写成 $D=D_0e^{-b/T}e^{-a/C}$，参数 $(a,b,D_0)$ 分别为 $(0.89,0,7\times10^{-9})$、$(0.45,3850,2.4\times10^{-3})$ 和 $(0.30,3850,4.2\times10^{-4})$。正文式(7)中，$Ce^{-a/C}$ 与 $a\operatorname{Ei}(-a/C)$ 的导数分别为 $e^{-a/C}(1+a/C)$ 和 $-(a/C)e^{-a/C}$，故 $\Phi'_a(C)=e^{-a/C}$。以面平均温度 $\overline T_i=(T_i+T_{i+1})/2$ 计算

$$
g^C_{i+1/2}=\gamma_iD_0e^{-b/\overline T_i}
\left[\Phi_a(C_{i+1})-\Phi_a(C_i)\right].
\qquad\mathrm{(26)}
$$

势差准确积分了浓度因子，面温度与空间重构仍有离散误差。不能对 $e^{-b/T}\Phi_a(C)$ 整体作差，否则即使浓度相同，也会因温差引入原 Fick 本构中不存在的通量。

令 $\Delta C=C_{i+1}-C_i$、$\overline C=(C_i+C_{i+1})/2$。相近浓度下为避免势差消减，实际代码采用

$$
\Delta\Phi\simeq e^{-a/\overline C}\Delta C,
\qquad |\Delta C|<10^{-7}\max(\overline C,10^{-3}).
\qquad\mathrm{(27)}
$$

这是中点积分近似，其差为 $O((\Delta C)^3)$。系数求值使用 $C^+=\max(C,10^{-12})$ 保护 Newton 试探点；求得的状态没有被裁剪为正值，接受状态的正性另行检查。

### B.3 稀疏 Jacobian 与离散收支

状态为 $\boldsymbol y=(T_0,C_0,\ldots,T_N,C_N,\ell)^{\mathsf T}$，$\ell$ 记录累计平均失水量。内部面只依赖左右两个节点，因此温湿方程具有相邻的 $2\times2$ 块带结构。水通量的常规分支令 $G_i=\gamma_iD_0e^{-b/\overline T_i}$，有

$$
\frac{\partial g^C}{\partial C_i}=-G_i e^{-a/C_i},\quad
\frac{\partial g^C}{\partial C_{i+1}}=G_i e^{-a/C_{i+1}},\quad
\frac{\partial g^C}{\partial T_i}=
\frac{\partial g^C}{\partial T_{i+1}}=g^C\frac{b}{2\overline T_i^2}.
\qquad\mathrm{(28)}
$$

对于式(27)，程序对实际中点表达式求导：两侧浓度偏导为 $\tfrac12f'(\overline C)\Delta C\mp f(\overline C)$，其中 $f(C)=e^{-a/C}$、$f'=af/C^2$；在保护区同时乘相应 $C>10^{-12}$ 的活跃标记。热通量中 $\partial k_H/\partial k_i=2k_{i+1}^2/(k_i+k_{i+1})^2$，另一侧对称。面导数向两侧控制体按正负号装配。

热方程分母随浓度变化，须补商法则项：

$$
B'_i=\rho'_{eff}c_p+\rho_{eff}c'_p,
\qquad
\left.\frac{\partial\dot T_i}{\partial C_i}\right|_{\mathrm{capacity}}
=-\dot T_i\frac{B'_i}{B_i}.
\qquad\mathrm{(29)}
$$

Q2、Q3 的 $(\rho'_{eff},c'_p,k')=(128,2736/(1+C)^2,0.38/(1+C)^2)$；Q4 对应为 $(90,2150/(1+C)^2,0.20/(1+C)^2)$。Q1 这些导数为零。边界偏导保留 $-hR$ 与 $-\beta R$；累计失水变量不反馈状态，Jacobian 对应整列为零。

水方程乘 $2w_i$ 求和，内部面相消，仅余表面项：

$$
\dot\ell=\frac{2\beta}{R}(C_N-C_{eq}),
\qquad 2\sum_iw_iC_i+\ell=C_0.
\qquad\mathrm{(30)}
$$

第四问也满足该式，因为 $\rho_dR^2$ 不变；节点算术平均不能替代加权平均。若向量 $\boldsymbol m$ 在水分分量取 $2w_i$、在末项取 1，其余为零，则 $\boldsymbol m\boldsymbol J=0$。热方程对应的瞬时收支为

$$
2\pi R^2\sum_iw_iB_i\dot T_i
=2\pi Rh(T_\infty-T_N).
\qquad\mathrm{(31)}
$$

两侧均为单位长度热率。$B$ 或 $R$ 变化时，$2\pi R^2\sum_iw_iB_i(T_i-T_{ref})$ 的总导数还含容量和几何变化项，故式(31)只能检验离散热算子的通量平衡。

### B.4 BDF 残量与 Newton 矩阵

空间离散后求解 $\dot{\boldsymbol y}=\boldsymbol F(t,\boldsymbol y)$。BDF 由当前未知状态和历史状态的插值导数形成隐式方程，例如以 $\Delta t$ 为步长的等步长二阶形式及 Newton 矩阵为

$$
\frac{3\boldsymbol y_n-4\boldsymbol y_{n-1}+\boldsymbol y_{n-2}}{2\Delta t}
=\boldsymbol F(t_n,\boldsymbol y_n),
\qquad
\left(\frac32\boldsymbol I-\Delta t\boldsymbol J\right)\delta\boldsymbol y
=-\boldsymbol G.
\qquad\mathrm{(32)}
$$

其中 $\boldsymbol G=\tfrac32\boldsymbol y_n-2\boldsymbol y_{n-1}+\tfrac12\boldsymbol y_{n-2}-\Delta t\boldsymbol F$。实际使用 SciPy BDF 的 1—5 阶自适应实现及解析稀疏 Jacobian；式(32)只解释隐式求解，不把固定二阶系数套用于不等步长。

## 附录 C 数值计算过程与误差范围

### C.1 输入与时间设置

计算使用清洗环境表的 241 个 0—4 h 记录及半径表的 145 个 0—72 h 记录。环境在观测区间内线性插值，4 h 后沿用正文式(10)的 50°C、$C_{eq}=0.05$ 平台。三条轨迹均从 $T_0=301.15$ K、$C_0=2.55$ 出发：Q1 取 $N=3200$ 并算至 1800 s；Q2、Q3 共用一条 $N=3200$ 轨迹；Q4 取 $N=6400$ 并随当前 $R(t)$ 更新几何。

积分在 4 h 处分段，以前段接受末态作为后段初态；此前最大步长 2 s，此后 120 s。分量尺度取 $s_j=\mathrm{atol}_j+\mathrm{rtol}|y_j|$，其中 $\mathrm{rtol}=10^{-10}$，温度绝对容差为 $10^{-10}$ K，水分与累计失水为 $10^{-12}$。这些是局部控制参数，不是连续解误差上界。BDF 稠密输出在题定时刻查询，1 s、60 s 输出间隔不等于内部步长；磁盘保存原始双精度多项式系数，只改变存储方式。

### C.2 网格选择与误差检查

在相同物性、边界和判据下比较数值方法。早期 Q23 调和面通量的 $N=50,100,200,400$ 临界时长约为 164.5440、71.5633、58.9518、57.6868 h，显示粗网格不足；Kirchhoff 格式在同系列 $N=50$ 至 800 约为 57.4792 至 57.4723 h。由推导、常系数极限和网格稳定性共同支持采用浓度势格式，随后继续加密检查局部场。

最终空间比较覆盖公共域内全整数秒及 21 个固定物理半径，Q1、Q23、Q4 最大含水率差分别为 $4.6903\times10^{-5}$、$3.8303\times10^{-5}$、$1.9799\times10^{-5}$ kg/kg。同 $N$ 将容差收紧十倍且步长上限减半，差值分别为 $3.6191\times10^{-9}$、$9.9411\times10^{-9}$、$9.8180\times10^{-10}$ kg/kg。空间结论依据原报告与现存稀疏数组，历史全秒投影未全部留存；时间检查的完整投影仍可逐值归约。以上是指定采样范围的数值敏感性，不是实验预测精度。

每次正式求解还检查接受状态物性为正、含水率范围及式(30)的质量残差。解析热场、导数差分、时间及空间检查承担不同验证作用，事件时长稳定不能替代局部场检验。附件未提供内部温湿度标签，因此不据此给出实测准确率。

### C.3 圆柱 Bessel 基准与采样

问题一常热物性热场令 $v=T-T_\infty(t)$，满足 $v_t=\alpha r^{-1}(rv_r)_r-\dot T_\infty$，其中 $\alpha=k/B$。齐次 Robin 特征根及圆柱加权展开系数为

$$
\mu_nJ_1(\mu_n)=Bi_hJ_0(\mu_n),\quad Bi_h=\frac{hR_0}{k},\quad
\lambda_n=\frac{\alpha\mu_n^2}{R_0^2},\quad
b_n=\frac{2J_1(\mu_n)}{\mu_n[J_0(\mu_n)^2+J_1(\mu_n)^2]}.
\qquad\mathrm{(33)}
$$

逐模态积分得到时变边界基准：

$$
T(x,t)=T_\infty(t)+\sum_{n=1}^{\infty}b_nJ_0(\mu_nx)
\left[(T_0-T_\infty(0))e^{-\lambda_nt}
-\int_0^te^{-\lambda_n(t-\tau)}\dot T_\infty(\tau)\,d\tau\right].
\qquad\mathrm{(34)}
$$

环境在 $[a,b]$ 上线性变化、斜率为 $s$ 时，卷积贡献为 $s[e^{-\lambda_n(t-b)}-e^{-\lambda_n(t-a)}]/\lambda_n$，末区间在 $t$ 截断。级数另做截断项数比较。N3200 数值热场与该基准在 1801 个整数秒、21 个半径点上最大相差 $1.804\times10^{-6}$ K；此基准不验证非线性水方程。

### C.4 严格阈值与结果查询

离散全域最大值 $M_N(t)=\max_iC_i(t)$ 定义事件 $g(t)=M_N(t)-0.15$，监测下降穿零。节点间作分段线性重构时，其最大值等于节点最大值。连续根 $t_*$ 对应等号，程序继续真实积分至 $\lceil t_*\rceil+1$ s，再选取小时报告网格上的候选时刻：

$$
t_{rep,h}=10^{-4}\left\lceil10^4\frac{t_*}{3600}\right\rceil,
\qquad M_N(3600t_{rep,h})<0.15.
\qquad\mathrm{(35)}
$$

式中 $t_*$ 以秒计。若候选点原精度最大含水率仍不小于 0.15，就将报告值增加 $0.0001$ h 并重查；超出已积分轨迹则报错。Q3 临界值为 57.47230195056044 h、严格报告为 57.4724 h；Q4 对应 51.09057478683054 h、51.0906 h。显示为 0.1500 不等于原精度未达标；不得改写为 0.1499。报告值是条件模型中的可行数值时刻。

从同一稠密解查询题定时间与物理半径，第四问先算 $x=r/R(t)$；$r>R(t)$ 留空，真实表面另查 $x=1$。最后才转换为 °C、h 和四位小数，并回读工作簿检查。完整运行与输出记录保留在支撑材料，以下只说明核心算法。

### C.5 经验边界阻力的限定

正文式(19)的 $p$ 情景只改变等效边界阻力。当 $C_s\ge C_{ref}>0$、$p\ge1$ 时，令 $z=(C_{ref}/C_s)^{1/p}\in[0,1]$，有 $1-z\le1-z^p\le p(1-z)$，从而 $1/p\le K_p\le1$；$C_s\to C_{ref}$ 时取连续极限 $1/p$。该族是在指定参考点下以活动度差缩放得到的经验形式，未标定药材等温线。历史 $p=1,2,4$ 的 N800 事件只用于条件情景比较，不替代正式网格的严格报告时刻，也不推出真实时长下界。

## 附录 D 必要算法片段

以下片段摘自冻结生产版本的原文件，保留实际关键语句，删去注释、导入头、空行、导出和完整验证逻辑。它们依赖原函数上下文，**不是独立运行程序，也不能拼接成完整程序**。生产条件为 Kirchhoff 面格式、解析 Jacobian、无表面潜热基线、无常物性或常扩散率验证覆盖。原行号和源文件完整 SHA-256 在下表及各片段标注，逐行对应与所有删省区间另存片段清单。

表D1 算法片段来源；三份源文件均位于 paper_output/code/modeling。

| 源文件 | 原始文件 SHA-256 |
|---|---|
| drying_core.py | 4b1e1fdacaf6eb195f94192cf1574c96609ca1058297e081dd474f59585f2305 |
| analytic_jacobian.py | d7dfda75b335e82eb27d39b8e2f12edf5a56254269ff4f273e7a828ed75a8665 |
| q3_model.py | 43a65b6a1982649503beaeec92d7aa553dd6d8f516703cc50b912a086ba9a137 |

### D.1 题给物性

来源：drying_core.py，原始行 108—126、131；共 20 行，SHA-256 见表D1。上下文：RadialModel.properties。

省略第127—130行仅供验证使用的constant_D与constant_thermal覆盖；第110行只删除行尾注释。其余物性关键语句按原文保留。

```python
def properties(self, T, C):
    s = self.settings
    positive_C = np.maximum(C, 1e-12)
    if np.any(T <= 0):
        raise FloatingPointError('Nonpositive absolute temperature')
    wet = positive_C / (1. + positive_C)
    if s.question == 'Q1':
        rho = np.full_like(C, 820.)
        cp = np.full_like(C, 2600.)
        k = np.full_like(C, .36)
        D = 7e-9 * np.exp(-.89 / positive_C)
    elif s.question in ('Q2', 'Q3', 'Q23'):
        rho, cp, k = 650 + 128 * positive_C, 1450 + 2736 * wet, .21 + .38 * wet
        D = 2.4e-3 * np.exp(-.45 / positive_C - 3850 / T)
    elif s.question == 'Q4':
        rho, cp, k = 760 + 90 * positive_C, 1850 + 2150 * wet, .12 + .20 * wet
        D = 4.2e-4 * np.exp(-.30 / positive_C - 3850 / T)
    else:
        raise ValueError(s.question)
    return rho, cp, k, D
```

### D.2 环形权重与内部面通量

来源：drying_core.py，原始行 76—80、133—135、145、150—157、159；共 18 行，SHA-256 见表D1。上下文：RadialModel.__init__ 的网格段、harmonic、water_internal_flux 的Kirchhoff段。

所列三处上下文分段合列；省略第81—132行其他初始化与物性、第136—144行稀疏模式、第146—149行调和水通量/模式分支和第158行注释。仅展示已选Kirchhoff路径。

```python
    self.x = np.linspace(0., 1., settings.intervals + 1)
    self.dx = 1. / settings.intervals
    faces = np.r_[0., (self.x[1:] + self.x[:-1]) / 2., 1.]
    self.w = np.diff(faces ** 2) / 2.
    self.internal_faces = faces[1:-1]
@staticmethod
def harmonic(a):
    return 2 * a[:-1] * a[1:] / np.maximum(a[:-1] + a[1:], np.finfo(float).tiny)
def water_internal_flux(self, T, C, D):
    a, D0 = {'Q1':(.89,7e-9), 'Q23':(.45,2.4e-3), 'Q2':(.45,2.4e-3),
              'Q3':(.45,2.4e-3), 'Q4':(.30,4.2e-4)}[self.settings.question]
    cc = np.maximum(C, 1e-12)
    potential = cc * np.exp(-a/cc) + a * expi(-a/cc)
    difference = np.diff(potential)
    small = np.abs(np.diff(cc)) < 1e-7 * np.maximum((cc[:-1]+cc[1:])/2, 1e-3)
    difference[small] = (np.exp(-a/((cc[:-1][small]+cc[1:][small])/2)) * np.diff(cc)[small])
    thermal_factor = 1. if self.settings.question == 'Q1' else np.exp(-3850/((T[:-1]+T[1:])/2))
    return self.internal_faces * D0 * thermal_factor * difference / self.dx
```

### D.3 材料控制体的守恒右端

来源：drying_core.py，原始行 161、164—173、180—184；共 16 行，SHA-256 见表D1。上下文：RadialModel.rhs。

省略第162行docstring、第163行调用计数和第174—179行可选表面潜热情景；基线surface_latent_fraction=0。中心通量由零数组直接表示。

```python
def rhs(self, t, state):
    T, C = state[:-1:2], state[1:-1:2]
    rho, cp, k, D = self.properties(T, C)
    radius = float(self.radius(t))
    tair, ceq = self.environment(t)
    heat_g = np.zeros(self.n + 1)
    water_g = np.zeros(self.n + 1)
    heat_g[1:-1] = self.internal_faces * self.harmonic(k) * np.diff(T) / self.dx
    water_g[1:-1] = self.water_internal_flux(T, C, D)
    water_g[-1] = -self.settings.beta * radius * (C[-1] - ceq)
    heat_g[-1] = -self.settings.h * radius * (T[-1] - tair)
    derivative = np.empty_like(state)
    derivative[:-1:2] = np.diff(heat_g) / (radius ** 2 * self.w * rho * cp)
    derivative[1:-1:2] = np.diff(water_g) / (radius ** 2 * self.w)
    derivative[-1] = 2 * self.settings.beta / radius * (C[-1] - ceq)
    return derivative
```

### D.4 稀疏装配与容量导数

来源：analytic_jacobian.py，原始行 76—77、138—139、145、157—164；共 13 行，SHA-256 见表D1。上下文：jacobian 的容量、几何尺度和稀疏行列装配段。

只摘四处关键装配语句；rho_c、cp_c按式(29)前后给出的物性导数，heat_deriv、water_deriv按式(25)—(28)，heat_g按式(24)边界构造。省略其余面偏导构造、add_face辅助函数、边界行、CSC转换及全部自检；相应公式和边界偏导在附录B保留。

```python
capacity = rho * cp
capacity_c = rho_c * cp + rho * cp_c
heat_scale = 1. / (radius**2 * model.w * capacity)
water_scale = 1. / (radius**2 * model.w)
temp_derivative = np.diff(heat_g) * heat_scale
add_face(2*face_index, heat_deriv, heat_scale[:-1])
add_face(2*face_index+2, heat_deriv, -heat_scale[1:])
add_face(2*face_index+1, water_deriv, water_scale[:-1])
add_face(2*face_index+3, water_deriv, -water_scale[1:])
cell_index = np.arange(n)
rows.append(2*cell_index)
columns.append(2*cell_index+1)
values.append(-temp_derivative * capacity_c / capacity)
```

### D.5 BDF 分段、事件与真实后延伸

来源：drying_core.py，原始行 306—318、320—333、336—337、339—342、345—346、349—350；共 37 行，SHA-256 见表D1。上下文：_solve_case_impl 的求解主体。

省略第319、338行注释，第334—335、343—344、347—348行缓存存储或断点整理，及主体之后的Run封装与诊断。保留首次BDF断点整理以显示DiskBDF上下文；该类保存原始BDF稠密系数，不改变方程。所有存储与断点整理仍在完整生产实现执行。

```python
model = RadialModel(settings)
method = disk_dense.DiskBDF if cache is not None else settings.method
jacobian_options = ({'jac': lambda t, y: analytic_jacobian.jacobian(model, t, y)}
    if settings.jacobian_mode == 'analytic' else {'jac_sparsity': model.jac_pattern})
if cache is not None:
    jacobian_options['dense_cache'] = cache
def dry_event(t, y):
    return float(np.max(y[1:-1:2]) - .15)
dry_event.terminal, dry_event.direction = True, -1
atol = np.empty(2 * model.n + 1)
atol[:-1:2], atol[1:-1:2], atol[-1] = settings.atol_temperature, settings.atol_moisture, settings.atol_moisture
horizon = 1800. if settings.question == 'Q1' else settings.horizon_h * 3600.
pieces, initial, event_s = [], model.initial(), None
endpoints = [0., min(14400., horizon)]
if horizon > 14400.:
    endpoints.append(horizon)
for left, right in zip(endpoints[:-1], endpoints[1:]):
    piece = solve_ivp(model.rhs, (left, right), initial, method=method,
        rtol=settings.rtol, atol=atol, **jacobian_options,
        max_step=settings.early_max_step_s if left < 14400. else settings.max_step_s,
        events=None if settings.question == 'Q1' else dry_event, dense_output=True)
    if cache is not None:
        disk_dense.align_bdf_segments(piece)
    pieces.append(piece)
    if not piece.success:
        raise RuntimeError(piece.message)
    initial = piece.y[:, -1].copy()
    if piece.t_events is not None and len(piece.t_events[0]):
        event_s = float(piece.t_events[0][0])
        end = float(np.ceil(event_s) + 1)
        tail = solve_ivp(model.rhs, (event_s, end), initial, method=method,
            rtol=settings.rtol, atol=atol, **jacobian_options,
            max_step=1., dense_output=True)
        if not tail.success:
            raise RuntimeError(tail.message)
        pieces.append(tail)
        break
```

### D.6 四位小时上取并核对严格达标

来源：q3_model.py，原始行 6—8、11—20；共 13 行，SHA-256 见表D1。上下文：completion 的候选报告时刻循环。

省略第1—5行说明、导入及空行，第9—10行注释，以及第21—27行结果字典；循环所得report_h为严格报告小时，values仍为原精度含水率。

```python
def completion(run):
    if run.event_s is None:
        raise ValueError('No full-domain drying event within the solved horizon')
    count = math.ceil(run.event_s / 3600. * 10000.)
    while True:
        report_h = count/10000.
        t = report_h*3600.
        if t > run.end_s:
            raise RuntimeError('Four-decimal reporting time is outside the verified trajectory')
        values = run.state([t])[1:-1:2,0]
        if float(np.max(values)) < .15:
            break
        count += 1
```

