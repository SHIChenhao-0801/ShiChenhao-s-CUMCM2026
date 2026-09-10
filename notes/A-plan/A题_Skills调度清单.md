# A题 Skills 调度清单

核查日期：2026-09-10；适用范围仅本届2026CUMCM目录。本清单覆盖本轮提供的可用技能目录及父项目隔离套件；重点读取本题相关技能的执行契约，不宣称逐项运行或验证所有插件。已核实当前联接启用10个yushui Standard主流程技能＋1个autoresearch附加技能；预检识别Standard 2.3.0，未混装其他主流程。

## 固定主流程

| 阶段/条件 | Skill | 任务与关键产物 |
| --- | --- | --- |
| 开题与每次恢复 | paper-workflow-orchestrator | 输入预检、哈希清单、S0–S8状态；按首个未完成阶段继续 |
| S1 | problem-doc-model-selector | problem_analysis.json；四问输入输出、约束、附录物性与歧义对应 |
| S2 | modeling-paper-rubric-and-model-selector | model_route.json、rubric_alignment.json、scoring_strategy.md；可解释基线、候选、采用理由与验证 |
| S3 | data-cleaning-and-visualization | 正式load_report、数据/图表计划、figure_index；只加载A题两份输入，四份result是模板 |
| S4–S5 | model-code-and-result-generator | 真正的逐问热/质传递求解、实际运行、run_manifest、指标、结论、图表索引 |
| S6 | quality-assurance-auditor | official证据审计；上游变化触发重算和重新审计 |
| S7–S8 | paper-formal-writer | 唯一正式作者；章节审计、全文统修、可编辑公式Word、PDF逐页验证 |
| 指定修复队列 | paper-micro-unit-generator | 仅处理正式写作反复失败后排队的局部修复，不从零拼全文 |
| 全程 | context-memory-keeper | 本届memoryskill与workflow_memory；真实阶段、模型口径、证据、阻塞、下一步 |
| 确实缺外部资料 | authoritative-data-harvester | 仅为相关物理/方法/数据缺口补权威来源，记录出处、时点、口径；不默认扩展数据集 |

原件入口：`D:/Document/数学建模/.agents/skills/<Skill名>/SKILL.md`，当前为只读共享联接。固定套件清单：`D:/Document/数学建模/agent-skills/suite-manifest.json`。

## 本题相关辅助技能

| 技能 | 何时使用 | 本题边界 |
| --- | --- | --- |
| computer-use | MATLAB实际执行；Python/C++在Visual Studio可视化复现 | GUI运行与用户代码审查分开记录；实际控制前检查当前接口和技能操作说明 |
| spreadsheets:Spreadsheets | 附件/模板读取与result1–result4.xlsx回填/回读 | 保留题面模板、单位、工作表与精度；不套商业报表样式；先加载bundled依赖 |
| spreadsheets:excel-live-control | 必须控制当前打开的Excel时 | 文件处理不自动要求打开GUI；遵守用户的源码复现约束 |
| pdf:pdf | 题面/说明会逐页阅读、最终PDF逐页检查 | 有PDF不等于渲染/匿名/页数已通过 |
| documents:documents | 辅助Word排版、公式/表/引用审查 | 正式文稿仍走paper-formal-writer；比赛规范优先于通用文档样式 |
| visualize:visualize | 团队理解薄壳守恒、收缩坐标、时间线 | 教学图与真实求解图区分；论文图由实际结果和标准绘图工具生成 |
| zotero:Zotero | 需要检索或管理实际使用的本地文献库时 | 核实文献与引用；不存在的文献不能进入参考文献；不为有插件而新建库 |
| latex:latex-doctor/latex-compile/texlive-runtime-installer | 团队确定采用TeX路线后检查/编译，缺运行时才考虑安装 | LaTeX本届未实测；已有Word/PDF路线时不临时迁移；所有cwd/产物留在本届目录 |
| superpowers调试/测试/代码审查/完成前验证 | 实际开发出现错误、需要独立审查或声明通过前 | 辅助S0–S8；不另起主流程或对已授权工作反复询问；测试验证数值性质与失效场景 |
| autoresearch | 用户明确要求用于本题且已有可靠基线后 | CPU有限预算、固定评价和停止条件；本轮未启动实验循环；无实测不能搜索虚构准确率 |
| BZD隔离审查套件 | 主流程完成后可追加独立终审 | 仅附加审查，不能替代主流程验证，不自动切换套件 |

## 其余技能的处理

隔离的handsome、xiaoma、zhnnky、lupynow套件保留只读方法参考，不与当前Standard并行争夺正式状态。skill-creator/installer、plugin-creator、template-creator只在需要且任务明确时使用；当前不升级共享技能或重建套件。Superpowers的worktrees/分支收尾/计划执行按真实开发结构选用，不为制造Git流程而拆分论文二进制主稿。

Canva、imagegen、product-design、presentations、game-studio、Remotion、Higgsfield等没有当前A题交付任务；如后续需要讲解材料再按目的调用，生成图像不能当作仿真证据。

boltz、life-science-research、NGS及相关生命科学数据库不因题目出现“药材”而触发，A题当前研究对象是烘干热/质传递。NVIDIA部署/加速/仿真基础设施不作为这台CPU主机求解本题的必要前置。

CircleCI、codex-security、Stripe、Mixpanel、PostHog、OpenAI应用/API开发与文档插件等没有当前任务，不额外引入服务、账号或部署。新闻/赛事提醒沿用已授权自动化；与A题无关的信息不进入论文。

## 必须覆盖的旧默认和冲突

1. 模型脚手架中的simulation趋势代理不能充当A题求解；必须实现实际PDE/守恒近似并运行验证。
2. 数据技能底部旧“QA→micro-unit”和选型技能旧“前置无/再审题”残句，服从总编排与最新执行契约。S6后正式作者是paper-formal-writer。
3. 写作技能默认18页/14000有效字符为可调内部默认，不是比赛规则。按9/10说明会的实际计页范围和上限配置并记录理由；正文≤30页，校内摘要至参考文献≥15页，20–30页是建议。
4. 通用数据技能的均值填补、异常删除、相关性图仅为样板。A附件已知无缺失，正式复核后可以不修改原始值；不同含水率质量基准不能靠改列名解决。
5. 数据指标不能为了适配契约而伪造实测标签、准确率或RMSE。使用适用的边界/守恒/正性/收敛、独立算例与敏感性证据。
6. Python契约若服务MATLAB核心求解，须记录真实源码、实际调用、输入输出和返回状态；不创建未运行空壳来骗过门禁。具体选型在正式路线中固定。
7. 所有通用输出目录和运行目录服从本届工作区约束；共享Skill只读，脚本使用-B或本届缓存，不能写回父目录或全局记忆。形式审查与真实运行分别记录。
8. 通用技能的模板/审批默认不覆盖用户已明确授权和本届优先规则。审计发现不一致先按现有授权处理，不能以无实际必要的确认阻断例行工作。

本轮实际运行范围：输入预检与流程状态/记忆维护；并行代理为只读技能、规则和模型计划审查。未执行A题正式模型、未启用autoresearch、未实际控制桌面、未形成论文或提交结果。
