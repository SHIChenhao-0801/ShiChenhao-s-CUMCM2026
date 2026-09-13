# 附录 B 支撑材料与复现说明

## B.1 材料范围与代码覆盖

本附录对应当前冻结的支撑材料目录，共106份正式文件。目录包括题面与原始数据、文献资料、独立生产程序、四问完整结果以及数值检验程序。Visual Studio自动产生的本机缓存和升级日志不列入正式材料计数。附录D完整收录47份源码、9917行：其中44份为支撑材料现有全部源码，另补充原始数据处理、六图数据导出和R绘图3份源码。语言构成为Python 43份，PowerShell、JavaScript、MATLAB和R各1份。

独立生产程序位于03_程序代码；05_数值检验与实验保留了模型依赖、交叉检验和历史诊断。这两部分有不同的运行目的和版本来源，不能互相混用模块。附录D各节列明用途和采用范围，并逐行给出完整源代码；实际验证范围与限制见B.5、B.6。未采用的早期算法副本、论文排版脚本和资料包表格展示工具不作为新增建模代码重复收录。

44份现有源码与已完成独立运行核查的去注释候选逐文件核对SHA256。追加的两份Python脚本删除说明性docstring及注释后，非注释抽象语法树与原文件相同；R脚本通过原生解析器确认去注释前后表达式相同。字符串中的颜色、格式符、文件名和运行提示保留。源码逐字节校验用于绑定版本，运行通过范围仍按本附录的实际证据分别说明。

## B.2 输入、单位与资料来源

数值输入来自本届A题题面和官方附件。原始PDF、Excel与清洗后CSV分别保存；数据处理不删除观测、不填充缺失、不平滑、不拟合外推。附件1、附件2均通过字段、有限值、重复时间和采样间隔检查，清洗操作仅为增加单位换算列。官方空白result1.xlsx至result4.xlsx用于规定导出结构；04_结果表格中的同名工作簿是已计算结果。

| 输入或变量 | 实际范围与单位 | 程序处理 |
|---|---|---|
| 附件1环境观测 | 241条；0—14400 s；每60 s一条；温度为°C；空气水分指标为kg/kg | 增加小时列与开尔文列；观测间分段线性插值 |
| 附件2半径观测 | 145条；0—259200 s；每1800 s一条；半径为cm | 增加小时列与米制列；正值、非增和采样间隔检查 |
| 时间与空间坐标 | 求解内部使用s、m | 输出表及图按题意转为h、cm或保留s |
| 材料温度 | 求解内部为K | 温度输出由T−273.15换算为°C |
| 材料含水率C | kg水/kg干物质，即干基kg/kg | 与空气水分指标的物理分母区别说明；二者映射需模型闭合 |
| 附录2—4物性 | 扩散系数m²/s；导热系数W/(m·K)；比热J/(kg·K) | 按各问给定函数计算，不从外部资料代入经验参数 |
| 对流与质量交换系数 | 热交换W/(m²·K)，质量交换m/s | 与模型的温度差及含水率通量定义一致 |

4 h以后的环境温度50°C和空气水分指标0.05 kg/kg属于延拓假设。附件1在4 h的真实末点为50.165°C和0.04986 kg/kg，程序及图件保留此点，并将后续平台作为右侧延拓。空气指标映射为材料平衡含水率、干物质骨架径向同比收缩、轴向长度不变及有效热容量均是模型闭合的一部分。题面未提供内部温湿实测、吸附等温线、测量不确定度或轴向收缩观测，不能将数值自洽解释为物理预测准确率。

外部资料用于干燥背景、有限体积方法、隐式积分与接口依据，未向正式求解引入额外环境实测或直接移植其他物料的经验参数。支撑文献中的两篇中文综述实际PDF分别为28页和8页；Handbook of Industrial Drying文件为5页节选；Finite Volume Methods文件为254页作者更新稿；The MATLAB ODE Suite扫描为35页，其期刊信息为1997年18卷1期1—22页。FAO网页用于平衡含水率概念，SciPy网页用于接口核查；文件范围与文献版本按02目录说明区分。

## B.3 计算环境与依赖

正式重算在独立Windows Sandbox中实际执行。该环境关闭网络，原宿主D盘工作区不可见，运行库、源码、输入和模板显式提供，不继承宿主Python的site-packages。Windows Sandbox使用CPU完成计算；所记录耗时只对应本次设备和环境，不构成其他机器的性能保证。

| 环节 | 实际验证环境 | 范围 |
|---|---|---|
| 03正式生产求解 | Windows 11；64位Python 3.14.7；NumPy 2.5.2；SciPy 1.18.1；openpyxl 3.1.5 | Q1/Q23为N3200，Q4为N6400；三条轨迹、四问完整导出与回读 |
| 03辅助入口 | Windows Sandbox；Windows PowerShell 5.1；同一Python依赖 | 原runLogged.ps1的quick全流程，N40三轨迹及四表 |
| 05检验 | Windows Sandbox；同版Python/NumPy/SciPy/openpyxl；Matplotlib 3.11.2 | 31个Python源码有实际入口或函数调用覆盖，结果和限制分别记录 |
| 原始数据预处理 | Windows 11；Python 3.14.7；NumPy 2.5.2；openpyxl 3.1.5；Matplotlib 3.11.1 | 原版已实际处理两附件并回读CSV；不是本轮VM运行版本声明 |
| 最终六图 | 宿主Windows 11；R 4.6.1自带graphics/grDevices；Cairo；Microsoft YaHei、Times New Roman | 已实际生成六张PNG/PDF/SVG和合并PDF；本次附录仅核对代码与现存产物 |
| JavaScript对照入口 | Windows Sandbox；Node.js 24.20.0 | 实际进程退出2，缺MATLAB结果文件；未通过 |
| MATLAB对照源码 | 本机历史环境记录为MATLAB R2026a；本轮VM没有MATLAB入口 | 本轮未执行，不能以Python对照替代 |

03的requirements.txt固定三项数值依赖。diskDense.py使用SciPy的BDF内部稠密输出接口，复现时应按指定版本安装。程序固定计算线程数并顺序求解三条轨迹，不要求GPU。Q4稠密输出缓存约8.33 GB，建议预留至少20 GB磁盘空间；已有运行设备约32 GB内存，最低内存需求未专门测定。Linux和macOS未实际验证。

## B.4 独立生产程序的复现步骤

在03_程序代码目录打开终端，先安装依赖，再预检输入。每次运行使用新的结果目录；若自行指定相同run-id且目录已存在，程序会拒绝覆盖。

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe -X utf8 -B runDelivery.py --preflight-only
.venv\Scripts\python.exe -X utf8 -B runDelivery.py --profile quick
.venv\Scripts\python.exe -X utf8 -B runDelivery.py --profile final
./runLogged.ps1 -Python .venv\Scripts\python.exe -Profile final
```

quick为N40小网格完整流程，final为正文采用的N3200/N3200/N6400正式流程。辅助PowerShell命令与直接Python命令是两种启动方式，使用任一方式完成目标网格即可。判定完成必须同时检查真实进程退出码0与该次运行记录中的PASS；preflight-only的PASS仅表示输入预检通过。N40全流程因问题二逐秒导出，仍需较长时间。

程序根目录按runDelivery.py位置确定。input_manifest.csv逐项核查12份输入、模板与参照的大小和SHA256；reference_data.py保存冻结数值参照，reference目录的三份NPZ用于轨迹比较。运行后在results下生成四份Excel、对应原精度CSV.GZ、七份正文CSV、轨迹NPZ及运行日志。运行产物包含程序生成的JSON校验记录，与本附录列出的静态支撑文件清单区分。

Visual Studio工程A_CodeReview.sln和A_CodeReview.pyproj可用于打开源码并选择本目录解释器。当前去注释源码已在Visual Studio中实际打开、命中dryingCore.py断点并单步核对初值和加载源码；本轮没有在Visual Studio完成正式全量求解，团队人工审查须由本人完成。

## B.5 已实际完成的数值复现与验证

正式Windows Sandbox运行真实退出码为0，程序内部PASS。程序记录耗时1810.989 s，外部监督记录1812.629 s。二者分别计入程序主体和外部启动监督开销，应按同一口径比较。四份正式冻结Excel在本次去注释与复现过程中未被覆盖，其SHA256与冻结清单一致。

| 核查项目 | 实际检查规模 | 结果及适用范围 |
|---|---|---|
| 正式三轨迹 | Q1/Q23 N3200；Q4 N6400 | 求解、四问导出、完整回读和冻结数值对照PASS |
| 四份工作簿 | Q1 79,244格；Q2 9,103,732格；Q3 75,922格；Q4 76,700格 | 共9,335,598格全量回读并对照同次原精度CSV归档，297正文数据格另由实际求解对象查询 |
| 七份正文CSV | 合计297个数据格 | 与同次求解对象逐格核对通过 |
| 三轨迹保存状态 | 共21个保存数组 | 与final_v6a冻结参照逐值相同；输入和源码运行前后SHA不变 |
| 严格阈值判定 | Q3报告57.4724 h，Q4报告51.0906 h | 未舍入全域最大值分别为0.14999989718225315与0.14999995339076624，均严格小于0.15 |
| 原PowerShell辅助入口 | quick，N40三轨迹、四表导出和回读 | 稳定重试真实退出0、内部PASS；监督耗时892.825 s |
| Bessel基准自检 | 原8项检查 | 满足原容差 |
| 解析稀疏Jacobian | 84状态、336方向、每方向3个差分步长；4条短BDF轨迹 | 原检查全部通过，无警告 |
| 内存/磁盘稠密输出 | N40的Q1/Q23/Q4各两条轨迹；38,337次稠密查询 | 接受步、状态与事件逐位相同，查询差为0，关闭后缓存清除 |
| Q1数值检查 | N20/N40网格比较；N20基准/紧容差双子进程 | 原比较链完成；用于相应小网格检查，不替代正式网格精度证明 |
| 独立Q1导出自检 | N40；79,244个工作簿格和84个正文CSV格 | 当前求解对象与导出回读一致，内部PASS |
| 二维关闭端面对照 | nr=6，nz=4，端面交换关闭 | 二维与一维事件差约−1.899×10⁻⁷ h；只对应本次小网格 |
| 事件独立复核 | N20 Q23/Q4，事件根与二分核验 | 时刻差约8.73×10⁻¹¹ s、5.82×10⁻¹¹ s，严格报告判据通过 |
| 求解方法比较 | quick的8次Q1计算 | N100/N200误差约1.489×10⁻⁵和3.729×10⁻⁶，原门槛通过 |

PowerShell首轮在内部数值检查完成后，外部观察器提前退出引发控制台状态错误，真实退出码为1；该轮未计入通过结论。后续在独立隐藏控制台中保留监督进程至结束，原辅助脚本重新完整运行得到上述成功记录。核验同时保留失败与重试的来源，避免以内部日志中的单一PASS覆盖真实进程状态。

## B.6 检验源码的限制与未通过项目

05目录包含33份源码：31份Python、1份MATLAB及1份JavaScript。Windows Sandbox中29项受控Python任务覆盖31份Python源码，24项退出0、5项退出1。源码覆盖、进程正常退出和数值判据通过是不同结论，不能据此概称05全部跑通。

这些历史检验使用原工作区路径。先验证未适配入口的路径问题后，仅在独立测试副本中修改14处根目录表达式，未改变物理模型、求解算法或误差门槛；正式支撑源码及附录D保留原路径。运行矩阵分别保存交付源码SHA和沙盒实测源码SHA。重建这些历史测试时，须提供对应的源码层级、两份观测CSV、四个模板和Q23参照NPZ，另按入口要求提供必要配置；03生产入口没有这些历史上级路径依赖。

首轮测试中6项因旧输出目录被带入而触发FileExistsError，随后在只含源码和必要输入的新目录重试，5项退出0，另1项明确缺model_route.json。旧输出与首轮目录错误不计为新的计算成果，也不将目录准备问题作为模型算法失败。

| 未通过任务 | 实际原因 | 处理与结论 |
|---|---|---|
| run_modeling.py | 缺少原要求的paper_output/plan/model_route.json | 保留真实FileNotFoundError，未伪造配置或删除检查 |
| isotherm_diagnose.py | 向ActivityModel传入旧B参数 | 真实TypeError；没有把B改释为p |
| isotherm_activity_closure.py | _extract将时间×空间数组按相反方向取值；真实形状3×2 | 第三个时点IndexError；p=1恒等式和RHS检查通过不消除此失败 |
| isotherm_jacobian_probe.py | 短时求解完成，替代Jacobian调用计数为0 | 注入诊断未被调用，不能证明已测试该Jacobian |
| 常数序列负例诊断 | crossvalidate_series.py的旧sequential_mk对40个相等值产生伪趋势 | 诊断任务退出1；主程序即使退出0，旧统计结论仍不成立 |

退出0的任务中也有明确限制。compare_analytic.py在N400的密集采样冻结扩散水分最大误差为2.875083008730961×10⁻⁴，超过原10⁻⁴门槛，内部状态为REVIEW_REQUIRED；N800该误差为7.158659870798445×10⁻⁵。analytic_metric_check.py的点值与单元平均差随网格加密递减，原静态解释与计算趋势不符。publication_plots.py完成4图生成，其状态仍为待视觉检查；这4张检验图不能替代正文6张R图的核验。

能量检查通过的明确范围是Q1 N20：瞬时相对残差约4.44×10⁻¹⁶，累计相对残差约2.385×10⁻⁴，小于原10⁻³门槛；Q23/Q4短时能量诊断中的较大累计残差保留，不能据此声称四问能量守恒全部通过。潜热情景只实测N20、latentFraction=0.25的一条Q23事件；灵敏度脚本只核验N200控制对照两条事件；未完成完整Morris或Sobol批次，也不将小网格局部运行记作原大批次通过。

Node.js原对照进程实际退出2，原因是缺少MATLAB的runSummary.json。Windows Sandbox未提供MATLAB可执行环境，MATLAB脚本本轮未运行。保留这两份完整源码用于追溯，其存在和历史对照材料不意味着本次独立沙盒验证通过。

## B.7 正文六图的代码与数据衔接

附录D.45的prepare_a_data.py处理官方原始数据，D.46的export_six_figure_package_20260912.py从冻结NPZ/JSON和观测CSV导出14张六图数据表，D.47的draw_figures.R直接读取这些CSV绘图。14张表共4627行；R输入副本与原导出CSV逐字节一致，现稿六图的DOCX媒体均可按SHA直接对应R目录中的实际图件。图1、3、4采用N3200结果，图5采用N6400结果，图6的6个情景点统一为N800、零潜热负荷。

| 图号 | 内容 | 数据与绘制约束 |
|---|---|---|
| 1 | 指定时刻径向温度和含水率 | 七个时刻；121个径向展示样点；原值作图 |
| 2 | 环境观测与4 h后平台 | 保留241条观测和4 h末点；平台左端开放，观测与假设分开 |
| 3 | 中心、表面热湿响应 | Q23同一轨迹；温度0—4 h，含水率至临界事件 |
| 4 | 全域阈值与临界放大 | 主图标示对数纵轴；中心与最大值重合处如实叠加；放大图只连接已有点，独立标注严格核验时刻 |
| 5 | 半径变化与收缩域内剖面 | 六条曲线各用其真实半径列；止于当时表面，域外留空 |
| 6 | 经验边界阻力情景 | 仅p=1、2、4的实际6点；不混入高分辨率生产结果，不添加误差棒 |

六图由R 4.6.1自带graphics/grDevices实际绘制，包含PNG 300 dpi和PDF/SVG矢量输出。原运行完成11组坐标范围检查及末点、开放平台、阈值和真实半径核验；本次编制附录没有重新积分或重新绘图。原始数据处理运行记录绑定了原脚本SHA；六图导出和R绘图的既有记录未完整绑定原源码SHA，因此本次对追加副本的结论限于语法、去注释等价及现存产物对应，不将其写作去注释版本已独立重跑。

追加脚本保留原项目相对层级和输入依赖，不能作为03独立生产入口的替代。复用已保存的14张CSV绘图时，在项目根目录执行以下命令；若迁移工程，应按源码中读取路径一并保留对应目录。

```powershell
Rscript --vanilla paper_output/figures/review_20260913/draw_figures.R
```

原始数据处理脚本依赖项目input_manifest.json；六图数据导出脚本依赖冻结结果和build_manifest.json中的来源索引。附录完整收录实际算法以便审阅，未把这些历史依赖删除或伪装成独立可运行条件。六图数值表来源、现存图件、程序验证范围和正文模型结论应结合阅读。

## B.8 当前106份正式支撑文件清单

下列清单覆盖本次冻结支撑材料的全部106份正式文件，编号连续。各表文件路径以表前所列目录为相对根；“根目录”条目直接位于支撑材料目录内。追加的3份数据与绘图源码单列于附录D.45—D.47，未据此改写原106文件目录。完整工作簿与轨迹参照保留在电子支撑中，其大型数值内容不在纸面逐格重印；七份正文结果表及关键高精度值见附录C。

根目录（6份）

| 编号 | 相对文件路径 |
|---|---|
| 1 | 00_可用于论文附录的支撑清单.txt |
| 2 | 00_支撑材料总说明.txt |
| 3 | 00_整理验收说明.txt |
| 4 | 00_文件清单.txt |
| 5 | 00_材料来源说明.txt |
| 6 | 源码去注释与沙盒核查.txt |

01_赛题与原始数据（10份）

| 编号 | 相对文件路径 |
|---|---|
| 7 | A题.pdf |
| 8 | 数据说明.txt |
| 9 | 清洗后数据/A_environment_observed.csv |
| 10 | 清洗后数据/A_radius_observed.csv |
| 11 | 附件/附件1.xlsx |
| 12 | 附件/附件2.xlsx |
| 13 | 附件/附件3/result1.xlsx |
| 14 | 附件/附件3/result2.xlsx |
| 15 | 附件/附件3/result3.xlsx |
| 16 | 附件/附件3/result4.xlsx |

02_参考文献与网络资料（11份）

| 编号 | 相对文件路径 |
|---|---|
| 17 | Handbook of Industrial Drying.pdf |
| 18 | Handbook of numerical analysis.pdf |
| 19 | 中药材干燥技术与装备研究现状.pdf |
| 20 | 参考文献文件说明.txt |
| 21 | 数值模拟仿真研究现状及其在中药干燥领域应用展望_王晓辉.pdf |
| 22 | 补充网络资料/FAO_干燥原理_官方网页.html |
| 23 | 补充网络资料/FAO_干燥原理_官方网页_离线文本.html |
| 24 | 补充网络资料/SciPy_solve_ivp_官方API网页.html |
| 25 | 补充网络资料/SciPy_solve_ivp_官方API网页_离线文本.html |
| 26 | 补充网络资料/Shampine1997_BYU原始扫描_35页.pdf |
| 27 | 补充网络资料/补充资料说明.txt |

03_程序代码（30份）

| 编号 | 相对文件路径 |
|---|---|
| 28 | A_CodeReview.pyproj |
| 29 | A_CodeReview.sln |
| 30 | README.txt |
| 31 | analyticJacobian.py |
| 32 | diskDense.py |
| 33 | docs/源码变更说明.txt |
| 34 | docs/运行验收说明.txt |
| 35 | dryingCore.py |
| 36 | exportOutputs.py |
| 37 | input_manifest.csv |
| 38 | inputs/cleaned/A_environment_observed.csv |
| 39 | inputs/cleaned/A_radius_observed.csv |
| 40 | inputs/original/附件1.xlsx |
| 41 | inputs/original/附件2.xlsx |
| 42 | inputs/templates/result1.xlsx |
| 43 | inputs/templates/result2.xlsx |
| 44 | inputs/templates/result3.xlsx |
| 45 | inputs/templates/result4.xlsx |
| 46 | numerical_design.txt |
| 47 | q1Model.py |
| 48 | q2Model.py |
| 49 | q3Model.py |
| 50 | q4Model.py |
| 51 | reference/Q1/sampled_solution.npz |
| 52 | reference/Q23/sampled_solution.npz |
| 53 | reference/Q4/sampled_solution.npz |
| 54 | reference/reference_data.py |
| 55 | requirements.txt |
| 56 | runDelivery.py |
| 57 | runLogged.ps1 |

04_结果表格（12份）

| 编号 | 相对文件路径 |
|---|---|
| 58 | Referrence Table Files/q1_paper_moisture.csv |
| 59 | Referrence Table Files/q1_paper_temperature.csv |
| 60 | Referrence Table Files/q2_paper_moisture.csv |
| 61 | Referrence Table Files/q2_paper_temperature.csv |
| 62 | Referrence Table Files/q3_paper_moisture.csv |
| 63 | Referrence Table Files/q4_paper_moisture.csv |
| 64 | Referrence Table Files/q4_paper_radius.csv |
| 65 | result1.xlsx |
| 66 | result2.xlsx |
| 67 | result3.xlsx |
| 68 | result4.xlsx |
| 69 | 结果表说明.txt |

05_数值检验与实验（37份）

| 编号 | 相对文件路径 |
|---|---|
| 70 | MATLAB对照证据/compareMatlab.mjs |
| 71 | MATLAB对照证据/runCrossCheck.m |
| 72 | Python检验源码/paper_output/code/modeling/analytic_jacobian.py |
| 73 | Python检验源码/paper_output/code/modeling/axisymmetric_check.py |
| 74 | Python检验源码/paper_output/code/modeling/compare_analytic.py |
| 75 | Python检验源码/paper_output/code/modeling/disk_dense.py |
| 76 | Python检验源码/paper_output/code/modeling/drying_core.py |
| 77 | Python检验源码/paper_output/code/modeling/export_outputs.py |
| 78 | Python检验源码/paper_output/code/modeling/production_provenance.py |
| 79 | Python检验源码/paper_output/code/modeling/publication_plots.py |
| 80 | Python检验源码/paper_output/code/modeling/q1_model.py |
| 81 | Python检验源码/paper_output/code/modeling/q2_model.py |
| 82 | Python检验源码/paper_output/code/modeling/q3_model.py |
| 83 | Python检验源码/paper_output/code/modeling/q4_model.py |
| 84 | Python检验源码/paper_output/code/modeling/run_experiments.py |
| 85 | Python检验源码/paper_output/code/modeling/run_modeling.py |
| 86 | Python检验源码/paper_output/code/modeling/validate_bessel.py |
| 87 | Python检验源码/paper_output/code/modeling/verify_convergence.py |
| 88 | Python检验源码/paper_output/code/modeling/verify_dense_storage.py |
| 89 | Python检验源码/paper_output/code/modeling/verify_time_accuracy.py |
| 90 | Python检验源码/paper_output/code/verification/analytic_metric_check.py |
| 91 | Python检验源码/paper_output/code/verification/crossvalidate_series.py |
| 92 | Python检验源码/paper_output/code/verification/crossvalidate_solver.py |
| 93 | Python检验源码/paper_output/code/verification/energy_balance_check.py |
| 94 | Python检验源码/paper_output/code/verification/energy_balance_diagnose.py |
| 95 | Python检验源码/paper_output/code/verification/energy_balance_diagnose2.py |
| 96 | Python检验源码/paper_output/code/verification/isotherm_activity_closure.py |
| 97 | Python检验源码/paper_output/code/verification/isotherm_diagnose.py |
| 98 | Python检验源码/paper_output/code/verification/isotherm_jacobian_probe.py |
| 99 | Python检验源码/paper_output/code/verification/latent_heat_scenarios.py |
| 100 | Python检验源码/paper_output/code/verification/method_comparison.py |
| 101 | Python检验源码/paper_output/code/verification/sensitivity_analysis.py |
| 102 | Python检验源码/paper_output/code/verification/threshold_and_scaling_checks.py |
| 103 | 数值检验说明.txt |
| 104 | 源码文件与校验值.txt |
| 105 | 独立沙盒运行矩阵.csv |
| 106 | 独立沙盒逐源码核查.txt |
