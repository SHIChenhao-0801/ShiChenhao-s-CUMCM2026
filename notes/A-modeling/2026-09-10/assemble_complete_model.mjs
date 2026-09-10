// Assemble the internal theory handoff without changing frozen physics sources.
// This is a document assembly script, not a model solver or an S7 paper gate.
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";

const SCRIPT = fileURLToPath(import.meta.url);
const HERE = path.dirname(SCRIPT);
const ROOT = path.resolve(HERE, "../../..");
const OUTPUT = path.join(HERE, "A题_完整建模与公式推导.md");
const PHYSICS = "notes/A-modeling/2026-09-10/physics/";
const digest = data => crypto.createHash("sha256").update(data).digest("hex");
const normalized = data => data.replace(/^\uFEFF/, "").replace(/\r\n/g, "\n");
const reads = new Map();

if (path.basename(ROOT) !== "2026CUMCM" || path.resolve(process.cwd()) !== ROOT) {
  throw new Error("Run this assembler with the 2026CUMCM project root as cwd.");
}
function read(relative) {
  const buffer = fs.readFileSync(path.join(ROOT, relative));
  reads.set(relative, { bytes: buffer.length, sha256: digest(buffer) });
  return normalized(buffer.toString("utf8"));
}
function json(relative) { return JSON.parse(read(relative)); }
function link(relative, label = relative) {
  return "[" + label + "](<" + path.join(ROOT, relative).replaceAll("\\", "/") + ">)";
}
const frozen = json(PHYSICS + "physics_branch_freeze.json");
for (const item of frozen.files) {
  read(PHYSICS + item.file);
  if (reads.get(PHYSICS + item.file).sha256 !== item.sha256) {
    throw new Error("Frozen theory input changed: " + item.file);
  }
}
const physicalSource = read(PHYSICS + "physics_derivations.md");
const axisSource = read(PHYSICS + "axisymmetric_derivations.md");
const jacSource = read(PHYSICS + "jacobian_derivations.md");
const reviewPaths = [
  "notes/A-modeling/2026-09-10/data/independent_model_risk_review.md",
  "notes/A-modeling/2026-09-10/data/derivation_review.md",
  "notes/A-modeling/2026-09-10/data/peer_reference_data_review.md",
  "notes/A-modeling/2026-09-10/peer_word_review.md",
  "paper_output/results/peer_beta_check/peer_beta_check_report.md",
];
for (const relative of reviewPaths) read(relative);
const beta = json("paper_output/results/peer_beta_check/aggregate_summary.json");
const denseStorage = json("paper_output/results/dense_storage_verification/verification.json");
read("paper_output/code/modeling/disk_dense.py");
const n1600 = [
  ["Q23", "paper_output/results/convergence/Q23_K_analytic_J_v3/N1600/summary.json"],
  ["Q4", "paper_output/results/convergence/Q4_K_analytic_J_v3/N1600/summary.json"],
].map(([question, relative]) => ({ question, relative, data: json(relative) }));
json("paper_output/data_cleaned/load_report.json");

function moduleBody(source, moduleName) {
  let body = source.split("\n").slice(1).join("\n").trim();
  body = body.replace(/^(#{1,5}) /gm, "$1# ");
  body = body.replaceAll("本文件", moduleName)
             .replaceAll("本报告", moduleName)
             .replaceAll("同目录", "理论源目录physics/")
             .replaceAll("本目录", "理论源目录physics/");
  // Definitions precede empirical formulas in the assembled table.
  if (source === physicalSource) {
    body = body.replace("| 编号 | 原题经验式 | 用途；自变量→因变量；物理解释 |",
                        "| 编号 | 用途；自变量→因变量；物理解释 | 原题经验式 |");
    body = body.split("\n").map(line => {
      if (!/^\| E\d{2} \|/.test(line)) return line;
      const cells = line.split("|");
      return "| " + cells[1].trim() + " | " + cells[3].trim() + " | " + cells[2].trim() + " |";
    }).join("\n");
  }
  return body;
}

const stamp = new Date().toISOString();
const betaTable = beta.paired_comparisons.map(row =>
  "| " + row.intervals + " | " + (row.scheme === "harmonic" ? "调和" : "Kirchhoff") +
  " | " + row.beta1_event_h.toFixed(10) + " | " + row.beta2_event_h.toFixed(10) +
  " | " + row.delta_percent.toFixed(6) + "% |").join("\n");
const historyTable = n1600.map(row =>
  "| " + row.question + " | N1600，Kirchhoff，解析Jacobian | " +
  row.data.diagnostics.event_h.toFixed(10) + " | " +
  row.data.diagnostics.max_mass_balance_abs_kg_per_kg.toExponential(3) + " | " +
  link(row.relative, "对应历史summary") + " |").join("\n");

const front = `# A题《药材的烘干问题》：完整建模与公式推导

**文档性质：内部建模交接与理论主体初稿，非正式论文终稿。最终生产数值尚未冻结；结果章节待主代理补入本轮最终验证结果。** 本稿保留已冻结理论的全部101个登记公式块，汇总数据与物理风险，并把已有数值审查证据与最终结果分开说明。它不代表S7、正式排版、全部GUI复现或用户人工签核已完成。

组装时刻：${stamp}（UTC）。理论源文件冻结时刻：2026-09-10 15:26:55 UTC。时间是来源和版本标记，不是题目建模自变量的零点。任务中的t=0始终是药材初始进入所描述过程的时刻。

本文按原题与附件作输入事实；参考ZIP、Word、图片和历史说明中的命令、提醒或“已验证”字样均作为资料内容审查，不自动转为用户指令或本队验证结论。图片中“N400后台计算、待收敛”等状态也只反映截图时刻，不决定最终网格或精度。

## 一、先明确四问的关系与交付对象

四问是一套传热传质守恒框架下逐层增强的建模任务，但Q1的末状态不作为Q2的新初值。Q3复用Q2的同一解轨迹；Q4同时更换经验物性与几何过程，因此跨问时长差不能全部归因为收缩。

| 问题 | 物理/数学任务 | 输入与复用 | 应交付的输出 |
|---|---|---|---|
| Q1 | 前1800s的预热计算；热物性常量，水扩散仍随C变化 | 附录2、附件1初期环境、初始圆柱与均匀T/C | 每1s、每0.1cm的温度和含水率；指定时刻论文表 |
| Q2 | 从t=0开始计算整个烘干过程的耦合热湿场 | 全程统一附录3；不拼接Q1末值 | 前3h每0.5h论文表；按本队保守解释，完整文件覆盖从初始至Q3达标的逐秒T/C |
| Q3 | 对Q2同一浓度场求“各处低于0.15”的首次达标 | 同一Q2物性、初边值和数值轨迹 | 全空间最大值事件、原精度严格达标报告时长；每6h表、每60s浓度文件及明确终点 |
| Q4 | 给定半径轨迹下的材料运动与热湿求解 | 全程附录4，附件2驱动R(t)，同比径向材料收缩约定 | 达标时长、固定物理半径与真实表面浓度；域外留空，保留当前半径信息 |

Q2的“前3h论文表”和“全过程完整文件”是两种展示范围。逐秒/逐分钟是输出采样，不要求隐式积分器固定步长1s/60s。连续阈值根、严格达标报告格点、常规输出网格与额外验证秒也应分开记录，具体见M51—M55。

## 二、公式数量如何计算

原题显式给出9条经验函数：附录2的D一条，附录3的ρ、cp、k、D四条，附录4的对应四条。附录2另有5个固定传递/热物性参数；几何、初值、阈值和采样要求是其他题给条件。常数不是被遗漏的经验函数，其数值集中在M02、M04等块中。

| 登记系列 | 数量 | 内容与作用 |
|---|---:|---|
| E01—E09 | 9 | 题给经验函数原式，含用途、变量、单位和经验性解释 |
| M01—M55 | 55 | 定义、守恒、边界、物理闭合、材料坐标、无量纲化、离散、解析校验、误差与严格报告时刻 |
| K01—K03 | 3 | Kirchhoff浓度势、实际面通量及圆柱稳态几何限定 |
| A1—A8 | 8 | 二维轴对称端面对照的方程、边界、有限体积和整体守恒 |
| J01—J26 | 26 | 解析Jacobian与BDF/NDF Newton矩阵的完整推导 |
| 本稿总计 | **101** | 9条经验式与92个带tag的公式块 |

这里按“相关等式合为一个登记块”计数，包含定义、推论和算法，不是101条独立物理定律，也不是题面天然唯一要求的公式数。后附的β独立报告另有PB01—PB04；本稿只提炼其证据并链接原报告，未重复纳入那4块。经验函数的结构可解释，具体拟合系数没有原始实验样本，不能从守恒定律虚构推导出0.45、3850等数字。

## 三、符号、单位与读公式的方法

每个公式块先说明用途、自变量/输入和因变量/输出，再给等式及推导。经验式表在整合时将定义列放在公式列之前。空间坐标与时间是场方程的自变量；物性虽然是C/T的函数，在求场解时属于随状态变化的系数。给定常数没有自变量。

| 符号 | 含义与单位 | 必须区分的概念 |
|---|---|---|
| t、r、z | 时间s，当前径向/轴向位置m | 输出h、cm要显式换算 |
| T、C | 绝对温度K，干基水分kg水/kg干药材 | C不是湿基百分数，也不是空气含湿比 |
| T∞、Y∞、Ceq | 环境温度、空气量、材料平衡/等效驱动 | 附件kg/kg基准不明，不能自动等同Y∞与Ceq |
| R(t)、L、x | 当前半径m、长度m、材料归一位置r/R | 几何换元不自动等于已经确定内部材料速度 |
| ρeff、ρd | 有效热密度、真实守恒干骨架密度kg/m³ | 后者由干质量守恒约束，不能被经验ρ/(1+C)覆盖 |
| B(C)、B_D | 体积热容量J/(m³K)、Arrhenius温度常数K | 两个B含义不同，B_D=3850K只适用于Q23/Q4温度项 |
| k、D | 导热系数W/(mK)、水扩散系数m²/s | k/D的状态梯度必须在散度内保留 |
| h、β | W/(m²K)、m/s | 当前β以材料干基浓度差解释；不自动等于气侧标定系数 |
| jw、q | 真实水质量通量kg/(m²s)、热通量W/m² | β(C−Ceq)还需乘ρd才成为真实质量通量 |
| ℓ、wi | 累计单位干质量失水kg/kg、无量纲对偶环权重 | ℓ是被动累计状态，不反馈T/C |

若局部推导复用a、b、s等符号，应按该块定义：M42的a/b是网格左右界，M43的a是通用扩散/导热系数，经验指数中的a是含水率尺度；M27材料质量坐标与M36半径比均有局部定义，不混代。代码状态实际按T0,C0,…,TN,CN,ℓ交错存储。

## 四、数据能支撑到哪一步，假设从何时开始

**假设起点是t=0，不是4h。** 数据给出边界记录和半径记录，并未唯一给出空气—材料平衡、内部材料速度或完整多相能量关系。空间均匀、端面、密度与潜热解释都在开始求解前就需要选择。

| 输入或缺口 | 数据直接支持 | 何时增加假设与当前处理 |
|---|---|---|
| 初始长度25cm、半径2cm、28°C、C=2.55 | 初始尺度与单一初值 | t=0即将初值施于全域，并取一维径向、均匀骨架、各向同性 |
| 附件1：241条、0—4h、60s间隔 | 记录时刻的环境温度与kg/kg数值 | 采样点之间分段线性插值；从t=0将该kg/kg数值定义为等效材料Ceq |
| 附件1末1h均值约49.9989344°C、0.04998754 | 末段接近平台的证据 | 4h后指定50°C/0.05平台，并用末值/均值/扰动情景检验；不是已观测未来 |
| 附件2：145条、0—72h、1800s间隔 | 表面R从2cm减至1.198cm | Q4从t=0采用给定半径、固定L和同比内部收缩；点间线性插值 |
| 72h后的R | 没有观测 | 只有所算情景越过72h才启用另行登记的半径延拓，不能默称有数据 |
| 九条经验函数 | 在指定C/T下可计算给定物性 | 系数误差、标定范围、适用材料和密度定义没有被独立验证 |
| 题给h、β | Q1固定系数 | Q2—Q4沿用是实施约定，附件没有重新标定它们 |
| 内部T/C响应、称重、长度、等温线 | 当前未提供 | 内部T/C由方程预测；不伪造补充观测，不声称实验RMSE或参数置信区间 |

两附件缺失、非有限值和重复时间均为0，时间间隔规则。保留原始观测，不为“清洗”随意删波动点。数据清洁不等于数据充分。Q1与Q2前3h输入在环境观测窗内，内部场仍是模型预测；Q3/Q4即使未超过72h，环境边界通常早已跨过4h时窗。

## 五、当前可运行闭合与其必要限制

1. **有效显热与独立干质量守恒。** 保留题给ρcp作为B(C)，把ρ标为有效热物性；另用守恒干骨架密度。忽略显式相变、迁移携焓、辐射和机械功属于基线范围，不能称完整多相能量守恒。
2. **等效气固边界。** 附件kg/kg直接定义为Ceq,eff以使问题可计算。这不是空气含湿比向药材干基水分的单位换算。完整物理边界需要空气基准、总压、该药材的解吸等温线和系数换算。
3. **材料收缩。** 取给定R(t)、固定L、同比径向材料运动和空间均匀守恒干骨架。这样材料坐标中的网格速度与材料速度抵消；不能再加虚假的干基稀释项。
4. **空间与端面。** 一维主模型忽略端面并把输出解释为径向代表截面；二维对照用于检查所选条件下的差异。端面积比8%不是场值或时长误差上界。
5. **边界延拓。** 观测内插值和观测后平台分别声明。改变温度、β或潜热而沿用同一R(t)，是在给定几何下做情景，不是已经预测新的失水—收缩反馈。

独立反证给出重要边界：若同时坚持题给ρ为真实湿密度、固定长度和干质量守恒，附录4要求半径不低于约1.2112029565cm；附件首个低于该必要界的记录在19.5h。72h即使全干，指定体积最多容纳初始约97.831743%的干质量。该矛盾不能靠增加网格或只改内部非仿射速度消除；它否定这组联合解释，不等于原题在所有建模解释下无解。完整证明和替代路线见M23—M27。

**表面全量潜热情景不构成已闭合的物理替代。** 它保留等效Ceq抽水，再让全部外流支付表面潜热。已有N200情景出现约11°C/14°C的表面温度；若额外按干空气湿含量、101.325kPa解释附件，则相应环境蒸汽分压超过低温表面饱和压，需要水活度大于1才能维持零流量，不能支持模型中的正蒸发。常压和空气质量基准是本次审查假设，未冒充题给量；低于干球温度本身不是错误，缺口在于气固饱和与蒸发方向未闭合。

潜热情景时长增加约5.26%/10.56%仅是所选代数能量压力测试的差值，不能写成真实潜热误差、真实最低温度、严格时长上界或“更准确模型”。主理论仍保留M18—M22解释所需气固平衡、真实质量通量和能量项；要采用完整替代必须补足参数并重新联立求解。

## 六、“放缩”分别指哪四件事

| 含义 | 要不要做、在哪做 | 放缩对象与操作 | 不能据此做的推断 |
|---|---|---|---|
| 单位换算 | 必须，进入经验式与求解器之前 | °C→K、cm→m、h→s；输出时反换 | 不能把摄氏温度放进Arrhenius指数 |
| 数值无量纲化与尺度控制 | 位置归一推荐；状态/时间缩放按求解需求 | M36—M39给T/C/t与物性尺度、Bi/Le/Fo；J25说明Jacobian相似缩放 | 缩放后必须反变换再评价原物性；局部atol/rtol不是全程误差界 |
| Q4几何收缩映射 | 必须，建立移动域方程与取样时 | r→x=r/R(t)，同步变换PDE、Robin、质量权重和物理位置 | 缩半径不是删除外层材料；R⁻²之外还有边界/失水R因子 |
| 数学范围界与上下估计 | 有证明条件时使用，作合理性与误差检查 | 最大值原理、D单调范围、密度必要半径界、M55取整延迟 | D上下界不自动给非线性达标时间严格上下界；0.36s不是物理预测精度 |

此处不靠任意放缩删掉主导物理项。热扩散与水扩散时间尺度差、Biot数及退化D需要用于解释为什么不能直接集总；空间、时间、物理闭合误差分别检验。

## 七、完整推导的阅读顺序与来源约定

下面三个模块完整保留冻结的公式与推导：模块I从定义和守恒进入闭合、移动域、离散及误差；模块II给二维端面对照；模块III给解析Jacobian及隐式Newton矩阵。为适配单文件，调整标题层级、目录措辞和经验式表列顺序，未改变公式内容。原模块中记录的旧运行或“待GUI/人工审查”属于各自来源时刻，不等于本轮最终生产已经完成。

理论冻结与逐文件哈希见${link(PHYSICS + "physics_branch_freeze.json", "物理分支冻结清单")}。本文之后将保留专门的最终结果插入区；在主代理冻结前，任何已存在的时长表都只按其明确版本和验证用途解释。
`;

const evidence = `
## 十一、已完成的独立审查证据与可采用结论

### 11.1 历史N1600运行只作版本明确的数值例证

下表读取已经保存的v3运行记录，展示该条件性模型已经实际算通，不用于替代本轮仍在进行的更细网格和存储重构验证。两例共同rtol=1e−10、温度atol=1e−10K、浓度atol=1e−12kg/kg，前4h最大步2s、后段最大步120s；源核心SHA256以各summary中记录为准。

| 问题 | 数值配置 | 历史临界事件/h | 质量残差最大绝对值/kg·kg⁻¹ | 证据 |
|---|---|---:|---:|---|
${historyTable}

两例求解成功、物性为正且末状态严格达标。上述事实不是全场四位精度证明，更不是实测预测误差。最终的网格、时间和输出插值误差必须由本轮最终记录给出；不能把历史N1600标签改为最终细网格结果。

### 11.2 β加倍的反常趋势经独立网格对照后如何解释

本队固定Q23的所有物理与环境输入，比较β=8e−7和1.6e−6m/s，以及N200/400/800、两种水面离散，共12例。全部使用核心v4和解析Jacobian，rtol=1e−8、温度atol=1e−8K、浓度atol=1e−10kg/kg、前4h最大步10s、后段300s。

| N | 水面通量 | β原值临界/h | β加倍临界/h | 加倍后变化 |
|---:|---|---:|---:|---:|
${betaTable}

N200调和面确实出现反常延时；加密到N400/N800后方向反转。Kirchhoff三层均显示加倍β缩短时长约4.876%，且后两层的β效应差仅约0.0168s。N200调和面的表层最后一个内部面在24h出现局部通量反向反馈，指标Ξ约13.31，支持欠分辨机制解释。

在共同保存的14个时刻，调和面反向浓度差集中于最外内侧节点并随加密下降；Kirchhoff反向差仅浮点量级。完整热湿耦合的温度也会随β改变，故不能未经证明套固定温度标量比较原理。两个β点不能识别全局最优β；单个N200调和面结果不足以支持后期减弱排湿的建议。

12例总墙钟约${beta.wall_elapsed_s.toFixed(3)}s、子进程累计CPU约${beta.completed_child_cpu_s.toFixed(3)}s，均在预定预算内；警告为0，质量残差最大约8.44e−15kg/kg。检查PASS并不保证所有场值收敛。详见${link("paper_output/results/peer_beta_check/peer_beta_check_report.md", "β独立验证与比较原理限定")}及${link("paper_output/results/peer_beta_check/aggregate_summary.json", "12例原始记录")}；这批结果不改变主代理的最终生产选型。

### 11.3 外来ZIP/Word参考的使用边界

已审查参考的公式、代码文本、数据文件和输出，不运行其代码、不加载其pickle。其早期端点与本队解接近可作交叉核对，但参考N400调和面时长接近本队旧调和结果，不能因文档成稿而取代收敛验证。

已确认的具体问题包括：Q2文件只含前3h；部分JSON平均量重复除2；Q3/Q4尾部时刻与“首个严格达标分钟”的文字不一致；Q4先抽稀为21个材料节点再插到物理半径，不能把求解N400直接当输出插值N400；参考的“2.35e−4低于1e−4”算术错误，四位显示也不自动说明四位可靠。

Word是同一ZIP结果的公式/图表汇编，21张嵌图与ZIP逐字节一致，六张表共有的225个场值/空域单元也相同，没有新增独立数值证据。Word表6还删去了ZIP正文表中的“药材表面”和“当前半径R”列，降低了收缩核对的完整性。原生公式存在空操作数和残留命令，部分原PNG文字已损坏；这些属于资料审查发现，不把版式完成程度转成模型通过状态。可借鉴的是结构、对照设计与明确的物理问题，不采纳未经验证的最优β、真实密度已闭合或潜热仅2%等结论。

审查入口：${link("notes/A-modeling/2026-09-10/data/peer_reference_data_review.md", "参考ZIP数据与模型审查")}、${link("notes/A-modeling/2026-09-10/peer_word_review.md", "参考Word对照审查")}。

### 11.4 审查结果怎样落到模型决策

${link("notes/A-modeling/2026-09-10/data/independent_model_risk_review.md", "独立物理反证审查")}支持的结论是：当前一维材料基线在声明假设后可计算、量纲一致；它不能同时保留真实湿密度、固定长度、给定半径和无损干质的所有字面解释，也没有关闭真实气固平衡。

${link(PHYSICS + "physics_physical_sensitivity_review.md", "物理敏感性审查")}区分可解释参数情景与未闭合潜热压力测试。${link("notes/A-modeling/2026-09-10/data/derivation_review.md", "早期推导独立审查")}提出的非等温Ceq、B符号和BDF描述问题，已反映到本稿冻结公式M18、M06/M09、M45及J附录；不能把该早期报告的旧公式总数继续套到本稿。

若决定改用严格真实密度、真实气侧传质或状态驱动的收缩本构，需重新定义变量与缺失参数、求解和验证。保持形式相似而只改文字符号不能完成模型切换。当前数据不足以唯一标定这些新函数，相关路线作为有据替代保留，不写成已运行结果。

### 11.5 核心v5的磁盘连续输出属于存储等价改动

为控制本机实际内存占用，DiskBDF把每个已接受BDF连续多项式的float64系数D原字节写入项目tmp/cache私有缓存，保存阶数、时间平移和分母；查询时重新读取系数并调用原SciPy BdfDenseOutput求值器。接受状态数组使用文件映射。该实现没有增加分段重启、改变积分步，或增加新的时间/空间插值，也不新增物理公式；因此本稿101块登记不变。

已只读核对${link("paper_output/code/modeling/disk_dense.py", "磁盘连续输出模块")}及${link("paper_output/results/dense_storage_verification/verification.json", "N40完整轨迹存储等价验证")}。记录状态为${denseStorage.status}：Q1、Q23、Q4三条N40完整轨迹的接受时刻与状态逐位相同，事件与末时刻逐位相同，分别2203/2206/2206个连续查询的最大差为0，无警告；私有缓存关闭后清理通过。这只验证存储等价，不验证N40空间精度，也不把所有诊断归约值声明为逐位相同。新版细网格最终数值与输出仍由主代理冻结。

## 十二、最终结果与本轮验证记录

<!-- ROOT_FINAL_RESULTS_BEGIN -->
**待主代理补入本轮最终验证结果。**

本区没有占位时长或伪造场值。主代理完成最终生产、输出和独立验证后，应将以下内容以实际记录填入：

| 项目 | 当前状态 | 应补入的具体证据 |
|---|---|---|
| Q1最终温湿场与输出表 | 待本轮最终冻结 | 采用网格/时间参数、全场误差、常系数/Duhamel校核及逐秒输出检查 |
| Q2全过程T/C及前3h论文表 | 待本轮最终冻结 | 同一完整Run来源、终止范围、逐秒21点输出和源/输入哈希 |
| Q3临界与严格报告时长 | 待本轮最终冻结 | 全域最大值事件、M55原精度后验值、60s输出与末时刻约定 |
| Q4缩域/表面输出与时长 | 待本轮最终冻结 | 当时R、域外空值、真实表面、固定厘米位置插值误差与同物性几何对照 |
| 空间、时间、存储/插值一致性 | N40存储等价通过；最终运行待核验 | 同模型同离散族的误差指标、磁盘连续输出细网格运行和查询记录 |
| VS GUI与人工审查 | 由主代理补充实际状态 | 代码版本、运行/断点/变量证据；GUI运行与用户已审查分别记录 |
| 交接摘要与交付文件 | 由主代理补充 | 浓缩MD、结果文件、来源/限制及实际发送或播放状态另行记录 |

本稿中的历史N1600、N200物理敏感性、二维和β表均已明确版本与用途，不能自动挪入该区作为本轮最终值。任何最终结果仍是所列物理与边界假设下的条件性预测，不冒充内部实测验证。
<!-- ROOT_FINAL_RESULTS_END -->

## 十三、实际组装与复现说明

本稿由同目录assemble_complete_model.mjs读取冻结推导与审查证据组装，只写本MD，不运行模型。脚本在写入前验证冻结源哈希、9个E表行、92个唯一公式tag以及全部原始display公式逐块保留；不产生S7通过声明。再次组装默认拒绝覆盖已存在文件；只有正文仍是未被人工修改的生成版本时才允许显式刷新，避免覆盖主代理补入的最终结果。

建议阅读次序为一至六节→M01—M35→M36—M55/K01—K03→A附录→J附录→独立证据与最终结果区。本文中的公式与现有源代码是建模工作成果，正式提交前仍须按当届要求整理引用、AI参与披露、匿名性、正文/附录边界与团队人工核实；这些尚未完成的正式论文工序不改变本文件作为内部交接稿的用途。
`;

const sources = [...reads.entries()].map(([relative, record]) =>
  "| " + link(relative, relative) + " | " + record.bytes + " | " + record.sha256 + " |").join("\n");
const provenance = `
### 来源文件与本次读取哈希

下表记录本次组装实际读取的文件快照；历史审查文件内部还可能记录更早的代码哈希，应按各次证据解释。没有把当前磁盘新核心哈希倒写到旧运行记录。

| 文件 | bytes | SHA-256 |
|---|---:|---|
${sources}

组装脚本SHA-256：${digest(fs.readFileSync(SCRIPT))}。
`;

const body = front + "\n## 八、理论模块I：主模型、物理闭合与全部E/M/K推导\n\n" +
  moduleBody(physicalSource, "本物理主模块") +
  "\n\n## 九、理论模块II：二维轴对称端面对照（A1—A8）\n\n" +
  moduleBody(axisSource, "本二维附录") +
  "\n\n## 十、理论模块III：解析Jacobian与隐式推进（J01—J26）\n\n" +
  moduleBody(jacSource, "本Jacobian附录") + "\n" + evidence + provenance + "\n";

const tags = [...body.matchAll(/\\tag\{([A-Z]+\d+)\}/g)].map(match => match[1]);
const expectedTags = [
  ...Array.from({ length: 55 }, (_, i) => "M" + String(i + 1).padStart(2, "0")),
  ...Array.from({ length: 3 }, (_, i) => "K" + String(i + 1).padStart(2, "0")),
  ...Array.from({ length: 8 }, (_, i) => "A" + (i + 1)),
  ...Array.from({ length: 26 }, (_, i) => "J" + String(i + 1).padStart(2, "0")),
];
if (tags.length !== 92 || new Set(tags).size !== 92 ||
    expectedTags.some(tag => !tags.includes(tag))) {
  throw new Error("Formula tag inventory failed.");
}
if ([...body.matchAll(/^\| E\d{2} \|/gm)].length !== 9) {
  throw new Error("Empirical formula table must contain exactly 9 registered rows.");
}
let preservedDisplays = 0;
for (const source of [physicalSource, axisSource, jacSource]) {
  for (const match of source.matchAll(/^\\\[\n[\s\S]*?^\\\]$/gm)) {
    if (!body.includes(match[0])) throw new Error("An original display formula was altered.");
    preservedDisplays++;
  }
}
if (preservedDisplays !== 98) throw new Error("Unexpected source display-block inventory.");
if (/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/.test(body)) {
  throw new Error("Unexpected control characters.");
}
const marker = "<!-- assembler-content-sha256: " + digest(body) + " -->\n";
if (fs.existsSync(OUTPUT)) {
  const previous = normalized(fs.readFileSync(OUTPUT, "utf8"));
  const match = previous.match(/^<!-- assembler-content-sha256: ([a-f0-9]{64}) -->\n/);
  if (!process.argv.includes("--refresh-generated") || !match ||
      digest(previous.slice(match[0].length)) !== match[1]) {
    throw new Error("Refusing to overwrite an existing or manually updated handoff.");
  }
}
fs.writeFileSync(OUTPUT, marker + body, "utf8");
console.log(JSON.stringify({
  output: OUTPUT, registered_formula_blocks: 101, unique_tags: 92,
  preserved_display_blocks: preservedDisplays, empirical_rows: 9,
  bytes: fs.statSync(OUTPUT).size, sha256: digest(fs.readFileSync(OUTPUT)),
  status: "THEORY_ASSEMBLED_FINAL_RESULTS_PENDING",
  frozen_sources_unchanged: true, new_model_runs: 0,
}, null, 2));
