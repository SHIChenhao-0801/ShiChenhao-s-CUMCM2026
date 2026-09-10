# MATLAB 独立交叉核验入口

`runCrossCheck.m` 是 A 题最终条件模型的独立 MATLAB 数值实现，采用 **N=40 的材料坐标有限体积离散 + Kirchhoff 水通量 + ode15s 隐式时间积分**，供同网格跨语言核验与用户阅读。它不读取 Python 的已计算场、不调用 Python 求解器，也不写回正式冻结结果。Q2、Q3 使用同一条从 t=0 开始的附录3轨迹，函数实际求解 Q1、Q23、Q4 三个不同初边值问题，再给 Q2/Q3 分别导出查阅入口。

本文件交给主代理时，仅完成源码静态检查；真实 MATLAB GUI 运行结果与跨语言差值由另行运行生成的证据确认。**N40 结果不能替代正式 N3200/N6400 结果，AI 静态审查不能充当用户人工认可。**

## GUI 运行方式

在 MATLAB Command Window 中执行：

```matlab
cd('D:/Document/数学建模/2026CUMCM');
addpath('D:/Document/数学建模/2026CUMCM/paper_output/code/review_delivery/matlab');
runSummary = runCrossCheck('D:/Document/数学建模/2026CUMCM/paper_output/qa/matlab_crosscheck_20260911');
```

也可直接 `runSummary = runCrossCheck();`，函数会在本工作区 `paper_output/qa/` 生成带本地时间戳的新目录。已存在 `runSummary.json` 的目录会被拒绝，避免覆盖旧运行；再次运行应指定新目录。运行目录必须位于 `2026CUMCM` 内。函数使用内置 Java 进行路径规范化和 SHA256，所以需要带 JVM 的普通 MATLAB GUI 会话；Java 不参与物理或数值求解。

可在主函数中的 `solveSingleCase(...)` 调用、局部函数 `balanceRhs(...)` 的热/水通量组装和最终 `diagnostic.strictlyDryAtEnd` 附近设置断点。建议重点观察 `temperature`、`waterContent`、`radiusM`、`heatFlux`、`waterFlux`、`derivative` 和质量守恒残差。断点观察不能替代完整继续运行，也不能替代本人的公式核查。

## 输入、输出与数值口径

只读输入是 `paper_output/data_cleaned/A_environment_observed.csv` 和 `A_radius_observed.csv`。运行前检查必需字段、有限值、严格递增时间、t=0、4h/72h终点、正绝对温度和正半径；保存输入路径、字节数与 SHA256，完成后再次核对源码和输入哈希。这里的接口检查不重新宣称完成了上游全部数据审计。

统一参数为初始 `T=301.15 K`、`C=2.55 kg/kg干物质`、`R0=0.02 m`、固定长度 `L=0.25 m`、`h=25 W/(m²·K)`、`beta=8e-7 m/s`。温度和含水率从每问 t=0 同时演化。环境数据内作分段线性插值，严格超过 4h 时使用 `323.15 K / 0.05` 平台闭合。Q4 半径按原观测表线性插值；若超过 72h 会保持最后半径并在诊断中明确标记，正常约51h事件预计不触发该延拓，但必须由实际输出确认。

Q1 积分到1800s；Q23/Q4最大240h，遇到向下的 `max(C)-0.15=0` 事件后终止该段，再实际续算到 `ceil(eventSec)+1`。最后用未四舍五入的状态核验 `max(C)<0.15`。这个整数秒仅作保守事件后检查，不自称最早整数秒，也不是论文四位小时的严格报告规则。

| 参数 | 值 |
|---|---:|
| 区间数 / 节点数 / 状态数 | 40 / 41 / 83 |
| RelTol | 1e-10 |
| 温度 AbsTol | 1e-10 K |
| 水分与累计损失 AbsTol | 1e-12 kg/kg |
| 0—4h MaxStep | 2s |
| 4h以后 MaxStep | 120s |
| 事件后续算 MaxStep | 1s |
| 显式的环境切段 | t=14400s |

每问输出时间为初始、1800s、10800s（若在积分域内）、连续临界事件、事件后验证秒；Q1仅有0和1800s。表格空间坐标统一为 `x=r/R(t)=[0,0.25,0.5,0.75,1]`。JSON 同时保留这些时刻的全41节点状态和累计损失，以便主代理用同N Python实现独立逐项对照。

| 输出文件 | 内容 |
|---|---|
| `runSummary.json` | 开始/结束UTC、耗时、MATLAB版本、配置、源码/输入哈希、各case结果、异常、待人工审查标记 |
| `runLog.txt` | 每case起止、耗时、事件秒、守恒残差、捕获的警告和异常 |
| `Q1_crossCheck.json` / `Q23_crossCheck.json` / `Q4_crossCheck.json` | 样本、全节点样本状态、事件、诊断 |
| `Q1_samples.csv` / `Q2_samples.csv` / `Q3_samples.csv` / `Q4_samples.csv` | 便于逐题查阅的长表，每行一个时间/材料位置 |
| `Q23_samples.csv` | Q2/Q3共用轨迹的直接接口 |

JSON 中 `temperatureK`、`temperatureC`、`moistureDryBasis` 的形状是 `[采样时间,5个材料位置]`；`fullStateBySample` 为 `[采样时间,83状态]`，状态顺序为 `T0,C0,T1,C1,...,T40,C40,cumulativeDryBasisLoss`。`sampleTimesSec`、`eventSec`、`endSec` 用秒；`meanMoisture` 与 `cumulativeLoss` 用kg/kg干物质。CSV 的 `radiusM=x*R(t)` 是查询点实际半径，`currentRadiusM=R(t)` 是当时表面半径。

警告记录采用每个积分分段的 `lastwarn`，不会虚称收集所有 MATLAB 警告。数值状态诊断覆盖 ode15s 接受步，不是连续全时空误差上界。失败会写 `FAILED` 与完整异常并重新抛错；成功只写 `COMPLETED_NUMERICAL_CHECKS`，不替外部GUI证据、Python对照或人工审查背书。

## 公式和实现

令材料节点 `x_i=i/N`，面坐标取相邻节点中点并包含0、1，控制体权重为 `w_i=(x_(i+1/2)^2-x_(i-1/2)^2)/2`。内面热通量为 `gT=xFace*kHarmonic*(T_right-T_left)/dx`，外表面为 `-h*R*(T_surface-T_air)`；因此 `dT_i/dt=diff(gT)/(R²*w_i*rho_i*cp_i)`。这里 `rho*cp` 是有效显热容量闭合，未增加潜热项。

Kirchhoff 势为 `Phi_a(C)=C*exp(-a/C)+a*Ei(-a/C)`。MATLAB 使用 `expint(z)=E1(z)`，正实数上 `E1(z)=-Ei(-z)`，故源码实现 `Phi_a(C)=C*exp(-a/C)-a*expint(a/C)`。近乎相同的两个C使用中点导数 `exp(-a/Cmean)*(C_right-C_left)` 避免势函数相减的消减误差，切换阈值与原 Python 一致。温度 Arrhenius 因子在面中点单独求值，不能把它乘入势函数再对节点差分。

水内面通量为 `gC=xFace*D0*thermalFactor*(Phi_right-Phi_left)/dx`，表面为 `-beta*R*(C_surface-Ceq)`，故 `dC_i/dt=diff(gC)/(R²*w_i)`。中心面通量为零。最后一个状态累计干基失水，满足 `dLoss/dt=2*beta/R*(C_surface-Ceq)`；离散不变量为 `2*sum(w_i*C_i)+Loss=C_initial`。

Q4 的材料控制体随给定 `R(t)` 同比径向缩放、长度固定。干密度按 `rhoDry(t)=rhoDryInitial*(R0/R(t))²` 解释以保证干物质守恒，故C方程无需另加移动网格平流项。该密度与经验热容量中的rho用途不同，不能再同时强加一套不相容的局部混合密度约束。

| case | rho | cp | k | D |
|---|---|---|---|---|
| Q1 | 820 | 2600 | 0.36 | `7e-9*exp(-0.89/C)` |
| Q23 | `650+128*C` | `1450+2736*C/(1+C)` | `0.21+0.38*C/(1+C)` | `2.4e-3*exp(-0.45/C-3850/T)` |
| Q4 | `760+90*C` | `1850+2150*C/(1+C)` | `0.12+0.20*C/(1+C)` | `4.2e-4*exp(-0.30/C-3850/T)` |

rho、cp、k、D的单位依次为kg/m³、J/(kg·K)、W/(m·K)、m²/s，T采用开尔文。仅在积分器Newton试探状态的系数求值中令 `positiveMoisture=max(C,1e-12)`；没有使用 `NonNegative` 或其他操作裁剪真正的积分状态。接受状态另查正物性、最低C、最高C、温度范围、径向水分增量、离散质量残差以及最终严格干燥条件。

## 函数、依赖和复杂度

`runCrossCheck` 负责输入/版本记录、三个case调度与持久化；`solveSingleCase` 创建网格和状态，分段积分、定位事件、采样与检验。其嵌套函数 `balanceRhs` 是实际守恒方程，`radiusAt`/`environmentAt` 处理明确的输入插值和延拓，`dryEvent` 定义标量事件，`recordWarning` 记录该分段最后一条警告。局部函数 `materialProperties` 集中维护各附录物性，`makeJacobianPattern` 构造相邻节点的2×2块三对角依赖，`evaluatePieces` 只在已积分域内调用稠密解，`makeSampleTable` 组织长表；其余函数负责输入验证、积分终点验证、哈希、JSON和日志。

数值依赖全部为 MATLAB 基础功能：`ode15s`/`odeset`、`deval`、`interp1`、`expint`、`sparse`、`table`/`readtable`/`writetable`、`jsonencode`、`datetime` 和文件I/O；不需要 Optimization Toolbox、Statistics Toolbox 或 Symbolic Math Toolbox。Java仅使用 `java.io.File` 与 `java.security.MessageDigest`。

设N为空间区间数、S为接受时间点数。网格和单次RHS运算/工作数组均为O(N)；稀疏依赖非零元为O(N)。隐式积分总成本还取决于刚性、自适应步数、Newton迭代、有限差分Jacobian次数和稀疏LU填充，不能仅用O(N)概括整次求解。对这种固定带宽相邻耦合，理想带状线性求解可线性增长，但本程序使用MATLAB内部通用稀疏求解与排序，不将该理想值当成已经测得的严格运行界。保留各段稠密解和接受状态的空间成本约O(SN)；本脚本固定N40，因此适于交叉核验而不是直接承担最大生产网格存储。

独立性主要来自不同库的隐式求解器实现、步长/阶数控制及Jacobian构造：MATLAB默认ode15s使用1—5阶NDF路线，SciPy的BDF实现本身也包含NDF修正，不能把两者简化为一方使用NDF而另一方没有；本MATLAB实现由JPattern辅助有限差分，原Python生产版为解析稀疏Jacobian；特殊函数分别使用MATLAB E1与SciPy Ei，数据读入和所有平衡方程在MATLAB重写。两者仍共享已冻结的物理假设、离散公式和数据，所以跨语言一致支持实现一致性，不能证明物理闭合正确或给出真实预测准确率。

跨语言比较须按实际 `sampleTimesSec` 和材料位置对齐。Python主入口的 `crossLanguageSamples` 为Q23/Q4包含严格上取报告时刻，本MATLAB样本包含连续事件时刻，行数相同不保证时刻相同；应查询相同时刻的live Python解，或只比较共同固定时刻并单独比较事件时间。MATLAB内部 `COMPLETED_NUMERICAL_CHECKS`、外部跨语言差值、GUI完整运行和用户人工接受分别记录。

MathWorks 一手接口核对：[ode15s算法与事件结构](https://www.mathworks.com/help/matlab/ref/ode15s.html)、[expint定义](https://www.mathworks.com/help/matlab/ref/expint.html)、[deval稠密解](https://www.mathworks.com/help/matlab/ref/deval.html)、[odeset与JPattern](https://www.mathworks.com/help/matlab/ref/odeset.html)。访问日期2026-09-11（北京时间）。
