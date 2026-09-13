# 附录 A 连续模型、坐标变换与数值方法的完整推导

本附录给出正文采用的有效热湿模型及其数值实现的推导，补充公式的成立条件、变量含义和计算检查范围。题给物性、环境观测及模型闭合分别说明；数学推导不改变正文已冻结的模型和结果。计算统一使用 m、s、K；含水率以 kg 水/kg 干物质计。题定长度为 $L_z=0.25\,\mathrm m$，初始半径为 $R_0=0.02\,\mathrm m$，初温为 $T_0=301.15\,\mathrm K$，初始干基含水率为 $C_0=2.55$。为避免与长度混淆，累计平均失水量统一记为 $\ell$。文献序号沿用正文参考文献；扩散与圆柱基准的理论出处为 Crank[4]，有限体积的一般构造见 Eymard 等[5]，隐式多步求解及具体实现见文献[6]、[7]。以下推导同时列明这些一般方法在当前题设中的使用条件。

## A.1 干基含水率、湿基含水率与参考质量

设某一材料微团内干物质质量为 $m_d$、水质量为 $m_w$。干基含水率 $C$ 与湿基水质量分数 $w$ 定义为

<!-- EQ_A_BASIS -->
$$
C=\frac{m_w}{m_d},\qquad
w=\frac{m_w}{m_d+m_w}=\frac{C}{1+C},\qquad
C=\frac{w}{1-w}.
$$

这里的 $C$ 是质量比，可以大于 1；$w$ 是总湿质量中的水质量分数，应在 0 与 1 之间。由式 [EQ_A_BASIS]，$C_0=2.55$ 对应 $w_0=2.55/3.55\approx0.7183098592$，即初始水分约占湿质量的 71.83%。不能将 $C_0=2.55$ 直接写成 2.55% 或 255%的湿基质量分数。

在当前物理体积内，分别记干物质质量密度为 $\rho_d$、水质量密度为 $\rho_w$。微团两组分占用同一统计体积时，干基定义等价于

<!-- EQ_A_DENSITY_BASIS -->
$$
\rho_w=\rho_d C,\qquad
m_d=\int_{\Omega(t)}\rho_d\,\mathrm dV,\qquad
m_w=\int_{\Omega(t)}\rho_d C\,\mathrm dV.
$$

$\Omega(t)$ 为当前药材区域，$\rho_d$ 与 $\rho_w$ 的单位均为 $\mathrm{kg/m^3}$。水质量的计算必须有相应的干物质权重，不能把含水率节点的算术平均直接当作体积总水质量。

附件 1 的烘房水分指标仅标注 kg/kg，记其观测数值为 $Y_\infty(t)$。基线采用 $C_{eq}(t)=Y_\infty(t)$ 的数值映射，构造表面有效平衡含水率。这是一项边界闭合假设。若进一步把 $Y_\infty$ 解释为空气湿度比，则其分母是干空气质量，与药材 $C$ 的干物质参考质量不同；两者同写 kg/kg 不能证明数值可直接相减。材料真实平衡含水率一般还依赖温度与吸附、解吸等温线，当前附件没有给出这种标定关系。

## A.2 从组分质量平衡得到干基扩散方程

设干物质骨架速度为 $\boldsymbol v_s$，水相对骨架的质量通量为 $\boldsymbol j_w$，其单位为 $\mathrm{kg/(m^2s)}$。无干物质生成、损失及相对于骨架迁移时，干物质连续性方程为

<!-- EQ_A_DRY_CONTINUITY -->
$$
\frac{\partial\rho_d}{\partial t}
+\nabla\cdot(\rho_d\boldsymbol v_s)=0.
$$

水的实验室坐标总通量由随骨架运输的 $\rho_d C\boldsymbol v_s$ 与相对通量 $\boldsymbol j_w$ 组成。无内部水源项时，水质量守恒为

<!-- EQ_A_WATER_CONTINUITY -->
$$
\frac{\partial(\rho_d C)}{\partial t}
+\nabla\cdot(\rho_d C\boldsymbol v_s+\boldsymbol j_w)=0.
$$

将式 [EQ_A_WATER_CONTINUITY] 展开，得到

<!-- EQ_A_PRODUCT_EXPANSION -->
$$
\rho_d\left(\frac{\partial C}{\partial t}
+\boldsymbol v_s\cdot\nabla C\right)
+C\left[\frac{\partial\rho_d}{\partial t}
+\nabla\cdot(\rho_d\boldsymbol v_s)\right]
=-\nabla\cdot\boldsymbol j_w.
$$

方括号为干物质连续性方程的左端，因而为零。定义随骨架运动的物质导数 $\mathrm D_s/\mathrm Dt=\partial_t+\boldsymbol v_s\cdot\nabla$，即可得到干基含水率的输运方程

<!-- EQ_A_MATERIAL_MOISTURE -->
$$
\rho_d\frac{\mathrm D_s C}{\mathrm Dt}
=-\nabla\cdot\boldsymbol j_w.
$$

式 [EQ_A_MATERIAL_MOISTURE] 显示，骨架压缩导致的干密度变化已经在质量比的求导过程中相消。若没有相对水通量，则 $\mathrm D_sC/\mathrm Dt=0$；纯几何收缩不使同一材料微团的干基质量比自行增加。

采用相对骨架的有效 Fick 闭合。扩散通量与浓度梯度关系的一般理论可参见 Crank[4]；这里对干骨架参考系和有效扩散率的选取仍是本模型的具体闭合：

<!-- EQ_A_FICK -->
$$
\boldsymbol j_w=-\rho_dD(T,C)\nabla C,
\qquad
\rho_d\frac{\mathrm D_s C}{\mathrm Dt}
=\nabla\cdot\left[\rho_dD(T,C)\nabla C\right].
$$

$D$ 的单位为 $\mathrm{m^2/s}$，负号表示水沿含水率下降方向迁移。将散度展开后，若 $\rho_d$ 空间不均匀，一般有

<!-- EQ_A_NONUNIFORM_DRY_DENSITY -->
$$
\frac{\mathrm D_s C}{\mathrm Dt}
=\nabla\cdot(D\nabla C)
+D\nabla(\ln\rho_d)\cdot\nabla C.
$$

因此只有在干骨架密度空间均匀时，才能从散度内约去 $\rho_d$。本文以初始干物质均匀分布、固定骨架或同比收缩保证这一条件；若采用非均匀收缩，须回到式 [EQ_A_FICK]，不能沿用已经约去密度的简式。

## A.3 圆柱薄壳收支与固定域方程

忽略轴向、周向差异及两端面的传递，所有场量仅随径向位置 $r$ 和时间 $t$ 变化。固定半径时 $\boldsymbol v_s=0$。半径 $r$ 至 $r+\mathrm dr$、长度 $L_z$ 的薄壳体积为 $2\pi rL_z\mathrm dr$，两侧传递面积分别为 $2\pi rL_z$ 与 $2\pi(r+\mathrm dr)L_z$。将水的净流入量除以薄壳体积并令 $\mathrm dr\to0$，有

<!-- EQ_A_RADIAL_WATER -->
$$
\frac{\partial C}{\partial t}
=\frac1r\frac{\partial}{\partial r}
\left[rD(T,C)\frac{\partial C}{\partial r}\right],
\qquad 0<r<R_0.
$$

这里 $1/r$ 来自圆柱薄壳面积随半径的变化。$D$ 随状态变化时，应保留在径向导数内；把右端写成 $D(C_{rr}+C_r/r)$ 会遗漏系数梯度贡献。

热侧采用 Fourier 通量 $\boldsymbol q=-k(C)\nabla T$，并以题给物性构造有效显热容量 $B(C)=\rho_{eff}(C)c_p(C)$。选择 $B(C)\mathrm D_sT/\mathrm Dt$ 作为本模型的局部温升需求，薄壳导热收支给出

<!-- EQ_A_EFFECTIVE_HEAT -->
$$
\begin{aligned}
B(C)\frac{\mathrm D_sT}{\mathrm Dt}
&=\nabla\cdot[k(C)\nabla T],\\
B(C)\frac{\partial T}{\partial t}
&=\frac1r\frac{\partial}{\partial r}
\left[rk(C)\frac{\partial T}{\partial r}\right]
\quad(\boldsymbol v_s=0).
\end{aligned}
$$

$k$ 的单位为 $\mathrm{W/(m\,K)}$，$c_p$ 为 $\mathrm{J/(kg\,K)}$，$\rho_{eff}$ 为 $\mathrm{kg/m^3}$，故 $B$ 为 $\mathrm{J/(m^3K)}$。式 [EQ_A_EFFECTIVE_HEAT] 是本文采用的有效显热闭合；由 Fourier 定律只能确定导热通量，不能单独推出完整多组分能量方程恰好等于该容量形式。

特别地，$\rho_{eff}$ 不自动等于质量守恒中的 $\rho_d$。比热、密度依赖含水率时，有

<!-- EQ_A_CAPACITY_NOT_ENTHALPY -->
$$
\frac{\mathrm D_s}{\mathrm Dt}[B(C)T]
=B(C)\frac{\mathrm D_sT}{\mathrm Dt}
+T B'(C)\frac{\mathrm D_sC}{\mathrm Dt}.
$$

因此不能把式 [EQ_A_EFFECTIVE_HEAT] 的左端改写为 $\mathrm D_s(BT)/\mathrm Dt$ 而省略第二项。基线未逐项建立水分迁移携焓、相变热及机械功，后面的有效热通量恒等式只检查所采用的方程，不证明真实完整过程的总能量平衡已经闭合。

## A.4 四问物性与驱动条件

问题一采用题给附录 2 的常热物性及含水率相关扩散率：

<!-- EQ_A_PROPERTIES_Q1 -->
$$
\rho_{eff}=820,\qquad c_p=2600,\qquad k=0.36,
\qquad D_1(C)=7\times10^{-9}\exp(-0.89/C).
$$

密度、比热、导热率和扩散率依次使用 $\mathrm{kg/m^3}$、$\mathrm{J/(kg\,K)}$、$\mathrm{W/(m\,K)}$ 和 $\mathrm{m^2/s}$。问题一的热场可独立求解，水分扩散仍是非线性的；$D_1$ 不含温度因子。

问题二与问题三从同一均匀初态开始，在整个过程采用题给附录 3：

<!-- EQ_A_PROPERTIES_Q23 -->
$$
\begin{aligned}
\rho_{eff}(C)&=650+128C,\\
c_p(C)&=1450+2736\frac{C}{1+C},\\
k(C)&=0.21+0.38\frac{C}{1+C},\\
D_{23}(T,C)&=2.4\times10^{-3}
\exp\left(-\frac{0.45}{C}-\frac{3850}{T}\right).
\end{aligned}
$$

问题四从初始时刻整组使用题给附录 4，并同时引入半径变化：

<!-- EQ_A_PROPERTIES_Q4 -->
$$
\begin{aligned}
\rho_{eff}(C)&=760+90C,\\
c_p(C)&=1850+2150\frac{C}{1+C},\\
k(C)&=0.12+0.20\frac{C}{1+C},\\
D_4(T,C)&=4.2\times10^{-4}
\exp\left(-\frac{0.30}{C}-\frac{3850}{T}\right).
\end{aligned}
$$

式 [EQ_A_PROPERTIES_Q23]、式 [EQ_A_PROPERTIES_Q4] 的单位与式 [EQ_A_PROPERTIES_Q1] 相同。$T$ 必须以 K 代入，3850 带有使 $3850/T$ 无量纲的温度尺度；$a/C$ 中参数 $a$ 与干基含水率采用同一数值口径。这些系数来自题给经验关系，不是由本次附件重新拟合，也不是从第一原理推导的常数。问题二、三不拼接问题一的末态，问题四也不在某一阶段才切换附录 4。

相同 $T,C$ 下，两组全过程扩散率之比为

<!-- EQ_A_DIFFUSIVITY_RATIO -->
$$
\frac{D_4(T,C)}{D_{23}(T,C)}
=0.175\exp\left(\frac{0.15}{C}\right),
\qquad C_\times=\frac{0.15}{\ln(1/0.175)}\approx0.08606.
$$

其中 $C_\times$ 是两扩散率相等的含水率。$C>C_\times$ 时 $D_4<D_{23}$，$0<C<C_\times$ 时顺序反转。因此不能写“附录 4 扩散系数在全程整体更小”；收缩和整组物性变化的净作用需由保持条件明确的数值对照判断。

环境表有 241 个 0—4 h 记录，半径表有 145 个 0—72 h 记录。对相邻时间节点 $t_j\le t\le t_{j+1}$，以 $f_j$ 表示同一观测变量，分段线性插值为

<!-- EQ_A_LINEAR_INTERPOLATION -->
$$
I_f(t)=f_j+\frac{f_{j+1}-f_j}{t_{j+1}-t_j}(t-t_j).
$$

温度观测先换成 K；半径换成 m。正文基线环境为

<!-- EQ_A_ENVIRONMENT_EXTENSION -->
$$
(T_\infty,C_{eq})(t)=
\begin{cases}
(I_T(t),I_Y(t)),&0\le t\le14400\,\mathrm s,\\
(323.15,0.05),&t>14400\,\mathrm s.
\end{cases}
$$

式 [EQ_A_ENVIRONMENT_EXTENSION] 后一段是平台延拓假设，不是持续数天的观测。收缩半径在附件 2 的观测区间内使用 $R(t)=I_R(t)$。正式问题四的达标时刻位于 72 h 内，未用到半径观测窗外延拓；对其他长时情景则必须另行说明。

## A.5 初始条件、表面边界与量纲

三条正式轨迹均从均匀初态开始，轴心由对称性给零径向梯度：

<!-- EQ_A_INITIAL_CENTER -->
$$
T(r,0)=T_0,\qquad C(r,0)=C_0,
\qquad T_r(0,t)=C_r(0,t)=0.
$$

记 $T_s=T(R(t),t)$、$C_s=C(R(t),t)$ 为真实表面状态。向外为正时，表面热、水通量分别为

<!-- EQ_A_SURFACE_PHYSICAL -->
$$
q_{out}=-kT_r=h(T_s-T_\infty),
\qquad
j_{w,out}=-\rho_d D C_r
=\rho_d\beta(C_s-C_{eq}).
$$

$h=25\,\mathrm{W/(m^2K)}$，$\beta=8\times10^{-7}\,\mathrm{m/s}$。热边界两侧单位均为 $\mathrm{W/m^2}$；水质量边界两侧单位均为 $\mathrm{kg/(m^2s)}$。将水边界约去同一表面干密度得到源码使用的形式

<!-- EQ_A_SURFACE_NORMALIZED -->
$$
-D C_r=\beta(C_s-C_{eq}).
$$

式 [EQ_A_SURFACE_NORMALIZED] 的两侧是以干密度归一化的传递量，其长度—时间单位为 m/s，尚不是质量通量。材料较空气冷时 $T_s<T_\infty$，向外热通量为负，热量进入材料；$C_s>C_{eq}$ 时向外水通量为正，材料失水。该符号规则贯穿边界与控制体离散。

初值与瞬时表面 Robin 条件未必在 $t=0$ 完全相容。这表示启动阶段形成快速边界层，不要求人为改动题给初态。数值求解采用较小的早期步长，并另行检查接受状态和早期场误差。

## A.6 干物质密度、有效密度与收缩的一致性

问题一至三令骨架固定；问题四采用定长、径向同比收缩。每个初始材料半径 $r_0$ 随时间变为 $r=r_0R(t)/R_0$，相应骨架速度为

<!-- EQ_A_SKELETON_VELOCITY -->
$$
v_s(r,t)=\left.\frac{\partial r}{\partial t}\right|_{r_0}
=\frac{r\dot R(t)}{R(t)},\qquad
\nabla\cdot\boldsymbol v_s
=\frac1r\frac{\partial(rv_s)}{\partial r}
=2\frac{\dot R(t)}{R(t)}.
$$

$\dot R<0$ 表示收缩；轴向速度取零。式 [EQ_A_DRY_CONTINUITY] 因而给出

<!-- EQ_A_DRY_DENSITY_SHRINK -->
$$
\begin{aligned}
\frac{\mathrm D_s\rho_d}{\mathrm Dt}
&=-2\frac{\dot R}{R}\rho_d,\\
\rho_d(t)&=\rho_{d0}\left(\frac{R_0}{R(t)}\right)^2,\\
M_d&=\pi L_zR(t)^2\rho_d(t)=\pi L_zR_0^2\rho_{d0}.
\end{aligned}
$$

这里 $M_d$ 为恒定总干质量，$\rho_{d0}$ 为初始均匀干物质密度。同比收缩使每个材料体积均按 $R^2/R_0^2$ 缩小，因此初始均匀干密度保持空间均匀而随时间变化。半径的表面观测不能单独证明内部运动同比，式 [EQ_A_SKELETON_VELOCITY] 是用于闭合内部运动的明确假设。

若同时强行把附录 4 的 $760+90C$ 解释为真实湿密度，则非负含水率下应有

<!-- EQ_A_DENSITY_BOUND -->
$$
\rho_d=\frac{760+90C}{1+C}
=90+\frac{670}{1+C}\le760.
$$

以初始关系 $\rho_{d0}=(760+90C_0)/(1+C_0)\approx278.7323943662$ 归一化干质量，再与式 [EQ_A_DRY_DENSITY_SHRINK] 联立，得到

<!-- EQ_A_RADIUS_COMPATIBILITY -->
$$
R(t)\ge R_0\sqrt{\frac{\rho_{d0}}{760}}
\approx1.2112029565\,\mathrm{cm}.
$$

附件 2 在 72 h 给出 1.198 cm，小于上述下界。因此真实湿密度解释、非负含水率、固定长度和给定收缩轨迹不能在所给全时段同时成立。本文将 $\rho_{eff}c_p$ 用作有效热容量，$\rho_d$ 独立守恒；初始归一化不意味着随时重新设置 $\rho_d=\rho_{eff}(C)/(1+C)$。基线温湿方程约去均匀干密度后不依赖其绝对标度；只有换算绝对水量或添加指定潜热负荷时才需要该标度。

## A.7 一般移动坐标与网格速度项

为明确网格运动的来源，先不假定网格速度等于骨架速度。取 $r=R(t)x$，$0\le x\le1$；定义 $\widehat C(x,t)=C(R(t)x,t)$，$\widehat T(x,t)=T(R(t)x,t)$。固定 $x$ 的网格速度为 $v_g=x\dot R$。链式法则给出

<!-- EQ_A_ALE_CHAIN -->
$$
\left.\frac{\partial C}{\partial t}\right|_r
=\left.\frac{\partial\widehat C}{\partial t}\right|_x
-\frac{x\dot R}{R}\frac{\partial\widehat C}{\partial x},
\qquad
\frac{\partial C}{\partial r}
=\frac1R\frac{\partial\widehat C}{\partial x}.
$$

把物理方程中的骨架运输项同时变换，得到

<!-- EQ_A_ALE_RESIDUAL -->
$$
\begin{aligned}
\frac{\mathrm D_s C}{\mathrm Dt}
&=\frac{\partial\widehat C}{\partial t}
+\frac{v_s-v_g}{R}\frac{\partial\widehat C}{\partial x},\\
\frac{\mathrm D_s T}{\mathrm Dt}
&=\frac{\partial\widehat T}{\partial t}
+\frac{v_s-v_g}{R}\frac{\partial\widehat T}{\partial x}.
\end{aligned}
$$

在干密度空间均匀的条件下，完整变换后的水分方程为

<!-- EQ_A_GENERAL_MOVING_COORDINATE -->
$$
\frac{\partial\widehat C}{\partial t}
+\frac{v_s-x\dot R}{R}\frac{\partial\widehat C}{\partial x}
=\frac1{R^2x}\frac{\partial}{\partial x}
\left(xD\frac{\partial\widehat C}{\partial x}\right).
$$

式 [EQ_A_GENERAL_MOVING_COORDINATE] 保留了网格相对骨架运动的项。如果假设骨架在空间固定而只有计算边界改变，则 $v_s=0$，左侧必须保留 $-x\dot R\widehat C_x/R$；不能直接套用材料随动形式。这样的假设是否与边界处物质流失、干质量守恒相容，还需重新说明，不能只换坐标而省略物理解释。

本文问题四采用式 [EQ_A_SKELETON_VELOCITY]，故 $v_s=v_g=x\dot R$。坐标变化项与骨架平流项恰好相消，材料坐标控制方程为

<!-- EQ_A_MATERIAL_PDE -->
$$
\begin{aligned}
\frac{\partial\widehat C}{\partial t}
&=\frac1{R(t)^2x}\frac{\partial}{\partial x}
\left(xD(\widehat T,\widehat C)\widehat C_x\right),\\
B(\widehat C)\frac{\partial\widehat T}{\partial t}
&=\frac1{R(t)^2x}\frac{\partial}{\partial x}
\left(xk(\widehat C)\widehat T_x\right).
\end{aligned}
$$

固定半径的前三问是 $R(t)=R_0$、$v_s=v_g=0$ 的特例。材料坐标形式不再重复添加网格平流，也不增加 $-2\dot RC/R$ 的体积浓缩项；后者只适用于相应体积密度的收支，不能施加在已由组分方程消去压缩项的干基比值上。

表面导数换元后，边界条件变为

<!-- EQ_A_MATERIAL_BOUNDARY -->
$$
\begin{aligned}
\widehat T_x(0,t)&=\widehat C_x(0,t)=0,\\
-\frac{k_s}{R}\widehat T_x(1,t)&=h(T_s-T_\infty),\\
-\frac{D_s}{R}\widehat C_x(1,t)&=\beta(C_s-C_{eq}).
\end{aligned}
$$

$k_s,D_s$ 为当前表面物性。$1/R$ 来自空间导数换元，内部方程中的 $1/R^2$ 来自两次长度缩放。半径折线的 $\dot R$ 在观测节点处可不连续，但相消后的求解方程只需连续的 $R(t)$；各开区间上的推导可拼接为相容的分段解，不需对折线半径作数值微分。

## A.8 节点控制体、轴心及表面权重

有限体积法以控制体积分收支和共用面通量建立离散方程，一般框架见 Eymard 等[5]；本题的具体圆柱权重和节点配置如下推导。取 $N$ 个均匀区间，$\Delta x=1/N$，节点 $x_i=i\Delta x$，$i=0,\ldots,N$。对偶控制体的内部边界为相邻节点中点，左、右外边界分别截在 0 和 1。记第 $i$ 个控制体为 $[a_i,b_i]$，其圆柱权重为

<!-- EQ_A_CONTROL_VOLUME_WEIGHTS -->
$$
\begin{aligned}
w_i&=\int_{a_i}^{b_i}x\,\mathrm dx=\frac{b_i^2-a_i^2}{2},\\
w_0&=\frac{\Delta x^2}{8},\qquad
w_i=x_i\Delta x\ (1\le i<N),\\
w_N&=\frac{\Delta x}{2}-\frac{\Delta x^2}{8}.
\end{aligned}
$$

中心控制体为 $[0,\Delta x/2]$，表面控制体为 $[1-\Delta x/2,1]$。由区间拼接可得 $\sum_iw_i=1/2$。单位轴向长度的实际控制体积为 $2\pi R^2w_i$，完整控制体体积为 $2\pi L_zR^2w_i$。

未知量 $T_i,C_i$ 位于节点，节点包括轴心与真实表面。用 $w_iC_i$ 近似积分 $\int_{a_i}^{b_i}x\widehat C\,\mathrm dx$，用 $w_iB(C_i)\dot T_i$ 近似有效热容量积分。这个集总近似不将节点值变成精确单元平均；点值基准与环体平均基准应分别比较。

定义便于装配的梯度面量

<!-- EQ_A_GRADIENT_FLUX -->
$$
g^T=xk\widehat T_x,\qquad g^C=xD\widehat C_x.
$$

$g^T$ 单位为 W/m，$g^C$ 为 $\mathrm{m^2/s}$，它们与向外物理热流、水流的符号相反。对式 [EQ_A_MATERIAL_PDE] 在控制体内乘 $x$ 积分，并采用上述节点集总，得到半离散方程

<!-- EQ_A_SEMIDISCRETE -->
$$
\dot T_i=\frac{g^T_{i+1/2}-g^T_{i-1/2}}{R^2w_iB_i},
\qquad
\dot C_i=\frac{g^C_{i+1/2}-g^C_{i-1/2}}{R^2w_i},
\qquad B_i=B(C_i).
$$

这里 $i-1/2,i+1/2$ 表示第 $i$ 个控制体的两侧面；中心外侧面和表面外侧面的坐标按 0、1 截断。内部面必须由相邻控制体共用同一个数值，左控制体取正贡献，右控制体取负贡献。

中心面直接令 $g^T_{-1/2}=g^C_{-1/2}=0$，因此程序不计算 $1/x_0$。例如常系数热方程的第一行是

<!-- EQ_A_AXIS_LIMIT -->
$$
\dot T_0=
\frac{4k(T_1-T_0)}{BR^2\Delta x^2}.
$$

若光滑轴对称场在中心展开为 $T(x)=T(0)+\tfrac12T_{xx}(0)x^2+O(x^4)$，式 [EQ_A_AXIS_LIMIT] 趋于 $2kT_{xx}(0)/(BR^2)$，与圆柱算子 $k(T_{xx}+T_x/x)/(BR^2)$ 的轴心极限一致。

由式 [EQ_A_MATERIAL_BOUNDARY]，表面外侧面直接取

<!-- EQ_A_BOUNDARY_GRADIENT_FLUX -->
$$
g^T_{N+1/2}=hR(T_\infty-T_N),
\qquad
g^C_{N+1/2}=-\beta R(C_N-C_{eq}).
$$

最后一个未知量本身位于实际表面，无须从末单元中心再外推一个表面值，也不额外附加半单元传质内阻。若改成单元中心网格，未知量位置与边界离散必须同步重建。

## A.9 导热调和平均与 Kirchhoff 水分面量

对内部面 $i+1/2$，记 $\gamma_i=x_{i+1/2}/\Delta x$。两侧各半间距的导热阻相加，等效导热系数与热面量为

<!-- EQ_A_HEAT_FACE -->
$$
\begin{aligned}
\frac{\Delta x}{k_H}
&=\frac{\Delta x/2}{k_i}+\frac{\Delta x/2}{k_{i+1}},\\
k_H&=\frac{2k_i k_{i+1}}{k_i+k_{i+1}},\\
g^T_{i+1/2}&=\gamma_i k_H(T_{i+1}-T_i).
\end{aligned}
$$

这里的等效阻力解释针对面附近两段系数近似，圆柱面位置也按 $x_{i+1/2}$ 近似；不是对整个有限厚圆柱壳稳态导热的无误差积分。

三组扩散率可统一写成 $D=D_0A(T)f_a(C)$，其中 $A(T)=\exp(-b/T)$、$f_a(C)=\exp(-a/C)$。参数 $(a,b,D_0)$ 依次为 $(0.89,0,7\times10^{-9})$、$(0.45,3850,2.4\times10^{-3})$ 和 $(0.30,3850,4.2\times10^{-4})$。对 $C>0$ 定义 Kirchhoff 浓度势

<!-- EQ_A_KIRCHHOFF_POTENTIAL -->
$$
\Phi_a(C)=C\exp(-a/C)+a\operatorname{Ei}(-a/C).
$$

$\operatorname{Ei}$ 为指数积分函数。利用 $\mathrm d\operatorname{Ei}(z)/\mathrm dz=e^z/z$ 和链式法则，分别有

<!-- EQ_A_KIRCHHOFF_DERIVATIVE -->
$$
\begin{aligned}
\frac{\mathrm d}{\mathrm dC}\left[C e^{-a/C}\right]
&=e^{-a/C}\left(1+\frac aC\right),\\
\frac{\mathrm d}{\mathrm dC}\left[a\operatorname{Ei}(-a/C)\right]
&=-\frac aC e^{-a/C},\\
\Phi_a'(C)&=e^{-a/C}.
\end{aligned}
$$

因此 $\Phi_a(C_{i+1})-\Phi_a(C_i)=\int_{C_i}^{C_{i+1}}e^{-a/c}\,\mathrm dc$。在面上用当前两侧温度平均 $\overline T_i=(T_i+T_{i+1})/2$，水分面量为

<!-- EQ_A_WATER_FACE -->
$$
g^C_{i+1/2}=\gamma_iD_0
\exp\left(-\frac b{\overline T_i}\right)
\left[\Phi_a(C_{i+1})-\Phi_a(C_i)\right].
$$

式 [EQ_A_WATER_FACE] 对浓度因子的积分采用解析势差；温度面值、空间重构、几何面值及时间积分仍有数值误差。Q1 的 $b=0$；其余两组的温度因子在一个面内单独取值。“面温度冻结”指这一步空间近似，不表示 Newton 迭代中温度不更新。

不能对 $A(T)\Phi_a(C)$ 整体作差。因为其空间导数为

<!-- EQ_A_SPURIOUS_TEMPERATURE_TERM -->
$$
\frac{\partial}{\partial x}[A(T)\Phi_a(C)]
=A(T)e^{-a/C}C_x
+A(T)\frac b{T^2}\Phi_a(C)T_x.
$$

第二项不在本题所用 Fick 闭合内。当两侧含水率相同、温度不同时，正确浓度梯度通量应为零，整体势差却会产生非零值，因而不符合原模型。

相邻浓度很接近时，两项势值相减存在消减误差。令 $\Delta C=C_{i+1}-C_i$、$\overline C_i=(C_i+C_{i+1})/2$，则中点积分展开给出

<!-- EQ_A_SMALL_DIFFERENCE -->
$$
\Delta\Phi
=f_a(\overline C_i)\Delta C
+\frac{f_a''(\overline C_i)}{24}(\Delta C)^3
+O((\Delta C)^5).
$$

现行源码在 $|\Delta C|<10^{-7}\max(\overline C_i,10^{-3})$ 时使用第一项，其局部差为 $O((\Delta C)^3)$。一般分支保留指数积分势差。系数求值采用 $C^+=\max(C,10^{-12})$ 保护 Newton 试探点，实际比较与势差分支以 $C^+$ 为准；它不裁剪求得的状态。正值保护是数值定义，不是干基含水率的物理下限。

## A.10 干基质量与有效热收支的离散恒等式

全体水方程乘 $2w_i$ 求和，内部面两两相消，只有表面项保留。定义加权平均含水率 $\overline C_N=2\sum_iw_iC_i$ 和累计平均失水量 $\ell(0)=0$，有

<!-- EQ_A_DISCRETE_MASS -->
$$
\begin{aligned}
\frac{\mathrm d\overline C_N}{\mathrm dt}
&=\frac{2g^C_{N+1/2}}{R^2}
=-\frac{2\beta}{R}(C_N-C_{eq}),\\
\dot\ell&=\frac{2\beta}{R}(C_N-C_{eq}),\\
\overline C_N(t)+\ell(t)&=C_0.
\end{aligned}
$$

连续材料域的对应平均为 $\overline C=2\int_0^1x\widehat C\,\mathrm dx$。由 $\rho_dR^2$ 恒定，水质量为 $M_d\overline C$；故式 [EQ_A_DISCRETE_MASS] 与移动体积下的干质量守恒相容。$\ell$ 单位为 kg 水/kg 干物质，$M_d\ell$ 才是累计水质量。当前基线以失水为主；若边界条件改变而出现吸湿，$\dot\ell$ 可以为负，仍是带符号的净流出量。

热方程乘 $2\pi R^2w_iB_i$ 求和，同样得到瞬时有效热通量恒等式

<!-- EQ_A_DISCRETE_HEAT_RATE -->
$$
2\pi R^2\sum_iw_iB_i\dot T_i
=2\pi Rh(T_\infty-T_N).
$$

式 [EQ_A_DISCRETE_HEAT_RATE] 两侧均为单位轴向长度的功率，单位 W/m。若另定义单位长度的容量加权温升量 $H_{eff}=2\pi R^2\sum_iw_iB_i(T_i-T_{ref})$，其中 $T_{ref}$ 为固定参考温度，则乘积法则给出

<!-- EQ_A_EFFECTIVE_ENERGY_DERIVATIVE -->
$$
\begin{aligned}
\frac{\mathrm dH_{eff}}{\mathrm dt}
={}&2\pi Rh(T_\infty-T_N)
+2\pi R^2\sum_iw_i(T_i-T_{ref})B_i'\dot C_i\\
&+4\pi R\dot R\sum_iw_iB_i(T_i-T_{ref}).
\end{aligned}
$$

第二项来自容量变化，第三项来自物理体积变化。二者是这一数学量的乘积求导项，未经额外热力学本构不能认定为真实机械功或潜热。Q1 的 $B,R$ 恒定时，后两项为零，可对式 [EQ_A_DISCRETE_HEAT_RATE] 积分核验相应常物性显热收支；Q23/Q4 不能省略它们后把残差解释为数值积分误差。

## A.11 解析 Jacobian：面量、容量、边界与累计量

将状态交错排列为 $\boldsymbol y=(T_0,C_0,T_1,C_1,\ldots,T_N,C_N,\ell)^{\mathsf T}$，维数为 $2N+3$，半离散系统写为 $\dot{\boldsymbol y}=\boldsymbol F(t,\boldsymbol y)$。Jacobian 为 $\boldsymbol J=\partial\boldsymbol F/\partial\boldsymbol y$。固定求值时刻时，$R,T_\infty,C_{eq}$ 是外部驱动，不对状态求导。

对内部热面，记 $\Delta T=T_{i+1}-T_i$。调和系数偏导为

<!-- EQ_A_HARMONIC_DERIVATIVES -->
$$
\frac{\partial k_H}{\partial k_i}
=\frac{2k_{i+1}^2}{(k_i+k_{i+1})^2},
\qquad
\frac{\partial k_H}{\partial k_{i+1}}
=\frac{2k_i^2}{(k_i+k_{i+1})^2}.
$$

由此，热面量对四个相邻状态的偏导是

<!-- EQ_A_HEAT_FACE_JACOBIAN -->
$$
\begin{aligned}
\partial_{T_i}g^T&=-\gamma_i k_H,
&\partial_{T_{i+1}}g^T&=\gamma_i k_H,\\
\partial_{C_i}g^T&=\gamma_i\Delta T
\frac{2k_{i+1}^2k_i'}{(k_i+k_{i+1})^2},
&\partial_{C_{i+1}}g^T&=\gamma_i\Delta T
\frac{2k_i^2k_{i+1}'}{(k_i+k_{i+1})^2}.
\end{aligned}
$$

其中 $k_i'=\mathrm dk(C_i)/\mathrm dC_i$。本题 $k$ 不显式依赖温度，故热通量的温度导数来自温差，浓度导数来自导热系数。

对水面量定义 $G_i=\gamma_iD_0e^{-b/\overline T_i}$、$\Delta\Phi=\Phi_a(C_{i+1})-\Phi_a(C_i)$。常规正值势差分支下

<!-- EQ_A_WATER_FACE_JACOBIAN -->
$$
\begin{aligned}
\partial_{C_i}g^C&=-G_i e^{-a/C_i},
&\partial_{C_{i+1}}g^C&=G_i e^{-a/C_{i+1}},\\
\partial_{T_i}g^C&=g^C\frac{b}{2\overline T_i^2},
&\partial_{T_{i+1}}g^C&=g^C\frac{b}{2\overline T_i^2}.
\end{aligned}
$$

温度偏导不能因采用面温度近似而省去；两侧温度各以 $1/2$ 进入 $\overline T_i$。Q1 的 $b=0$，相应热对水耦合偏导才为零。

近等浓度分支必须对实际用到的 $f_a(\overline C_i)\Delta C$ 求导，得到

<!-- EQ_A_SMALL_DIFFERENCE_JACOBIAN -->
$$
\begin{aligned}
\partial_{C_i}\Delta\Phi
&=\frac12 f_a'(\overline C_i)\Delta C-f_a(\overline C_i),\\
\partial_{C_{i+1}}\Delta\Phi
&=\frac12 f_a'(\overline C_i)\Delta C+f_a(\overline C_i),\\
f_a'(C)&=\frac a{C^2}e^{-a/C}.
\end{aligned}
$$

在系数保护区，势差与物性关于浓度的偏导还需乘对应节点的活跃标记 $\mathbf1_{C_i>10^{-12}}$。表面驱动使用原状态 $C_N-C_{eq}$，其下述边界偏导不因此变为零。保护阈值处属于分段数值规则，不是处处光滑的物理本构；Jacobian 采用与右端相同的分支，不能用另一表达式的导数替代。

热方程除面量外还有依赖 $C_i$ 的分母 $B_i$。设 $H_i=g^T_{i+1/2}-g^T_{i-1/2}$，则

<!-- EQ_A_CAPACITY_JACOBIAN -->
$$
\partial_{C_i}\dot T_i
=\frac{\partial_{C_i}H_i}{R^2w_iB_i}
-\dot T_i\frac{B_i'}{B_i},
\qquad
B_i'=\rho_{eff}'(C_i)c_p(C_i)+\rho_{eff}(C_i)c_p'(C_i).
$$

物性导数由题给表达式直接求得：

<!-- EQ_A_PROPERTY_DERIVATIVES -->
$$
\begin{aligned}
\text{Q1: }&\quad (\rho_{eff}',c_p',k')=(0,0,0),\\
\text{Q23: }&\quad
(\rho_{eff}',c_p',k')=
\left(128,\frac{2736}{(1+C)^2},\frac{0.38}{(1+C)^2}\right),\\
\text{Q4: }&\quad
(\rho_{eff}',c_p',k')=
\left(90,\frac{2150}{(1+C)^2},\frac{0.20}{(1+C)^2}\right).
\end{aligned}
$$

将每个面偏导向左、右控制体按正、负号加入，再乘各自的 $1/(R^2w_iB_i)$ 或 $1/(R^2w_i)$；热方程同时添加式 [EQ_A_CAPACITY_JACOBIAN] 的容量项。由此得到邻近节点的 $2\times2$ 块带结构。

基线表面与累计量导数为

<!-- EQ_A_BOUNDARY_JACOBIAN -->
$$
\partial_{T_N}g_s^T=-hR,
\qquad
\partial_{C_N}g_s^C=-\beta R,
\qquad
\partial_{C_N}\dot\ell=\frac{2\beta}{R}.
$$

累计量 $\ell$ 不反馈温湿场，因此 Jacobian 对 $\ell$ 的整列为零。令行向量 $\boldsymbol m^{\mathsf T}$ 在每个 $C_i$ 分量取 $2w_i$、在 $\ell$ 分量取 1、其余取零，则式 [EQ_A_DISCRETE_MASS] 的微分结构要求

<!-- EQ_A_JACOBIAN_LEFT_NULL -->
$$
\boldsymbol m^{\mathsf T}\boldsymbol F=0,
\qquad
\boldsymbol m^{\mathsf T}\boldsymbol J=\boldsymbol0^{\mathsf T}.
$$

前者检查共享通量的质量装配，后者检查其导数装配。方向差分检验采用 $[\boldsymbol F(\boldsymbol y+\varepsilon\boldsymbol v)-\boldsymbol F(\boldsymbol y-\varepsilon\boldsymbol v)]/(2\varepsilon)$ 与 $\boldsymbol J\boldsymbol v$ 对照；必须同时覆盖浓度、温度、边界、累计量及近等浓度分支，不能只检查对角项。

## A.12 隐式 BDF 与连续数值输出

空间加密使扩散算子的快速尺度约随 $(R\Delta x)^{-2}$ 增大，状态相关扩散率又带来不同的局部时间尺度。系统因此采用隐式 BDF 推进。以当前状态和若干历史状态的插值多项式在当前时刻求导，可得一般后向差分残量

<!-- EQ_A_BDF_RESIDUAL -->
$$
\boldsymbol G(\boldsymbol y_n)
=\alpha_0\boldsymbol y_n
+\sum_{j=1}^{q}\alpha_j\boldsymbol y_{n-j}
-\Delta t_n\beta_q\boldsymbol F(t_n,\boldsymbol y_n)
=\boldsymbol0.
$$

$q$ 为阶数，$\alpha_j,\beta_q$ 是该历史时间布局对应的系数。等步长二阶仅作为原理示例：

<!-- EQ_A_BDF2 -->
$$
\frac{3\boldsymbol y_n-4\boldsymbol y_{n-1}+\boldsymbol y_{n-2}}{2\Delta t}
=\boldsymbol F(t_n,\boldsymbol y_n).
$$

对式 [EQ_A_BDF_RESIDUAL] 作 Newton 线性化，每次修正求解

<!-- EQ_A_NEWTON_SYSTEM -->
$$
\left(\alpha_0\boldsymbol I-\Delta t_n\beta_q\boldsymbol J\right)
\delta\boldsymbol y=-\boldsymbol G.
$$

实际采用 SciPy BDF 的 1—5 阶自适应实现及 NDF 精度修正；式 [EQ_A_BDF2] 不表示全程固定二阶。隐式多步常微分方程求解的算法背景见 Byrne 与 Hindmarsh[6]，当前 BDF 的阶数、误差控制与 Jacobian 接口依 SciPy 官方说明[7]及本次使用版本源码核对。变步长、变阶时的历史差分更新、误差估计和失败重试由库实现，不能将固定等步长系数用于任意不等间距历史点。

时间局部误差按分量尺度归一化：

<!-- EQ_A_ERROR_SCALE -->
$$
s_j=\operatorname{atol}_j+\operatorname{rtol}|y_j|.
$$

正式参数为 $\operatorname{rtol}=10^{-10}$，温度绝对容差 $10^{-10}\,\mathrm K$，水分与累计失水绝对容差 $10^{-12}$。前 4 h 最大步长 2 s，之后 120 s；程序在 14400 s 处切段，并用上一段接受末态作为下一段初态。这些参数控制时间积分局部误差，不能当作全时空场误差的严格上界。

BDF 每个接受步带有连续输出多项式。以一个接受步的右端 $t_n$、多项式步长尺度 $h_p$、阶数 $q$ 和后向差分系数向量 $\boldsymbol D_0,\ldots,\boldsymbol D_q$ 表示，其求值形式为

<!-- EQ_A_BDF_DENSE -->
$$
\boldsymbol P_n(t)=\boldsymbol D_0+
\sum_{j=1}^{q}\boldsymbol D_j
\prod_{k=0}^{j-1}\frac{t-(t_n-kh_p)}{(k+1)h_p}.
$$

式 [EQ_A_BDF_DENSE] 中的差分系数和尺度是求解器为该步输出对象保存的量，不应另从稀疏采样反推。`diskDense.py` 保存原始双精度系数与接受状态，并使用同一求值公式；只改变存储位置。BDF 内部断点恰好落在查询点时，保留与 SciPy 原 BDF 一致的右侧多项式选择；跨显式分段边界则保持 `Run.state` 的段选择规则。

题定每 1 s 或 60 s 的数值直接从尚未关闭的连续数值轨迹查询。保存的 60 s 等审查用 NPZ 并不是逐秒输出的插值来源。连续输出多项式是离散 ODE 解的数值表示，不是偏微分方程的解析解。

## A.13 全域最大含水率、临界根与严格报告时刻

对连续模型定义

<!-- EQ_A_CONTINUOUS_MAXIMUM -->
$$
M(t)=\max_{0\le r\le R(t)}C(r,t)
=\max_{0\le x\le1}\widehat C(x,t).
$$

$M(t)$ 表示时刻 $t$ 最湿位置的干基含水率，单位仍为 kg/kg。题目要求各处含水率均低于 $C_*=0.15$，等价于 $M(t)<C_*$；平均含水率低于阈值不能替代这一条件，也不应在求解前只指定中心为唯一检查点。

数值计算实际采用全部 $N+1$ 个节点的最大值

<!-- EQ_A_DISCRETE_EVENT -->
$$
M_N(t)=\max_{0\le i\le N}C_i(t),
\qquad g_N(t)=M_N(t)-C_*.
$$

节点间作分段线性重构时，每段值都是两个端点的凸组合，因此重构场的最大值恰等于 $M_N$。这使数值判据覆盖整个重构空间域，但不等于证明真实连续场与重构场的最大值完全相同。二者差异仍需空间、时间误差检查；若需要真实连续场的严格可行保证，还需可用的统一误差界。

以 $g_N$ 从正到负的第一次穿零定位临界时刻 $t_{c,N}$。在临界附近连续下降时，$M_N(t_{c,N})=C_*$ 对应等号，严格可行集合的下确界为该根，严格集合本身未必具有最小时间点。最大值函数在控制节点切换时可以不可微，但连续性仍使包围区间上的标量事件定位有意义；不要求对最大值求解析导数。

正文式(14)对应在指定报告网格上求严格可行的首点。本附录以离散数值模型明确写为

<!-- EQ_A_STRICT_REPORT -->
$$
\begin{aligned}
\mathcal K_N&=\left\{k\in\mathbb N_0:
k\Delta t_r\ge t_{c,N},\ M_N(k\Delta t_r)<C_*\right\},\\
t_{r,N}&=\Delta t_r\min\mathcal K_N,
\qquad \Delta t_r=0.36\,\mathrm s=10^{-4}\,\mathrm h.
\end{aligned}
$$

$\mathbb N_0$ 为非负整数集合，$\mathcal K_N$ 为满足时间与严格含水率条件的整数指标集合。所有集合内比较使用未舍入的数值解，$t_{c,N},t_{r,N},\Delta t_r$ 统一以秒计算。该定义在所搜索区间内有可行点时才成立；未触发事件不能把预设计算上限当作烘干时长。

程序先从临界状态实际续算至

<!-- EQ_A_POST_EVENT_END -->
$$
t_{end}=\Delta t_s\left[
\left\lceil\frac{t_{c,N}}{\Delta t_s}\right\rceil+1\right],
\qquad \Delta t_s=1\,\mathrm s,
$$

再生成报告候选首点

<!-- EQ_A_REPORT_CANDIDATE -->
$$
t_r^{(0)}=\Delta t_r
\left\lceil\frac{t_{c,N}}{\Delta t_r}\right\rceil,
\qquad t_r^{(j)}=t_r^{(0)}+j\Delta t_r.
$$

从 $j=0$ 起逐点查询 $M_N$，第一个严格小于 0.15 的点作为 $t_{r,N}$；若查询超出已实际积分的 $t_{end}$，程序报错，不外推状态。$t_{end}$ 是保守的事件后整数秒核对点，不宣称是最早严格可行整数秒；$t_{r,N}$ 才是按 0.0001 h 精度报告的时长。若根恰在报告格点且该点仍为等号，必须继续到下一格点。

现行正式轨迹给出问题三 $t_{c,N}/3600=57.47230195056044\,\mathrm h$、$t_{r,N}/3600=57.4724\,\mathrm h$；问题四相应为 $51.09057478683054\,\mathrm h$ 和 $51.0906\,\mathrm h$。四位最近舍入得到的临界根显示值，不能替代式 [EQ_A_STRICT_REPORT] 的严格可行时刻。表格中含水率显示 0.1500 也不直接否定未舍入值小于 0.15；不通过手改末位改变判定。

## A.14 固定物理位置查询与缩域输出

给定物理半径 $r_j$，先在每个查询时刻计算 $x_j(t)=r_j/R(t)$。若 $0\le x_j\le1$ 且 $x_i\le x_j\le x_{i+1}$，使用

<!-- EQ_A_SPATIAL_QUERY -->
$$
\widehat C_N(x_j,t)
=(1-\eta)C_i(t)+\eta C_{i+1}(t),
\qquad
\eta=\frac{x_j-x_i}{\Delta x}.
$$

温度查询采用同样的空间重构，时间值先由式 [EQ_A_BDF_DENSE] 所在轨迹查询。$r_j>R(t)$ 时该位置已不在药材内，输出留空，不能填零或外推。真实表面另查 $x=1$，不能用最近的 0.1 cm 固定列替代。代码对仅由浮点边界换算造成的约 $10^{-12}$ m 容差内归属差异按表面值一致处理，不把它扩展成物理域外预测。

完整逐秒或逐分钟工作簿、正文采样表与达标时刻均源自同一条轨迹。最后才转换 K→°C、s→h，并进行四位显示舍入。问题二和问题三复用 Q23 的同一个 `Run`，避免场表和事件时间来源不同。

## A.15 圆柱 Robin–Bessel 解析基准

常系数圆柱扩散的特征函数方法可参见 Crank[4]。本节只对问题一常热物性热方程展开当前时变边界下的推导，令 $\alpha=k/B$、$x=r/R_0$、$v(x,t)=T(x,t)-T_\infty(t)$。由于外界温度在空间均匀，有

<!-- EQ_A_BESSEL_FORCED_PDE -->
$$
\begin{aligned}
v_t&=\frac{\alpha}{R_0^2}\frac1x(xv_x)_x-\dot T_\infty(t),\\
v_x(0,t)&=0,\qquad v_x(1,t)+Bi_hv(1,t)=0,\\
Bi_h&=\frac{hR_0}{k}.
\end{aligned}
$$

$Bi_h$ 为该常系数热问题的 Biot 数。空间特征方程为 $(xX')'+\mu^2xX=0$，轴心有界的解取第一类零阶 Bessel 函数 $X(x)=J_0(\mu x)$；第二类函数在轴心发散而舍去。利用 $J_0'(z)=-J_1(z)$，表面 Robin 条件给出特征根

<!-- EQ_A_BESSEL_ROOT -->
$$
\mu_nJ_1(\mu_n)=Bi_hJ_0(\mu_n),
\qquad
\lambda_n=\frac{\alpha\mu_n^2}{R_0^2},
\qquad n=1,2,\ldots.
$$

$\lambda_n$ 为正的模态衰减率，单位 $\mathrm{s^{-1}}$。

本题 $Bi_h$ 有限且大于零，设 $j_{\nu,n}$ 为 $J_\nu$ 的第 $n$ 个正零点，根的计算可在下列区间分别包围并求解：

<!-- EQ_A_BESSEL_ROOT_BRACKETS -->
$$
0<\mu_1<j_{0,1},\qquad
j_{1,n-1}<\mu_n<j_{0,n}\quad(n\ge2).
$$

该区间选择与现行解析基准源码一致，避免用等距扫描漏根。绝热 $Bi_h=0$ 时包含零模态，均匀初态保持不变，应单独处理；不能把这一极限直接代入只列正根的展开流程。对两个不同正根，将特征方程交叉相乘、相减并积分，边界项因同一 Robin 条件消失，得到带圆柱权重 $x$ 的正交性：

<!-- EQ_A_BESSEL_ORTHOGONALITY -->
$$
\int_0^1 xJ_0(\mu_mx)J_0(\mu_nx)\,\mathrm dx=0
\quad(m\ne n).
$$

均匀函数的投影系数需要以下两项积分：

<!-- EQ_A_BESSEL_INTEGRALS -->
$$
\int_0^1xJ_0(\mu_nx)\,\mathrm dx
=\frac{J_1(\mu_n)}{\mu_n},
\qquad
\int_0^1xJ_0(\mu_nx)^2\,\mathrm dx
=\frac{J_0(\mu_n)^2+J_1(\mu_n)^2}{2}.
$$

因此常数 1 的加权展开系数为

<!-- EQ_A_BESSEL_COEFFICIENT -->
$$
b_n=
\frac{2J_1(\mu_n)}
{\mu_n[J_0(\mu_n)^2+J_1(\mu_n)^2]}.
$$

令 $v=\sum_na_n(t)J_0(\mu_nx)$，将式 [EQ_A_BESSEL_FORCED_PDE] 投影到每一特征函数，得

<!-- EQ_A_BESSEL_MODE_ODE -->
$$
\dot a_n+\lambda_na_n=-b_n\dot T_\infty(t),
\qquad a_n(0)=b_n[T_0-T_\infty(0)].
$$

使用积分因子求解该一阶常微分方程，得到时变边界的圆柱热场基准

<!-- EQ_A_BESSEL_SOLUTION -->
$$
\begin{aligned}
T(x,t)=T_\infty(t)+\sum_{n=1}^{\infty}b_nJ_0(\mu_nx)
\Bigg[&[T_0-T_\infty(0)]e^{-\lambda_nt}\\
&-\int_0^t e^{-\lambda_n(t-\tau)}\dot T_\infty(\tau)\,\mathrm d\tau\Bigg].
\end{aligned}
$$

这里的解析基准包含附件给定时变温度的卷积，不是恒温阶跃公式。外界温度在一段 $[a,b]$ 内线性变化、斜率为 $s$ 时，该段在 $t\ge b$ 的卷积贡献为

<!-- EQ_A_PIECEWISE_CONVOLUTION -->
$$
\int_a^b e^{-\lambda_n(t-\tau)}s\,\mathrm d\tau
=\frac{s}{\lambda_n}
\left[e^{-\lambda_n(t-b)}-e^{-\lambda_n(t-a)}\right].
$$

若 $t$ 落在当前段，则把上限截为 $b=t$；尚未开始的段不贡献。分段线性导数在节点处的跳变不影响该积分；若要推广到边界值本身跳变的时刻，必须另外处理对应阶跃，不能只积普通斜率。

对固定半径且常扩散率 $D_*$ 的水分验证特例，同样令 $Bi_m=\beta R_0/D_*$、$\lambda_n=D_*\mu_n^2/R_0^2$，将 $T,T_\infty,T_0$ 替换为 $C,C_{eq},C_0$ 即可构造相同类型的线性基准。这个特例只用于检验算法，不替代正式 $D_1(C)$ 非线性水分结果，也不能验证 Q23/Q4 的变物性收缩问题。

## A.16 解析比较的点值、单元平均及误差范围

本文生产未知量按节点点值解释，主要比较 $T_i$ 与 $T(x_i,t)$。若为了诊断另外比较解析环体平均，应明确使用

<!-- EQ_A_BESSEL_CELL_AVERAGE -->
$$
\begin{aligned}
\left\langle J_0\right\rangle_i
&=\frac{1}{w_i}\int_{a_i}^{b_i}xJ_0(\mu x)\,\mathrm dx\\
&=\frac{b_iJ_1(\mu b_i)-a_iJ_1(\mu a_i)}{\mu w_i}.
\end{aligned}
$$

式 [EQ_A_BESSEL_CELL_AVERAGE] 与节点点值 $J_0(\mu x_i)$ 不是同一个对象。尤其表面控制体为单侧区间，若梯度非零，平均值与端点值之差可为 $O(\Delta x)$；不能把这种表示差异直接称为物理误差。

对指定公共采样集合 $\mathcal S$，定义点值最大差和均方根差

<!-- EQ_A_COMPARISON_METRICS -->
$$
\begin{aligned}
E_\infty&=\max_{(t,r)\in\mathcal S}|U_N(t,r)-U_{ref}(t,r)|,\\
E_{RMS}&=\sqrt{\frac1{|\mathcal S|}
\sum_{(t,r)\in\mathcal S}[U_N(t,r)-U_{ref}(t,r)]^2}.
\end{aligned}
$$

$U$ 可表示温度或含水率，$U_{ref}$ 是明确指定的解析解或更细数值轨迹。解析级数实际截为有限项，需另比较 120、240、480 等截断项数；截断差估计不自动成为全空间全时间的严格上界。正文 N3200 常热物性温度与解析基准在 1801 个整数秒、21 个半径点上的最大差约为 $1.804\times10^{-6}\,\mathrm K$，只支持该比较范围内的实现一致性。

早期及本轮独立复核中，冻结扩散率的 N400 密集样点最大水分误差为 $2.875083008730961\times10^{-4}$，超过当时 $10^{-4}$ 门槛；N800 对应约 $7.158659870798445\times10^{-5}$。程序外层退出 0 不改变该内部不通过结果。另一个历史脚本得到的点值/环体平均差随 N800→6400 逐次约减半，而其静态解释称“不随细化减少”；本附录按实际数值与式 [EQ_A_BESSEL_CELL_AVERAGE] 解释，不采纳该错误文字结论。

## A.17 方法比较、收缩尺度与参数敏感性

在不同空间网格间比较时，采用相同物性、环境、边界、初态及时间判据，在共同物理位置上求差；问题四排除较小当前域之外的位置并单列真实表面。若观察到幂律误差 $E_N\approx KN^{-p}$，两倍加密下可计算观察阶

<!-- EQ_A_OBSERVED_ORDER -->
$$
p_{obs}=\frac{\ln(E_N/E_{2N})}{\ln2}.
$$

该式仅在误差度量一致且进入渐近区时具有通常的阶数解释；若只有两条未知误差数值解，则它们的差本身并非真实误差。正式正文分别采用 Q1/Q23 的 N1600/N3200 和 Q4 的 N3200/N6400 比较，并在最细网格保持空间设置不变、同时收紧容差和最大步长检查时间敏感性。本轮没有为本附录新增正式 PDE 重算；旧全秒空间投影未全部保留的限制继续保留，不将摘要差值冒充重新全量回放。

对另一守恒水分面格式，可将相邻 $D_i,D_{i+1}$ 的调和平均乘浓度差，与式 [EQ_A_WATER_FACE] 对比。常 $D$ 时两式退化为同一个线性面量；变量 $D$ 时差别属于空间离散。现行 `method_comparison.py --quick` 的 8 条 Q1 轨迹实际完成，变量 D 的 N100 与 N200 两格式最大差约为 $1.4891\times10^{-5}$ 和 $3.7288\times10^{-6}$，观察阶约 1.9977。历史粗网格调和格式严重偏离时长的记录不能用来否定调和平均在所有问题中的适用性，但足以说明本题不能采用未加密检查的粗网格答案。

从式 [EQ_A_MATERIAL_PDE] 看，在给定参考扩散率 $D_{ref}$ 下，内部扩散自然累积尺度为

<!-- EQ_A_SHRINK_TIME_SCALE -->
$$
\tau(t)=\int_0^t\frac{D_{ref}}{R(s)^2}\,\mathrm ds,
\qquad
\widetilde t(t)=R_0^2\int_0^t\frac{1}{R(s)^2}\,\mathrm ds.
$$

$\tau$ 无量纲，$\widetilde t$ 的单位为秒。该换算只揭示几何缩短路径的尺度，Robin 边界中的 $R$、随状态变化的物性和温湿反馈同时存在，所以不能由 $R^2$ 比例直接得出精确全过程时长。使用仿真事件作积分上限的尺度核对也不构成独立求得的解析烘干时间。

分离收缩影响时，应固定附录 4 的全部物性、初态、环境和数值设置，只改变 $R(t)$。正文已有 N200 对照：定半径临界时长约 129.8452 h，给定收缩约 51.0910 h。问题三与问题四的正式时长差约 6.3818 h 同时含物性与几何变化，不能全部归因于收缩。对照网格 N200 用于所列机理比较，不替代 Q4 N6400 正式结果。

参数敏感性必须真正进入正在使用的面通量。以扩散前因子倍率 $s_D$、导热率倍率 $s_k$ 为例，应分别将式 [EQ_A_WATER_FACE] 中的 $D_0$ 和热面中的 $k$ 同步改变。只修改未被 Kirchhoff 分支读取的节点 D 数组，可能使所谓扩散参数扰动实际没有进入 RHS，不能作为有效敏感性结果。已采用的修复后 N200 单参数扫描表明，$s_D$ 从 0.7 增至 1.4 时，问题三临界时长由约 79.4187 h 降至 43.0796 h，问题四由 70.4059 h 降至 38.3160 h；$k$ 在±15%范围内变化时，两问时长跨度均小于 0.011%。这些是指定工况的一维参数扫描，不能扩大为完整全局敏感性排序，未完成的 Sobol 和旧无效 Morris 注入不采纳。

## A.18 经验边界阻力及潜热情景的推导范围

为展示气固映射未标定的影响，可在 $C_s\ge C_{ref}=0.05$、$p\ge1$ 的限定下定义如下经验关系。分式适用于 $C_s>C_{ref}$；在 $C_s=C_{ref}$ 处按连续延拓定义 $K_p(C_{ref})=1/p$，不直接计算 $0/0$：

<!-- EQ_A_EMPIRICAL_RESISTANCE -->
$$
\begin{aligned}
K_p(C_s)&=\frac{1-(C_{ref}/C_s)^{1/p}}{1-C_{ref}/C_s}
\quad(C_s>C_{ref}),\\
K_p(C_{ref})&=\frac1p,\\
j_{w,out}&=\rho_d\beta K_p(C_s)(C_s-C_{eq}).
\end{aligned}
$$

$p$ 为无量纲经验参数。取 $z=C_{ref}/C_s\in(0,1]$、$q=1/p\in(0,1]$。由 $z^q\ge z$ 与凹函数 $z^q$ 在 1 处的切线不等式 $z^q\le1+q(z-1)$，得到

<!-- EQ_A_EMPIRICAL_RESISTANCE_BOUNDS -->
$$
\begin{aligned}
q(1-z)&\le1-z^q\le1-z,\\
\frac1p&\le K_p(C_s)\le1,\qquad K_1(C_s)=1,\\
\lim_{C_s\downarrow C_{ref}}K_p(C_s)&=\frac1p.
\end{aligned}
$$

这个族包含原边界并可控地减弱所设传质驱动，但不是由实测材料等温线推得的唯一边界。界限仅在上述 $C_s,p$ 范围成立。正文历史 N800 的 $p=1,2,4$ 情景保留为条件数值比较，不据几个参数点证明所有 $p$ 下时长单调，也不能作为真实烘干时长下界。当前旧经验闭合源码存在参数接口和结果数组方向问题，本轮 sandbox 没有把该批历史情景重新完整跑通；p=1 代数恒等性检查不能替代其原入口复现。

若另指定比例 $\chi$ 的外流水在表面汽化，汽化潜热为 $L_v$，则热边界梯度面量改为

<!-- EQ_A_LATENT_SCENARIO -->
$$
g_s^T=hR(T_\infty-T_s)
-R\chi L_v\rho_d\beta(C_s-C_{eq}).
$$

$\chi=0$ 恢复正式基线，$L_v$ 单位为 J/kg；加入 $K_p$ 情景时，蒸发质量项也须一致乘 $K_p(C_s)$。固定求值时刻下，不含 $K_p$ 的潜热项对 $C_s$ 的偏导为 $-R\chi L_v\rho_d\beta$，应加入表面热行，累计失水方程保持与实际水边界一致。这类情景约定了蒸发位置和比例，但没有识别真实气膜传递、凝结、吸附热或内部相变，不能声称补入一个潜热项就完成总热力学闭合。

## A.19 公式与现行程序的对应关系及验证限度

`03_程序代码/dryingCore.py` 对应物性、材料网格、面量、半离散 RHS、事件监测、物理位置查询及质量诊断；`analyticJacobian.py` 对应解析导数装配；`diskDense.py` 对应式 [EQ_A_BDF_DENSE] 及断点选择；`q1Model.py`、`q2Model.py`、`q4Model.py` 分别给出正式 N3200、N3200、N6400 参数；`q3Model.py` 对应式 [EQ_A_STRICT_REPORT] 的上取候选及严格核验。`exportOutputs.py` 负责从同一未关闭轨迹导出、舍入和回读，`runDelivery.py` 与 `runLogged.ps1` 记录执行、输入及退出状态。现行支撑源码及追加的数据处理、绘图源码在后续源码附录完整列出，文件数与逐行清单以该附录为准；各文件仍应保持原有模块边界，不能合并成一个可运行文件。

2026-09-13 实际 Windows Sandbox 正式 03 重算采用独立运行库及禁网环境，原宿主工作区不可见；三条正式网格轨迹和四表回读完成，9,335,598 个工作簿格及 297 个正文格核验，21 个保存数组与冻结参照逐值一致，严格报告时长未变。该证据支持当前源码的数值复现，不提供内部温湿实验准确率。

05 检验目录的 31 个 Python 源码在实际 sandbox 中有原入口或函数调用覆盖，29 项 Python 任务中 24 项退出 0、5 项退出 1。其范围包含小网格与函数级检查，没有把所有默认长批次写成完整通过。Bessel 的 8 项自检、Jacobian 的 84 状态与 336 方向检查，以及三条 N40 内存/磁盘轨迹的 38,337 次查询一致性分别承担解析实现、局部线性化和存储等价性检查。Node 对照入口缺少旧 MATLAB 结果输入而失败；该 sandbox 没有 MATLAB 运行环境，历史 MATLAB 对照与本轮 Python 重算分别记录。

旧 M-K 顺序统计对常数序列产生伪趋势、经验闭合旧 B 参数接口失败、时间与空间数组反向访问、替代 Jacobian 注入没有被调用、N400 解析误差门槛未过等问题均保留。公式推导不将这些历史程序的存在或退出 0 视为科学结论。正文采用的有限网格差、参数扫描及条件情景，只在其明确输入、版本、网格、时间和采样范围内解释。

完整连续场误差界、真实材料等温线、内部温湿测量以及完整组分能量关系尚不由当前附件提供。以后若修改这些闭合、物性或收缩运动，须从组分守恒重新检查方程并重新求解；本附录的代数正确性与实现自洽性不能替代这些外部证据。

## A.20 推导依据

本附录沿用正文文献序号。扩散理论支持通量和圆柱基准的一般构造；有限体积文献支持积分离散框架；常微分方程算法论文和 SciPy 文档支持时间求解方法。题给物性系数、气固映射、有效热容量与同比收缩假设均由本模型另行声明，不能用这些一般文献替代实验标定。

[4] CRANK J. The mathematics of diffusion[M]. 2nd ed. Oxford: Clarendon Press, 1975.

[5] EYMARD R, GALLOUËT T, HERBIN R. Finite volume methods[M]//CIARLET P G, LIONS J L, eds. Handbook of numerical analysis. Vol. 7. Amsterdam: North-Holland, 2000: 713–1018. DOI: 10.1016/S1570-8659(00)07005-8.

[6] BYRNE G D, HINDMARSH A C. A polyalgorithm for the numerical solution of ordinary differential equations[J]. ACM Transactions on Mathematical Software, 1975, 1(1): 71–96. DOI: 10.1145/355626.355636.

[7] THE SCIPY COMMUNITY. scipy.integrate.BDF[EB/OL]. [2026-09-12]. https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.BDF.html.
