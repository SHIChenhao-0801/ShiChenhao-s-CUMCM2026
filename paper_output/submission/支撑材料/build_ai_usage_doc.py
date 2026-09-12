# -*- coding: utf-8 -*-
"""生成支撑材料文件《AI工具使用详情.pdf》的可编辑源文件（.docx）。

用法（在本届工作区根目录执行）：
    C:/Python314/python.exe -B paper_output/submission/支撑材料/build_ai_usage_doc.py

说明：
- 本脚本只生成可编辑的 .docx 源；PDF 由 LibreOffice 无头模式转换（见同目录 README 或生成记录）。
- 文档属性中的 author / last_modified_by 等全部显式置为空字符串，保证匿名。
- 正文内容全部来自本届工作区中已存在的记录，逐项可回溯；不含学校、姓名、队号、赛区、本机用户名。
"""

from __future__ import annotations

import os
import sys

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

CN_BODY = "宋体"
CN_HEAD = "黑体"
EN_FONT = "Times New Roman"
HEADER_FILL = "D9D9D9"

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DOCX = os.path.join(OUT_DIR, "AI工具使用详情.docx")


# --------------------------------------------------------------------------
# 基础排版工具
# --------------------------------------------------------------------------
def set_run_font(run, name=CN_BODY, size=10.5, bold=False, italic=False, color=None):
    run.font.name = EN_FONT if name == CN_BODY else name
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color is not None:
        run.font.color.rgb = color
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), EN_FONT)
    rFonts.set(qn("w:hAnsi"), EN_FONT)
    rFonts.set(qn("w:eastAsia"), name)


def shade_cell(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def cell_text(cell, text, size=9, bold=False, align=None):
    cell.text = ""
    para = cell.paragraphs[0]
    if align is not None:
        para.alignment = align
    para.paragraph_format.space_before = Pt(1)
    para.paragraph_format.space_after = Pt(1)
    para.paragraph_format.line_spacing = 1.0
    for i, seg in enumerate(str(text).split("\n")):
        if i:
            para = cell.add_paragraph()
            para.paragraph_format.space_before = Pt(1)
            para.paragraph_format.space_after = Pt(1)
            para.paragraph_format.line_spacing = 1.0
        run = para.add_run(seg)
        set_run_font(run, CN_BODY, size, bold)


def add_paragraph(doc, text, size=10.5, bold=False, indent=True, space_after=4,
                  align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_line=True):
    para = doc.add_paragraph()
    para.alignment = align
    pf = para.paragraph_format
    pf.space_before = Pt(2)
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.35
    if first_line and indent:
        pf.first_line_indent = Pt(size * 2)
    if indent and not first_line:
        pf.left_indent = Pt(size * 2)
    run = para.add_run(text)
    set_run_font(run, CN_BODY, size, bold)
    return para


def add_h(doc, text, level=1):
    sizes = {1: 14, 2: 12, 3: 11}
    para = doc.add_paragraph()
    pf = para.paragraph_format
    pf.space_before = Pt(10 if level == 1 else 7)
    pf.space_after = Pt(5)
    pf.line_spacing = 1.2
    pf.keep_with_next = True
    run = para.add_run(text)
    set_run_font(run, CN_HEAD, sizes[level], bold=(level <= 2))
    return para


def add_table(doc, headers, rows, widths=None, header_size=9, body_size=9):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for i, h in enumerate(headers):
        cell_text(table.rows[0].cells[i], h, header_size, True, WD_ALIGN_PARAGRAPH.CENTER)
        shade_cell(table.rows[0].cells[i], HEADER_FILL)
    for row in rows:
        cells = table.add_row().cells
        for i, v in enumerate(row):
            cell_text(cells[i], v, body_size)
    if widths:
        tblPr = table._tbl.tblPr
        layout = OxmlElement("w:tblLayout")
        layout.set(qn("w:type"), "fixed")
        tblPr.append(layout)
        grid = table._tbl.find(qn("w:tblGrid"))
        if grid is not None:
            for gc, w in zip(grid.findall(qn("w:gridCol")), widths):
                gc.set(qn("w:w"), str(int(round(w * 567))))
        for r in table.rows:
            for i, w in enumerate(widths):
                r.cells[i].width = Cm(w)
    return table


def add_caption(doc, text):
    """表题：居中加粗，并移动到其前一张表格的上方（表题在表上）。"""
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = para.paragraph_format
    pf.space_before = Pt(6)
    pf.space_after = Pt(3)
    pf.keep_with_next = True
    run = para.add_run(text)
    set_run_font(run, CN_BODY, 9, bold=True)
    body = doc.element.body
    last_tbl = None
    for child in body.iterchildren():
        if child.tag == qn("w:tbl"):
            last_tbl = child
    if last_tbl is not None:
        last_tbl.addprevious(para._p)
    return para


def add_footer_page_number(section):
    footer = section.footer
    para = footer.paragraphs[0]
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run()
    set_run_font(run, CN_BODY, 9)
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "end")
    run._r.append(fld1)
    run._r.append(instr)
    run._r.append(fld2)


def scrub_properties(doc):
    cp = doc.core_properties
    cp.author = ""
    cp.last_modified_by = ""
    cp.title = ""
    cp.subject = ""
    cp.comments = ""
    cp.category = ""
    cp.keywords = ""
    cp.content_status = ""
    cp.identifier = ""
    cp.language = ""
    cp.version = ""
    cp.revision = 1


# --------------------------------------------------------------------------
# 文档内容
# --------------------------------------------------------------------------
def build():
    doc = Document()

    style = doc.styles["Normal"]
    style.font.name = EN_FONT
    style.font.size = Pt(10.5)
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), EN_FONT)
    rFonts.set(qn("w:hAnsi"), EN_FONT)
    rFonts.set(qn("w:eastAsia"), CN_BODY)

    sec = doc.sections[0]
    sec.page_width = Cm(21.0)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(2.5)
    sec.bottom_margin = Cm(2.5)
    sec.left_margin = Cm(2.5)
    sec.right_margin = Cm(2.5)
    add_footer_page_number(sec)

    # ---------------- 标题 ----------------
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    t.paragraph_format.space_after = Pt(4)
    r = t.add_run("AI 工具使用详情")
    set_run_font(r, CN_HEAD, 18, bold=True)

    st = doc.add_paragraph()
    st.alignment = WD_ALIGN_PARAGRAPH.CENTER
    st.paragraph_format.space_after = Pt(10)
    r = st.add_run("（支撑材料文件；文件名：AI工具使用详情.pdf）")
    set_run_font(r, CN_BODY, 10.5)

    meta = [
        "编制依据：《全国大学生数学建模竞赛人工智能工具使用规定（2026 年试行）》第 4 条；2026 年 9 月 10 日赛前说明会材料第 29 页。",
        "配套声明：参赛论文已在参考文献之前设置《AI 工具使用声明》（选用官方规定的第(2)类表述），其末句“详细使用情况见支撑材料”指向本文件。",
        "本文件状态：由本队依据工作区内的真实记录整理，随支撑材料一并提交。",
    ]
    for m in meta:
        add_paragraph(doc, m, size=10, indent=False, space_after=2)

    # ---------------- 0 阅读指引 ----------------
    add_h(doc, "0　阅读指引与如实声明", 1)
    add_paragraph(doc, "本文件按官方规定的四项强制内容组织，位置对应关系如下：")
    add_table(
        doc,
        ["官方第 4 条要求的强制内容", "本文件落实位置"],
        [
            ["(1) 所用 AI 工具名称、版本或型号", "第 2 节　AI 工具清单（表 1）"],
            ["(2) 具体使用目的和环节", "第 3 节　七个环节逐项说明（表 2 及 3.1–3.7）"],
            ["(3) 主要提示方式与使用过程说明", "第 4 节　提问方式、通用约束与三个典型交互示例（表 3–表 5）"],
            ["(4) 对 AI 输出的采纳、人工修改和核验的主要情况（语言润色除外）", "第 5 节　汇总表与十个具体例子（表 6 及 5.2）"],
            ["赛前说明会第 29 页补充要求：AI 工具清单表；七个核心环节说明；2–3 份关键交互示例；核心环节本队主导确认表与队伍真实性声明", "工具清单表见第 2 节表 1；七环节见表 2；交互示例见表 3–表 5；核心环节确认表见表 7，真实性声明见第 6.2 节"],
        ],
        widths=[7.6, 8.4],
    )
    add_caption(doc, "表 0　官方强制内容与本文件位置的对应关系")

    add_paragraph(doc, "如实声明（合规红线，逐条对应本文件后续表述）：", bold=True, indent=False, space_after=2)
    for i, s in enumerate([
        "本队在竞赛过程中使用了 AI 工具，故不采用官方“未使用任何 AI 工具”的声明方式；本文件亦不出现“未使用任何 AI 工具”的表述。",
        "核心模型选择、关键闭合假设与最终数值结论均由本队确定，AI 未独立完成模型；本文件不出现“AI 独立完成了模型”一类表述。",
        "核心代码的人工审查状态为“进行中”：已通过 Visual Studio GUI 实际运行复现（完整四问求解与导出，数值工作进程实际退出码 0），但核心代码人工审查尚未完成。本文件一切涉及人工审查的表述均为“已通过 Visual Studio GUI 实际运行复现；核心代码人工审查进行中”，不写作“人工审查已通过”，亦不写作“人工审查未进行”。状态以工作区记录 paper_output/context/code_delivery_status.json（humanReview = PENDING_USER_REVIEW）为准。",
        "AI 生成的文献条目一律不进入参考文献；本文件与论文中引用的公开资料均经本队当次实际打开核对。",
    ]):
        add_paragraph(doc, "（%d）%s" % (i + 1, s), indent=False, space_after=2)

    # ---------------- 1 时间范围 ----------------
    add_h(doc, "1　时间范围与总体工作方式", 1)
    add_paragraph(doc, "时间范围：自 2026-09-10 18:00（北京时间）竞赛开始起，至本文件编制时止；全部工作均在本队自建工作区内完成，工作区内的时间戳与运行记录可逐条回溯。")
    add_paragraph(doc, "总体工作方式为“人下达任务 → AI 执行或生成 → 人工核验 → 本队决定采纳、修改或作废”的循环：")
    for s in [
        "由本队成员给出任务与验收口径，AI 只能读取本队工作区内的规则、技能、题面、数据与运行报告，不联网抓取未经核对的结论作为依据；",
        "任何要写入论文的数值必须绑定代码版本、输入哈希与运行记录；没有运行证据的数值一律不得写入论文；",
        "已冻结的结果不得被 AI 改写；任何模型、网格、容差或输入数据的变化都必须新建运行编号并重算、复检；",
        "AI 报出的失败、不通过与被否决的结论一律保留记录，不得改写为通过。",
    ]:
        add_paragraph(doc, "·　" + s, indent=False, space_after=2)

    # ---------------- 2 工具清单 ----------------
    add_h(doc, "2　所用 AI 工具名称、版本或型号（第(1)项）", 1)
    add_table(
        doc,
        ["序号", "工具名称", "版本 / 型号", "在本队工作中的主要用途", "版本核实依据与核实状态"],
        [
            [
                "1",
                "Codex 桌面代理（会话式编程与研究代理）",
                "系统说明为基于 GPT-6；更细模型标识未在记录中核实",
                "读取本地规则、技能、题面、记忆与运行报告；调度辅助技能；公式与代码复核；数值验证脚本编写；记录整理；文稿一致性与格式检查；工作区流程与记忆维护。",
                "依据 notes/ai-use/2026-09-10_A题计划与技能核查.md 原文：“工具：Codex桌面代理，系统说明为基于GPT-6；更细模型标识未在本记录中核验，不推测型号。”　状态：型号已部分核实，更细标识未核实，本文件不作推测。",
            ],
            [
                "2",
                "DeepSeek Harness（DSH）会话代理",
                "模型标识：deepseek-v4-flash-vision-exp",
                "只读核查与一次独立复跑；输出进度核查与逐问核实报告；本次支撑材料文书的生成与排版。",
                "依据：① 本机该工作区会话存储的默认模型配置（.dsh/settings.yaml 中 agent-default-model 记录 provider 为 deepseek-official、model 为 deepseek-v4-flash-vision-exp）；② 工作区记录 notes/A-coding/2026-09-11/independent-verification/verification_report.md 署“核查人：DSH 代理（只读核查 + 一次独立复跑）”。　状态：配置级已核实。",
            ],
        ],
        widths=[1.1, 3.1, 3.0, 4.4, 4.4],
        body_size=8.5,
    )
    add_caption(doc, "表 1　AI 工具清单表（名称、精确版本或型号、主要用途、核实依据）")

    add_paragraph(doc, "关于上表的四点说明：", bold=True, indent=False, space_after=2)
    for s in [
        "本表不写“最新版”“最新模型”这类无法核实的表述；凡本队记录中确实未核到更细版本的，如实写为“未在记录中核实”，不作推测。上表第 1 项的更细模型标识即属此种情形。",
        "本队未使用图像生成类 AI 工具。论文与支撑材料中的全部图（图 1–图 7 等）、全部表格与全部公式排版均由本队代码与本队成员完成，AI 未生成任何图片素材。",
        "本队未使用 AI 生成参考文献条目；论文参考文献中每一条均经本队成员当次实际打开核对过出版信息，查不到出版信息的条目一律删除。",
        "为可追溯起见，以下非 AI 软件在本工作中被实际使用，但不属于 AI 工具，故不计入本表：Visual Studio（用于核心代码的实际打开、断点、逐语句观察与完整运行；其版本号未在记录中核实）、MATLAB R2026a Update 5（程序日志记录版本 26.1.0.3346908，用于独立交叉实现的运行对照）、Python 3.14.7 与 NumPy 2.5.2、SciPy 1.18.1（求解与检验代码的运行环境）、LibreOffice（用于把本文件的 .docx 源转换为 PDF，并用于论文格式门禁的渲染检查）。",
    ]:
        add_paragraph(doc, "·　" + s, indent=False, space_after=2)

    # ---------------- 3 七环节 ----------------
    add_h(doc, "3　具体使用目的和环节（第(2)项，覆盖七个环节）", 1)
    add_paragraph(doc, "本节按赛前说明会第 29 页要求的七个论文核心环节逐项写明“是否使用 AI / AI 在该环节具体做了什么”，并同时写明本队主导内容与人工核验方式。总表见表 2，逐环节细节见 3.1–3.7。")

    add_table(
        doc,
        ["环节", "是否使用 AI", "AI 在该环节具体做了什么（摘要）", "本队主导与人工核验", "证据（工作区相对路径）"],
        [
            [
                "一、赛题理解",
                "使用",
                "读取题面 4 页与附件 1、附件 2，抽取字段、单位、时间跨度与采样间隔；读取赛前说明会材料与 AI 使用规定原文，逐条摘出页码与原文；指出题目未给出药材内部温湿度实测，因而结果只能是条件性预测。",
                "选题口径与四问理解由本队确定；AI 的解读必须附页码与原文摘句，由本队逐条比对原件。",
                "notes/A-principles/A题_公式推导与原理讲解.md；notes/selection-evaluation/2026-09-10/A题_可行性评估.md；notes/A-writing/2026-09-12/02_赛前说明会要求落实对照.md",
            ],
            [
                "二、模型假设",
                "使用",
                "起草七条假设（一维径向与端面、有效显热闭合、干基与干骨架守恒、等效平衡映射、环境插值与 4 h 后延拓、同比径向收缩、传热与传质系数沿用），并逐条配“依据 → 失效边界 → 我们的检验”；核对量纲与干基/湿基换算。",
                "七条假设与三项关键闭合（等效平衡映射、有效显热闭合、同比径向收缩）由本队选定；AI 提出的每条假设都必须写明失效边界与检验方式，无检验的假设不得进正文。",
                "notes/A-modeling/2026-09-10/A题_完整建模与公式推导.md；paper_output/paper/A题_论文写作交接包/02_统一模型与可复制公式.md",
            ],
            [
                "三、建模设计",
                "使用",
                "整理统一轴对称一维径向热湿耦合偏微分方程；提出并论证 Kirchhoff 浓度势处理强非线性水通量；整理问题四的材料坐标移动域与干骨架守恒；设计解析稀疏 Jacobian；起草有界自主实验的协议与预算。",
                "模型路线、方法取舍与“修正与创新点”的最终采纳由本队决定；密度相容性修正、潜热包络、材料坐标与等温线水活度闭合的取舍均由本队确认。",
                "notes/A-modeling/2026-09-10/autoresearch_protocol.md；notes/A-modeling/2026-09-12/交叉验证岛状态与发现.md；notes/A-plan/2026-09-10_A题执行计划.md",
            ],
            [
                "四、代码求解",
                "使用",
                "编写与重构求解代码：守恒型节点对偶有限体积离散、Kirchhoff 水分面通量、解析稀疏 Jacobian、事件判定与严格报告时刻；编写交付包内的正式入口与模块、MATLAB 独立交叉实现、导出器与逐格回读校验脚本。",
                "求解器总体结构与关键离散由本队确认；已在 Visual Studio 中打开交付工程、设置断点、逐语句观察变量并完整运行四问求解与导出（数值工作进程实际退出码 0）；MATLAB GUI 运行独立交叉实现并返回完成状态；核心代码人工审查进行中。",
                "notes/A-coding/2026-09-11/gui/IDE运行观察.md；notes/A-coding/2026-09-11/gui-artifact-audit/audit_summary.md；paper_output/context/code_delivery_status.json",
            ],
            [
                "五、结果检验",
                "使用",
                "编写并运行独立验证脚本：圆柱 Robin–Bessel 解析基准；离散质量恒等式；温度侧速率守恒证书；两种面离散与两套积分族对照；空间网格与时间设置收紧；独立二分根与事件根对照；收缩的长度尺度折算；潜热负荷与等温线闭合的情景包络；导出文件的逐格回读。",
                "检验项与“通过 / 不通过”判定口径由本队确认；AI 报出的不通过项一律保留原样，不得改写为通过；本队另行读取原始 JSON、日志与哈希进行反查。",
                "notes/A-modeling/2026-09-10/data/final_numerical_audit.md；notes/A-modeling/2026-09-10/data/autoresearch_final_review.md；paper_output/results/crossvalidation/",
            ],
            [
                "六、论文撰写",
                "使用",
                "起草论文骨架与页数预算；整理写作交接材料；把冻结结果转写为可复制的正文段落、表格与公式文本；逐条核对正文数值与冻结结果文件；做格式与页数检查；并对中文表述做语言润色（按官方规定，语言润色不计入第(4)项核验记录，但本文件仍在第 5 节如实登记其使用方式）。",
                "论文结构、技术路线、创新点的表述口径、结论措辞与“禁止写入清单”由本队确定；论文写作成员负责图表编排与全文一致性；AI 不得改写任何冻结数值。",
                "notes/A-writing/2026-09-12/00_论文写作总纲与执行指令.md；notes/A-writing/2026-09-12/问题分析2.2-2.4页_与冻结模型逐条核对.md；paper_output/paper/A题_论文写作交接包/",
            ],
            [
                "七、辅助工作",
                "使用",
                "工作区流程与记忆维护；技能可用性核查；官方公告与赛程信息的检索与页面实际打开核对；版本备份的定时任务配置说明；支撑材料打包体积核算与解压回读哈希核对；匿名性自查（文件名、文件夹名、文档属性、代码注释、路径）。",
                "提交口径、匿名边界与文件取舍由本队决定；版本提交由队伍指定的一名成员统一执行，避免并发写入；打包体积与哈希由本队核对后才认账。",
                "notes/workspace-maintenance/github-sync.md；notes/contest-watch/2026-progress/index.md；paper_output/context/code_delivery_status.json",
            ],
        ],
        widths=[1.7, 1.3, 5.0, 4.2, 3.8],
        body_size=8,
    )
    add_caption(doc, "表 2　AI 在七个环节中的使用情况、本队主导内容与证据路径")

    add_h(doc, "3.1　赛题理解", 2)
    add_paragraph(doc, "使用 AI：是。AI 读取题面与两个附件，抽出附件 1 为 241 条、0–14400 s、每 60 s 采样，附件 2 为 145 条、0–259200 s、每 1800 s 采样，合计 386 条记录、627 个非时间观测值；核对出附件给出的是边界驱动与几何，不是药材内部温湿度实测，因此全文不得声明实测准确率、RMSE 或置信区间。AI 同时读取赛前说明会材料，逐条摘出与 AI 披露、支撑材料、页数口径有关的要求并给出页码。")
    add_paragraph(doc, "本队主导与核验：四问的物理含义与求解目标由本队确认；对 AI 摘录的规则要求，本队逐条回查原始 PDF 页码与原文；对材料中互相冲突之处（例如篇幅“15–35 页”一说与官方“不超过 30 页”并存）不作自行统一，而是记录冲突并按最严一侧执行。")

    add_h(doc, "3.2　模型假设", 2)
    add_paragraph(doc, "使用 AI：是。AI 起草并整理七条假设，采用“假设内容 → 依据 → 失效边界 → 我们的检验”四句式；核对量纲与单位换算，指出干基含水率与湿基含水率必须区分（干基 2.55 kg/kg 对应湿基约 71.83%，达标阈值干基 0.15 对应湿基约 13.04% 而不是 15%），并指出有效热容量密度与干物质密度必须分行列出、全文不得混用。")
    add_paragraph(doc, "本队主导与核验：七条假设与三项关键闭合由本队选定；每条假设都必须写明失效边界与对应的检验方式，写不出检验的假设不得进入正文。")

    add_h(doc, "3.3　建模设计", 2)
    add_paragraph(doc, "使用 AI：是。AI 参与统一模型的推导整理（薄壳守恒 → Fourier/Fick 本构 → 初边值条件 → 题面附录经验式 → 干基与湿基换算），参与 Kirchhoff 浓度势处理强非线性水通量的方案论证，参与问题四材料坐标移动域与干骨架守恒的推导整理，参与解析 Jacobian 与实验协议的设计。")
    add_paragraph(doc, "本队主导与核验：模型路线与全部方法取舍由本队决定；“修正与创新点”最终采纳哪几条、以什么口径写入论文，由本队于 2026-09-12 确认。本队另行要求 AI 为每条公式标注“该处是题面给定，还是本文假设”，禁止把题面附录的经验式说成本队自行推导或拟合的结果。")

    add_h(doc, "3.4　代码求解", 2)
    add_paragraph(doc, "使用 AI：是。AI 编写与重构了求解代码与交付包，包括守恒型节点对偶有限体积离散（中心零面积面天然规避一维径向的奇点）、Kirchhoff 水分面通量、解析稀疏 Jacobian、事件判定与“上取整后重新查询未舍入场值”的严格报告时刻处理，以及 MATLAB 独立交叉实现、导出器与逐格回读校验脚本。")
    add_paragraph(doc, "本队主导与核验：求解器总体结构与关键离散由本队确认。已通过 Visual Studio 打开交付工程 A_CodeReview.sln，在入口处与右端函数处设置断点、逐语句执行并观察变量（初始温度 3201 个 301.15 K、初始含水率 3201 个 2.55、环境平衡含水率 0.01963、比热 2600、导热系数 0.36、密度 820、状态长度 6403 等），随后完整运行四问求解与导出，外部只读观察确认对应数值工作进程实际退出码为 0；MATLAB R2026a 图形界面运行独立交叉实现，三个案例完成并返回提示符。核心代码的人工审查仍在进行中，审查清单共 15 项，当前状态均为“待审”（paper_output/code/review_delivery/docs/人工审查清单.md）。")

    add_h(doc, "3.5　结果检验", 2)
    add_paragraph(doc, "使用 AI：是。AI 编写并运行了独立验证脚本，覆盖：圆柱 Robin–Bessel 解析基准（问题一，级数实现自身另有 8 项自检）；离散质量恒等式（问题一 / 问题二·三 / 问题四的最大残差分别为 5.77×10⁻¹⁵、1.15×10⁻¹⁴、7.99×10⁻¹⁵ kg/kg）；温度侧速率守恒证书（相对偏差 2.22×10⁻¹⁶ ~ 4.44×10⁻¹⁶，与网格无关）；两种积分族对照（变阶变步长隐式 BDF/NDF 与 Radau IIA）；两种面离散（调和平均与 Kirchhoff 势）随网格加密的对照；空间网格与时间设置收紧；独立二分根与事件根对照（相差 5.8×10⁻¹¹ s）；收缩的长度尺度独立折算（残差 1.37%）；表面潜热负荷与等温线闭合的情景包络；四个提交工作簿共 9 335 598 格的完整回读与正文 7 张表 297 格核验。")
    add_paragraph(doc, "本队主导与核验：检验项目与判定口径由本队确认；AI 报出的所有不通过项一律保留、不得改写为通过——例如某次网格批次因资源上限被中止（记录为 ABORTED_RESOURCE_LIMIT）即原样保留，不补造成“已运行成功”；本队另行读取原始 JSON、运行日志与哈希进行反查。")

    add_h(doc, "3.6　论文撰写", 2)
    add_paragraph(doc, "使用 AI：是。AI 起草论文骨架与页数预算，整理写作交接材料，把冻结结果转写为可复制的正文段落、表格与公式文本，逐条核对正文数值与冻结结果文件是否一致，并做格式与页数检查；同时对中文表述做语言润色。按官方规定，语言润色不计入第(4)项的核验记录，但本文件仍在第 4 节与第 5 节如实登记其使用方式。")
    add_paragraph(doc, "本队主导与核验：论文结构、技术路线、创新点的表述口径、逐问结论措辞与“禁止写入清单”（不得出现准确率、RMSE、置信区间、把 4 h 后延拓写成实测等）均由本队确定；论文写作成员负责图表编排与全文一致性；AI 不得改写任何冻结数值。")

    add_h(doc, "3.7　辅助工作", 2)
    add_paragraph(doc, "使用 AI：是。AI 用于工作区流程与记忆维护、技能可用性核查、官方公告与赛程信息的检索并实际打开页面核对、版本备份定时任务的配置说明、支撑材料打包体积核算与解压回读哈希核对，以及匿名性自查（检查文件名、文件夹名、文档属性中的作者与最后保存者、代码注释、路径与版本信息）。")
    add_paragraph(doc, "本队主导与核验：提交口径、匿名边界与文件取舍由本队决定；版本提交由队伍指定的一名成员统一执行以避免并发写入；打包体积与哈希由本队核对后才认可。经体积实测，支撑材料不得整目录打包（整目录压缩实测 55.85 MB，超出 20 MB 上限），只放入结果工作簿、源码、本文件与必要图表。")

    # ---------------- 4 提示方式 ----------------
    add_h(doc, "4　主要提示方式与使用过程说明（第(3)项）", 1)
    add_paragraph(doc, "本节说明本队是怎么提问、怎么下达任务的，并附三份典型交互示例。示例中的提示词与回复要点均按工作区内的真实记录整理，已作匿名处理（不出现学校、姓名、队号、赛区与本机用户名）。")

    add_h(doc, "4.1　本队的五类提问方式", 2)
    for s in [
        "一、原文核对型：不转述、不概括，直接把原件（赛前说明会材料、AI 使用规定、题面、格式规范）交给 AI，要求逐条摘录原文并标注页码；两处要求冲突时，必须列出两种说法与待澄清状态，不得自行裁决出一个确定答案。",
        "二、逐式核对型：把题面附录的经验式与代码逐式对齐，要求核对指数中的除号位置、温度是否用开尔文、干基与湿基是否换算正确、每个系数归属哪一个问题，并明确指出哪一处属于本文假设而不是题面给定。",
        "三、不变量与制造解型：要求为每一步离散写出能在机器精度上验证的恒等式（离散质量恒等式、温度侧速率恒等式），并给出解析基准或制造解；明确不接受“曲线光滑”“求解器返回成功”作为正确性证据。",
        "四、反例与守卫型：要求每个结论都自带守卫与自检——参数注入必须验证注入确实生效、敏感性扫描必须在基准处复现基准值、达标时刻必须用未舍入的场值复核严格不等式；并要求“失败就保留失败记录”。",
        "五、口径与措辞型：要求区分“节点值口径”与“控制体平均口径”、“条件性预测”与“实测精度”、“情景包络”与“置信区间”，并在每轮任务末尾附一份“不得写入论文的表述”清单。",
    ]:
        add_paragraph(doc, s, indent=False, space_after=3)

    add_h(doc, "4.2　本队对 AI 的通用约束（每一条都实际写入过任务）", 2)
    for s in [
        "不得改动已冻结的结果；任何模型、网格、容差或输入数据的改动都必须新建运行编号、重算并复核，原运行日志保留。",
        "所有数值必须绑定代码哈希、输入哈希与运行记录；没有运行证据的数值不得写入论文。",
        "不得生成或引用未亲眼核对过出版信息的文献；AI 给出的文献条目一律不得直接进参考文献。",
        "人工审查未完成前，任何文件（含本文件与论文中的 AI 声明）都不得写“人工审查已通过”。",
        "全部输出必须匿名：文件名、文件夹名、文档属性、代码注释、路径与版本信息中均不得出现学校、姓名、队号、赛区与本机用户名。",
        "结论只能写成“在给定假设下的条件性预测”，不得声称实测准确率、RMSE 或置信区间。",
        "不允许把“求解器成功退出”“四位小数一致”“机器量级的守恒残差”包装成物理精度或预测准确率。",
    ]:
        add_paragraph(doc, "·　" + s, indent=False, space_after=2)

    add_h(doc, "4.3　三份典型交互示例", 2)

    add_table(
        doc,
        ["项目", "内容"],
        [
            ["示例编号", "示例一（对应环节：赛题理解、论文撰写前的规则核对）"],
            ["时间与场景", "2026-09-10，选题确定后，需要一次性把 AI 披露与支撑材料的全部硬要求落到执行清单。"],
            ["提示词（摘录）", "“读取工作区内赛前说明会材料原件与官网《人工智能工具使用规定》原文，逐条列出与‘AI 工具使用声明’和支撑材料中的‘AI工具使用详情.pdf’有关的要求；每条必须给出所在页码与原文摘句；两份材料冲突的地方不要自己裁决，列出冲突与待澄清状态。”"],
            ["AI 回复要点", "① AI 声明应设在参考文献之前，二者择一，本队属“已使用”一类，末句“详细使用情况见支撑材料”不能省；② 支撑材料中的文件名须逐字为 AI工具使用详情.pdf；③ 详情文件须含四项内容：工具名称与版本或型号、具体使用目的和环节、主要提示方式与使用过程（可附典型交互示例）、对 AI 输出的采纳与人工修改核验情况（语言润色除外）；④ 说明会另要求 AI 工具清单表、七个核心环节逐项说明、2–3 份关键交互示例，以及核心环节由本队主导完成的确认与真实性声明；⑤ 指出材料内部关于篇幅存在“15–35 页”与官方“不超过 30 页”两种说法。"],
            ["队伍处理方式", "采纳该清单并据此建立落实对照表（notes/A-writing/2026-09-12/02_赛前说明会要求落实对照.md）；对篇幅冲突不采纳任何“自行统一”的说法，记录冲突并按更严的 30 页上限执行；把“核心代码人工审查进行中”写进执行清单，禁止任何文件提前写“已通过”。"],
            ["人工核验手段", "本队按 AI 给出的页码逐条回查原始 PDF 原文；对 AI 引用的官网链接当次实际打开，确认页面与条文存在后才写入执行清单。"],
        ],
        widths=[2.6, 13.4],
        body_size=8.5,
    )
    add_caption(doc, "表 3　典型交互示例一：规则与披露要求的原文核对")

    add_table(
        doc,
        ["项目", "内容"],
        [
            ["示例编号", "示例二（对应环节：建模设计、代码求解）——一次被守恒守卫拦下的真实错误"],
            ["时间与场景", "2026-09-12，构造“由数据锚定的吸附 / 水活度闭合”情景族，用于检验冻结基线是否高估了干燥后段的表面驱动。"],
            ["提示词（摘录）", "“按冻结模型的口径构造水活度闭合族，表面通量按冻结驱动缩放；必须给出两项恒等式检查：① 锚点水活度与烘房平台段相对湿度之差；② p=1 时本族右端函数与冻结模型右端逐位比较。任何一项不通过就如实报告失败，不许调整口径让它通过。”"],
            ["AI 回复要点", "第一版把内部面通量的符号约定误当成“向外为正”，表面边界写成了方向相反的形式，导致 p=1 时表面通量整体反号。运行结果表现为含水率不再下降而是单调上升至 15.96 kg/kg，随即被离散质量恒等式守卫拦下（冻结基线的该项残差量级为 10⁻¹⁴ kg/kg，此处失配远超该量级）。AI 在回复中如实报告了这次失败并定位到符号约定。"],
            ["队伍处理方式", "不接受该结果，也不允许用调松阈值的方式绕过；要求按冻结模型“向内为正”的约定把表面通量改为对冻结驱动的直接缩放，并复跑 p=1 的情景与冻结模型做逐位对照。修正后 p=1 情景与冻结模型的右端函数逐位一致（最大差恰为 0.0），据此确认冻结基线是该闭合族的一个成员，而不是族外模型。失败与修正过程一并留档，不删除。"],
            ["人工核验手段", "① 检查恒等式是“逐位相等”而不是“数值接近”；② 要求事件时间与更早一次独立运行逐位复现；③ 本队另行读取原始结果 JSON 复核判定字段，而非只看 AI 的文字结论。"],
        ],
        widths=[2.6, 13.4],
        body_size=8.5,
    )
    add_caption(doc, "表 4　典型交互示例二：吸附闭合情景的边界符号错误与修正")

    add_table(
        doc,
        ["项目", "内容"],
        [
            ["示例编号", "示例三（对应环节：结果检验、参数敏感性）——一次“参数无影响”的假象"],
            ["时间与场景", "2026-09-11 至 09-12，对冻结求解器做参数敏感性筛选与扫描，用于支撑“本工况由传质控制”的结论。"],
            ["提示词（摘录）", "“对冻结求解器做 Morris 筛选，逐一报告每个参数的基本效应；如果某个参数的影响恰好为 0，先怀疑注入是否生效，不要直接写成‘该参数无影响’，并给出定位方法。”"],
            ["AI 回复要点", "Morris 筛选给出扩散前因子尺度的影响恰为 0.0000，20 条轨迹的基本效应全为 0。按提示要求先查注入：定位到在 Kirchhoff 面格式下，内部水分面通量使用硬编码的扩散前因子，不读取物性函数返回的扩散系数数组，因此“只缩放物性数组”的注入完全不生效。改用对 Kirchhoff 面通量直接乘尺度因子后重扫，扩散系数前因子从 0.70 变到 1.40 时，问题二·三的达标时间由 79.42 h 变到 43.08 h（跨度 63.2%），问题四由 70.41 h 变到 38.32 h（跨度 62.8%）；作为对照，导热系数 ±15% 的影响不到 0.011%。"],
            ["队伍处理方式", "作废 Morris 筛选中该参数的条目，论文只引用带注入自检的单参数扫描结果。同期另一次方差分解因观测到一阶指数为负、且一阶大于总阶等违反其自身恒等式的现象，本队判定为样本量不足导致的噪声，终止该次运行、不写入论文、明确记为“未做”，而不是拿噪声充数。"],
            ["人工核验手段", "要求注入实验自带哨兵：在尺度为 1.00 处必须复现基准结果，实测复现到 10⁻⁶ h 以内，以此证明“注入确实生效且不改变基准”；同时用另一个物理量（导热系数）的对照扫描确认该实验并非“对什么都敏感”。"],
        ],
        widths=[2.6, 13.4],
        body_size=8.5,
    )
    add_caption(doc, "表 5　典型交互示例三：参数注入失效导致的假阴性结论")

    add_paragraph(doc, "除上述三例外，本队还保留了其余的完整交互与处置记录（见第 5 节与第 7 节所列路径），未被采纳的 AI 输出同样留有记录，未作删除。")

    # ---------------- 5 采纳修改核验 ----------------
    add_h(doc, "5　对 AI 输出的采纳、人工修改和核验的主要情况（第(4)项，语言润色除外）", 1)
    add_paragraph(doc, "本队对 AI 输出的处理分三类：直接采纳（须有运行证据与自检）、人工修改后采纳、以及人工核查后作废或拒绝报告。三类情况均有具体例子与可回溯记录。语言润色部分不属于本项核验范围，其使用方式已在第 3.6 节如实登记。")
    add_table(
        doc,
        ["处置类别", "条目数（本文件列举）", "说明"],
        [
            ["采纳（附自检与证据）", "3 类", "规则与要求的原文摘录；求解与检验代码；验证脚本与情景计算。采纳的前提是：有运行记录、有哈希绑定、结论处自带基准自检。"],
            ["人工修改后采纳", "4 例", "见 5.2 第(2)(3)(4)(7)条：注释勘误、边界符号、守恒口径、脚本实现缺陷。"],
            ["人工核查后作废或拒绝报告", "4 例", "见 5.2 第(1)(5)(6)(8)条：参数注入失效导致的假阴性、口径误判、导出缺陷导致的失败运行、统计上不可用的方差分解。"],
        ],
        widths=[3.4, 3.0, 9.6],
        body_size=8.5,
    )
    add_caption(doc, "表 6　对 AI 输出的处置汇总")

    add_h(doc, "5.2　具体例子", 2)

    examples = [
        (
            "（1）敏感性分析因参数注入未生效而得出“该参数无影响”的错误结论，人工核查后作废并重跑（强制作废例）",
            "AI 首次的 Morris 筛选报告扩散前因子尺度的基本效应恰为 0.0000，20 条轨迹全为 0，且无失败记录。本队判断这在物理上不可能（该参数是水分扩散率的直接乘子），要求先查注入是否生效。核查定位到：在 Kirchhoff 面格式下内部水分面通量使用硬编码的扩散前因子，不读取物性函数返回的数组，因此任何“只缩放物性数组”的设置都不会改变模型。处置：作废 Morris 中该参数的条目，改为对 Kirchhoff 面通量直接乘尺度因子后重新扫描，并在尺度 1.00 处复现基准值作为注入有效性自检（复现到 10⁻⁶ h 以内）。最终论文只引用带自检的单参数扫描结果。记录：notes/A-modeling/2026-09-12/交叉验证岛状态与发现.md 第 4.10 节、notes/A-coding/2026-09-11/innovation-and-crossvalidation/paper-section-素材.md。",
        ),
        (
            "（2）源码注释把“原始环境温度 K”与“含水率 kg/kg”混写，已列勘误并更正文案",
            "AI 交付代码中有一行注释写成“原始环境时间单位为秒，温度为 K，含水率为 kg 水/kg 干物质”。人工核对后确认该注释不准确：程序读取的是已经清洗并换算为开尔文的环境表，题面原环境温度为摄氏度；而环境水分列的 kg/kg 其真实质量分母在题面中并未明确，程序只是把它当作等效平衡含水率使用。处置：登记为源码注释勘误，给出准确的更正文案（写明“读取清洗后的环境表，温度单位 K，环境水分列保留题给数值并按等效平衡含水率使用，真实气相质量基准与气固映射待核”），并明确该勘误不影响数值行为——运行代码读取的温度与等效平衡含水率数值未变。同时保留原源码与既有运行记录的哈希对应关系，未声称旧运行是在已修正注释的文件上完成的。记录：notes/A-modeling/2026-09-11/effects-rounding/四张易错点截图逐条对照与判断.md 第 6 节。",
        ),
        (
            "（3）构造吸附闭合情景时表面边界符号写反，被离散质量恒等式拦截后修正；修正后 p=1 与冻结模型右端逐位一致",
            "AI 在构造水活度闭合情景族时按“向外为正”的约定书写表面边界，与冻结模型“向内为正”的内部面约定相反，使 p=1 时表面通量整体反号。运行表现为含水率不降反升，单调上升至 15.96 kg/kg；离散质量恒等式守卫立即报出远超 10⁻¹⁴ kg/kg 量级（冻结基线残差量级）的失配，运行被拦下。处置：本队不接受该结果，要求按冻结约定改为对冻结驱动的直接缩放并重跑；修正后 p=1 情景与冻结模型的右端函数逐位一致，最大差恰为 0.0，据此确立“冻结基线是本闭合族的 p=1 成员”。该错误与修正过程保留在记录中。记录：notes/A-modeling/2026-09-12/交叉验证岛状态与发现.md 第 4.15 节第 3 条。",
        ),
        (
            "（4）守恒残差不随网格下降，人工追查后改写结论口径，并查出两个真实缺陷",
            "AI 首次报告温度侧累积守恒检验时，常物性的问题一通过（相对残差 7.85×10⁻¹⁰），而两个耦合问题的残差不通过且不随网格加密下降。人工不接受“残差小就说明正确、残差大就归因于求解器精度”的含糊处理，要求把丢弃的容量功单独积出来比较。结论改为：耦合问题的累积残差主要来自有效热容量闭合本身丢掉的功（占残差 98.5% 与 100%），不是求解器误差；论文只把速率形式、达到机器精度的守恒证书作为主要证据，累积式只对常物性的问题一作为精确恒等式。同一追查还查出两个真实实现缺陷——表面通量漏掉半径因子（在本例半径 0.02 m 时相差 50 倍）、累积式中误用瞬时热容量——均已修正。记录：notes/A-modeling/2026-09-12/交叉验证岛状态与发现.md 第 4.12 节。",
        ),
        (
            "（5）解析基准在表面报出的偏差被误读为求解器误差，人工判定为口径差异",
            "AI 首次报告问题一的解析基准最大误差恒出现在表面节点且不随网格加密下降（不同网格分别约 1.9×10⁻⁶、2.4×10⁻⁶、1.8×10⁻⁶ K），容易被读成“求解器有极限精度”。人工要求改用“节点值对精确环形平均”的口径重新比较，得到四种网格下的最大差分别为 2.0512×10⁻³、1.0258×10⁻³、5.1292×10⁻⁴、2.5647×10⁻⁴ K，恰好一阶收敛（表面控制体是单侧的），内部为二阶。处置：判定表面约 2×10⁻⁶ K 是口径差而不是求解器误差，论文中两种口径分别标注、不得互相替代。记录：notes/A-modeling/2026-09-12/交叉验证岛状态与发现.md 第 4.8 节。",
        ),
        (
            "（6）导出器来源路径保留旧文件名导致复核失败，失败运行保留、修复后定向验证",
            "AI 交付的导出器在问题三的来源标注中保留了旧模块文件名，导致该次运行的复核失败，进程实际退出码为 1。处置：不以“重跑一次就对了”收场——失败运行的记录与退出码原样保留，先定位并修复来源路径，再对问题三与问题四做定向导出验证（验证结果另存）。本队另行确认修复后的版本与图形界面完成记录一致。同时把这项事实写进人工审查清单，明确“该失败路径不在首次 AI 审查覆盖范围内”，不得由清单预填为人工“接受”。记录：paper_output/context/code_delivery_status.json 的 retainedFailure 字段、notes/A-coding/2026-09-11/gui/IDE运行观察.md。",
        ),
        (
            "（7）验证脚本的两处实现缺陷被真实崩溃暴露，修复后重跑",
            "AI 编写的阈值与标度检查脚本在拼接求解器状态返回时使用了错误的拼接方向，末段只有一列，首次运行真实崩溃（数组长度不匹配）；另一个脚本在提取材料坐标时把坐标值当成了列索引，导致下标越界崩溃。两处均由 AI 定位并修复后重跑，崩溃信息保留在记录中。处置：接受修复后的结果，但要求所有情景数据在基准处都带自检。记录：notes/A-modeling/2026-09-12/交叉验证岛状态与发现.md 第 4.15 节第 1、2 条。",
        ),
        (
            "（8）方差分解指数违反其自身恒等式，人工判定为统计上不可用并拒绝报告",
            "AI 完成的一轮方差分解给出的指数出现一阶指数为负、以及一阶指数大于总阶等情形，违反该方法的基本恒等式（一阶应为非负且不大于总阶）。处置：判定为样本量不足导致的噪声而非物理发现，终止该次运行，不写入总报告、不写入论文，并明确记录为“在剩余时间内未做”，而不是拿噪声充数。记录：notes/A-modeling/2026-09-12/交叉验证岛状态与发现.md 第 4.14 节。",
        ),
        (
            "（9）AI 转写的正文表格数值由脚本逐行与冻结结果文件比对后才采纳",
            "论文正文使用的多张数值表格由 AI 从冻结结果转写。本队不接受“看起来对”，而是用核对脚本把表格逐行与冻结结果文件精确比对，比对结果为通过后才进入正文；同时要求正文数值、附录数值与摘要数值三处一致。记录：notes/A-coding/2026-09-11/independent-verification/verification_report.md、paper_output/context/code_delivery_status.json（正文表 297 格核验通过）。",
        ),
        (
            "（10）AI 给出的文献条目一律删除，除非本队亲眼核对到出版信息",
            "本队明确规定：AI 生成的“看起来很像真的”文献条目绝对不得进入参考文献。执行结果：论文参考文献中的每一条都由本队成员当次实际打开核对出版信息；凡是查不到出版信息或无法打开的条目一律删除；正文引用与文末条目一一对应。记录：paper_output/paper/A题_论文写作交接包/08_参考文献与检索方法.md、notes/A-writing/2026-09-12/00_论文写作总纲与执行指令.md 第 2.4 节。",
        ),
    ]
    for title, body in examples:
        add_paragraph(doc, title, bold=True, indent=False, space_after=2)
        add_paragraph(doc, body, space_after=6)

    add_h(doc, "5.3　人工审查状态的如实说明", 2)
    for s in [
        "已完成的机器侧与图形界面侧证据：Visual Studio 图形界面完整运行四问求解与导出（外部只读观察确认数值工作进程实际退出码为 0）；MATLAB 图形界面运行独立交叉实现，三个案例完成；四个提交工作簿共 9 335 598 格完整回读通过；正文 7 张表共 297 格核验通过；冻结版本的 107 项输入/输出哈希全部匹配。",
        "未完成的部分：本队成员对核心代码的逐项人工审查。人工审查清单共 15 项，当前状态均为“待审”，见 paper_output/code/review_delivery/docs/人工审查清单.md。",
        "因此本文件与论文中一切涉及人工审查的表述统一为：“已通过 Visual Studio GUI 实际运行复现；核心代码人工审查进行中”，全文没有任何“人工审查已通过”的表述。状态依据为 paper_output/context/code_delivery_status.json（status = COMPLETED_READY_FOR_USER_CODE_REVIEW，humanReview = PENDING_USER_REVIEW）。",
        "需要特别说明的边界：图形界面的运行与截图证据由代理在受控方式下采集并留档，可以证明“程序在图形界面中确实被打开、断点观察并完整跑通”，但不能代替本队成员本人对代码逻辑的审查；两者不得互相代签。",
        "此外，检验结论的适用边界同样如实登记：本题没有药材内部温度与含水率的实测数据，因此全部数值结果只能是给定假设下的条件性预测，不得声明实测准确率、RMSE 或置信区间。",
    ]:
        add_paragraph(doc, "·　" + s, indent=False, space_after=2)

    # ---------------- 6 核心环节确认与声明 ----------------
    add_h(doc, "6　核心环节由本队主导完成的确认与队伍真实性声明", 1)
    add_paragraph(doc, "按赛前说明会第 29 页要求，本队对模型创新、公式推导、代码逻辑与核心论述四项核心环节逐项确认其为本队主导完成，确认表见表 7，真实性声明见 6.2 节。")

    add_h(doc, "6.1　核心环节本队主导完成确认表", 2)
    add_table(
        doc,
        ["核心环节", "本队主导完成的内容", "AI 的参与边界", "可核验记录"],
        [
            [
                "模型创新",
                "确定统一模型路线；确定采用并写入论文的修正与创新点，包括：题给密度与几何的相容性修正（干物质密度另行守恒）、表面蒸发的潜热负荷情景包络、Kirchhoff 浓度势处理强非线性水通量的必要性论证、问题四的材料坐标移动域与干骨架守恒，以及由题面自身两个数字推出的等温线水活度闭合。其中最后一项由本队于 2026-09-12 明确选定为最终创新点，并规定其结论只能表述为闭合族的下界。",
                "AI 参与推导整理、代码实现与情景计算，并如实报告失败项；创新点是否采纳、以什么口径写入论文，全部由本队决定，AI 不参与取舍。",
                "notes/A-modeling/2026-09-12/交叉验证岛状态与发现.md；notes/A-writing/2026-09-12/00_论文写作总纲与执行指令.md 第 5 节",
            ],
            [
                "公式推导",
                "定稿薄壳守恒方程、Fourier 导热与 Fick 扩散本构、初边值条件、干基与湿基换算、问题四材料坐标变换与干骨架守恒关系式；并定下三条严谨性禁令：非线性系数不得移出散度、热容量系数位于时间导数外侧时不得改写为焓式、材料坐标下不得加体积浓缩项且不得重复加平流项。",
                "AI 参与推导的整理与逐式核对，并按本队要求标注每一条是“题面给定”还是“本文假设”；每条公式均由本队对照题面原文与物理量纲逐条确认后才定稿。",
                "notes/A-modeling/2026-09-10/A题_完整建模与公式推导.md；paper_output/code/review_delivery/docs/公式与算法说明.md",
            ],
            [
                "代码逻辑",
                "确认求解器总体结构与关键离散：守恒型节点对偶有限体积、中心零面积面处理、Kirchhoff 水分面通量、解析稀疏 Jacobian、事件判定与严格报告时刻（上取整后重新查询未舍入场值以验证严格小于阈值）、干物质质量另行守恒。",
                "AI 负责编码、重构与验证脚本编写；本队在 Visual Studio 中打开交付工程、设置断点、逐语句观察变量并完整运行四问求解与导出，数值工作进程实际退出码为 0；核心代码的人工审查仍在进行中，人工审查清单 15 项当前均为“待审”。",
                "notes/A-coding/2026-09-11/gui/IDE运行观察.md；notes/A-coding/2026-09-11/gui-artifact-audit/audit_summary.md；paper_output/code/review_delivery/docs/人工审查清单.md",
            ],
            [
                "核心论述",
                "确定论文的技术路线与四问递进关系、结果的表述口径、局限与“不声明清单”（不声明实测准确率、不声明置信区间、不把情景范围写成置信区间、不把四位小数写成计算精度），以及参考文献的取舍标准。",
                "AI 用于语言润色（按官方规定不计入第(4)项核验记录，其使用方式已在第 3.6 节如实登记）、格式与页数检查、以及正文数值与冻结结果文件的一致性核对；论述内容与结论措辞由本队写作成员撰写并定稿。",
                "notes/A-writing/2026-09-12/00_论文写作总纲与执行指令.md；notes/A-writing/2026-09-12/问题分析2.2-2.4页_与冻结模型逐条核对.md",
            ],
        ],
        widths=[1.7, 6.0, 4.6, 3.7],
        body_size=8,
    )
    add_caption(doc, "表 7　核心环节本队主导完成确认表")

    add_h(doc, "6.2　队伍真实性声明", 2)
    add_paragraph(doc, "本参赛队郑重声明：")
    for s in [
        "本参赛队在本届竞赛过程中使用了 AI 工具，具体工具、版本或型号、使用目的与环节、提示方式与使用过程、以及对 AI 输出的采纳与人工核验情况，均已在本文件中逐项如实说明，无隐瞒、无虚假记载。",
        "参赛作品的模型创新、公式推导、代码逻辑与核心论述四项核心环节，均由本参赛队成员主导完成；AI 工具用于资料与规则核对、公式与代码复核、数值验证脚本编写、文稿一致性与格式检查，以及中文语言润色。AI 未独立完成模型，AI 生成的内容均未被直接作为核心建模与分析成果提交。",
        "本参赛队对所提交作品的原创性、真实性和准确性负全部责任。所有引用他人或公开资料之处均已按科技论文规范列出并在正文引用处标注；参考文献中不含任何 AI 生成、未经核实的条目。",
        "本参赛队未使用“本参赛队在竞赛过程中未使用任何 AI 工具”一类声明；本文件同样不含该表述。",
        "截至本文件编制时，核心代码的人工审查仍在进行中，尚未完成。本文件不声称人工审查已经通过；全部涉及人工审查的表述均以“已通过 Visual Studio GUI 实际运行复现；核心代码人工审查进行中”为准，并以工作区记录 paper_output/context/code_delivery_status.json 的状态字段为唯一依据。",
        "题目未提供药材内部温度与含水率的实测数据，因此本参赛队的全部数值结果均为给定假设下的条件性预测，未声明实测准确率、均方根误差或置信区间。",
    ]:
        add_paragraph(doc, "·　" + s, indent=False, space_after=2)

    # ---------------- 7 来源与生成方式 ----------------
    add_h(doc, "7　本文件的信息来源与生成方式", 1)
    add_paragraph(doc, "本文件所述全部事实均来自本队工作区内已存在的记录，可逐条回溯。主要来源如下（工作区相对路径）：")
    for s in [
        "工具与总体使用记录：notes/ai-use/2026-09-10_A题计划与技能核查.md；notes/A-coding/2026-09-11/independent-verification/verification_report.md。",
        "赛题理解与规则核对：notes/A-principles/A题_公式推导与原理讲解.md；notes/selection-evaluation/2026-09-10/A题_可行性评估.md；notes/A-writing/2026-09-12/02_赛前说明会要求落实对照.md。",
        "建模与假设：notes/A-modeling/2026-09-10/A题_完整建模与公式推导.md；notes/A-modeling/2026-09-10/autoresearch_protocol.md；notes/A-plan/2026-09-10_A题执行计划.md。",
        "代码与图形界面复现：notes/A-coding/2026-09-11/gui/IDE运行观察.md；notes/A-coding/2026-09-11/gui-artifact-audit/audit_summary.md；notes/A-coding/2026-09-11/matlab-static-review.md；paper_output/context/code_delivery_status.json；paper_output/code/review_delivery/docs/人工审查清单.md。",
        "结果检验与交叉验证：notes/A-modeling/2026-09-10/data/final_numerical_audit.md；notes/A-modeling/2026-09-10/data/autoresearch_final_review.md；notes/A-modeling/2026-09-12/交叉验证岛状态与发现.md；notes/A-coding/2026-09-11/innovation-and-crossvalidation/paper-section-素材.md；paper_output/results/crossvalidation/。",
        "论文撰写与一致性核对：notes/A-writing/2026-09-12/00_论文写作总纲与执行指令.md；notes/A-writing/2026-09-12/问题分析2.2-2.4页_与冻结模型逐条核对.md；paper_output/paper/A题_论文写作交接包/。",
        "辅助工作：notes/workspace-maintenance/github-sync.md；notes/contest-watch/2026-progress/index.md；paper_output/results/code_delivery/交付与运行记录.md。",
    ]:
        add_paragraph(doc, "·　" + s, indent=False, space_after=2)
    add_paragraph(doc, "生成方式与匿名化处理：本文件先由本队用 Python 的 python-docx 库生成可编辑的 .docx 源文件，再用 LibreOffice 以无头模式转换为 PDF。生成时已显式把文档属性中的“作者”与“最后保存者”设为空字符串，标题、主题、备注、类别、关键字等属性一并置空。本文件全文、表格、文件名与文档属性中均不含学校、姓名、队号、赛区与本机用户名信息。生成的 PDF 为文本型文件，正文文字可直接提取。")

    scrub_properties(doc)
    doc.save(OUT_DOCX)
    return OUT_DOCX


if __name__ == "__main__":
    path = build()
    print("OK:", path, os.path.getsize(path), "bytes")
