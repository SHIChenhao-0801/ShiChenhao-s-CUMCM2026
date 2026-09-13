from pathlib import Path
import hashlib, json, shutil

ROOT = Path.cwd()
QA = ROOT / 'paper_output/qa/support_completion_20260913/ai'
old_builder = (QA / 'build_ai_details.py').read_text(encoding='utf-8')
# Reuse only established page, style and table helpers, without executing the old content.
exec(old_builder.split("title = doc.add_paragraph('AI工具使用详情'")[0])
shutil.copy2(OUT, QA / 'AI工具使用详情_原填写模板.docx')

title = doc.add_paragraph('AI工具使用详情', style='Title')
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
para('对应论文  药材热湿耦合模型与干燥时间计算', size=11).alignment = WD_ALIGN_PARAGRAPH.CENTER
para('本队使用 Deepseek Harness 与 Deepseek v4.1 flash 辅助代码语法检查和部分程序调试，使用 Codex 与 GPT6-Astra 辅助题意理解、文献检索、模型与结果检查、公式整理，以及绘图和提交材料整理。AI参与内容及具体处理情况如下。')
heading('一 AI工具清单')
table(['工具', '模型名称与版本', '主要用途'], [
    ['Deepseek Harness', 'Deepseek v4.1 flash', '对已编写代码进行语法检查，结合报错信息辅助定位和修改部分程序问题。'],
    ['Codex', 'GPT6-Astra', '梳理题意与模型条件；检索文献；检查公式和数值结果；整理绘图程序、数据及论文支撑材料。'],
], [3.7, 4.8, 8.5], padding=115)
para('版本登记采用论文第9.3节记载的模型名称。以下典型交互发生于2026年9月13日，均为Codex中的实际文字交互。')
heading('交互方式', 2)
para('本队通过文字提出任务，并指定论文DOCX、程序、CSV和结果表作为工作对象；AI读取文件、提出检查结论，并按指令修改支撑材料。结果以可编辑文档、源码、数据清单和运行记录交付。')
para('以下三例来自同一轮提交前补件交互，按绘图、数值检验和附录整理三个任务分别记录。提示词和AI回复按对应主题摘录，保留原文；处理情况和核验结果依据实际文件与运行记录整理。')

newpage()
heading('二 分环节使用记录')
table(['环节', '使用情况', '具体工作与采用位置'], [
    ['赛题理解', '使用', 'Codex辅助梳理四问的输入、输出和递进关系，区分附件1环境观测、附件2半径变化与附件3结果模板。采用位置：问题分析、符号说明和各问模型；支撑01。'],
    ['模型假设', '使用', 'Codex辅助检查4小时后的环境平台假设、空气湿度向平衡含水率的映射、同比收缩与固定长度等闭合条件，说明预测结果依赖这些假设。采用位置：模型假设、模型评价。'],
    ['建模设计', '使用', 'Codex辅助整理热湿耦合方程、边界条件、Kirchhoff水通量离散及各问模型的联系，检查符号和量纲。采用位置：模型建立与算法说明；03中的dryingCore.py和q1Model.py至q4Model.py。'],
    ['代码求解', '使用', 'Deepseek Harness辅助语法检查和部分调试；Codex辅助程序实现、路径与依赖整理、运行入口和复现检查。本次为method_comparison.py修正一行ROOT定位，并补run_checks.py及依赖清单。采用位置：03、05；实例2。'],
    ['结果检验', '使用', 'Codex辅助核对冻结结果与论文表格，检查网格收敛、时间误差和方法对照。本次实际运行适量检验并读取内部数值报告。采用位置：04、05；实例2。'],
    ['论文撰写', '使用', 'Codex辅助整理公式与符号、检查正文和结果的一致性，编写支撑文件说明、AI使用记录和附录清单。采用位置：论文第9.3节、AI工具使用详情、附录文件列表；实例3。'],
    ['辅助工作', '使用', 'Codex辅助文献检索、文件来源与校验值整理、绘图脚本适配、CSV及PNG归档。采用位置：02、06；实例1。'],
], [2.3, 2.0, 12.7], fs=10.5, padding=100)

records = [
    ('绘图程序与数据补件', '代码求解与辅助工作',
     '2\\. 把绘图程序和CSV加进去，留下PNG格式即可',
     '绘图程序和数据已加入 `支撑材料/06_绘图程序与数据`：R 程序、14 份 CSV、6 张 PNG及说明、校验文件。图像仅保留 PNG，R 程序已在独立目录实际运行通过。',
     '将原论文六图对应的R程序和输入CSV加入支撑06。脚本按自身位置定位CSV，图像输出保留PNG，并提供可指定的输出目录；交付保留原论文PNG。',
     '14份CSV共4627行数据及6张PNG与原图目录逐字节一致。R程序在独立目录实际退出0。当前环境重绘与历史PNG有少量像素差异；原程序与适配程序在同一当前环境重绘结果一致。',
     '06_绘图程序与数据/draw_figures.R；CSV和PNG子目录；绘图复现说明.txt、数据来源与校验.csv、图像校验.csv。'),
    ('数值检验的独立复现补件', '代码求解与结果检验',
     '3. 你提到的：对论文采用的网格、时间误差、方法对照，至少补齐两份 CSV 的预期位置、实验根路径及 Matplotlib 依赖。这个请你核实，添加。\n历史废弃试验继续如实保留失败状态，不需要临交时把所有探索程序改成“通过”。 这个保留不动作。',
     '数值检验补件已加入：两份 CSV 的预期位置、实验根路径、运行入口和包含 Matplotlib 的依赖清单。网格、时间误差、方法对照均已完成适量重跑并核验通过，具体命令见独立运行说明。',
     '补齐A_environment_observed.csv、A_radius_observed.csv、requirements.txt与run_checks.py。method_comparison.py仅将ROOT改为由脚本位置确定。按本队指令保留其他原检验源码和历史失败状态。',
     '新建虚拟环境安装并检查依赖。网格Q1 N20/40、时间误差Q1 N20及方法对照quick N100/200均实际退出0并核查内部报告。两CSV与生产输入一致，方法对照除ROOT赋值外语法树不变。未将小规模检查表述为全部高网格重跑。',
     '05_数值检验与实验/论文采用检验_独立运行说明.txt、本轮补件与运行核验.txt；Python检验源码下的run_checks.py、requirements.txt及paper_output/data_cleaned。'),
    ('完整支撑文件清单', '论文撰写与辅助工作',
     '4. 在结束之后，我希望你生成所有支撑材料的文件列表，我要放在正文的附录中。',
     '共 8 页，按目录逐项列出当前全部 137 个文件及用途，已核对无遗漏、无重复，可以放进正文附录。另有 TXT 完整清单。',
     '按现有支撑目录生成逐文件路径和用途说明，提供独立DOCX供正文附录排版，并同步两份TXT清单。将空白模板和正式结果分别说明，保持本队当前目录结构。',
     '独立核查逐项重建清单路径，137个文件全部出现且各出现一次；DOCX与两份TXT清单一致。文件列表共8页，渲染后逐页检查。生成清单未改论文正文，四份正式结果表保持冻结版本。',
     '支撑材料文件列表_附录用.docx；支撑根目录00_文件清单.txt及00_可用于论文附录的支撑清单.txt。'),
]
for i, (topic, stage, prompt, reply, adopted, verified, locations) in enumerate(records, 1):
    newpage()
    heading('三 典型交互实例')
    heading(f'实例{i} {topic}', 2)
    table(['记录项', '实际内容'], [
        ['工具与时间', f'Codex 与 GPT6-Astra；2026年9月13日；{stage}。'],
        ['提示词节选', prompt],
        ['AI回复节选', reply],
        ['队伍处理与落地', adopted],
        ['核验方式与结果', verified],
        ['采用文件位置', locations],
    ], [3.0, 14.0], fs=10.5, padding=130)
    para('记录中的运行、哈希比对和逐页检查由AI调用工具完成；团队人工审查与签认由本队负责。', size=9.5, after=0)

newpage()
heading('四 采纳修改及人工主导确认')
table(['类别', 'AI辅助内容', '采用及修改情况'], [
    ['建模思路', '题意整理、假设边界与模型联系检查。', '围绕热湿耦合和收缩条件组织四问；结果限定为给定假设下的预测，不将数值检验写成实测验证。'],
    ['公式', '公式、量纲与符号整理。', '区分有效体积热容和干骨架密度，区分连续阈值时刻和严格报告时刻；具体表达以论文采用方程及冻结程序为准。'],
    ['代码', '语法调试、依赖与复现入口、绘图适配。', '本次采纳相对ROOT定位和新增运行入口；正式03及结果04字节保持，历史废弃检验未修复或改判。'],
    ['分析与材料', '结果一致性检查、支撑整理和附录清单。', '形成三项适量检验记录、绘图补件和137文件清单；保留检验范围、图像重绘差异及模型适用边界。'],
], [2.0, 5.0, 10.0], fs=10, padding=85)
heading('人工主导事项', 2)
table(['核心环节', '本队承担的工作与责任'], [
    ['模型选型与创新', '负责模型路线、假设及创新内容的最终选择，判断AI建议是否适用。'],
    ['公式推导', '负责理解和审查所采用方程、条件、推导及量纲，决定最终表达。'],
    ['代码逻辑', '负责掌握核心程序逻辑并进行人工审查；区分程序运行记录和人工审核结论。'],
    ['核心论证', '负责审查结果解释、适用范围与局限性，决定论文最终结论。'],
], [3.5, 13.5], fs=10, padding=80)
heading('真实性声明', 2)
para('本队签认本文件时，确认所登记的AI工具、使用环节和采纳情况与实际过程一致，交互节选来自真实对话，并承担论文与支撑材料的真实性、准确性及完整性责任。程序运行和自动检查记录不替代本队对模型、公式、代码及核心论证的人工审查。', size=10)
para('本队确认签名：________________    日期：________________', size=10, after=0)

cp = doc.core_properties
cp.title = 'AI工具使用详情'
cp.subject = '药材热湿耦合模型与干燥时间计算 AI工具使用记录'
cp.author = cp.last_modified_by = cp.comments = cp.keywords = cp.category = ''
doc.save(OUT)
text = '\n'.join(p.text for p in doc.paragraphs) + '\n'.join(c.text for t in doc.tables for r in t.rows for c in r.cells)
assert not any(word in text for word in ['待填写', '请核实', '待本队确认', '待粘贴'])
(QA / 'filled_text.txt').write_text(text, encoding='utf-8')
(QA / 'filled_records_audit.json').write_text(json.dumps({'output_sha256': hashlib.sha256(OUT.read_bytes()).hexdigest(), 'actual_examples': 3, 'same_exchange_topic_excerpts': True, 'signature_not_forged': True, 'unfilled_prompt_templates': 0, 'source': 'Current thread user four-part request and assistant preceding final response', 'tables': len(doc.tables)}, ensure_ascii=False, indent=2), encoding='utf-8')
print('Filled three actual topic excerpts and all seven stages; signature remains blank.')
