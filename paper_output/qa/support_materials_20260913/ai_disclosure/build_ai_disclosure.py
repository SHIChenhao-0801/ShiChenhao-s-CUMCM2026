# -*- coding: utf-8 -*-
"""Build an anonymized, evidence-bounded AI disclosure; no model execution."""
from pathlib import Path
import hashlib, json, re
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pymupdf

ROOT = Path(__file__).resolve().parents[4]
QA = Path(__file__).resolve().parent
OUT = ROOT / '支撑材料'
RECORD = OUT / '06_AI使用记录'
for folder in (QA, OUT, RECORD): folder.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(TTFont('CJK', 'C:/Windows/Fonts/simhei.ttf'))
INK = colors.HexColor('#162B3D')
MUTED = colors.HexColor('#536779')
styles = {
    'title': ParagraphStyle('title', fontName='CJK', fontSize=23, leading=30, textColor=INK, spaceAfter=14),
    'subtitle': ParagraphStyle('subtitle', fontName='CJK', fontSize=10, leading=16, textColor=MUTED, spaceAfter=14),
    'heading': ParagraphStyle('heading', fontName='CJK', fontSize=15, leading=21, textColor=INK, spaceBefore=10, spaceAfter=9),
    'subhead': ParagraphStyle('subhead', fontName='CJK', fontSize=11.6, leading=17, textColor=INK, spaceBefore=9, spaceAfter=4),
    'body': ParagraphStyle('body', fontName='CJK', fontSize=10.4, leading=16, textColor=INK, spaceAfter=7, wordWrap='CJK'),
    'small': ParagraphStyle('small', fontName='CJK', fontSize=9.0, leading=13.5, textColor=INK, spaceAfter=5, wordWrap='CJK'),
    'cell': ParagraphStyle('cell', fontName='CJK', fontSize=9.3, leading=14, textColor=INK, wordWrap='CJK'),
    'headcell': ParagraphStyle('headcell', fontName='CJK', fontSize=9.5, leading=14, textColor=colors.white, wordWrap='CJK'),
}

pages = []
def page(title, subtitle=''):
    p = {'title':title, 'subtitle':subtitle, 'blocks':[]}; pages.append(p); return p
def para(p, text, style='body'): p['blocks'].append({'type':'p','text':text,'style':style})
def heading(p, text): para(p,text,'subhead')
def table(p, headers, rows, widths): p['blocks'].append({'type':'table','headers':headers,'rows':rows,'widths':widths})

p=page('AI 工具使用详情','A题《药材的烘干问题》 | 支撑材料记录 | 编制日期：2026-09-13（北京时间）')
para(p,'本文件据现存任务记录、源码、运行报告和论文修订证据整理，披露 AI 在本题中的实际参与。它由 AI 辅助编制；团队对内容完整性、采纳决定及最终稿的人工核实尚待确认。本文件没有代替队员签署真实性承诺。')
heading(p,'工具名称、型号与使用时间')
table(p,['工具 / 使用范围','型号与可核实边界'],[
 ['OpenAI Codex 桌面代理\n本题建模与材料整理','当前会话系统标明基于 GPT-6。2026-09-10 的项目 AI 记录也记载 GPT-6。其他历史会话的逐轮型号、更细模型标识和桌面客户端精确版本未完整记录，均列为未知，不反推为同一版本。'],
 ['Codex 并行代理与工具调用','用于资料、代码、数值核验、论文及材料分工。本次并行代理继承当前会话模型；历史各子代理具体型号未逐一核实。浏览检索、终端执行和 Computer Use 属于代理调用能力，不另冒列为模型。'],
 ['使用时段','本文件覆盖现存证据中的 2026-09-10 至 2026-09-13 正式赛题工作；不把赛前环境小样当作正式题验证。没有完整逐消息记录的部分只报告可核实摘要。'],
], [133,354])
heading(p,'实际参与范围')
para(p,'AI 实际参与了审题和资料检索、模型及闭合假设建议、公式推导与修正、求解和验证代码生成及调试、已有结果的解释、论文草拟和实质修改、图表制作与支撑材料打包。它的作用包含建模和写作内容，不能只登记为语言润色。')
heading(p,'证据与采纳状态的读法')
para(p,'本文件中的“采用”表示相关内容已进入现存程序、冻结结果或修订稿；“机器核验”表示有实际运行或静态 / 渲染审计记录。这两种状态都不等于队员已逐项审查或最终签核。“历史 GUI 运行”只对应原工程版本；当前包装代码另行验收。')
para(p,'Python、NumPy、SciPy、R、MATLAB、Visual Studio、LibreOffice 和文档生成库是执行或编辑环境，不是本文件另行认定的生成式 AI 模型。其具体运行版本以对应代码说明及运行日志为准。','small')

p=page('七个环节的实际使用','各环节均存在 AI 参与；以下按实际工作内容记录。')
stages=[
 ('1 赛题理解','读取题面和附件，拆分四问的输入、物性、初边值条件及输出格式；指出问题二 / 三应从初始状态使用附录3整组物性，不能把问题一终态拼接过去。附件1仅有0至4 h环境观测，后续平台需明确为假设。'),
 ('2 模型假设','起草、解释并核对一维径向传递、有效显热、干基含水率、气相指标映射为材料平衡含水率、固定长度及同比径向收缩等假设。AI 指出这些闭合缺少内部温湿实测标定，不能由一般文献替代证明。'),
 ('3 建模设计','参与薄壳守恒、Fourier / Fick 本构、材料坐标变换和干骨架守恒推导；提出 / 整理有限体积、Kirchhoff 水通量、BDF 与稀疏 Jacobian 的求解方案，并修正时间阈值、单位和符号解释。'),
 ('4 代码求解','生成、重构和调试 Python 求解器、参数配置、导出与回读验证代码；组织真实 CPU 求解与运行日志。通过 Computer Use 操作原 Visual Studio 工程及 MATLAB 对照。当前支撑包另有入口、路径与依赖包装修复。'),
 ('5 结果检验','编写 / 执行解析与数值对照、网格和容差检查、质量收支、事件定位、参数情景和导出一致性检查；分析既有 autoresearch 实验日志。保留注入失效、资源中止和未完成实验，不把它们写成通过。'),
 ('6 论文撰写','基于已有结果草拟正文及附录，并实质修改假设、推导说明、结果解释和局限；完成文献核查、公式编号 / 交叉引用、代码摘录、表格一致性和逐页渲染检查。按冻结数据生成六张图，最终选用待团队确认。'),
 ('7 辅助工作','整理数据和参考资料来源、运行证据、文件清单与哈希；编制交接说明、代码运行说明及本 AI 披露文件。历史记录用于追溯，本轮仅按最新有效版本组装支撑材料。')]
for title,body in stages:
    heading(p,title); para(p,body)
para(p,'团队任务与修改意见可从现存记录追溯；四项核心环节是否由团队主导及其具体依据，须由队员本人逐项确认，见末页。AI 不在本文件中替队员作出已确认的结论。','small')

p=page('典型交互与实际修正','以下都是依据项目记录整理的提示 / 回复摘要，非逐字聊天记录，未伪造用户原话。')
heading(p,'示例一：审题、模型路线与闭合（9月10日起）')
para(p,'提示摘要：确定 A 题后，要求核对题面、附件和可用工具，给出建模及验证安排。该需求见 AI 计划记录；后续建模与实现见既有程序和说明。')
para(p,'AI 回复 / 行动摘要：整理问题一、问题二 / 三、问题四的求解框架，参与径向守恒和收缩坐标推导，明确三类物性各自从初始条件使用。提出气相 kg/kg 指标到材料平衡含水率的等效映射，并将环境后续平台、有效热容解释列为闭合假设。')
para(p,'修正 / 处理：采用相关计算框架，但不把等效映射写成题面已给的吸附等温线。无内部实测数据，保留条件预测限制；模型采用状态可由现存程序确认，不能据此声称队员已逐式签核。证据 E1、E2、E7。')
heading(p,'示例二：精简附录、核对推导与日志（9月12日）')
para(p,'提示摘要：根据用户修改稿规范公式排版，精简附录，使用 autoresearch 检查已有工作。用户调整过几何长度、方法名称和引用处理；AI 保留其修改并另存新稿。')
para(p,'AI 回复 / 行动摘要：将完整源码附录缩为六段117行算法摘录，保留核心推导；核对材料坐标、干基守恒、轴心通量和环境指标含义；审阅42条有效实验记录及已有检查，未声称新增 GPU 训练或生产 PDE 求解。')
para(p,'修正 / 处理：把“中心外侧面零通量”改为“轴心面零通量”，恢复气固指标映射的假设限定。按当时指示保留删除文献后的批注；后续9月13日新指示授权重新检索和修订，旧引用处理不再作为当前版本。证据 E3、E7。')
heading(p,'示例三：文献、严格达标公式与引用（9月13日）')
para(p,'提示摘要：核查最新用户稿的文献和公式，修改正文并整理编号与交叉引用。')
para(p,'AI 回复 / 行动摘要：核对7条书目及可取得的内容；修复13处错引，建立39处公式REF及8处文献REF；解释全域最大含水率 M(t)，改写严格达标时间集合及附录候选上取式。')
para(p,'修正 / 处理：明确0.36 s时间网格上的首个未舍入值严格达标点；修正 D4/D3关系，说明其在 C约0.08606处反转。未改8张结果表和117行摘录，未重算生产 PDE；全文阅读不足之处如实登记。证据 E4、E5、E6。')

p=page('采纳、修改和弃用记录','采纳是文件状态；下表不将 AI 核查改称为人工复核。')
table(p,['事项','实际处理与理由'],[
 ['守恒模型与数值方案\n采用并保留假设边界','现存程序使用径向有限体积、Kirchhoff 水通量、解析稀疏 Jacobian 和 BDF。问题四在材料坐标体现收缩，干基方程不重复加入体积浓缩项。数值自洽不证明模型闭合的真实物理精度。'],
 ['严格阈值与显示数值\n修正说明后采用','判定使用全域最大含水率的未舍入值；连续临界根和四位小时报告时刻分别记录。论文公式与单位改正，原冻结数值保持不变。'],
 ['扩散系数关系\n修正过强描述','相同温度和含水率下 D4/D3=0.175 exp(0.15/C)，在C约0.08606 kg/kg时反转。固定半径 / 收缩的同物性对照，与问题三 / 四的物性及几何综合差异分别解释。'],
 ['参数敏感性注入\n原无效结果弃用','旧 Morris 中只缩放物性数组，未作用到 Kirchhoff 面通量，所得扩散尺度零效应无效。当前解释只采用有真实通量注入的修补扫描及其适用网格；未完成 Sobol 不报告指数。'],
 ['序列与经验闭合\n限制或弃用结论','常数序列 M-K 伪越界不采纳；吸附 / 水活度经验闭合未标定，不将其情景时长解释为真实工艺下界。有效显热收支自洽也不等于完整物理能量验证。'],
 ['文献与正文\n核实范围内采用','最新稿保留7条文献，依据刊方、元数据、目录或可取得全文核对，逐条区分已读范围。AI 参与正文草拟及内容修改，不能说仅做排版润色；最终引用和论述待团队复核。'],
 ['旧支撑 ZIP\n不继承其通过状态','2026-09-12旧包独立启动因路径和输入缺失等失败。历史原工程运行成功不能抵消包装失败；本轮目录所含程序的验收范围另见运行记录。']
], [123,364])
heading(p,'可核实的人工修改与尚缺的签核')
para(p,'现存9月12日修订记录显示用户稿已修改几何长度、BDF名称及作者“等”等内容；AI 按任务保留并修正其他可核实问题。现存记录没有提供队员对全部核心模型、完整源码或最终论文逐项审查通过的证据，因此不补写“已人工核验全部内容”。')

p=page('结果与验证状态','区分冻结数值、原工程运行、当前包装验收和团队人工审查。')
heading(p,'冻结结果及解释边界')
table(p,['问题','连续临界时刻 / h','严格报告时刻 / h'],[
 ['问题三（N3200）','57.47230195056044','57.4724'],
 ['问题四（N6400）','51.09057478683054','51.0906'],
], [128,189,170])
para(p,'报告时全域最大干基含水率分别为0.14999989718225315和0.14999995339076624 kg/kg，均严格小于0.15。数值绑定 final_v6a 及原运行记录，是给定闭合和输入条件下的模型预测；题目没有提供内部温度 / 含水率实测真值，不能据此报告预测准确率或四位小时的实际工艺精度。')
heading(p,'四类验证状态')
status_path=QA/'current_package_status.json'
current=json.loads(status_path.read_text(encoding='utf-8')) if status_path.exists() else {
    'text':'本轮正在整理独立运行入口、路径、输入和依赖。当前包 CLI 验收以随包最新运行记录为准，本文件编制时未取得最终全量验收结论，故不声称新包全量通过。',
    'status':'AWAITING_CURRENT_PACKAGE_EVIDENCE'}
table(p,['项目','真实状态与不能替代的事项'],[
 ['原工程 CLI / GUI\n历史记录','camel_final_v2 有实际退出0记录；gui_camel_final_v2 有 Computer Use 在 Visual Studio 打开、断点、单步及实际退出0证据。GUI记录属代理操作和观察，不能改称队员亲自完成审查。原工程有297正文数据格、21保存数组等一致性证据。'],
 ['当前交付程序 CLI\n本次材料整理',current['text']],
 ['当前交付程序 VS GUI','当前版本尚无完成断点、变量及全量运行的独立证据。旧原工程 GUI 成功不自动覆盖改过入口的代码版本；本轮 GUI 状态为未执行。'],
 ['团队人工审查','核心代码、模型闭合、文献支持范围、论文和图表最终采纳及完整AI披露均待团队本人确认。AI 的独立审计、代码阅读、CLI与GUI运行不能代签。'],
], [123,364])
para(p,'9月13日文献公式修订有37个编号公式、39处公式REF与8处文献REF的静态及渲染审计；这些检查仅绑定相应修订稿。六图由R实际生成，最终选用待团队确认。本次CLI重现既有冻结模型，不构成内部实测验证或人工审查通过。','small')

p=page('证据索引与团队确认','本文件是可复核披露记录；最终提交前由团队补足确认。')
para(p,'下列证据标题及SHA-256登记在06_AI使用记录/证据索引.json。本目录提供匿名证据摘要，原始私人聊天和含个人信息的运行路径不纳入其中。完整技术输入、代码、结果和文献另在支撑材料相应目录。','small')
table(p,['ID','依据与支持范围'],[
 ['E1','9月10日《A题计划与技能核查的AI使用记录》：当时GPT-6记录、任务、审题规划及未人工签核状态。'],
 ['E2','代码交付状态与原gui_camel_final_v2进程记录：原代码CLI、GUI及实际退出；humanReview仍待确认。'],
 ['E3','9月12日《用户修改稿的公式排版与精简附录》：AI执行内容、用户修改保留、117行摘录与未新增GUI。'],
 ['E4','《本轮修订与公式核查说明》：最新文献、公式、骨架假设及D4/D3关系修订，冻结结果未变。'],
 ['E5','revision_20260913最终语义 / 交付审计：公式与引用计数、结果表不变、人工审查未完成。'],
 ['E6','最新参考文献核查清单：7条文献的真实性、取得内容和支持边界，非全条目全文已读。'],
 ['E7','最新项目记忆与既有建模 / 交叉验证记录：有效版本、无效注入与未完成实验、模型局限。'],
 ['E8','旧包可移植性审计：绑定旧ZIP的启动 / 输入失败，不覆盖当前交付目录。'],
 ['E9','本次程序验收报告：同机隔离CLI小网格及正式复现、实际退出0和冻结数据一致性；新版GUI及人工签核未执行。'],
], [34,453])
heading(p,'团队本人需要逐项完成的确认')
table(p,['确认事项','状态'],[
 ['模型创新 / 选型：实际主导内容、闭合依据及AI建议取舍','待团队确认'],
 ['公式推导：关键守恒、材料坐标与阈值公式的理解及复核','待团队确认'],
 ['代码逻辑：当前版本源码人工审查、GUI复现及验收范围','待团队确认'],
 ['核心论述：结论、图表、局限、引用与最终稿一致性','待团队确认'],
 ['披露完整性：工具、使用过程及采纳 / 修改是否有遗漏','待团队确认'],
 ['真实性声明与最终提交授权：由队员自行完成，不由AI签署','待团队确认'],
], [373,114])
para(p,'如团队补充确认或本次代码验收产生新证据，应同步更新本文件及其Markdown源，重新生成PDF、核对内容并更新支撑材料哈希。单纯更改状态文字而没有相应证据，不构成完成确认。','small')

def par(text,style='body'):
    return Paragraph(escape(text).replace('\n','<br/>'),styles[style])
story=[]
markdown=['# AI 工具使用详情','']
for i,p in enumerate(pages):
    if i: story.append(PageBreak())
    story.append(par(p['title'],'title' if i==0 else 'heading'))
    if p['subtitle']: story.append(par(p['subtitle'],'subtitle'))
    markdown.extend(['## '+p['title'],'',p['subtitle'],''])
    for b in p['blocks']:
        if b['type']=='p':
            story.append(par(b['text'],b['style']))
            markdown.extend([('### ' if b['style']=='subhead' else '')+b['text'],''])
        else:
            data=[[par(x,'headcell') for x in b['headers']]]+[[par(x,'cell') for x in r] for r in b['rows']]
            t=Table(data,colWidths=b['widths'],repeatRows=1,hAlign='LEFT')
            t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),INK),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F1F5F7'),colors.white]),('LINEBELOW',(0,0),(-1,-1),0.4,colors.HexColor('#D5DFE5'))]))
            story.extend([t,Spacer(1,8)])
            markdown += ['| '+' | '.join(b['headers'])+' |','| '+' | '.join(['---']*len(b['headers']))+' |']
            markdown += ['| '+' | '.join(x.replace('\n',' / ') for x in r)+' |' for r in b['rows']]+['']

def page_decoration(c,doc):
    c.setTitle('AI工具使用详情'); c.setAuthor(''); c.setSubject('A题支撑材料：AI实际参与和证据边界'); c.setCreator('');
    c.setStrokeColor(colors.HexColor('#BCCBD5')); c.setLineWidth(0.5); c.line(54,791,541,791)
    c.setFont('CJK',8); c.setFillColor(MUTED); c.drawString(54,804,'A题  /  AI工具使用详情'); c.drawRightString(541,31,f'{doc.page}  /  6')
    c.drawString(54,31,'2026-09-13  |  团队人工确认状态另行记录')

pdf_path=OUT/'AI工具使用详情.pdf'
SimpleDocTemplate(str(pdf_path),pagesize=(595.276,841.89),rightMargin=54,leftMargin=54,topMargin=65,bottomMargin=55,title='AI工具使用详情',author='').build(story,onFirstPage=page_decoration,onLaterPages=page_decoration)
(RECORD/'AI工具使用详情.md').write_text('\n'.join(markdown),encoding='utf-8')
(RECORD/'AI披露内容.json').write_text(json.dumps({'compiledDate':'2026-09-13','model':'GPT-6','historicalModelCoverage':'partial; unknown for unverified turns','humanReview':'PENDING_TEAM_CONFIRMATION','pages':pages},ensure_ascii=False,indent=2),encoding='utf-8')

source_specs=[
 ('E1','notes/ai-use/2026-09-10_A题计划与技能核查.md'),
 ('E2','paper_output/context/code_delivery_status.json'),
 ('E2','notes/A-coding/2026-09-11/gui/guiProcessExit.json'),
 ('E3','notes/ai-use/2026-09-12_用户修改稿公式排版与精简附录.md'),
 ('E4','paper_output/paper/本轮修订与公式核查说明.md'),
 ('E5','paper_output/qa/revision_20260913/final_semantic_audit.json'),
 ('E5','paper_output/qa/revision_20260913/final_delivery_audit.json'),
 ('E6','paper_output/qa/revision_20260913/references/references_verified.json'),
 ('E7','memoryskill.md'),
 ('E7','notes/A-modeling/2026-09-12/交叉验证岛状态与发现.md'),
 ('E8','paper_output/qa/portability_20260912/audit_summary.json'),
 ('E9','paper_output/qa/support_materials_20260913/code_validation/code_package_audit.json'),
 ('E9','paper_output/qa/support_materials_20260913/code_validation/execution.json'),
]
sources=[]
for evidence_id,relative in source_specs:
    s=ROOT/relative
    if not s.is_file(): raise FileNotFoundError(relative)
    sources.append({'id':evidence_id,'sourceName':s.name,'sha256':hashlib.sha256(s.read_bytes()).hexdigest(),'bytes':s.stat().st_size,'originalPath':relative})
(QA/'source_provenance.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
public=[{k:v for k,v in s.items() if k!='originalPath'} for s in sources]
(RECORD/'本次代码验收摘要.json').write_text(json.dumps(current,ensure_ascii=False,indent=2),encoding='utf-8')
(RECORD/'证据索引.json').write_text(json.dumps({'note':'原始证据SHA支持追溯；随包不附原始聊天或含本机路径的内部日志，正文中的证据是匿名摘要。','sources':public},ensure_ascii=False,indent=2),encoding='utf-8')
(RECORD/'README.md').write_text('# AI使用记录\n\n根目录的“AI工具使用详情.pdf”为披露阅读件，本目录包含同内容Markdown源、结构化内容和证据索引。典型交互为依据已有任务记录整理的摘要，不是原始对话摘录。\n\n当前已核实工具为OpenAI Codex（当前GPT-6；部分历史记录GPT-6，其他逐轮型号未知）。实际参与涵盖模型建议、推导、程序生成与调试、核验、论文草拟及修改、绘图和材料整理。\n\n“采用”表示进入现存成果，不表示队员已逐项签核。历史原工程CLI/VS GUI、当前包装CLI、当前包装GUI、队员人工审查分别登记。所有待团队确认事项见PDF末页；这里没有代签承诺。\n\n模型结果是条件预测，无内部温湿实测精度。冻结报告时长仍为57.4724 h和51.0906 h。\n',encoding='utf-8')
doc=pymupdf.open(pdf_path)
text='\n'.join(p.get_text() for p in doc)
(QA/'extracted_text.txt').write_text(text,encoding='utf-8')
bad=[s for s in ['福州大学','厦门大学','Shi Chenhao','SHICHE','微信','乐乐','Apple Music','D:\\','D:/','C:\\','C:/'] if s in text]
assert not bad,bad
assert len(doc)==6, f'Unexpected pages: {len(doc)}'
for value in ['57.4724','51.0906','GPT-6','待团队确认','论文草拟','代码生成']:
    assert value in re.sub(r'\s+','',text),value
audit={'status':'TEXT_AND_STRUCTURE_PASS_VISUAL_REVIEW_PENDING','pages':len(doc),'sha256':hashlib.sha256(pdf_path.read_bytes()).hexdigest(),'bytes':pdf_path.stat().st_size,'metadata':doc.metadata,'anonymousSensitiveTokenHits':bad,'pageTextLengths':[len(p.get_text()) for p in doc],'currentPackageStatus':current}
(QA/'build_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False,indent=2))
