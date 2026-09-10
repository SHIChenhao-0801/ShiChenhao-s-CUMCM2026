"""Build A-specific S1/S2 contracts only; no production model is executed.

Run from the 2026CUMCM root with python -B and --stage s1 or --stage s2.
The shared skill's generic scanner is deliberately not used because it scans
all contest questions, whereas active_problem_scope limits this task to A.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path.cwd().resolve()
EXPECTED = Path(r"D:\Document\数学建模\2026CUMCM").resolve()
assert ROOT == EXPECTED, f"Unexpected workspace: {ROOT}"
OUT = ROOT / "paper_output"
S1 = OUT / "step1"
S2 = OUT / "plan"
GENERATED_BY = "paper_output/code/contracts/build_a_contracts.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def base():
    return {"schema_version": "1.0", "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"), "generated_by": GENERATED_BY}


def provenance():
    scope = read_json(OUT / "context/active_problem_scope.json")
    assets = scope["selected_assets"]
    assert scope["problem_id"] == "A" and len(assets) == 7
    for item in assets:
        assert digest(ROOT / item["path"]) == item["sha256"], item["path"]
    return assets


PARAMETER_SETS = {
    "Q1": {"source": "A题.pdf 第3页附录2", "rho": "820", "cp": "2600", "k": "0.36", "D": "7e-9*exp(-0.89/C)", "h": 25.0, "beta": 8e-7},
    "Q2_Q3": {"source": "A题.pdf 第4页附录3", "rho": "650+128*C", "cp": "1450+2736*C/(1+C)", "k": "0.21+0.38*C/(1+C)", "D": "2.4e-3*exp(-0.45/C)*exp(-3850/T_K)", "h_beta_status": "沿用附录2是明确记录的模型约定；两问未另给参数"},
    "Q4": {"source": "A题.pdf 第4页附录4", "rho": "760+90*C", "cp": "1850+2150*C/(1+C)", "k": "0.12+0.20*C/(1+C)", "D": "4.2e-4*exp(-0.30/C)*exp(-3850/T_K)", "h_beta_status": "沿用附录2是明确记录的模型约定；第四问未另给参数"},
}

COMMON_VALIDATION = [
    "每条公式先说明目的、自变量、因变量、单位和物理含义；经验系数只作题给，不能伪造第一性原理推导",
    "对源PDF第3—4页人工可视核对指数中的除号；温度进入Arrhenius项前必须换算为K",
    "检查初始场、中心零通量、表面Robin通量、C正性及温度/含水率范围；不以数值裁剪掩盖失败",
    "常系数圆柱Bessel级数对照验证离散求解器，报告截断误差与数值误差的区别",
    "分别加密空间网格和时间步；满足渐近收敛条件才报告Richardson外推或观测阶",
    "检查累计水分流出量与干基总水量减少的离散闭合；核对单位与相对残差",
    "保存输入/代码/参数/输出SHA256、实际运行退出码与有限数值；VS GUI复现、用户人工审查分别记录",
    "没有药材内部T/C实测真值；不得将数值一致性写为实测RMSE、预测准确率或校准成功",
]

ASSUMPTIONS = [
    {"id": "A01", "title": "径向一维及端面处理", "statement": "采用轴对称、轴向近似均匀的一维径向场，固定长度L=0.25m，Q1—Q3半径R0=0.02m。", "start": "由真实三维药材抽象为圆柱的一维传递域时", "basis": "题目按到中心的距离输出；长径比L/(2R0)=6.25", "limit": "题目有限圆柱事实不等于端面绝热；端面积/侧面积=R0/L=0.08，不足以独自证明影响可忽略", "validation": "至少量级分析；有预算时采用有限圆柱二维轴对称或可核验常系数端面修正情景"},
    {"id": "A02", "title": "有效显热", "statement": "用a(C)=rho(C)*cp(C)作为有效体积热容量，a(C)D_tT=div(k(C)grad(T))；基准不显式增加相变潜热或湿分携带焓。", "start": "从总能量守恒约化到有效显热方程时", "basis": "题给rho、cp、k及对流换热参数，未给完整相变/焓闭合", "limit": "rho(C)在此作为题给有效热容量的组成部分，不能同时无条件声明其为严格守恒的湿物料总密度", "validation": "表面潜热替代情景需明确j_w、Lv及能量方向，禁止内外双重扣潜热"},
    {"id": "A03", "title": "干物质骨架及Fick闭合", "statement": "C为kg水/kg干物质。Q1—Q3固定均匀干骨架；Q4均匀同比径向材料收缩，rho_d(t)=rho_d0*(R0/R(t))^2。水通量j_w=-rho_d*D*grad(C)。", "start": "把干基质量比C转为守恒水质量，并为通量选择本构时", "basis": "干物质质量守恒与给定半径轨迹可相容闭合", "limit": "rho_d0仅决定总水质量单位尺度，不影响空间均匀rho_d下的C解；不能把rho(C)/(1+C)再强塞入同一均匀骨架", "validation": "干物质守恒、累计水分质量守恒，必要时对替代总密度闭合单独立模"},
    {"id": "A04", "title": "环境到材料的等效平衡映射", "statement": "基准令Ceq(t)=附件1给出的烘房水分值，使用-D*C_r=beta*(Cs-Ceq)。", "start": "把空气观测变为材料表面Robin边界时，早于4h外推", "basis": "题目提供kg/kg环境水分与m/s有效传质系数，未给吸附等温线", "limit": "kg水/kg干空气与kg水/kg干药材不是同一基准；这里是简化约定，并非由单位相同推得物理等价", "validation": "对Ceq映射比例/偏移或不同平衡值做敏感性；没有品种吸附数据不能唯一恢复真实映射"},
    {"id": "A05", "title": "环境插值和4h后延拓", "statement": "0—14400s按附件1分段线性插值，超过4h基准取50°C与Ceq=0.05。", "start": "相邻60s观测之间采用插值时已有局部假设；超过14400s明确进入观测外延拓", "basis": "附件末时段接近恒温、恒湿平台，题面称恒温干燥", "limit": "50/0.05只是候选工况，不是其后68h的实测值，也不能声称给出了统计置信区间", "validation": "末值保持、末1h均值保持、平台温湿扰动；时长对工况变化另列"},
    {"id": "A06", "title": "收缩材料运动", "statement": "Q4以附件2的R(t)确定边界，取u(r,t)=r*R'(t)/R(t)，长度固定。x=r/R(t)为材料坐标，网格速度等于骨架速度。", "start": "由仅有半径观测推断内部材料速度场时", "basis": "与表面速度及空间均匀干物质骨架守恒相容的最简闭合", "limit": "附件没有内部位移或长度轨迹，不能证明真实内部收缩均匀；仅坐标变换本身不构成物理假设证据", "validation": "R插值保持非增、正值；同物性固定/收缩对照；不得重复加入ALE平流或C体积稀释项"},
    {"id": "A07", "title": "传热传质系数延用", "statement": "Q2—Q4沿用h=25 W/(m²K)、beta=8e-7m/s。", "start": "附录3/4未重给边界系数，建立对应边界条件时", "basis": "同一药材烘房，题面仅明确更换给出的经验物性", "limit": "温湿风速变化可能改变系数，当前无风速或系数测量", "validation": "h、beta独立±10%/±20%参数情景，报告设置而非实测误差"},
]

AMBIGUITIES = [
    {"id": "U01", "issue": "烘房kg/kg的参考质量基准与材料平衡含水率映射未明", "resolution": "按A04显式约定并敏感性，不能隐去", "blocks": "不阻塞条件性机理求解；阻塞无条件的实测预测准确性声明"},
    {"id": "U02", "issue": "附件1仅4h而全过程约2—3天", "resolution": "按A05平台延拓并对照末值/末段均值/扰动", "blocks": "无假设不能唯一预测4h以后"},
    {"id": "U03", "issue": "result2完整结果的终止时刻未明确，正文只列3h", "resolution": "保留从0至Q3达标时刻的逐秒全程T/C；另导出前3h，依据20M支撑上限实测压缩体积后形成明确提交方案", "blocks": "不影响求解；最终文件范围解释与体积仍待导出验证"},
    {"id": "U04", "issue": "Q4半径不落0.1cm或0.5cm格点时表面及域外单元如何表达", "resolution": "固定物理距离列+独立表面列，域外留空且不得填0；配套时间到R(t)映射/元数据，最终保证模板格式清晰", "blocks": "最终模板结构需实际导出检查"},
    {"id": "U05", "issue": "rho(C)与干基/固定或给定收缩体积的严格总质量守恒不自动相容", "resolution": "有效热容量和干骨架质量守恒分清；另一密度解释必须新建并标明替代模型", "blocks": "阻塞把相互不相容闭合全部称为严格守恒"},
    {"id": "U06", "issue": "Q4若达标超过72h则R数据不足", "resolution": "先在实测范围内求解；超出时标记数据域外并比较末半径保持与正值非增外推，不能静默延长", "blocks": "72h后时长依赖额外半径外推"},
    {"id": "U07", "issue": "严格低于0.15和四位小数显示0.1500可能冲突", "resolution": "事件求根报告连续阈值交叉时间、严格达标的首个输出时刻及未舍入max(C)；等于阈值点不称严格低于", "blocks": "不阻塞模型；需保留未舍入判定证据"},
]


def questions():
    names = ["问题一：预热平衡阶段", "问题二：全过程热湿耦合", "问题三：全域达标时间", "问题四：收缩下的达标时间"]
    summaries = [
        "在0—1800s求固定圆柱T(r,t)、C(r,t)，使用附录2，输出7个时刻×5个半径的两张表及逐秒/0.1cm完整网格。",
        "从同一初值出发，全过程统一使用附录3，求T/C双向物性耦合，正文显示前3h，文件保留逐秒/0.1cm完整解。",
        "沿用问题二全过程模型，在整个空间域max(C)<0.15条件下确定结束时间；按6h及60s导出含水率。",
        "使用附录4整组物性及附件2半径轨迹，建立与材料收缩守恒相容的模型，求全域达标时刻及移动域内C。",
    ]
    baselines = [
        "固定半径常系数圆柱Robin-Bessel解析解（热方程可直接验证，水扩散D冻结作求解器基准）",
        "固定半径、同一初值的常物性圆柱热/水基线，作为附录3变物性耦合的对照",
        "问题二已验证解的max(C)阈值事件；常D/Bessel时长仅作可解释尺度对照",
        "附录4相同物性、固定R0、同边界的全过程模型，用于隔离半径收缩的净影响",
    ]
    mains = [
        "固定骨架一维径向热传导及D(C)非线性扩散；守恒有限体积+隐式时间积分",
        "固定骨架一维径向非线性热湿耦合PDE；rho*cp与k依赖C、D依赖C及绝对温度",
        "继承Q2的守恒数值解并对全域最大干基含水率做阈值事件定位",
        "同比径向材料收缩x=r/R(t)的一维热湿耦合PDE；rho_d随R^-2变化守恒，有限体积在固定材料网格求解",
    ]
    figure_titles = [
        ["前30min温度径向剖面", "前30min含水率径向剖面", "常系数Bessel与数值解误差"],
        ["前3h中心与表面温湿演化", "全过程温度含水率及D变化", "变物性与冻结物性对照"],
        ["max(C)与0.15阈值及结束时间", "每6h径向含水率剖面", "网格时间步与边界延拓敏感性"],
        ["半径数据与插值", "收缩材料网格及物理域含水率", "附录4固定/收缩同物性时长对照"],
    ]
    source_pages = [[1,3],[2,4],[2,4],[2,3,4]]
    output_specs = [
        {"file": "result1.xlsx", "sheets": ["温度", "水分浓度"], "time_unit": "s", "time_step_s": 1, "time_start_s": 0, "time_end_s": 1800, "radius_unit": "cm", "radius_grid_cm": {"start": 0, "end": 2, "step": 0.1}, "paper_times_s": [100,300,600,900,1200,1500,1800], "paper_radii_cm": [0,0.5,1,1.5,2]},
        {"file": "result2.xlsx", "sheets": ["温度", "水分浓度"], "time_unit": "s", "time_step_s": 1, "time_start_s": 0, "time_end_rule": "全程保存至Q3达标时刻；前3h单独可提取，最终提交体积实测后明确口径", "radius_unit": "cm", "radius_grid_cm": {"start": 0, "end": 2, "step": 0.1}, "paper_times_h": [0.5,1,1.5,2,2.5,3], "paper_radii_cm": [0,0.5,1,1.5,2]},
        {"file": "result3.xlsx", "sheets": ["Sheet1"], "variable": "C", "time_unit": "s", "time_step_s": 60, "time_start_s": 0, "time_end_rule": "全域达标末时刻另加末行，即使不整除60s", "radius_unit": "cm", "radius_grid_cm": {"start": 0, "end": 2, "step": 0.1}, "paper_time_step_h": 6, "paper_radii_cm": [0,0.5,1,1.5,2], "paper_add_endpoint": True},
        {"file": "result4.xlsx", "sheets": ["Sheet1"], "variable": "C", "time_unit": "s", "time_step_s": 60, "time_start_s": 0, "time_end_rule": "全域达标末时刻另加末行", "radius_unit": "cm", "radius_grid_rule": "0,0.1,...<=R(t)，另含真实表面；r>R(t)为域外，留空而非0", "paper_time_step_h": 6, "paper_radius_step_cm": 0.5, "paper_add_surface": True, "paper_add_endpoint": True},
    ]
    out = []
    for i in range(4):
        qid = f"Q{i+1}"
        validations = COMMON_VALIDATION.copy()
        if i >= 1:
            validations += ["50°C/0.05平台、末值、末1h均值延拓与h/beta情景对照"]
        if i >= 2:
            validations += ["全域最大值而非均值判定；中心是否为最大值逐时验证，不能直接假定", "分别报告事件插值误差、时间步误差、空间误差及模型情景差异"]
        if i == 3:
            validations += ["附录4固定半径与收缩半径同物性对照；Q3/Q4跨物性对比单列", "半径数据0—72h覆盖检查、物理坐标输出映射和域外空值核验"]
        out.append({"id": qid, "title": names[i], "summary": summaries[i], "task_type": "机理建模/非线性传热传质仿真", "source": {"path": "problem_files/CUMCM2026Problems/A题/A题.pdf", "pages": source_pages[i]}, "inputs": ["题给圆柱尺寸与均匀初值", "附件1时间、烘房温度与水分", f"附录{2 if i == 0 else 4 if i == 3 else 3}物性"] + (["附件2时间与药材半径"] if i == 3 else []), "outputs": [summaries[i], output_specs[i]["file"], "未舍入机器可读解与验证证据"], "output_specification": output_specs[i], "constraints": ["内部用SI单位；D(T)的T为K；导出温度为°C、距离为cm", "所有显示结果四位小数，内部运算与阈值判断保留全精度", "原始输入和结果模板不覆盖"] + (["全程统一附录3，不先运行附录2再切換"] if i in [1,2] else []) + (["全域C严格低于0.15kg/kg"] if i >= 2 else []), "independent_variables": ["t:时间/s", "r:物理径向距离/m"] + (["x=r/R(t):材料径向坐标/1"] if i == 3 else []), "dependent_variables": ["T(r,t):温度/K", "C(r,t):干基含水率/kg水每kg干物质"] + (["t*:全域达标时间/s（最后转h）"] if i >= 2 else []), "recommended_models": {"baseline": baselines[i], "improved": mains[i]}, "validation_plan": validations, "figure_suggestions": figure_titles[i], "data_support": {"environment_observed_s": [0,14400], "radius_observed_s": [0,259200] if i == 3 else None, "interior_ground_truth": False, "assumptions_needed": [a["id"] for a in ASSUMPTIONS if not (i != 3 and a["id"] == "A06")], "profile_status": "S1引用经SHA256匹配的既有附件结构检查；S3必须重新加载并形成正式审计"}, "model_selection_status": "由主代理依据题意与可解释性记录选择理由，尚非用户人工核签"})
    return out


def s1():
    import pymupdf
    assets = provenance()
    S1.mkdir(parents=True, exist_ok=True)
    with pymupdf.open(ROOT / assets[0]["path"]) as pdf:
        pages = [{"page": i+1, "text": p.get_text()} for i,p in enumerate(pdf)]
    assert len(pages) == 4
    source_text = "\n\n".join(f"--- 第{p['page']}页 ---\n{p['text']}" for p in pages)
    (S1 / "A题_原文抽取.txt").write_text(source_text, encoding="utf-8")
    data_files = []
    for item in assets[1:]:
        data_files.append({"path": item["path"], "sha256": item["sha256"], "role": item["role"], "usable_for_modeling": item["usable_for_modeling"], "sheets": item.get("sheets", []), "profile_source": "paper_output/context/active_problem_scope.json; notes/selection-evaluation/2026-09-10/A附件_只读核对.json", "profile_is_full_s3_audit": False})
    qs = questions()
    analysis = {**base(), "problem_id": "A", "problem_title": "药材的烘干问题", "source_dir": "problem_files/CUMCM2026Problems/A题", "scope_file": "paper_output/context/active_problem_scope.json", "scope_sha256": digest(OUT / "context/active_problem_scope.json"), "input_manifest_sha256": digest(OUT / "input_manifest.json"), "status": "S1_CONTRACT_READY_NOT_NUMERICALLY_VALIDATED", "documents": [{"path": assets[0]["path"], "sha256": assets[0]["sha256"], "pages": 4, "extracted_text": "paper_output/step1/A题_原文抽取.txt", "extraction_sha256": digest(S1 / "A题_原文抽取.txt"), "formula_visual_review_reference": "notes/A-principles/A题_公式推导与原理讲解.md; 原PDF第3—4页须本轮复核"}], "data_files": data_files, "questions": qs, "question_relationships": [{"from": "Q1", "to": "Q2", "relation": "复用守恒结构和数值框架，更换整组物性从相同初值重算；并非1800s处拼接"}, {"from": "Q2", "to": "Q3", "relation": "同一动态模型和全程解上添加全域最大含水率阈值事件"}, {"from": "Q3", "to": "Q4", "relation": "同一达标任务，在附录4新物性与实测收缩域上重建守恒闭合；跨问差异包含两类变化"}], "given_geometry_and_initial_conditions": {"L_m": 0.25, "R0_m": 0.02, "T0_C": 28, "T0_K": 301.15, "C0_kg_per_kg_dry": 2.55, "C_threshold": 0.15, "status": "题给事实"}, "parameter_sets": PARAMETER_SETS, "empirical_formula_count": {"explicit_equations_in_appendices": 9, "basis": "附录2的D一条，附录3和附录4各四条；尺寸、初值、五个常参数及模型新增守恒/边界/离散公式另计，不能称九条覆盖全部建模公式"}, "global_constraints": ["仅A题7份资产，4份结果模板不得作为训练或测量数据", "数据→守恒及假设→基线与选型→实际计算与验证→冻结→写作", "正文表格与附件时空采样不同，全部保留四位小数，不能降低要求以缩减体积", "Python正式模型须通过Visual Studio GUI复现；AI审读与CLI成功不替代人工核验", "参考9月10日赛前说明会的PDF/支撑文件20M等要求；此阶段未完成格式终审"], "assumptions": ASSUMPTIONS, "ambiguities": AMBIGUITIES, "data_coverage": {"attachment1": {"observations": 241, "step_s": 60, "coverage_s": [0,14400], "fields": [{"name": "时间", "unit": "s", "role": "边界驱动自变量"}, {"name": "温度", "unit": "°C", "role": "烘房温度边界，不是内部真值"}, {"name": "水分浓度", "unit": "kg/kg", "role": "环境水分观测，材料平衡映射需假设"}]}, "attachment2": {"observations": 145, "step_s": 1800, "coverage_s": [0,259200], "fields": [{"name": "时间", "unit": "s", "role": "收缩轨迹自变量"}, {"name": "半径", "unit": "cm", "role": "移动外边界R(t)"}], "last_radius_cm": 1.198}, "training_target_available": False, "data_support_limit": "可支撑给定工况与几何下的条件性机制计算、插值及数值验证；无法从附件唯一识别吸附等温线、潜热闭合、内部速度或实测预测误差"}, "recommended_models": {q["id"]: q["recommended_models"] for q in qs}, "validation_plan": COMMON_VALIDATION, "figure_suggestions": {q["id"]: q["figure_suggestions"] for q in qs}, "data_requirements": [], "external_data_decision": {"required_for_baseline": False, "reason": "题面未要求搜集外部数据，给定经验物性足以建立显式假设下的有效模型；内部真值不可凭外部类似药材代替", "optional_primary_sources": ["扩散及Robin-Bessel理论", "干基物料守恒与移动材料坐标", "若采用潜热/吸附替代模型则查有材料适配性的原始来源并独立记录"]}, "next_outputs": {"model_route": "paper_output/plan/model_route.json", "data_plan": "paper_output/plan/data_plan.json", "load_report": "paper_output/data_cleaned/load_report.json"}}
    write_json(S1 / "problem_analysis.json", analysis)
    write_json(S1 / "D_模型路线.json", [{"question_id":q["id"], "title":q["title"], "task_type":q["task_type"], "baseline_model":q["recommended_models"]["baseline"], "improved_model":q["recommended_models"]["improved"], "validation_plan":q["validation_plan"], "figure_suggestions":q["figure_suggestions"], "assumptions":q["data_support"]["assumptions_needed"]} for q in qs])
    a = ["# A题题意对齐\n", "本文件为正式S1审题契约。题面及7份资产哈希已逐一核对；尚未运行生产求解，不包含真实模拟结果。", "## 四问之间的关系", "Q1是短时固定圆柱基线；Q2复用守恒结构但从初值开始全程使用附录3；Q3在Q2解上寻找全域达标事件；Q4同时更换附录4物性并加入半径收缩。Q4对Q3的差异不能单独归因于收缩。", "## 逐问输入输出", "| 问题 | 输入和模型增量 | 可量化输出 | 关键验收 |\n|---|---|---|---|"]
    for q in qs:
        a.append(f"| {q['title']} | {'；'.join(q['inputs'])} | {q['summary']} | 数值收敛、通量/质量守恒、模板采样；无内部实测真值 |")
    for q in qs:
        a += [f"## {q['title']}", f"- 基线：{q['recommended_models']['baseline']}", f"- 主模型：{q['recommended_models']['improved']}", f"- 自变量：{'；'.join(q['independent_variables'])}。因变量：{'；'.join(q['dependent_variables'])}。", f"- 输出契约：`{q['output_specification']['file']}`，详见JSON；内部全精度、展示四位小数。", "- 验证：" + "；".join(q["validation_plan"])]
    a += ["## 数据能支撑到哪里", "附件1的241条记录仅覆盖0—4h，每60s一个环境点；附件2的145条记录覆盖0—72h，每1800s一个半径点。两者都是驱动条件，不是药材内部温度或含水率观测。由数据直接支持的是边界和尺寸；从一维几何、等效平衡映射、材料速度场和显热闭合起就已经加入假设，绝不是等到4h后才开始假设。插值后的逐秒驱动是模型输入重采样，不能增加独立实测样本数。4h后的温湿平台、72h后的任何半径外推必须单独标记。", "## 模型假设起点与影响"]
    a += [f"- **{v['id']} {v['title']}**：{v['statement']} 起点：{v['start']}。依据：{v['basis']}。限制：{v['limit']}。检验：{v['validation']}。" for v in ASSUMPTIONS]
    a += ["## 待解释口径"] + [f"- **{v['id']}**：{v['issue']}。处理：{v['resolution']}。状态：{v['blocks']}。" for v in AMBIGUITIES]
    a += ["## 公式和放缩交接", "题面附录显式给出9条经验式：1+4+4。题给常数和建立模型需要的守恒、通量、边界、坐标变换、离散及检验公式另外编号，完整清单由物理推导交接文件给出；不声称经验式的拟合系数可由守恒定律推导。", "放缩首先区分单位换算、无量纲化、空间域映射和不等式界估计。SI单位換算为必要操作；Q4采用x=r/R(t)固定移动域；T/C数值缩放用于误差控制，恢复后按物理单位导出。D(C,T)上下界仅用于量级/可比较模型分析，不能把非线性PDE的逐点解排序当作当然结论。无需对环境列做机器学习式z-score来替代物理模型。"]
    (S1 / "A_题意对齐.md").write_text("\n\n".join(a)+"\n", encoding="utf-8")
    outline = """# A题论文大纲（结构规划，尚未进入正式写作）

1. 摘要：逐问给出任务、模型、真实结果及检验；结果未冻结前仅写结构，不填写占位数值。
2. 问题重述与四问递进关系：短时基线→全程耦合→阈值事件→收缩与物性变化。
3. 数据审计与适用范围：7份A题资产、字段/单位/时间范围、模板角色、无内部真值、4h与72h界限。
4. 假设与符号：圆柱径向、有效显热、干基与干骨架、等效平衡含水率、工况延拓、同比收缩；每项写依据、起点、影响。
5. 统一物理模型：薄壳热/水守恒、Fourier/Fick本构、初始及Robin边界、九条题给经验物性、干基/湿基转换；每个式子先写用途和自/因变量，再推导和解释。
6. 问题一：固定域非线性扩散与常热物性，Bessel常系数基准；正文表1/2与result1输出。
7. 问题二：附录3全程热湿耦合、分段环境驱动和延拓；正文表3/4、result2范围及文件体积说明。
8. 问题三：全域max(C)严格阈值、连续事件与首个达标输出时刻；正文表5与result3。
9. 问题四：附件2插值、材料守恒与移动域变换、附录4；同物性固定/收缩对照，正文表6与result4表面/域外表示。
10. 数值求解及验证：有限体积、隐式非线性积分、中心与表面处理、离散守恒、Bessel误差、空间/时间独立收敛、阈值定位及未舍入数据。
11. 不确定性和模型边界：环境延拓、Ceq映射、h/beta、潜热替代、端面效应；明确数值误差与结构/参数不确定性不同。
12. 逐问结论、优点与局限：只从冻结证据写结论；不报告不存在的实测拟合精度。
13. AI使用声明（置于参考文献前）与参考文献：题面、数据、主要原始理论来源、实际工具使用记录。
14. 附录与支撑：关键源码、参数、输入输出哈希、实际运行和VS GUI复现记录、人工核验状态、扩展图表、完整结果文件；提交匿名及20M体积单独核验。

全文格式按9月10日说明会最新优先级执行：正文不超过30页（AI声明及参考文献计入），摘要/附录另计；摘要至参考文献校内至少15页，20—30页为建议，不照搬默认三问/六段模板。完整正文必须等待S6真实证据门禁通过。
"""
    (S1 / "B_论文大纲.md").write_text(outline, encoding="utf-8")
    rubric = """# A题评分点与证据对齐

以下是团队内部证据清单，并非宣称掌握官方未公布的分数或评分权重。

| 评分关注点 | 必需证据 | 论文位置 | 不可替代的验收 |
|---|---|---|---|
| 题意覆盖 | 4问输入输出映射、表1—6和result1—4 | 问题重述及逐问结果 | 不遗漏Q4表面、Q2全程、严格全域阈值 |
| 公式合理 | 薄壳守恒→本构→边界→数值，全式自/因变量和单位 | 统一模型与各问 | 经验系数无伪推导，D使用K和正确除号 |
| 数据可靠 | 原始SHA256、清洗/插值日志、4h/72h界限 | 数据审计 | 模板不能作观测，插值不伪增样本 |
| 干基与收缩守恒 | 干物質/水分守恒式、rho_d闭合、材料坐标 | Q4与模型检验 | rho(C)解释一致，不重复平流或稀释 |
| 数值可信 | Bessel常系数基准、质量残差、独立空间和时间收敛 | 数值检验 | 实际运行、有限数值；不能只贴方程 |
| 有效比较 | 同附录4固定/收缩对照、冻结物性对照 | Q2/Q4及综合分析 | 跨问两种变化不得单因果归因 |
| 不确定性 | 环境延拓、Ceq、h/beta、端面/潜热情景 | 敏感性和局限 | 情景范围不冒充统计置信区间 |
| 可复现 | 代码/配置/输入输出哈希、退出码、VS GUI与人工核验 | 附录与支撑 | CLI、GUI、人工审查三者分开 |
| 表达与合规 | 符号索引、图表引用、AI记录、匿名和大小检查 | 全文及终审 | 真实结果冻结后写作；逐页渲染另验 |
"""
    (S1 / "C_评分点对齐表.md").write_text(rubric, encoding="utf-8")
    print("S1 A-specific contract written; 4 questions, 7 verified assets, no numerical execution.")


def s2():
    provenance()
    analysis = read_json(S1 / "problem_analysis.json")
    assert [q["id"] for q in analysis["questions"]] == ["Q1","Q2","Q3","Q4"]
    S2.mkdir(parents=True, exist_ok=True)
    route_questions = []
    for q in analysis["questions"]:
        qid = q["id"]
        formulas = ["C=m_w/m_d，湿基w=C/(1+C)", "rho*cp*(T_t+u*T_r)=(1/r)*d_r(r*k*T_r)", "rho_d*(C_t+u*C_r)=(1/r)*d_r(r*rho_d*D*C_r)", "T_r(0,t)=C_r(0,t)=0", "-k*T_r(R,t)=h*(Ts-Tinf)", "-D*C_r(R,t)=beta*(Cs-Ceq)", "T(r,0)=301.15K，C(r,0)=2.55", "附录对应物性表达式，D指数用除以C及绝对温度T_K", "环形控制体积守恒、面通量与隐式时间积分；物性位于导数内", "Bi_h=h*R/k、Bi_m=beta*R/D、Fo_h=alpha*t/R²、Fo_m=D*t/R²"]
        if qid == "Q4":
            formulas += ["x=r/R(t)，u=x*R'(t)，rho_d=rho_d0*(R0/R)^2", "固定材料x下T_t=[1/(rho*cp*R²*x)]*d_x(x*k*T_x)", "固定材料x下C_t=[1/(R²*x)]*d_x(x*D*C_x)", "两式材料平流与网格速度相消；不可再额外加xR'/R平流", "附录4固定/收缩时长差和相对变化率；跨物性比较另列"]
        if qid in ["Q3","Q4"]:
            formulas += ["M(t)=max_{0<=r<=R(t)}C(r,t)，t*=inf{t:M(t)<0.15}", "阈值连续交叉估计、严格首达输出时刻、未舍入余量分别记录"]
        route_questions.append({"question_id": qid, "title": q["title"], "task_type": q["task_type"], "core_goal": q["summary"], "baseline_model": q["recommended_models"]["baseline"], "main_model": q["recommended_models"]["improved"], "model_id": {"Q1":"cylindrical_fixed_nonlinear_diffusion", "Q2":"cylindrical_fixed_coupled_heat_moisture", "Q3":"whole_domain_drying_event", "Q4":"cylindrical_material_shrinkage_coupled"}[qid], "backup_models": ["常物性Bessel基准，只验证可解析边界与常系数情景", "二维轴对称端面或表面潜热替代情景，另标物理闭合与数据要求"], "model_reason": q["summary"] + "采用题给传递系数与经验物性直接建立守恒PDE；附件缺内部真值，黑箱预测或泛化趋势代理无可训练/可验证依据。", "formula_requirements": formulas, "parameter_set": "Q1" if qid == "Q1" else "Q4" if qid == "Q4" else "Q2_Q3", "validation": q["validation_plan"], "figures": [{"figure_id":f"fig_{qid.lower()}_{i+1}", "title":title, "purpose":f"支撑{qid}真实模型结果或独立验证", "expected_path":f"paper_output/figures/fig_{qid.lower()}_{i+1}.png", "status":"planned_not_generated"} for i,title in enumerate(q["figure_suggestions"])], "paper_sections": [q["title"]+"模型建立", q["title"]+"结果分析", q["title"]+"模型检验"], "output_contract": q["output_specification"], "assumptions": q["data_support"]["assumptions_needed"], "implementation": {"language": "Python", "libraries_planned": ["numpy", "scipy"], "method": "圆柱环形有限体积、面通量、隐式积分；常系数Bessel基准；耦合非线性需收敛/容差证据", "production_entry": "paper_output/code/modeling/run_modeling.py", "source_status": "主代理另行编写，本契约不声称已执行", "visual_studio_reproduction": "required_pending", "human_review": "pending"}, "acceptance_metrics": ["Bessel最大/相对误差（仅可解析对照，不是实测精度）", "空间与时间加密下关键表格/时长变化", "水分质量守恒相对残差", "非有限/负含水率/域外伪数值计数必须为0", "逐问输出时间半径网格及四位小数显示完整性"]})
    route = {**base(), "source": "paper_output/step1/problem_analysis.json", "source_sha256": digest(S1 / "problem_analysis.json"), "problem_id": "A", "selection_rationale": "可解释守恒PDE先行，新增耦合和移动域均由题目逐问要求驱动；选择理由已记录，用户人工核验仍待完成", "status": "S2_ROUTE_READY_NOT_NUMERICALLY_VALIDATED", "questions": route_questions, "shared_assumptions": ASSUMPTIONS, "ambiguities": AMBIGUITIES, "parameter_sets": PARAMETER_SETS, "data_plan_handoff": {"required_skill": "data-cleaning-and-visualization", "scope": "仅A题7资产；2输入数据与4模板分开", "fresh_load_report": "paper_output/data_cleaned/load_report.json", "no_data_leakage": "环境与半径不是内部T/C标签；4h以后延拓不是观测"}, "experiment_plan": {"budget_mode": "CPU有限预算，autoresearch附加实验不替代主流程", "deadline_utc": "2026-09-10T19:00:00+00:00", "deadline_beijing": "2026-09-11T03:00:00+08:00", "requested_nominal_radial_cells": 400, "grid_sequence_candidate": [100,200,400], "time_step_strategy": "按实际求解器选择1、2、4秒或容差阶梯；分别做空间和时间研究，输出每1秒不等于积分步长必为1秒", "priority_order": ["S3数据审计", "可解释短时与Bessel基准", "四问实际解", "干物质及水分守恒", "空间时间收敛", "同物性收缩对照", "边界延拓与参数敏感性", "端面和潜热替代", "模板完整性与压缩大小", "VS GUI复现及核心代码人工交接"], "stop_rules": ["物理守恒或正性失败则修模型/算法后重新运行", "任何模型、输入、参数变化重算受影响输出", "禁止为了赶进度用占位数值或未运行图填充结果", "预算不足时明确未执行项；不能将计划改为PASS"]}, "scaling_policy": {"unit_conversion": "cm→m、°C→K（D用K）、s→h仅在展示；必须", "moving_domain": "Q4 x=r/R(t)固定材料域；作用对象为自变量/空间域，并同步变换导数及边界", "nondimensionalization": "以R0、温差尺度、C0及时间尺度形成无量纲数用于量级和误差控制；不改变物理输出", "inequality_bounds": "可在所算T/C范围推D上下界估算扩散时间尺度；要比较PDE解须证明同初边界与比较原理适用，不将系数上下界直接当精确时长界", "normalization_not_required": "不为物理模型套机器学习特征标准化；如数值缩放T/C，必须记变换及反变换"}, "official_evidence_requirements": {"S5": ["model_results.json", "metrics.json", "conclusions.json", "tables.json", "run_manifest.json", "actual_usable_figures"], "S6": "真实证据和输入新鲜度PASS后才进入正式写作", "independent_review": "所有主要公式、边界和守恒闭合以及数值结果须独立检查", "no_empirical_validation_claim": "当前无内部实测，验证仅解析/离散/物理一致性与条件性敏感性"}}
    write_json(S2 / "model_route.json", route)
    rubric_items = []
    for q in route_questions:
        for point, evidence, rule in [
            ("题意覆盖", [q["core_goal"],q["output_contract"]["file"]], "采样、坐标、变量、达标及显示口径与原题对应"),
            ("模型合理性", q["formula_requirements"], "守恒、本构、初边值闭合清晰；每式用途和自/因变量定义明确"),
            ("结果可信", q["acceptance_metrics"], "报告实际计算的指标及局限；无内部实测不能宣称实测预测准确率"),
            ("图表证据", [f["figure_id"]+": "+f["title"] for f in q["figures"]], "每张已采用图存在、与冻结结果一致、正文引用并解释；未运行图不得作结果"),
            ("可复现", ["输入/源码/配置/输出哈希", "运行退出码及耗时", "VS GUI证据", "用户人工审查状态"], "三类执行/复現/审查状态分别记录，不能互相替代"),
        ]:
            rubric_items.append({"rubric_point":point, "question_id":q["question_id"], "evidence_required":evidence, "paper_location":q["paper_sections"], "qa_rule":rule, "evidence_status":"planned_pending_actual_execution"})
    rubric = {**base(), "source":"paper_output/plan/model_route.json", "source_sha256":digest(S2 / "model_route.json"), "rubric_status":"内部质量映射；非官方分值及权重", "items":rubric_items}
    write_json(S2 / "rubric_alignment.json", rubric)
    strategy = ["# A题模型路线与证据策略", "本文件记录S2路线和后继验收。它是计划契约，不是运行、实测拟合或论文成稿证明。", "## 路线选择", "数据仅提供边界、经验物性及尺寸；主路线必须回答热传导、水分扩散、双向物性耦合、全域达标与收缩。选择守恒PDE和有限体积直接承接这些结构。第一问热水可在基准闭合下分别求解，第二问起通过物性耦合；第三问是事件检测，第四问是新物性下的材料移动域。", "## 最小可信证据集", "先完成A题范围的S3新鲜加载，再依次实际运行常系数Bessel核验、非线性四问、守恒和空间/时间加密。N=400是图中期望计算设置，必须通过实际网格研究确认够用；用户图片中的完成标记不算本次运行证据。每秒导出与内部积分步长分开配置并核验。", "## 四问证据落位"]
    for q in route_questions:
        strategy += [f"### {q['question_id']} {q['title']}", f"任务：{q['core_goal']}", f"主模型：{q['main_model']}。对照：{q['baseline_model']}。", "结果："+q["output_contract"]["file"]+"及未舍入机器可读数组。关键指标："+"；".join(q["acceptance_metrics"])+"。", "论文位置："+"；".join(q["paper_sections"])+"。"]
    strategy += ["## 不确定性分开报告", "数值误差来自网格、时间积分、非线性容差与阈值插值；模型情景差异来自环境延拓、Ceq映射、h/beta、端面与潜热；参数/结构影响不是无观测真值下的统计置信区间。Q4同附录4物性下固定与收缩比较才反映尺寸作用；与Q3的比较需明确同时改了物性。", "## 假设起点和数据边界", "一维几何、有效显热、干物质骨架和等效平衡边界都是从模型建立起便引入的闭合。附件1可直接驱动前4h，此后平台取值须标为延拓；附件2可驱动前72h，此后不得静默外推。当前没有内部T/C真值，不能为追求评分补造校准数据或RMSE。", "## 结果冻结和交付", "记录每次运行输入、脚本、配置、输出哈希；模型或数据变化触发重新计算。正式Python需VS GUI可视复现，核心代码由用户人工审查，两项分别保留状态。只有S6真实证据门禁通过后进入正式论文；本轮用于用户的建模MD可以如实总结已完成/未完成内容，不能伪装正式定稿。", "## 立即后继", "主代理统一更新memoryskill及workflow_memory；本子代理不并发写主记忆。调用data-cleaning-and-visualization前运行对应guard，按A范围形成load_report、data_plan、visualization_plan、figure_index。随后编写题意专属源码，禁止采用共享通用simulation趋势代理替代物理方程。"]
    (S2 / "scoring_strategy.md").write_text("\n\n".join(strategy)+"\n", encoding="utf-8")
    print("S2 A-specific model route and rubric written; all execution/GUI/human-review statuses remain pending.")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--stage", choices=["s1","s2"], required=True)
    args = p.parse_args()
    {"s1":s1,"s2":s2}[args.stage]()
