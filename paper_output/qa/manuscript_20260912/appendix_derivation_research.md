# 附录 A 控制方程、守恒离散与求解算法的详细推导

<!-- research-handoff: 技术研究稿，供主代理编入正式 authoring_state 对应附录；本稿未修改冻结模型或重新求解生产轨迹。正文引用序号与全文公式编号由统稿统一。 -->

## A.1 干基含水率与组分质量守恒

以药材干物质骨架作为运动参考，记其速度为 $\boldsymbol u$，单位当前体积的干物质质量为 $\rho_d$，水质量为 $\rho_w$，水相对骨架的质量通量为 $\boldsymbol j_w$。干基含水率定义为 $C=\rho_w/\rho_d$，单位为 kg 水/kg 干物质。它可以大于 1，不是质量百分数。初值 $C_0=2.55$ 对应的湿基水分质量分数为

$$w_0=\frac{C_0}{1+C_0}=0.7183098592.$$

环境空气含湿量 $Y_\infty$ 的分母是干空气质量，与 $C$ 的分母不同。虽然数值单位都写成 kg/kg，把二者直接相减仍需要等效映射。本文以 $C_{eq}(t)$ 表示由环境数据构造的等效边界量，不将其解释为已测得的药材平衡含水率。

忽略干物质来源和损失时，干骨架与总水质量分别满足

$$\frac{\partial\rho_d}{\partial t}+\nabla\cdot(\rho_d\boldsymbol u)=0,$$

$$\frac{\partial(\rho_dC)}{\partial t}+\nabla\cdot(\rho_dC\boldsymbol u+\boldsymbol j_w)=0.$$

将第二式展开，再减去第一式的 $C$ 倍，可消去骨架压缩引起的密度变化，得到

$$\rho_d\left(\frac{\partial C}{\partial t}+\boldsymbol u\cdot\nabla C\right)=-\nabla\cdot\boldsymbol j_w.$$

采用相对骨架的有效 Fick 本构 $\boldsymbol j_w=-\rho_dD\nabla C$，有

$$\rho_dD_tC=\nabla\cdot(\rho_dD\nabla C),\qquad D_t=\frac{\partial}{\partial t}+\boldsymbol u\cdot\nabla.$$

只有在 $\rho_d$ 空间均匀时，才能从散度内约去它。固定半径的前三问取 $\boldsymbol u=0$，干骨架保持初始均匀，方程于是化为圆柱一维径向形式

$$\frac{\partial C}{\partial t}=\frac1r\frac{\partial}{\partial r}\left(rD\frac{\partial C}{\partial r}\right).$$

这里的 $1/r$ 来自圆柱壳传递面积随半径的变化，而不是额外的经验修正。若删除它改成平板扩散方程，即使程序仍能收敛并保持某个离散和不变，也已经改变了药材几何。

## A.2 有效热容量与题给物性的使用范围

傅里叶定律给出导热通量 $\boldsymbol q=-k\nabla T$。本文采用的热方程为有效显热容量闭合

$$B(C)D_tT=\nabla\cdot(k(C)\nabla T),\qquad B(C)=\rho_e(C)c_p(C).$$

$B$ 的单位为 $\mathrm{J/(m^3K)}$。题给密度记作 $\rho_e$，以区别质量守恒中的 $\rho_d$。按四问分别使用的经验关系如下，扩散系数中温度一律以 K 代入，显示温度才换成摄氏度。

$$\begin{aligned}
\text{Q1:}\quad &\rho_e=820,\quad c_p=2600,\quad k=0.36,\\
&D_1(C)=7\times10^{-9}\exp(-0.89/C).
\end{aligned}$$

$$\begin{aligned}
\text{Q2、Q3:}\quad &\rho_e=650+128C,\\
&c_p=1450+2736\frac C{1+C},\quad k=0.21+0.38\frac C{1+C},\\
&D_{23}(T,C)=2.4\times10^{-3}\exp(-0.45/C-3850/T).
\end{aligned}$$

$$\begin{aligned}
\text{Q4:}\quad &\rho_e=760+90C,\\
&c_p=1850+2150\frac C{1+C},\quad k=0.12+0.20\frac C{1+C},\\
&D_4(T,C)=4.2\times10^{-4}\exp(-0.30/C-3850/T).
\end{aligned}$$

这些系数来自题给经验公式，不能说由本次实验重新拟合。Q1 的热方程与水方程解耦，水扩散系数仍随 $C$ 变化；Q2、Q3 从初始时刻统一使用附录 3，而不把 Q1 的末状态或常热物性拼接进去。Q4 从初始时刻整组换用附录 4，同时引入半径变化。

若坚持把 Q4 的 $\rho_e$ 同时解释成真实湿密度，应有

$$\rho_d=\frac{760+90C}{1+C}=90+\frac{670}{1+C}\le760\quad(C\ge0).$$

初始干物质密度为 $\rho_{d0}=(760+90\times2.55)/3.55=278.7323943662$。固定长度且干物质量守恒要求

$$\pi LR_0^2\rho_{d0}\le760\pi LR(t)^2,\qquad R(t)\ge1.2112029565\ \mathrm{cm}.$$

附件 2 的 72 h 半径为 1.198 cm，表明这些字面解释不能在所给全时段同时成立。因此本文保留题给 $\rho_ec_p$ 作为有效热容量，干骨架质量另行守恒。这是明确的闭合选择，并非证明了真实湿密度、收缩体积及组分质量的全部关系。

容量形式还限定了能量解释。由于 $B$ 随 $C$ 变化，$B(C)T_t$ 不等于 $\partial_t[B(C)T]$。完整组分焓平衡还可能包含水迁移携焓、相变热和机械功；当前基线没有逐项识别这些机制。以下守恒检验针对所采用的有效方程，不能据此宣称完整热力学过程已闭合。

## A.3 同比收缩的材料坐标变换

第四问采用定长、同比径向收缩假设。半径 $R(t)$ 由附件 2 分段线性插值，内部骨架速度选为

$$u_r(r,t)=\frac r{R(t)}\dot R(t),\qquad x=\frac r{R(t)}\in[0,1].$$

这一速度使表面骨架恰随测得半径移动，并令每个材料坐标保持不变。圆柱对称下 $\nabla\cdot\boldsymbol u=2\dot R/R$，因此干骨架连续性方程给出

$$D_t\rho_d=-2\frac{\dot R}R\rho_d,\qquad
\rho_d(t)=\rho_{d0}\left(\frac{R_0}{R(t)}\right)^2.$$

设 $C(r,t)=\widehat C(x,t)$。在物理位置固定与材料位置固定两种求导条件下，链式法则分别为

$$\left.\frac{\partial C}{\partial t}\right|_r=\widehat C_t-\frac{x\dot R}R\widehat C_x,\qquad
\frac{\partial C}{\partial r}=\frac1R\widehat C_x.$$

骨架平流项恰为 $u_rC_r=x\dot R\widehat C_x/R$，两者相消，$D_tC=\widehat C_t$。将空间导数换元后得到

$$\widehat C_t=\frac1{R^2x}\frac{\partial}{\partial x}\left(xD\widehat C_x\right),\qquad
B(\widehat C)\widehat T_t=\frac1{R^2x}\frac{\partial}{\partial x}\left(xk\widehat T_x\right).$$

其结果只有时变几何因子，不再含额外网格平流。干基含水率是质量比，纯收缩而无相对水通量时 $D_tC=0$，也不应添加 $-2\dot RC/R$ 的体积浓缩项。若内部骨架并非同比运动，或干物质密度在空间上不均匀，应回到一般守恒方程，不能继续照搬上述简式。

中心满足对称零通量。表面条件为

$$-\frac kR\widehat T_x(1,t)=h(T_s-T_\infty),\qquad
-\frac DR\widehat C_x(1,t)=\beta(C_s-C_{eq}),$$

其中 $h=25\ \mathrm{W/(m^2K)}$、$\beta=8\times10^{-7}\ \mathrm{m/s}$。变换后方程只需当前 $R(t)$，不需要计算折线半径的数值导数。因子 $R^{-2}$ 表明尺度缩短会加强内部扩散，但 Robin 边界仍含 $R$，物性也随状态变化，不能仅凭平方尺度就推导全过程时长的严格比例。

## A.4 节点有限体积、中心控制体与真实表面

取 $N$ 个均匀区间，$x_i=i\Delta x$、$\Delta x=1/N$，共 $N+1$ 个节点。中心与表面都是真实未知量节点。内部控制体边界取相邻节点中点，中心控制体为 $[0,\Delta x/2]$，表面控制体为 $[1-\Delta x/2,1]$。定义环形权重

$$w_i=\int_{a_i}^{b_i}x\,dx=\frac{b_i^2-a_i^2}{2},\qquad \sum_{i=0}^{N}w_i=\frac12.$$

权重展开为

$$w_0=\frac{\Delta x^2}{8},\qquad
w_i=x_i\Delta x\ (1\le i\le N-1),\qquad
w_N=\frac{\Delta x}{2}-\frac{\Delta x^2}{8}.$$

单位长度的控制体积为 $2\pi R^2w_i$。环体积分用节点值乘权重近似，未知量仍位于节点；不能将其无条件当成精确的环形平均值，也不能把点值解析解与控制体平均解析解混用。

对于变热容量，控制体上的准确积分首先是 $\int_{a_i}^{b_i}xB(C)\widehat T_t\,dx$，离散时将它近似为 $w_iB(C_i)\dot T_i$。此处没有先构造 $B(C_i)T_i$ 再作时间差分，因而不会凭空引入容量导数项。网格控制体的几何边界在材料坐标中固定，其物理体积随 $R^2$ 变化；两种坐标下的体积口径应贯穿质量、热量与输出查询，不能在中途交换。

记 $g^T=xkT_x$、$g^C=xDC_x$ 为沿径向正坐标的梯度通量。它们与向外的物理传递通量相反，因此药材向外失水时表面 $g^C$ 为负。对控制体积分得到

$$\dot T_i=\frac{g^T_{i+1/2}-g^T_{i-1/2}}{R^2w_iB_i},\qquad
\dot C_i=\frac{g^C_{i+1/2}-g^C_{i-1/2}}{R^2w_i}.$$

中心面半径为零，直接令 $g^T_{-1/2}=g^C_{-1/2}=0$，无需在代码中计算 $1/x_0$。常系数热方程在中心退化为

$$\dot T_0=\frac{4k(T_1-T_0)}{B R^2\Delta x^2}.$$

系数 4 与光滑偶函数在圆柱中心的拉普拉斯极限一致。表面直接用 Robin 条件给外侧面值

$$g^T_{N+1/2}=hR(T_\infty-T_N),\qquad
g^C_{N+1/2}=-\beta R(C_N-C_{eq}).$$

本格式的最后一个未知量就在实际表面，不需要再从“最后单元中心”额外外推一个表面值，也不应重复叠加半单元内阻。若改用单元中心网格，则未知量位置与边界离散都必须同步改变。

热内部面采用调和平均

$$k_H=\frac{2k_i k_{i+1}}{k_i+k_{i+1}},\qquad
g^T_{i+1/2}=\frac{x_{i+1/2}}{\Delta x}k_H(T_{i+1}-T_i).$$

它对应两侧半间距导热阻串联，并保持相邻控制体共用同一面通量。共享通量的正负配对是离散守恒的基础；若两侧分别计算并取不同近似，整体求和时就可能产生虚假的内部源。

## A.5 浓度 Kirchhoff 势与近等浓度稳定计算

三组扩散率均可写为 $D=D_0\exp(-b/T)\exp(-a/C)$，其中 Q1 取 $b=0$，其他两组取 $b=3850$。引入

$$\Phi_a(C)=Ce^{-a/C}+a\operatorname{Ei}(-a/C).$$

利用指数积分的导数，分别有

$$\frac d{dC}(Ce^{-a/C})=e^{-a/C}(1+a/C),\qquad
\frac d{dC}\left[a\operatorname{Ei}(-a/C)\right]=-\frac aC e^{-a/C}.$$

相加得 $\Phi_a'(C)=e^{-a/C}$，从而势差等于浓度非线性系数的积分。生产水面通量为

$$g^C_{i+1/2}=\frac{x_{i+1/2}}{\Delta x}D_0
\exp\left(-\frac b{\overline T_i}\right)
\left[\Phi_a(C_{i+1})-\Phi_a(C_i)\right],\qquad
\overline T_i=\frac{T_i+T_{i+1}}2.$$

浓度势积分关系本身准确，温度面值、空间重构和圆柱几何面值仍有离散近似。不能对温度因子与势函数的乘积整体作差，因为

$$\partial_x\left(e^{-b/T}\Phi_a(C)\right)
=e^{-b/T}e^{-a/C}C_x+e^{-b/T}\frac b{T^2}T_x\Phi_a(C).$$

后一项不属于当前 Fick 本构。相等浓度、不同温度即可构成反例：正确浓度通量为零，整体乘积势差却不为零。

当相邻浓度接近时，直接相减两个势值可能损失有效位。程序在 $|\Delta C|<10^{-7}\max(\overline C,10^{-3})$ 时改用

$$\Delta\Phi\approx f(\overline C)\Delta C,\qquad f(C)=e^{-a/C},\quad \overline C=\frac{C_i+C_{i+1}}2.$$

该式为中点积分近似，局部截断差为 $O((\Delta C)^3)$。求解器对非物理 Newton 试探点仅在系数求值时令 $C^+=\max(C,10^{-12})$；它没有把已求得的状态直接裁成正值。因此正性需由接受状态检查确认，不能把这个保护值当作物理含水率下限。

## A.6 解析稀疏 Jacobian 的关键块

状态按 $\boldsymbol y=(T_0,C_0,T_1,C_1,\ldots,T_N,C_N,\ell)^\mathsf T$ 交错排列，维数为 $2N+3$。$\ell$ 是平均累计失水量，不反馈温湿场。每个内部面只依赖左右两个节点，故除最后的诊断行外，Jacobian 具有邻近的二乘二块带结构。

记 $\gamma_i=x_{i+1/2}/\Delta x$、$\Delta T=T_{i+1}-T_i$。调和平均对两侧导热系数的导数为

$$\frac{\partial k_H}{\partial k_i}=\frac{2k_{i+1}^2}{(k_i+k_{i+1})^2},\qquad
\frac{\partial k_H}{\partial k_{i+1}}=\frac{2k_i^2}{(k_i+k_{i+1})^2}.$$

热通量对 $(T_i,C_i,T_{i+1},C_{i+1})$ 的四个偏导于是为

$$\left(-\gamma_i k_H,\quad
\gamma_i\frac{\partial k_H}{\partial k_i}k'_i\Delta T,\quad
\gamma_i k_H,\quad
\gamma_i\frac{\partial k_H}{\partial k_{i+1}}k'_{i+1}\Delta T\right).$$

水通量记为 $g^C=G_i\Delta\Phi$，其中 $G_i=\gamma_iD_0e^{-b/\overline T_i}$。正常势差分支下有

$$\frac{\partial g^C}{\partial C_i}=-G_i e^{-a/C_i},\qquad
\frac{\partial g^C}{\partial C_{i+1}}=G_i e^{-a/C_{i+1}},$$

$$\frac{\partial g^C}{\partial T_i}
=\frac{\partial g^C}{\partial T_{i+1}}
=g^C\frac b{2\overline T_i^2}.$$

这两项温度偏导来自实际面平均温度，不能因“面上冻结温度”而在 Newton 迭代中将其误置零。Q1 的 $b=0$，水方程对温度偏导确实为零。

近等浓度分支必须对实际用到的 $f(\overline C)\Delta C$ 求导，得到

$$\frac{\partial\Delta\Phi}{\partial C_i}
=\frac12f'(\overline C)\Delta C-f(\overline C),\qquad
\frac{\partial\Delta\Phi}{\partial C_{i+1}}
=\frac12f'(\overline C)\Delta C+f(\overline C),$$

$$f'(C)=\frac a{C^2}e^{-a/C}.$$

否则右端与 Jacobian 在数值分支上不一致，会干扰 Newton 收敛。对于系数延拓区，程序还按 $C>10^{-12}$ 的活跃标记处理导数；阈值处是分段规则，不把它当成平滑物理本构。

每个面偏导分别以正、负符号加入左、右控制体，再乘对应热或水的几何尺度。热方程的分母也依赖 $C_i$，因此局部还必须加上商法则项

$$\left.\frac{\partial\dot T_i}{\partial C_i}\right|_{\text{容量}}
=-\dot T_i\frac{B'_i}{B_i},\qquad
B'_i=\rho'_e c_p+\rho_e c'_p.$$

例如 Q23 有 $\rho'_e=128$、$c'_p=2736/(1+C)^2$、$k'=0.38/(1+C)^2$；Q4 对应为 $90$、$2150/(1+C)^2$、$0.20/(1+C)^2$。遗漏容量项会使热湿交叉块不完整，即使物性公式本身抄写正确也不能得到正确 Jacobian。

固定时刻的 $R,T_\infty,C_{eq}$ 是外部量。表面热、水梯度通量对表面状态的偏导分别为 $-hR$ 与 $-\beta R$。诊断状态满足

$$\dot\ell=\frac{2\beta}R(C_N-C_{eq}),\qquad
\frac{\partial\dot\ell}{\partial C_N}=\frac{2\beta}R.$$

最后一整列为零。令行向量 $\boldsymbol m$ 在各 $C_i$ 位置取 $2w_i$、在 $\ell$ 位置取 1，其余取零，则守恒关系要求 $\boldsymbol m\boldsymbol J=0$。该左零关系与对右端直接扰动的导数比较，可分别检验守恒装配和局部线性化。

## A.7 质量及有效热通量的整体检验

将水方程乘 $2w_i$ 求和，所有内部面相消，仅剩表面通量，得到

$$\frac d{dt}\left(2\sum_{i=0}^Nw_iC_i\right)
=-\frac{2\beta}R(C_N-C_{eq}),\qquad
2\sum_{i=0}^Nw_iC_i+\ell=C_0.$$

这个式子与第四问的移动体积相容，因为 $\rho_dR^2=\rho_{d0}R_0^2$ 不变，平均干基含水率乘初始干质量就是剩余水质量。不能把单纯未加权的节点算术平均代入该恒等式。

温度方程的正确加权关系是

$$2\pi R^2\sum_iw_iB_i\dot T_i=2\pi Rh(T_\infty-T_N).$$

两边都是单位长度的瞬时热率，单位 W/m。若构造 $H'=2\pi R^2\sum_iw_iB_i(T_i-T_{ref})$，其总导数还含

$$\frac{dH'}{dt}=2\pi Rh(T_\infty-T_N)
+2\pi R^2\sum_iw_i(T_i-T_{ref})B'_i\dot C_i
+4\pi R\dot R\sum_iw_iB_i(T_i-T_{ref}).$$

容量变化项和体积变化项不能遗漏，更不能未经物理推导称为已测得的机械功。只有 Q1 的容量、半径均固定时，可将瞬时关系直接积分为常物性显热收支。耦合问的瞬时恒等式检验的是离散热算子，不能替代完整组分焓与相变能量平衡。

## A.8 隐式 BDF、分段环境与阈值事件

空间离散后得到刚性常微分系统 $\dot{\boldsymbol y}=\boldsymbol F(t,\boldsymbol y)$。扩散特征尺度随网格加密约按 $\Delta x^{-2}$ 增大，低含水率的指数扩散率又使时标差异突出，因而采用隐式时间推进。BDF 的基本思想是以若干已接受历史点与当前未知点构造插值多项式，用其当前时刻导数近似状态导数。等步长二阶形式为

$$\frac{3\boldsymbol y_n-4\boldsymbol y_{n-1}+\boldsymbol y_{n-2}}{2h}
=\boldsymbol F(t_n,\boldsymbol y_n).$$

一般写为 $\alpha_0\boldsymbol y_n+\sum_{j=1}^{q}\alpha_j\boldsymbol y_{n-j}-h\beta_q\boldsymbol F(t_n,\boldsymbol y_n)=0$。Newton 修正需要求解

$$\left(\alpha_0\boldsymbol I-h\beta_q\boldsymbol J\right)\delta\boldsymbol y=-\boldsymbol G.$$

上节的解析稀疏矩阵因此同时承担热湿耦合线性化与刚性求解的作用。实际生产使用 SciPy BDF 的 1—5 阶自适应实现及 NDF 精度修正，不是始终固定为二阶；上式用于说明原理。磁盘密集输出类只保存原始双精度多项式系数，并未降低阶数或另换积分方法。

从插值观点看，若 $P_q(t)$ 是通过当前未知状态和前 $q$ 个历史状态的次数不超过 $q$ 的多项式，则令 $P'_q(t_n)=\boldsymbol F(t_n,\boldsymbol y_n)$ 就得到相应后向差分关系。等步长时各项系数由插值基函数导数给出，变阶或步长调整时则需同步变换历史差分量。本文使用库内经过实现的历史更新、误差估计和步长控制，不自行把固定二阶系数套在任意不等时间间隔上。Newton 线性化失败或误差估计过大时，求解器会重试或缩短步长；输出的整数秒不等于每个被接受的内部时刻。

误差控制按分量尺度 $s_j=\mathrm{atol}_j+\mathrm{rtol}|y_j|$ 归一化。正式设置取 $\mathrm{rtol}=10^{-10}$，温度绝对容差 $10^{-10}$ K，含水率及累计失水绝对容差 $10^{-12}$。这是局部误差控制参数，不等于全时空误差上界。前 4 h 最大步长为 2 s，之后为 120 s；题目要求的 1 s 或 60 s 是输出采样间隔，密集输出在这些时刻求值，不要求内部积分步长始终小于输出间隔。

环境观测只覆盖 0—4 h。代码在 4 h 处分段求解，之前按观测线性插值，之后采用已声明的 50°C、等效 $C_{eq}=0.05$ 平台。分段可明确处理延拓接口；它不使平台变成实测。Q4 的半径使用观测范围内插值，固定物理位置 $r_j$ 查询时换算为 $x_j=r_j/R(t)$，若 $x_j>1$ 则留空，真实表面另在 $x=1$ 查询。

Q3 与 Q2 使用同一条场解。令 $M_N(t)=\max_i C_i(t)$，事件函数为

$$g(t)=M_N(t)-0.15.$$

求解器定位由正到负的零点，并取终止方向为 $-1$。该零点是临界阈值时刻，等号本身不满足严格小于。节点间若采用分段线性重构，重构场最大值等于节点最大值；这仍不是对真实连续场误差的严格界。

程序由事件状态继续真实积分到 $\lceil t_*\rceil+1$ s，再在 $0.0001$ h 网格上取不早于事件的候选时刻

$$t_{rep,h}=10^{-4}\left\lceil10^4\frac{t_*}{3600}\right\rceil.$$

随后查询该时刻未舍入的全域最大含水率；若仍不小于 0.15，就继续增加一个报告网格单位，并检查查询始终位于已积分区间内。四位显示可能仍为 0.1500，不应人为改成 0.1499。报告时长是条件模型中的可行数值时刻，不能解释为实测置信上界。

整个求解与导出次序如下。首先读取并核对原始驱动的单位、时间顺序和输入版本，建立材料网格及均匀初态；其次逐段积分，使用真实接受状态传递段间初值，并在每次求值中更新物性与面通量；随后定位全域阈值事件、继续计算并核对严格报告时刻；最后从同一密集解查询正文时刻和完整工作簿日程，换算显示单位、处理缩域空白并实施四位舍入。参数、状态、域内外判别及阈值比较均在舍入前完成，不能为了某个表格末位改动判据或在求解前把物性截成四位小数。

在连续数学意义上，严格达标集合可能是一个开时间区间，其下确界是含水率恰等于阈值的临界时刻，并不一定存在“最早的严格小于时刻”。所以本文将连续根与离散报告网格上的可行时刻分开记录。有限时间搜索未触发事件时，应报告该搜索区间内尚未得到达标结果，而不能把搜索上限当成烘干时长。

## A.9 可选经验阻力情景及其物理边界

在保持基线不变的前提下，可令表面边界乘以含水率相关的系数

$$K_p(C)=\frac{1-(C_{ref}/C)^{1/p}}{1-C_{ref}/C},\qquad
C\ge C_{ref}=0.05,\quad p\ge1.$$

其启发来自假设活动度曲线 $a_p(C)=1-(1-a_{ref})(C_{ref}/C)^{1/p}$ 相对基准成员的驱动比。令 $z=C_{ref}/C$、$q=1/p$，由 $z^q\ge z$ 及凹函数的切线界 $z^q\le1+q(z-1)$ 得

$$\frac1p\le K_p(C)\le1,\qquad K_1(C)=1,\qquad
\lim_{C\downarrow C_{ref}}K_p(C)=\frac1p.$$

因此它是可控且含基线的经验传质阻力族。程序实际只将 $\beta(C_s-C_{eq})$ 替换成 $\beta K_p(C_s)(C_s-C_{eq})$，没有把表面饱和蒸气压或真实材料等温线代入边界。参数 $p$ 未由内部温湿或称重数据标定，$p\ge1$ 表示只研究传质减弱情景；它不是因 $p<1$ 必然产生负活动度。有限参数点的时长排序也不能证明耦合模型对所有 $p$ 的全局单调性。

若进一步施加比例为 $\chi$ 的表面汽化负荷，则 $j_w=\rho_d\beta K_p(C_s)(C_s-C_{eq})$，热面值改为

$$g_s^T=hR(T_\infty-T_s)-R\chi L_vj_w.$$

这只表达指定排水在表面汽化的能量情景。真实气固边界还需材料等温线、表面温度、气膜传质系数、蒸发或凝结与吸附热的一致关系；缺少这些信息时，不把情景温度或时长作为真实预测误差的上下界。此扩展展示的是边界假设的敏感性，不能取代基线结果的来源说明。

## A.10 公式与实现的对应说明

本附录对应的核心算法为 `drying_core.py` 的物性、材料网格和右端函数，`analytic_jacobian.py` 的稀疏导数，`q1_model.py`、`q2_model.py`、`q4_model.py` 的正式参数，以及 `q3_model.py` 的严格报告时刻。Q1/Q23 分别使用 $N=3200$，Q4 使用 $N=6400$；对应状态维数为 6403 与 12803。

交付程序中的 `dryingCore.py`、`analyticJacobian.py` 等为驼峰审查副本。登记的标识符、模块路径和配置键反向规范化后，与冻结模块的运算结构对应；中文注释、模块命名及来源路径变更不构成另一套物理模型。特别地，读取环境数据的早期中文注释混用了空气与药材干基口径，应以实际 CSV 字段和本附录的定义为准。

内部对照材料为 `paper_output/qa/paper_readiness_20260912/innovation_verified.md` 与 `innovation_proof_checks.json`；本附录不额外宣称新的生产重算。正式提交时源码文件名、依赖环境和输入输出路径应与支撑包一致，内部工作区绝对路径及个人身份信息不应混入匿名文稿。
