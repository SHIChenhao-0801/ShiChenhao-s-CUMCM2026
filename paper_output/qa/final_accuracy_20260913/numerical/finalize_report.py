from pathlib import Path
import json,hashlib,datetime
R=Path.cwd();assert R.as_posix()=='D:/Document/数学建模/2026CUMCM'
Q=R/'paper_output/qa/final_accuracy_20260913/numerical'
a=json.loads((Q/'numerical_audit.json').read_text(encoding='utf-8'))
b=json.loads((Q/'evidence_and_claims.json').read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
issues=[{'id':'NUM-01','priority':'P2','type':'appendix_support_path_mismatch','pdf_page':164,'location':'9.2.32 method_comparison.py 源码第11行','issue':'论文仍为固定D盘ROOT，当前支撑采用脚本parents[3]相对根路径。未改变方法或结果，但正文附录不是当前交付源码。','paper_line':'ROOT = pathlib.Path(r"D:\\Document\\数学建模\\2026CUMCM")','support_line':'ROOT = pathlib.Path(__file__).resolve().parents[3]','action':'将附录该一行同步为当前支撑；如更新PDF，重新核对文件哈希和对应页面。'},
 {'id':'NUM-02','priority':'P3','type':'duplicate_abstract_text','pdf_page':1,'location':'摘要“针对问题三”段后半及下一“针对问题四”段','issue':'问题四的材料坐标、51.0906 h、1.2000 cm、域外与表面输出重复两次；数字本身正确。','action':'删除问题三段中提前出现的问题四说明，保留独立问题四段。'},
 {'id':'NUM-03','priority':'P2','type':'outdated_appendix_references','location':'正文的附录A.2、附录A、附录C、附录C.4','issue':'正文仍保留旧分组指引，当前真实章节已为9.1.x。','action':'A.2的密度/收缩解释改指9.1.6；C.4的严格报告时刻改指9.1.13；其他A/C按具体主题映射。详细页码由主代理格式审计合并。'}]
limits=[
 '本轮只读核对与数值约减，无新增全量PDE计算。9,335,598工作簿格、297正文格和21数组全等，是与当前03/04文件哈希仍匹配的既有Windows Sandbox实跑证据；不是本轮重跑。',
 '表8和正文的数值检验是离散一致性与指定模型敏感性，不构成内部温度/含水率实测准确率、真实干燥时长置信区间或连续解严格误差界。',
 '网格全整数秒的历史最大差记录可追溯，但该批全秒空间投影没有全部保留；本轮未全量回放。时间对照已有保存投影与历史复核证据。',
 '经验边界阻力p=2、4对应历史N800事件积分；事件数值存在，现交付旧入口尚未重新完整通过。论文附录已注明接口/方向问题和复现边界，不能说05全部默认高网格检验通过。',
 '论文9.2.36标题明确为compareMatlab.mjs主要部分，省去完整源码155–162行的markdown格式化函数；191行节选其余部分与199行支撑完全相同。节选保留markdown(report)调用，不能作为独立可运行完整文件；完整可运行源码以支撑为准。',
 '35项完整源码中34项逐行一致，另一项仅NUM-01一行路径不同；另外1项是上述明确节选。不能沿用旧“36源码7715行全部一致”结论。',
 '历史MATLAB源码原路径paper_output/code/review_delivery/matlab/runCrossCheck.m已不在；原SHA字节仍保存在comment_sandbox_20260913/before归档。历史MATLAB数值证据仍可溯源，不等于当前去注释源码重新GUI实跑。',
 '没有新增Visual Studio GUI实跑或团队人工代码/论文签核；这些状态仍由主代理单独核实。'
]
model_review=[
 {'topic':'题目覆盖','result':'四问参数组、起始状态、时间/径向输出、全域严格<0.15判据及Q4域外/真实表面约定均有对应实现和结果。Q23从t=0共用附录3轨迹，Q4从t=0使用整组附录4，无Q1拼接。'},
 {'topic':'题给数据','result':'附件1的241个0–14400秒环境点、附件2的145个0–259200秒半径点与清洗CSV逐值相同；温度K和半径m换算在代码与文稿一致。4h后的50°C/0.05明确是平台假设，不是原最后一点50.165°C/0.04986，也非长期实测。'},
 {'topic':'参数与公式','result':'题给三套rho、cp、k、D数值及指数中的a/C和3850/T均与核心properties和Kirchhoff通量匹配；T采用K。D4/D3=0.175exp(0.15/C)，交叉点约0.08606及前后大小关系正确。'},
 {'topic':'移动坐标','result':'干基组分平衡、均匀干骨架、固定长度/同比径向收缩假设下材料坐标抵消平流项；R^-2内部项和R^-1表面导数一致；未重复增加体积浓缩项。有效rho*cp与守恒干密度分开，物理解释边界已明确。'},
 {'topic':'数值方法','result':'环形控制体权重、轴心系数4、表面真实节点、导热调和平均、Kirchhoff势导数、共享通量守恒、状态维数2N+3、Jacobian面量/容量/累计量结构及BDF连续输出与核心代码相符。未发现需要改动已冻结模型的公式错误。'},
 {'topic':'阈值与报告','result':'连续根57.47230195056044/51.09057478683054小时分别选到严格报告57.4724/51.0906小时；未舍入最大含水率0.14999989718225315/0.14999995339076624均严格低于0.15。四位显示0.1500已明确解释。'},
 {'topic':'正文主要数值','result':'27项主要时长、差值、百分比、对照/灵敏度值与表8误差逐项匹配证据；7结果表297格与当前7CSV、final_v6a和PDF完整数值行一致。'}
]
report={'status':'ACTION_REQUIRED','numerical_results_consistent':True,'generated_at_local':datetime.datetime.now().isoformat(timespec='seconds'),'input_files':a['inputs'],'unchanged_at_completion':all(sha(R/x['path'])==x['sha256'] for x in a['inputs']),'evidence_reports':[{'path':str(p.relative_to(R)),'sha256':sha(p)} for p in [Q/'numerical_audit.json',Q/'evidence_and_claims.json']],
 'summary':{'result_table_count':7,'result_cells':297,'docx_result_cells_equal':a['all_297_docx_cells_equal'],'pdf_full_number_rows_found':a['all_pdf_table_rows_found'],'frozen_xlsx_identical':all(x['frozen_equal'] for x in a['four_workbooks']),'frozen_manifest_hash_items':len(b['frozen_run_manifest_rehash']),'frozen_manifest_all_equal':b['all_frozen_manifest_files_match'],'historical_evidence_items':165,'historical_evidence_bytes_available':b['all_165_prior_evidence_bytes_available'],'major_numeric_claims':len(b['major_numerical_claims']),'major_numeric_claims_all_consistent':b['all_major_claims_consistent'],'visual_review_pages':list(range(97,145))},'findings':issues,'model_and_logic_review':model_review,'limitations':limits,'no_submission_changes':True}
(Q/'final_numerical_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['提交前数值、模型及论文—支撑一致性独立核查','审计结论：ACTION_REQUIRED；主要数值与冻结结果一致，尚有附录路径和文字对应问题。','时间：'+report['generated_at_local'],'', '当前审计输入：']
for x in a['inputs']:lines += [x['path']+'，'+str(x['bytes'])+'字节，SHA256 '+x['sha256']]
lines+=['','已核实：','1. 7份正文结果CSV逐字节等于final_v6a；DOCX的7表297格逐格相同，PDF中全部完整数字行均检出。4份正式XLSX逐字节相同。','2. 当前03/04文件与正式Windows Sandbox验收清单及8项证据绑定全部匹配；final_v6a原运行账本118项输入/代码/输出SHA全部匹配。','3. 历史独立数值复核的165项输入：164项原路径SHA一致，1项旧MATLAB源码通过同SHA归档定位，原证据字节均仍存在。','4. 附件1的241行和附件2的145行原数值与清洗CSV无差异；27项主要论文数值/百分比/表8指标均匹配原精度证据。','5. 已逐一查看PDF97–144共48页的12张原尺寸四页拼图；未见截字、重叠、乱码或页脚冲突，所有文字几何框均在纸面内。长源码行自动换行，字号小，查看需放大。','','需要处理：']
for x in issues:lines += [x['id']+' '+x['priority']+' '+('PDF第'+str(x['pdf_page'])+'页，' if 'pdf_page' in x else '')+x['location'],x['issue'],'建议：'+x['action'],'']
lines+=['模型和逻辑复核：']
for x in model_review:lines += [x['topic']+'：'+x['result']]
lines+=['','证据边界：']+limits
lines+=['','本轮未改动论文、支撑材料或模型；没有PDE重算、没有Git操作、没有登记或上传。完整逐项数据见numerical_audit.json、evidence_and_claims.json。']
(Q/'数值与模型独立终审.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8-sig')
print(json.dumps({'status':report['status'],'unchanged_at_completion':report['unchanged_at_completion'],'historical_evidence_bytes_available':b['all_165_prior_evidence_bytes_available'],'report':str(Q/'数值与模型独立终审.txt')},ensure_ascii=False))
