# 解析Jacobian数学附录：从物理通量到BDF Newton矩阵

2026-09-10。独立推导，读取已冻结paper_output/code/modeling/analytic_jacobian.py及其所导出的drying_core.RadialModel.rhs。解析Jacobian源码SHA256为d7dfda75b335e82eb27d39b8e2f12edf5a56254269ff4f273e7a828ed75a8665。本附录不修改代码、不新运行数值计算；已有验证记录的状态单独说明。

本文件共登记**26个公式块，J01—J26**。块内相关等式合并计数，不把这26块称为题目天然唯一要求的公式数。它们是主物理模型在数值求解阶段的导数与线性化，既不增加物理定律，也不改变题给经验参数。主物理公式E/M/K及二维公式A另有各自登记。

## 1. 先说明用途、变量和量纲

Jacobian的用途是在隐式时间推进中回答：**某节点温度或含水率轻微改变时，各节点的瞬时升温率、失水率怎样改变？** 它对已经选定的空间离散ODE右端求导，帮助Newton线性化。它不是物性实验拟合，也不是对初值/参数的统计回归。

**J01：状态、ODE和Jacobian定义。自变量为当前固定时刻t及状态向量y；因变量为右端f与矩阵J。**

\[
\begin{aligned}
\mathbf y&=(T_0,C_0,T_1,C_1,\ldots,T_N,C_N,\ell)^\mathsf T,\qquad n=N+1,\\
\dot{\mathbf y}&=\mathbf f(t,\mathbf y),\qquad
J_{ab}(t,\mathbf y)=\left.\frac{\partial f_a}{\partial y_b}\right|_t,\qquad
\mathbf J\in\mathbb R^{(2n+1)\times(2n+1)} .
\end{aligned}\tag{J01}
\]

T单位K；C和累计失水ℓ单位均为χ=kg水/kg干物质。虽然χ的SI基本量纲为无量纲，仍保留其物理基准标记。T行时间导数单位K/s，C/ℓ行单位χ/s。因此JTT、JCC和JℓC单位s⁻¹，JTC单位K/(χ·s)，JCT单位χ/(K·s)。不能不加说明将整个混合状态矩阵的每个元素都称为s⁻¹。

在对y求偏导时，t、外部给定R(t)、T∞(t)、Ceq(t)、配置参数h/β/潜热系数、固定网格和初始定标ρd0都保持不变。即使Q4半径随t变，也不在本Jacobian中额外求∂R/∂C：当前R来自观测驱动，而非把收缩本构作为未知状态。

## 2. 连续物理模型到半离散右端

**J02：导数应当对应的连续方程。自变量为材料位置x、t；因变量为T、C。**

\[
B(C)T_t=\frac1{R(t)^2x}\partial_x[xk(C)T_x],\qquad
C_t=\frac1{R(t)^2x}\partial_x[xD(C,T)C_x],\qquad B=\rho_{\rm eff}c_p .
\tag{J02}
\]

来源是圆柱薄壳热/干基水守恒，Q4采用同比径向材料坐标。题给ρ在这里是有效热容量密度，干质量密度另守恒；这一物理约定见主稿M23—M31。D随T/C变时，温度扰动会改变水流；k和B随C变时，含水率扰动会改变热流和升温率。这两条因果链对应Jacobian中的交叉块，不能只保留纯温度或纯水分三对角项。

**J03：有限体积右端及其几何因子。输入为节点状态、网格和R；输出为各节点的时间导数。**

\[
\begin{aligned}
w_i&=\frac{x_{i+1/2}^2-x_{i-1/2}^2}{2},\qquad
g_{i+1/2}=\frac{x_{i+1/2}}{\Delta x},\\
H_i&=G^T_{i+1/2}-G^T_{i-1/2},\qquad
M_i=G^C_{i+1/2}-G^C_{i-1/2},\\
s_i^T&=\frac1{R^2w_iB_i},\qquad s_i^C=\frac1{R^2w_i},\\
f_i^T&=s_i^TH_i,\qquad f_i^C=s_i^CM_i .
\end{aligned}\tag{J03}
\]

推导：J02乘x积分于节点对偶环，积累近似为wi乘节点导数，空间散度成为界面差。此处G为代码采用的“正坐标方向扩散梯度通量”，例如GT=xkTx；实际向外传导热通量带负号。GT单位W/m，GC单位m²χ/s；乘相应s后得到K/s与χ/s。g为无量纲几何因子。沿用这种符号时，内部同一面G对左单元为正贡献、对右单元为负贡献。

## 3. 经验物性与链式法则

**J04：仅用于Newton试探的系数延续。输入为当前C；输出为系数用c及其局部导数aC。**

\[
c_i=\max(C_i,\varepsilon_C),\quad \varepsilon_C=10^{-12},\qquad
a_i^C=\begin{cases}1,&C_i>\varepsilon_C,\\0,&C_i<\varepsilon_C.\end{cases}
\tag{J04}
\]

物理可接受状态C远大于εC时，c=C、aC=1。它不裁剪已求得状态，只防止非线性试探误入经验指数的非法值。阈值恰好相等时max不可微，冻结实现采用下侧分支导数0；这是数值延续的选定单侧值，不是物理材料在该点的真实光滑导数。所有通过aC相乘的后续导数均由链式法则而来。

**J05：ρ、cp、k对含水率的偏导。输入为c及所选附录；输出为热物性导数。**

\[
\begin{aligned}
\rho(c)&=\rho_a+\rho_bc,&\quad \rho_C&=\rho_ba^C,\\
c_p(c)&=c_{pa}+c_{pb}\frac c{1+c},
& (c_p)_C&=\frac{c_{pb}}{(1+c)^2}a^C,\\
k(c)&=k_a+k_b\frac c{1+c},
& k_C&=\frac{k_b}{(1+c)^2}a^C .
\end{aligned}\tag{J05}
\]

推导：c/(1+c)的导数=[(1+c)−c]/(1+c)²=1/(1+c)²，再乘J04的dc/dC。Q23取ρb=128、cpb=2736、kb=0.38；Q4取90、2150、0.20。Q1常热物性下三者都为0。constant_thermal校验模式将热物性固定，则无论问题标签也必须把三项导数置0；不能让被关闭的物性依赖留在Jacobian中。

**J06：体积热容量的乘积导数。输入为ρ、cp及其导数；输出为BC。**

\[
B_i=\rho_i(c_p)_i,\qquad
(B_C)_i=(\rho_C)_i(c_p)_i+\rho_i((c_p)_C)_i,\qquad
\frac{(B_C)_i}{B_i}=\frac{(\rho_C)_i}{\rho_i}+
\frac{((c_p)_C)_i}{(c_p)_i}.
\tag{J06}
\]

这是乘积法则。B单位J/(m³K)，BC单位J/(m³Kχ)。导数将在热右端分母中出现；仅对界面导热k求导会漏掉这一贡献。

**J07：扩散系数偏导。输入为C、T和参数a、D0、BD；输出为DC和DT。**

\[
D=D_0\exp(-a/c)\exp(-B_D/T),\qquad
D_C=D\frac a{c^2}a^C,\qquad
D_T=D\frac{B_D}{T^2}.
\tag{J07}
\]

推导：对lnD=lnD0−a/c−BD/T求导后乘D。Q1取a=0.89、D0=7e−9、BD=0；Q23取0.45、2.4e−3、3850K；Q4取0.30、4.2e−4、3850K。constant_D模式的D是配置常量，故DC=DT=0，并回到常系数水面通量。BD专指Arrhenius温度常数，与体积热容量B(C)不同。

## 4. 调和平均界面的通量偏导

**J08：两个正系数串联阻力的导数。输入为左/右系数a、b；输出为调和平均及其两侧偏导。**

\[
\mathcal H(a,b)=\frac{2ab}{a+b},\qquad
\mathcal H_a=\frac{2b^2}{(a+b)^2},\qquad
\mathcal H_b=\frac{2a^2}{(a+b)^2}.
\tag{J08}
\]

调和平均来自两个等半距离的扩散/导热阻力相加；偏导由商法则得到，例如∂a(2ab/(a+b))=[2b(a+b)−2ab]/(a+b)²。它们非负，表示一侧系数增加不会降低等效通量能力。

冻结实现将分母替换为max(a+b,τtiny)。在a+b<τtiny的非物理下溢延续分支，分母按常数处理，偏导为2b/τtiny、2a/τtiny；a+b>τtiny时采用上式。相等处不可微，采用选定分支。物理正系数区间的推导不依赖这一机器下溢保护。

**J09：内部导热面四个状态偏导。输入为TL、CL、TR、CR；输出为该面的GT及其梯度。**

\[
\begin{aligned}
\Delta T&=T_R-T_L,\quad K_f=\mathcal H(k_L,k_R),\quad G_f^T=g_fK_f\Delta T,\\
\partial_{T_L}G_f^T&=-g_fK_f,&
\partial_{T_R}G_f^T&=g_fK_f,\\
\partial_{C_L}G_f^T&=g_f\mathcal H_a(k_L,k_R)(k_C)_L\Delta T,&
\partial_{C_R}G_f^T&=g_f\mathcal H_b(k_L,k_R)(k_C)_R\Delta T .
\end{aligned}\tag{J09}
\]

温度偏导来自ΔT的±1，因为本题k只依赖C；含水率偏导来自k(C)→调和平均→热通量的链式法则。即使TL=TR使含水率偏导为零，温度偏导仍非零，不能将“本面当前通量为零”误作“本面所有导数为零”。

**J10：调和扩散面四个偏导。输入为四个状态；输出为GC及其梯度。**

\[
\begin{aligned}
\Delta C&=C_R-C_L,\quad D_f=\mathcal H(D_L,D_R),\quad G_f^C=g_fD_f\Delta C,\\
\partial_{T_L}G_f^C&=g_f\mathcal H_a(D_L,D_R)(D_T)_L\Delta C,\\
\partial_{T_R}G_f^C&=g_f\mathcal H_b(D_L,D_R)(D_T)_R\Delta C,\\
\partial_{C_L}G_f^C&=g_f[\mathcal H_a(D_L,D_R)(D_C)_L\Delta C-D_f],\\
\partial_{C_R}G_f^C&=g_f[\mathcal H_b(D_L,D_R)(D_C)_R\Delta C+D_f].
\end{aligned}\tag{J10}
\]

温度只能经D改变通量；含水率既改变D，也改变直接驱动力ΔC，故必须同时保留物性链式项和末尾±Df。物理区C=c；冻结调和分支的直接差ΔC使用原状态C，所以即使某非物理试探点系数导数因J04为0，驱动力的±1仍应保留。constant_D模式仅余±gDf，其温度导数为0。

## 5. Kirchhoff非线性面通量偏导

**J11：浓度势及非近等分支导数。输入为CL、CR；输出为势差P及其两侧偏导。**

\[
\begin{aligned}
\Phi(c)&=c e^{-a/c}+a\,{\rm Ei}(-a/c),\qquad \Phi'(c)=e^{-a/c},\\
P&=\Phi(c_R)-\Phi(c_L),\\
P_{C_L}&=-e^{-a/c_L}a_L^C,\qquad
P_{C_R}=e^{-a/c_R}a_R^C .
\end{aligned}\tag{J11}
\]

原函数推导：第一项求导为exp(−a/c)(1+a/c)，第二项利用Ei'(z)=ez/z得到−aexp(−a/c)/c，两者相加仅剩exp(−a/c)。势差再按链式法则求两侧导数；无需对特殊函数作数值差分。

**J12：接近相等浓度时的稳定分支及精确分支导数。输入为cL、cR；输出为替代势差Pm及偏导。**

\[
\begin{aligned}
\bar c&=(c_L+c_R)/2,\quad \delta c=c_R-c_L,\quad
q(\bar c)=e^{-a/\bar c},\quad q'(\bar c)=q(\bar c)a/\bar c^2,\\
|\delta c|&<10^{-7}\max(\bar c,10^{-3})
\quad\Longrightarrow\quad P_m=q(\bar c)\delta c,\\
\partial_{C_L}P_m&=\left[\tfrac12q'(\bar c)\delta c-q(\bar c)\right]a_L^C,\\
\partial_{C_R}P_m&=\left[\tfrac12q'(\bar c)\delta c+q(\bar c)\right]a_R^C .
\end{aligned}\tag{J12}
\]

势差在δc很小时可能发生浮点相消，用中点导数乘δc作为一致稳定近似。对当前实际采用的Pm求导：中点对两侧导数均为1/2，而δc对左/右分别−1/+1，于是得到两项。**这里必须求实现中稳定分支的导数，不能稳定分支仍套J11而称完全解析一致。**

分支切换面上的指示函数不可微，不额外形式化求“指示函数导数”；冻结实现使用当前活动分支的局部导数。接近但不在切换面的状态，以上严格是该实现分支的偏导；δc=0时两侧退化为−q、+q，与原势极限一致。

**J13：Kirchhoff面四个偏导。输入为四状态及当前势差分支；输出为GC梯度。**

\[
\begin{aligned}
\bar T&=(T_L+T_R)/2,\qquad
K_f^C=g_fD_0e^{-B_D/\bar T},\qquad G_f^C=K_f^C P,\\
\partial_{T_L}G_f^C&=
\partial_{T_R}G_f^C=
G_f^C\frac{B_D}{2\bar T^2},\\
\partial_{C_L}G_f^C&=K_f^C P_{C_L},\qquad
\partial_{C_R}G_f^C=K_f^C P_{C_R}.
\end{aligned}\tag{J13}
\]

温度链式法则给出∂TLexp(−BD/Tbar)=exp(−BD/Tbar)BD/(2Tbar²)；P与温度无关。两个温度偏导相等是采用对称面温的结果，不意味着整个温度/水分Jacobian对称。Q1 BD=0，两温度导数均零。

面温冻结只表示**面附近空间上用一个对称T值评价系数**，不表示在Newton线性化时把该面温从状态依赖中删掉。仍须保留上面的温度偏导。也不能把完整exp(−BD/Ti)Φ(Ci)跨节点差分，否则改变了原连续通量。

## 6. 把面导数组装为各节点Jacobian

**J14：内部同一面对应的四行块。输入为GT/GC对四个面状态的导数；输出为左、右相邻单元Jacobian贡献。**

\[
\begin{array}{ll}
\displaystyle \partial_{y_b}f_i^T\big|_f=+s_i^T\partial_{y_b}G_f^T,
&\displaystyle \partial_{y_b}f_{i+1}^T\big|_f=-s_{i+1}^T\partial_{y_b}G_f^T,\\[4pt]
\displaystyle \partial_{y_b}f_i^C\big|_f=+s_i^C\partial_{y_b}G_f^C,
&\displaystyle \partial_{y_b}f_{i+1}^C\big|_f=-s_{i+1}^C\partial_{y_b}G_f^C,
\end{array}
\quad y_b\in\{T_i,C_i,T_{i+1},C_{i+1}\}.
\tag{J14}
\]

从J03的界面差直接求偏导。此处暂把热比例因子sT固定，下一块再补分母变化。相邻单元守恒要求同一个面导数以相反符号进入，不能为两侧分别近似成不一致通量。不同单元w/B会改变数值系数大小，因此单看矩阵条目不一定互为相反数；乘回物理体积权重才体现守恒。

**J15：热容量分母的本地偏导。输入为热通量净量Hi、B(Ci)；输出为必须附加到本地T行/C列的项。**

\[
\begin{aligned}
\frac{\partial f_i^T}{\partial C_j}
&=s_i^T\frac{\partial H_i}{\partial C_j}
-\delta_{ij}\frac{H_i}{R^2w_iB_i^2}(B_C)_i\\
&=s_i^T\frac{\partial H_i}{\partial C_j}
-\delta_{ij} f_i^T\frac{(B_C)_i}{B_i}.
\end{aligned}\tag{J15}
\]

商法则：fT=Hi/(R²wiBi)，只有j=i会改变该单元分母。BC并不是需要另加到热方程的能量源，而是**既有温度右端对状态的导数**，二者概念不同。若升温率fT>0且BC>0，提高含水率增加热容量会降低同净热流下的升温率，所以附加项为负，物理意义与代数符号一致。

Hi必须包括边界显热及当前启用的潜热负荷后再求fT；如果先用不含潜热的fT计算分母导数，会遗漏潜热负荷经B变化引起的敏感性。

**J16：水方程分母不含当前C。输入为Mi及给定R、wi；输出为水Jacobian行。**

\[
\frac{\partial f_i^C}{\partial y_b}
=\frac1{R^2w_i}\frac{\partial M_i}{\partial y_b},
\qquad
\partial_{y_b}(R^2w_i)=0.
\tag{J16}
\]

这是当前材料干基模型的结构：空间均匀干骨架密度已在方程中约去，R是外部时间函数。不应套用热容量类似项再给水方程添加ρeff/(1+C)导数，否则会换回已经证明不相容的质量口径。若将来改成自洽的状态依赖收缩/非均匀干密度模型，Jacobian也必须重新推导，本附录不能直接覆盖。

## 7. 中心、表面与累计失水

**J17：中心边界导数。输入为任意状态；输出为中心内侧面通量及其导数。**

\[
G^T_{-1/2}=G^C_{-1/2}=0,\qquad
\frac{\partial G^T_{-1/2}}{\partial y_b}
=\frac{\partial G^C_{-1/2}}{\partial y_b}=0 .
\tag{J17}
\]

中心界面面积为零且对称无流量。中心节点本身仍通过第一个内部面变化，并非T0或C0的ODE为零；它的非零Jacobian由J14和J15给出。不得为避免1/r而把中心节点冻结。

**J18：表面Robin与潜热负荷偏导。输入为表面TN、CN；输出为边界GT、GC及梯度。**

\[
\begin{aligned}
\rho_d(t)&=\rho_{d0}(R_0/R)^2,\qquad
\Lambda_s(t)=R f_{\rm lat}L_v\rho_d(t)\beta,\\
G_s^T&=-hR(T_N-T_\infty)-\Lambda_s(C_N-C_{eq}),\\
G_s^C&=-\beta R(C_N-C_{eq}),\\
\partial_{T_N}G_s^T&=-hR,\quad
\partial_{C_N}G_s^T=-\Lambda_s,\quad
\partial_{T_N}G_s^C=0,\quad
\partial_{C_N}G_s^C=-\beta R .
\end{aligned}\tag{J18}
\]

先把原表面法向通量按材料坐标转换为G，再对当前状态求导。ρd只随外部R(t)变，在本Jacobian对CN求偏导时为常量；不应误乘ρeff(C)的额外导数。热边界四项乘表面sT/sC进入各行，另加J15的表面热容量项。

f_lat=0时Λs=0。f_lat=1的已有试验只是等效Ceq下的全量表面潜热负荷压力测试，气固饱和限制见physics_physical_sensitivity_review.md；解析导数正确不代表该能量情景已成为完整真实蒸发模型。若改用aw(C,T)得到的真实气侧通量，∂TN GC通常不再为零，并且所有边界偏导需重写。

**J19：累计失水状态的一行和一整列。输入为CN和累计状态ℓ；输出为ℓ'及其导数。**

\[
f^\ell=\dot\ell=\frac{2\beta}{R}(C_N-C_{eq}),\qquad
\frac{\partial f^\ell}{\partial C_N}=\frac{2\beta}{R},\quad
\frac{\partial f^\ell}{\partial T_i}=0\quad(0\le i\le N),\qquad
\frac{\partial f^\ell}{\partial C_i}=0\quad(0\le i<N),
\qquad
\frac{\partial f_a}{\partial\ell}=0\quad\text{对所有行}a .
\tag{J19}
\]

累计量只记录已经流失多少水，不反馈材料传递。所以“最后一行只有表面浓度列非零”与“最后一整列严格为零”同时成立。温度列全部为零，所有非表面浓度列为零；累积列包括自己的对角也为零。不能通过扰动ℓ制造一个虚假的非零反馈导数。

## 8. 稀疏结构与守恒的导数检验

**J20：Jacobian分块结构。输入为节点局部耦合；输出为整体稀疏矩阵模式。**

\[
\mathbf J=
\begin{pmatrix}
\mathbf J_{\rm active}&\mathbf 0\\
\mathbf b^\mathsf T&0
\end{pmatrix},
\qquad
b_{C_N}=2\beta/R,\quad b_{\rm 其他}=0 .
\tag{J20}
\]

主动状态按T0,C0,…,TN,CN交错排列，Jactive为2×2节点块组成的块三对角矩阵，因为每个节点仅依赖自身及相邻节点；潜热及热容量项仍在本地块内。累计行形成一个被动附加行，不扩大主动热/质方程的物理作用范围。矩阵一般不对称，因为耦合方向、单位、物性和权重不同。

**J21：干基质量恒等式的Jacobian版本。输入为体积权重和J；输出为左零向量关系。**

\[
\bar C_d=2\sum_iw_iC_i,\qquad
\bar C_d+\ell=C_{\rm init},\qquad
\boldsymbol\omega^\mathsf T=(0,2w_0,0,2w_1,\ldots,0,2w_N,1),
\]
\[
\boldsymbol\omega^\mathsf T\mathbf f=0
\quad\Longrightarrow\quad
\boldsymbol\omega^\mathsf T\mathbf J=\mathbf0^\mathsf T .
\tag{J21}
\]

第一行由水有限体积求和内部通量抵消、表面出流由ℓ累计得到；在固定t对任意状态分量求导即得最后的矩阵关系。权重wi在材料x网格上固定，Q4同样适用。它是检查解析面组装及边界失水行是否一致的有效独立检验，而不是单看某些矩阵条目与数值差分接近。

## 9. BDF/NDF如何使用这个Jacobian

**J22：基本BDF隐式残差及Newton矩阵。输入为历史状态、当前试探值和时间步；输出为Newton增量。**

\[
\begin{aligned}
\mathbf R(\mathbf y^n)&=
\alpha_0\mathbf y^n+\sum_{j=1}^{k}\alpha_j\mathbf y^{n-j}
-h\,\mathbf f(t_n,\mathbf y^n),\\
\mathbf R(\mathbf y^{(m)}+\delta\mathbf y)
&\simeq\mathbf R(\mathbf y^{(m)})
+(\alpha_0\mathbf I-h\mathbf J)\delta\mathbf y,\\
(\alpha_0\mathbf I-h\mathbf J)\delta\mathbf y
&=-\mathbf R(\mathbf y^{(m)}),\qquad
\mathbf y^{(m+1)}=\mathbf y^{(m)}+\delta\mathbf y .
\end{aligned}\tag{J22}
\]

推导：BDF用历史插值导数近似当前时间导数；历史状态和系数在本次Newton迭代中固定。对非线性右端作一阶Taylor展开，移项得到线性方程。除以α0后求解矩阵为I−cJ，c=h/α0。解析Jacobian用于这个残差线性化，**不需要单独求J的逆**。

**J23：实际SciPy NDF修正/预测校正形式中的同一个矩阵。输入为后向差分历史、阶k、步长h；输出为校正d。**

\[
\begin{aligned}
\gamma_k&=\sum_{j=1}^{k}\frac1j,\qquad
\alpha_k^{\rm NDF}=(1-\kappa_k)\gamma_k,\qquad
c=\frac h{\alpha_k^{\rm NDF}},\\
\mathbf y_{\rm pred}&=\sum_{j=0}^{k}\mathbf D_j,\qquad
\boldsymbol\psi=\frac1{\alpha_k^{\rm NDF}}\sum_{j=1}^{k}\gamma_j\mathbf D_j,\\
\mathbf r(\mathbf d)&=\mathbf d-c\mathbf f(t_{n+1},\mathbf y_{\rm pred}+\mathbf d)
+\boldsymbol\psi,\qquad
\frac{\partial\mathbf r}{\partial\mathbf d}=\mathbf I-c\mathbf J .
\end{aligned}\tag{J23}
\]

当前SciPy实现的κ1…κ5分别为−0.1850、−1/9、−0.0823、−0.0415、0；自动阶数1—5。Dj是当前经过步长尺度调整的后向差分，不是本题扩散系数D(C,T)。由校正式对d求导时，ypred、ψ、c固定，故即使NDF修改历史系数，右端线性化仍需同一个∂f/∂y。

已只读核对本机SciPy 1.18.1的bdf.py，其中通过I−cJ稀疏分解解校正。实际求解器可能在若干Newton迭代间复用已有J或LU，并在需要时重算，这是修正Newton的计算策略；不能表述成每一次迭代都重新计算解析矩阵。可变阶与NDF机制亦见[SciPy BDF官方说明](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.BDF.html)。

**J24：零累计列为何不导致Newton累计块奇异。输入为J20结构和c；输出为Newton块结构及增量关系。**

\[
\mathbf I-c\mathbf J=
\begin{pmatrix}
\mathbf I-c\mathbf J_{\rm active}&\mathbf0\\
-c\mathbf b^\mathsf T&1
\end{pmatrix},\qquad
\begin{cases}
(\mathbf I-c\mathbf J_{\rm active})\delta\mathbf u=-\mathbf R_u,\\
\delta\ell=-R_\ell+c\mathbf b^\mathsf T\delta\mathbf u .
\end{cases}
\tag{J24}
\]

直接将J20代入；主动块如果可解，累计块对角为1，随后解出δℓ。J本身确有被动列为零，但隐式Newton矩阵有单位阵项，不因此奇异。解析地保留零列可避免对本来不影响任何右端的累计变量做无效数值差分自适应。

**J25：不同状态单位下的数值缩放。输入为固定正对角尺度S；输出为无量纲状态的Jacobian与Newton矩阵。**

\[
\mathbf y=\mathbf S\mathbf z,\quad
\dot{\mathbf z}=\mathbf S^{-1}\mathbf f(t,\mathbf S\mathbf z),\quad
\mathbf J_z=\mathbf S^{-1}\mathbf J_y\mathbf S,\quad
\mathbf I-c\mathbf J_z=\mathbf S^{-1}(\mathbf I-c\mathbf J_y)\mathbf S.
\tag{J25}
\]

推导：链式法则。S可按温度、干基含水率的典型变化量配置，但缩放只改善数值量级，不允许把缩放后的z直接代入原经验式。原混合状态的I−cJ非对角元素带“行变量/列变量”的单位比，乘对应δy后行量纲一致；全部状态无量纲化后，Jz元素均为s⁻¹、Newton矩阵为无量纲。实际生产当前通过不同atol/rtol进行误差尺度控制，不等于已经显式作了本块全部状态变量变换。

## 10. 如何验证推导而不以实现自证

**J26：方向导数与守恒检查。输入为独立方向v、扰动步ε及解析J；输出为导数偏差指标。**

\[
\mathbf J\mathbf v\approx
\frac{\mathbf f(t,\mathbf y+\epsilon\mathbf v)-
\mathbf f(t,\mathbf y-\epsilon\mathbf v)}{2\epsilon},
\]
\[
\eta_a=
\frac{|(\mathbf J\mathbf v)_a-(\delta_\epsilon\mathbf f)_a|}
{\mathrm{atol}_{J,a}+\mathrm{rtol}_J
\max(|(\mathbf J\mathbf v)_a|,|(\delta_\epsilon\mathbf f)_a|)},
\qquad
\max_a\eta_a\le1,
\quad \mathbf J\mathbf e_\ell=\mathbf0,\quad
\boldsymbol\omega^\mathsf T\mathbf J=\mathbf0^\mathsf T .
\tag{J26}
\]

Taylor展开在光滑当前分支下给出中心差分误差O(ε²)；使用三种递减步长时可识别截断与舍入/分支噪声。式中rtolJ与max相乘，atolJ,a和该乘积相加。现有自检rtolJ=5e−6，atolJ,a在每行已约定的输出数值单位下均取5e−10；a下标强调温度行与浓度行各有自身输出单位，η无量纲。扰动应覆盖温度、浓度、累计分量，且近等浓度稳定分支、潜热、收缩、常物性校验分支分别检查。边界开关、max延续和分支切换恰好不可微处，不能用跨分支中心差分宣称存在唯一经典Jacobian。

只读查验现有integrated_v3/analytic_jacobian_selftest.json：冻结源哈希一致、状态PASS，84个配置/状态组合，336个方向，每个方向3种差分步长，并检查零累计列与质量左零关系；另含4次短BDF接线检查。其用途是导数和接线验证，不是正式全程精度、模型真实性或GUI/人工审查。本轮没有新增运行。

## 11. 与整篇模型的衔接和审稿重点

1. J02沿用原物理PDE，解析Jacobian只更准确/稳定地求其离散ODE，不能将“换解析Jacobian后更稳定”写成新增物理假设或实验发现。
2. 内部面四偏导、J15热容量分母、J18表面负荷、J19累计行/列缺一不可。若主文只展示基础BDF或简化水扩散式，需明确它们是教学结构而非遗漏已实现交叉项。
3. 所有状态下标按T、C交错；x网格恒定、R是外部时变参数；BD、热容量B、差分历史Dj应分别定义。
4. 物理真值仍受等效湿度、热密度解释、潜热相容性等限制。导数验证不关闭这些物理缺口。
5. 全篇公式登记时，本文J01—J26计26块，和题给E01—E09、主模型M/K、二维A分别登记。扩展公式数量取决于选定方法，不能声称题面本身“唯一需要这么多公式”。
