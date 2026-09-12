"""Freeze scoped editorial QA and its active-workspace handoff."""
from pathlib import Path
import json,hashlib,datetime
ROOT=Path.cwd();assert ROOT.as_posix()=='D:/Document/数学建模/2026CUMCM'
QA=ROOT/'paper_output/qa/manuscript_revision_20260912'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=read(QA/'final_structural_check.json');docsha=base['docxSha256']
assert sha(ROOT/base['docx'])==docsha
body=read(QA/'final_body_preservation.json')
assert body['final']['sha256']==docsha and all(body['checks'].values())
report_files=['final_body_preservation.json','final_structural_check.json','compact_appendix_final_review.json',
 'visual_pages_1_10.json','visual_review_body_11_22_v5.json','visual_review_appendix_23_31.json']
for name in report_files:
    data=read(QA/name)
    assert docsha in json.dumps(data),name
middle=read(QA/'visual_review_body_11_22_v5.json')
assert str(middle.get('status','')).startswith('PASS'),middle.get('status')
log=ROOT/'paper_output/results/experiments/manuscript_revision_20260912_log_review.json'
assert read(log)['status']=='PASS_SCOPED_LOG_REVIEW'
record={**base,'status':'PASS_SCOPED_EDITORIAL_REVISION','generatedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'allPagesVisuallyReviewed':True,'visualMethod':'All 31 v4 pages actually viewed. Six changed v5 pages re-viewed; remaining 25 images have identical SHA256.',
 'reports':[{'path':str((QA/n).relative_to(ROOT)),'sha256':sha(QA/n)} for n in report_files],
 'autoresearchLogReview':{'path':str(log.relative_to(ROOT)),'sha256':sha(log),'validHistoricalTrials':42,'machineChecks':456,'newPdeRuns':0},
 'sourceOfTruth':'The user-edited source snapshot is authoritative for preserved body content; this revised DOCX is the latest editorial delivery.',
 'mainWorkflowScope':'Existing S8/DONE evidence binds the earlier canonical manuscript. This supplemental QA binds the user-edited typography/appendix revision; no claim of rerunning original model gates.',
 'pendingUserWork':['Create and insert six figures using the drawing guide; recheck pagination after insertion.','Review comments, models and source excerpts as a team.'],
 'musicReminder':'Explicitly authorized; execute Computer Use after file work and Git sync, verify actual playing state in UI.'}
(QA/'final_revision_audit.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
(QA/'final_revision_audit.md').write_text(f'''# 用户修改稿的最终编辑审查

判定：PASS_SCOPED_EDITORIAL_REVISION。交付 `{base['docx']}`，SHA256 `{docsha}`。

真实渲染31页：摘要1页、正文含AI声明与参考文献21页、附录9页，从第23页开始。满足用户本轮正文20–30页口径。35个编号公式、161个原生可编辑数学对象、9张表、6处绘图说明；未嵌入图片，制图由用户完成。

正文保留以用户452310字节快照为准。192段、9表、19个原公式逐项核对；只调整6处绘图前缀和符号表1处重复乘点。用户正文[3]–[6]及引文句保留，缺失文献仅加4条批注；文献表仍是用户留下的[1][2]。维护后共10条批注，锚点检查通过。

变量与必要上下标采用Times New Roman，并按数学变量、说明性下标、函数和单位区分斜体与正体。上取整符号做了5种实际小样并选择可读方案；最终表头小时单位h和边界函数K_p已再次独立核实。原中文标题字体与单栏布局保持。

附录A–C保留物理守恒、有效密度解释、随动坐标、有限体积、Kirchhoff势、Jacobian、隐式时间推进、阈值判定和数值检查的关键推导；D为6段117行算法摘录，与来源逐行一致。完整源码仍在工作区保留，摘录不作为可独立运行文件。所有片段各自在同一页内。

autoresearch采用实际实验日志分析模式：42条有效记录与另外两次资源中止分开，456项机器检查通过，6份时间NPZ已实际重新归约。附录误差数值有来源；不以时间更短作为算法优胜，不把缺失/失败指标记为零误差。本轮未新跑PDE或GPU训练。

31页都已实际目视：v4逐页完成，v5的11、12、14、17、18、28页重新查看，其余25页图SHA完全一致。无裁切、重叠或不可读公式；代码长行的软折行及末页D.6完整片段留白可接受。第7页句末引用换行、第10页分段左花括号较小但完整可读，留作轻微版式备注。

绘图说明已在正文第9、11、12、15、18、19页黄色标识，配套清单说明数据、单位和假设。插图后须再次核对20–30页正文范围。

本次PASS只覆盖所列编辑与检查范围，不替代团队人工核实、当前源码GUI复现、真实材料精度验证或旧支撑ZIP独立运行修复。原S8门禁仍绑定旧规范稿，最新修订入口以本记录和workflow_memory.latest_docx_revision为准。
''',encoding='utf-8')
memory=ROOT/'memoryskill.md';s=memory.read_text(encoding='utf-8')
heading='## 用户修改稿公式排版与精简附录（2026-09-12，最新）'
section=f'''{heading}

- 当前交付 `paper_output/paper/A题_论文_公式规范与精简附录版.docx`，SHA256 {docsha}；用户前版与旧规范源保留，今后正文继续编辑优先从本修订版开始。
- 用户再次明确正文20–30页，摘要/附录另计；当前实渲染31页＝摘要1＋正文含AI/参考文献21＋附录9。35编号公式、161可编辑OMML、9表、6黄色绘图位置，无实际插图。图由用户制作，清单 `paper_output/paper/绘图说明与位置清单.md`，当前页9/11/12/15/18/19，插图后复核页数。
- 正文权威快照SHA 0c8bb744b568fd751dc0ad0d883f69b5f895a74b9f8fcb3666b99975db7b05ee；192段/9表/19公式一致，只有六处标记前缀与一格重复乘点修正。正文修改（25cm、骨架限定、BDF、作者等）保留。
- 用户引用最新答复“维持删除，只加批注标明未对应的引用”优先：不恢复文献[3]–[6]，正文原标号/句子保留并加4条批注。维护旧批注后共10条；不能再按早先较宽“删除有关引用”解释删正文。
- IEEE/厦大规范仅作数学字体与下标参考，不套整套论文版式；变量TNR斜体，单位/函数/说明性下标正体，ceil实际5方案检查修复。附录保留关键推导/数值过程，仅6段117行源码片段，完整源码在原工作区保留。精简要求覆盖旧全量源码附录安排。
- autoresearch本轮实际日志分析42条有效trial，456项检查通过，六时间NPZ重新归约；两资源中止单列，未重新跑PDE/训练。附录轴心面零通量及气固指标假设表述已修正，无生产模型/数值改变。
- 全31页实际视觉检查，v5变化6页复看、其余25页SHA一致。独立正文语义/代码保真/科学及视觉QA在 `paper_output/qa/manuscript_revision_20260912/final_revision_audit.json`；旧S8只绑定早前规范稿，本修订有单独QA，不扩大为人工签核或旧ZIP修复。
- 用户再次授权全部结束后Computer Use播放Apple Music提醒，须以真实UI状态核实结果；后续不要凭历史成功或打开应用声称播放。本记录在最终音乐动作之前写入，实际结果以本轮工具记录/答复为准。

'''
if heading not in s:
    s=s.replace('## 完整DOCX论文交付（2026-09-12，当前）',section+'## 完整DOCX论文交付（2026-09-12，历史全量代码版）')
memory.write_text(s,encoding='utf-8')
wm=ROOT/'paper_output/context/workflow_memory.json';w=read(wm)
w['latest_docx_revision']={'status':record['status'],'docx':base['docx'],'sha256':docsha,
 'audit':'paper_output/qa/manuscript_revision_20260912/final_revision_audit.json','bodyPages':21,'totalPages':31,
 'scope':record['mainWorkflowScope'],'autoresearchMode':'experiment-log analysis','newPdeRuns':0,'teamHumanReview':'PENDING'}
wm.write_text(json.dumps(w,ensure_ascii=False,indent=2),encoding='utf-8')
wmmd=ROOT/'paper_output/context/workflow_memory.md'
note='\n\n## 最新用户修改稿编辑补充\n\n当前修订另存 `'+base['docx']+'`，实渲染31页（正文21页），独立审查通过。正文仍以用户修改为准；公式排版、精简附录、绘图定位见 `paper_output/qa/manuscript_revision_20260912/final_revision_audit.json`。上方S8/DONE是旧规范稿门禁，不能替代本修订QA；模型未重算、人工签核待完成。\n'
wmmd.write_text(wmmd.read_text(encoding='utf-8')+note,encoding='utf-8')
print(json.dumps({'status':record['status'],'docx':base['docx'],'sha256':docsha,'allPages':31},ensure_ascii=False))
