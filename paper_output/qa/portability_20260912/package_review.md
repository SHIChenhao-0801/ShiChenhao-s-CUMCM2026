# 原始提交包完整性与可移植性独立审计

结论：**原始ZIP不具备脱离作者工程的独立运行条件（FAIL_PORTABILITY_ORIGINAL_PACKAGE）**。这是对本报告绑定的原始版本的只读审计；修复后的新包应单独验收。

- ZIP：`paper_output\submission\支撑材料\A题_支撑材料.zip`
- SHA256：`6460f3299e012c2728385b1f78212386ba98b30a1acad926b9c446cc890c5b91`
- 体积：13,254,253字节；178项；CRC通过；178项与打包清单SHA256一致；无重复项。
- 包含55个Python文件，其中code下46个、evidence下9个；另有1个MATLAB和1个PowerShell；无C++。55个Python均通过语法解析/编译检查，本子审计未执行这些生产或历史程序。
- 独立代码身份词扫描未命中所列人名/学校/用户目录词；该结果仅是限定文本扫描，不等于完整匿名终审。

## 运行阻断与补齐项

### P01 包内目录与核心根目录推导不一致（blocking）

ZIP将交付代码放到code/，但Python仍向上取parents[3]，MATLAB仍向上四层。解压根目录启动时会触发cwd检查；绕过该检查也会读写解压目录外的错误根目录。主求解、导出和MATLAB入口均受影响。

包内定位：`code/runDelivery.py:29`；`code/runDelivery.py:230`；`code/dryingCore.py:27`；`code/exportOutputs.py:40`；`code/matlab/runCrossCheck.m:10`

### P02 入口无条件依赖未打包的冻结工程（blocking）

final和audit均调用verifyFrozenBaseline，要求paper_output/results/production/final_v6a/run_manifest.json及账本中107项输入输出存在并逐字节匹配。包中只有重定位到evidence/final_v6a_run的部分账本/摘要，没有全量NPZ、原精度gz与原目录树。final还要求新解、事件、原精度CSV与冻结结果精确相等；此回归模式不能作为无历史工程的独立生产入口，也不能据此保证不同平台浮点逐位相等。

包内定位：`code/runDelivery.py:110`；`code/runDelivery.py:115`；`code/runDelivery.py:253`；`code/runDelivery.py:159`；`code/runDelivery.py:176`

### P03 输入CSV存放位置不匹配，原始附件和输出模板缺失（blocking）

两份清洗数据存在于figures/A_*_observed.csv，求解器读取paper_output/data_cleaned。题面附件1/2原始XLSX与附件3四个空白模板均未打包；顶层result1—4.xlsx是正式结果，不能冒称原始模板。仅修正根目录仍不能完成求解和导出，也不能完整重跑数据准备。

包内定位：`code/dryingCore.py:35`；`code/exportOutputs.py:43`；`code/exportOutputs.py:105`；`code/matlab/runCrossCheck.m:64`；`code/data/prepare_a_data.py:39`

### P04 交叉验证代码仍绑定作者磁盘路径（blocking）

14个code/verification脚本直接将ROOT绑定D:/Document/数学建模/2026CUMCM；validate_bessel还强制cwd等于该绝对路径。另一设备或另一解压位置会读不到源码/数据，甚至误读同名旧工程，无法依靠ZIP独立复现。

包内定位：`code/modeling/validate_bessel.py:291`；`code/verification/analytic_metric_check.py:24`；`code/verification/crossvalidate_solver.py:28`；`code/verification/isotherm_activity_closure.py:59`

### P05 扩展管线依赖未列全且绘图强制本机字体（blocking_for_extended_pipeline）

实际ZIP包含19个旧建模脚本、14个验证脚本及数据准备程序；requirements仅列numpy/scipy/openpyxl，遗漏实际导入的matplotlib。publication_plots在C:/Windows/Fonts/msyh.ttc不存在时直接raise，run_modeling无条件stat该字体。精确依赖是否能在目标平台安装应另作干净环境实测；本次不把语法通过当成安装验证。

包内定位：`code/requirements.txt:2`；`code/modeling/publication_plots.py:25`；`code/modeling/publication_plots.py:32`；`code/modeling/run_modeling.py:65`；`code/data/prepare_a_data.py:23`

### P06 运行说明和监督器保留本机启动方式（blocking_for_documented_commands）

README让接收者打开未打包的A_CodeReview.sln，并切到作者D盘目录，以包内不存在的paper_output/code/review_delivery路径启动。监督器默认C:/Python314/python.exe。README全部6个本地Markdown链接在包中无法解析；需要面向解压根目录的安装、运行、预期输出与失败判定说明。

包内定位：`code/README.md:27`；`code/README.md:40`；`code/README.md:45`；`code/runLogged.ps1:4`；`code/runLogged.ps1:7`

### P07 重命名和旧修复验证工具的历史依赖缺失（blocking_for_historical_tools）

旧代码实际在code/modeling，但工具仍找paper_output/code/modeling。verifyExportPathFix另外读取明确排除的tools/exportPathFixBefore和camel_final_v1失败目录。这些文件可用作开发历史证据，当前无法作为随包可执行复现程序。

包内定位：`code/tools/verifyCamelCopies.py:17`；`code/tools/buildCamelCopies.py:16`；`code/tools/verifyExportPathFix.py:32`；`code/tools/verifyExportPathFix.py:40`；`code/tools/verifyExportPathFix.py:66`

### P08 打包通过仅证明容器完整，未证明运行闭包完整（assurance_gap）

附录目录项仅检查any(n.startswith(item))，并未验证其中程序的输入、依赖、路径或调用链。退出条件只检查压缩大小与身份词零命中，missing_sources/附录完整性也未纳入返回码。现有178项CRC/SHA一致和体积合规可确认，但不能推出独立运行通过。

包内定位：`paper_output/submission/支撑材料/build_support_package.py:406`；`paper_output/submission/支撑材料/build_support_package.py:477`

## 验证边界

本报告仅证明原包容器/文件指纹和静态依赖问题；未安装新环境、未执行数值求解、未操作MATLAB/Visual Studio、未替用户人工签核。实际隔离重跑由主代理另存证据。不得将旧本机GUI成功、CRC/SHA通过、或Python语法通过合并称为另一设备已独立复现。

修复应提供解压根目录入口、完整输入与模板、可安装的依赖和平台说明、可选的历史回归模式、可运行的验证/绘图入口及包内有效链接。最终以不接触作者源工程的解压副本实际运行、全量导出回读和预期数值比较为验收依据。
