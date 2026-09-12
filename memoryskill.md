# 2026 CUMCM 比赛记忆

仅适用于 D:/Document/数学建模/2026CUMCM 及其子目录。当前持续任务：A题《药材的烘干问题》，停止B题分支。

## 长期准则

- 2026-09-10 18:00北京时间起，所有新增正式工作与终端cwd在本目录，父目录只读作为历史资料和共享工具。子代理同样遵守。
- 首要依据是最新9月10日赛前说明会，其原件在 reference_materials/contest-admin；保留要求/建议区别及讲义内部冲突，不编造校内澄清。
- 赛期至9月13日20:00；建议19:00前完成MD5，硬截止20:00；上传窗口9月13日20:30至9月14日14:00，上传文件须与所交哈希相同。正文最多30页（含AI声明/参考文献，摘要/附录另计），摘要至参考文献至少15页，20–30页是建议。PDF和支撑zip/rar各最多20M；MD5阶段需登记支撑哈希。
- 福州大学参赛小组；用户主导模型/结论，有论文同学协作。软件来源不改变队伍身份；论文匿名与AI披露按当届要求，内部材料不能直接作为匿名提交包。
- 数据审计→模型→真实运行检验→结果冻结→论文成稿→独立终审；S0–S8只认本届证据，旧练习PASS无效。当前准确阶段见 workflow_guard.py --status 与 paper_output/context/workflow_memory.json。
- Python/C++正式代码必须通过Computer Use在Visual Studio实际打开、断点/变量/运行复现；CLI成功、AI阅读均不能等同GUI复现或用户人工审查。MATLAB通过GUI，R通过Rscript；默认CPU与有限预算。
- 用户持续授权：每完成可复核工作单元由主代理检查后commit/push到私有GitHub仓库 SHIChenhao-0801/ShiChenhao-s-CUMCM2026/main，核对远端哈希才称备份；子代理不操作Git索引，不强推/删锁/丢弃修改。UTC04/10/16/22六小时同步安排见notes/workspace-maintenance。

## 接班核验更新（2026-09-12 北京时间，覆盖下方旧快照）

- 最新接班入口：`notes/A-handoff/2026-09-12/代班工作接班核对.md`。本轮用户要求阅读代班工作；已对 Git、源码/JSON、PDF/ZIP 与旧记忆交叉核对，未重跑生产、未改冻结结果或稿件。
- 实际已有完整论文/附件：`paper_output/submission/A题_论文.pdf` 108页，摘要1页、正文含AI/参考文献30页、附录第32页起；支撑ZIP178项/13254253B，CRC本轮通过。当前实际guard为S7→S8、INCOMPLETE；14项提交静态检查全绿不等于S8通过，旧格式报告FAIL且过期。`make_s7_contracts.py`直接写PASS与approved_sha256，不能理解成人工签核或完整章节审计。
- 交叉验证30个求解器案例、两种离散、独立根、潜热8例、边界缩放p=1/2/4共6例、D/k扫描已落盘。水活度情景只到事件，未验证事件后1秒。Morris旧dScale注入失效，余项仅为D固定下筛选；修补D/k扫描带基准自检可用，Sobol尝试后作废，未形成有效指数。
- **水活度重要勘误**：气相kg/kg直接当材料Ceq仍是假设，非题面已知平衡点；JSON中RH=.6072710989856436而awRef=.6，所谓零差比较的是aw(Cref)-awRef，是假阳性。partitionFactor未使用awRef，实际是原Robin乘K；p<1在C>=Cref时不必使aw负。不能据这些情景宣称真实时长必以57.4724/51.0906为下界；该错误已进入论文11.5/13.4节，待修。
- **热侧重要勘误**：CHECK A验证sum(2wBR²*Tdot)边界通量相消，不是d/dt sum(2wBTR²)。汇总用min(1,abs(丢弃功)/abs(残差))写100%解释不成立；JSON仍有Q23 177303.71、Q4 497934.08 J/m未解释残差。不得继承新报告总PASS作为全部科学结论通过。
- **人工审查**：code_delivery_status仍PENDING_USER_REVIEW，清单15项及签核空；未见本轮新增用户签核。论文/AI详情的“已逐项人工审查”当前无记录支持。PS5.1仍不能解析无BOM的runLogged.ps1，PS7解析通过、Python备用入口存在。完整CLI/GUI交付沿用camel_final_v2证据，不将9/12部分final目录当全量完成。
- 下一步优先修复上述科学/声明口径，贯通稿件和支撑；再补当前哈希下章节审核、S8与逐页终审、用户代码审查，最后冻结/MD5/登记上传。本轮已算文件指纹仅为接班快照，无比赛系统已登记或已上传的证据。

## 提交代码可移植性核验（2026-09-12 晚间，最新）

- 用户要求证实本次可提交代码是否完善、能否脱离本地环境在另一设备独立运行；本轮完成审计，原代码、正式结果和ZIP未改。主报告 `paper_output/qa/portability_20260912/提交代码独立运行核验报告.md`，机器判定 `audit_summary.json`，code_delivery_status新增submissionPortability。
- **当前提交ZIP独立运行FAIL**，绑定SHA256 `6460f3299e012c2728385b1f78212386ba98b30a1acad926b9c446cc890c5b91`，13,254,253B/178项，CRC/178项SHA与55个Python语法均通过。容器/语法通过不等于可运行。
- 从官方PyPI在不继承site-packages的新venv实际安装numpy2.5.2/scipy1.18.1/openpyxl3.1.5（传递et_xmlfile2.0.0），安装、pip check、BDF内部接口导入均exit0；只覆盖本机WindowsAMD64/Python3.14.7，非第二物理设备/其他系统。
- 干净venv原样解压final/audit均exit1（根目录检查）；仅复制为旧源码层级后两模式均exit1（缺final_v6a/run_manifest）；loadInputs实际exit1（CSV位置错）。只执行启动/输入探测，未进入PDE。命令、真实退出码和日志在clean_venv_execution.json。
- 包代码放code/、CSV放figures/，源码仍parents[3]/paper_output路径；14个verification脚本写死D盘根。两模式无条件核验107冻结文件，按SHA允许重映射仍48项内容缺失；四原模板缺失。原legacy已在code/modeling，不能误报未打包，但运行路径仍错。
- requirements未涵盖matplotlib（5个数据/绘图/验证脚本）及pymupdf（2个历史审计脚本）；强制微软雅黑字体。README要求未打包sln且路径/六链接失效；PS7解析过、PS5.1失败且无Kill(bool)。跨设备浮点逐位比较需独立预设数值验收标准。
- 已尝试Computer Use启动VS，但文件对话框未能可靠聚焦/输入，未打开诊断方案、未运行/命中断点；本轮GUI=NOT_COMPLETED，humanReview仍PENDING_USER_REVIEW。不得把旧gui_camel_final_v2等价为当前ZIP迁移通过。
- 下一步修复候选包的独立入口/路径/必需输入模板/依赖/说明，保留完整历史回归为可选；新包需隔离N40三轨迹+四题导出回读、正式全量和数值校验，再补当前哈希GUI与人工审查。本次未创建或认可修复后新包。

## 持续有效模型与代码交付要点

- 当前A题四问冻结基线final_v6a：Q1/Q23 N3200、Q4 N6400；Kirchhoff水通量、解析稀疏Jacobian；Q3连续57.47230195056044h、严格报告57.4724h；Q4连续51.09057478683054h、严格报告51.0906h。均为条件模型预测，无内部T/C实测精度。
- 附件1只0–4h共241环境点，其后50°C/0.05是平台延拓假设；附件2为0–72h共145半径点。Q1用附录2、Q2/Q3从t0整组附录3、Q4从t0整组附录4；Q2/Q3共享轨迹，不拼接Q1。
- 有效rho*cp、气相kg/kg等效材料Ceq、给定径向同比收缩且固定长度均需明示闭合；潜热只作压力情景；热/水活度重要勘误见上方接班核验。不能把灵敏度、网格差或质量自洽当实测精度或真实工艺界限。
- 原review_delivery有runDelivery.py、8核心模块、PS监督器、VS工程及MATLAB N40；camel_final_v2真实exit0/697.719秒，9,335,598工作簿格、297正文格、21保存数组对冻结版一致。原GUI gui_camel_final_v2 exit0证据在notes/A-coding/2026-09-11/gui/guiProcessExit.json；MATLAB独立GUI对照PASS。它们是原工程运行历史，用户签核待确认。
- 四位显示不代表严格阈值；Q3上取报告与最近舍入临界标签有不同用途。Q4原模板未强制固定2cm，当前0–2cm固定列并集/域外空白/独立surface是导出约定。Q2曾有1.5h表面温度处于四位舍入边界，不能保证所有末位稳定。
- 用户要求保留原始成果、开展有预算autoresearch和多方法交叉验证，允许代理并行；只使用当前明确有效的扫描/修补证据，不继承Morris dScale失效或Sobol未成结果。用户已取消旧03:00叫醒，旧微信发送在Escape后未完成，不自动恢复。
- 本次长记忆压缩前完整快照已追加memory_archive.md（2026-09-12 UTC审计时间标题），旧公式/截图/数据审计/GUI/交付细节和所有历史证据路径完整保留；既有接班核验勘误优先于旧快照。
