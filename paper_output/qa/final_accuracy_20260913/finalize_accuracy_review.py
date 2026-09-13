from pathlib import Path
from datetime import datetime
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
QA = Path(__file__).resolve().parent
assert ROOT.name == '2026CUMCM'

def read(relative):
    return json.loads((QA / relative).read_text(encoding='utf-8'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

numerical = read('numerical/final_numerical_review.json')
numerical_detail = read('numerical/numerical_audit.json')
claims = read('numerical/evidence_and_claims.json')
support = read('support/support_audit.json')
rules = read('rules/rules_final_audit.json')
pdf = read('pdf_inventory.json')
now = datetime.now().astimezone().isoformat(timespec='seconds')
notice = ROOT / 'reference_materials/contest-admin/20260913提交前最新通知_用户转发.txt'

findings = [
    {'id': 'F01', 'priority': 'P1', 'issue': '当前支撑按内存ZIP测算超出20M，旧ZIP不是当前版本', 'location': '支撑材料目录；根目录支撑材料临时.zip', 'evidence': '138项共42,805,705 B；内存DEFLATE9为21,891,321 B，超过20,000,000和20,971,520两口径。旧ZIP缺35项、55项内容旧、多6项IDE文件。', 'action': '按说明会制作本届最终RAR或ZIP并实际检查大小、内容和完整性；最终包生成前不可拿旧包登记MD5。保留完整必要输出，不凭单位换算宣布达标。'},
    {'id': 'F02', 'priority': 'P1', 'issue': '支撑AI详情DOCX含本队姓名属性', 'location': '支撑材料/AI工具使用详情.docx 的 docProps/core.xml', 'evidence': '作者和最后修改者字段均含本队成员真实姓名；两个提交PDF的作者字段为空，已查图片未发现本队身份。', 'action': '清理DOCX个人属性，或将编辑用DOCX移出最终支撑、保留独立AI PDF；选定文件集合后同步所有清单。按最新通知不添加队伍承诺书。'},
    {'id': 'F03', 'priority': 'P2', 'issue': 'AI记录节选措辞和实例指引需校正', 'location': 'AI工具使用详情.pdf第2–4页及对应DOCX', 'evidence': '第2页论文撰写仍指实例3，实际只剩实例1/2。例1提示词和例2提示/回复部分改写，与本线程保存的原文不逐字相同；PDF与当前DOCX正文2639字符一致。', 'action': '恢复真实原文，或明确标成“提示内容概述/回复内容概述”；删除悬空实例3指引或准确指向现有例子。示例不是必须三则；不据差异推定造假。'},
    {'id': 'F04', 'priority': 'P2', 'issue': '论文和说明清单未跟随当前文件集合更新', 'location': '论文第24页9.0；支撑00_文件清单.txt、00_可用于论文附录的支撑清单.txt；支撑材料文件列表_附录用.docx；支撑补件说明', 'evidence': '当前138项、根目录8项；旧清单写137和7，列DOCX、未列AI PDF。旧补件说明还写6页、三实例、仅DOCX等。', 'action': '若保留两个AI文件改为138/8并补PDF；若最终只留AI PDF则仍137/7但清单必须将DOCX换为PDF。同步说明为当前5页和实际实例数。'},
    {'id': 'F05', 'priority': 'P2', 'issue': '附录源码ROOT一行未与支撑同步', 'location': '论文第164页，9.2.32 method_comparison.py源码第11行', 'evidence': '附录仍为固定D盘绝对ROOT；当前可移植支撑使用脚本所在目录推导根路径。', 'action': '将该行替换为 ROOT = pathlib.Path(__file__).resolve().parents[3]。这是路径一致性修正，未涉及模型或冻结数值。'},
    {'id': 'F06', 'priority': 'P2', 'issue': '正文旧附录A/C章节指引无对应标题', 'location': '论文第5、7、9、13、16、19、20页', 'evidence': '当前实际章节9.1.x；附录公式A.1–A.78仍有对应，应保留。', 'action': 'p5附录A.2→9.1.6；p13/p20 C.4→9.1.13；解析级数→9.1.15–9.1.16；网格/时间/方法→9.1.12及9.1.17；坐标推导→9.1.2、9.1.6–9.1.7。逐项映射见规则报告。'},
    {'id': 'F07', 'priority': 'P3', 'issue': '摘要的问题四重复介绍', 'location': '论文第1页，问题三段后半和下一个问题四段', 'evidence': '两次51.0906 h及1.2000 cm等数字相同，没有数值冲突。', 'action': '问题三段在“得到烘干时长57.4724 h。”处结束，删除该段后面的重复问题四描述，保留下一独立问题四段。'},
]

inputs = []
for p in [ROOT/'论文.pdf', ROOT/'药材热湿耦合模型与干燥时间计算_附录修订版.docx', ROOT/'支撑材料/AI工具使用详情.pdf', ROOT/'支撑材料/AI工具使用详情.docx', notice]:
    inputs.append({'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size, 'sha256': digest(p)})
assert inputs[0]['sha256'] == pdf['sha256'], '论文审计期间已改变，必须重核'
assert inputs[1]['sha256'] == digest(QA/'inputs/药材热湿耦合模型与干燥时间计算_附录修订版.docx')
current_support = {str(p.relative_to(ROOT/'支撑材料')).replace('\\','/'): digest(p) for p in (ROOT/'支撑材料').rglob('*') if p.is_file()}
recorded_support = {f['path'].replace('\\','/'): f['sha256'] for f in support['files']}
assert current_support == recorded_support, '支撑审计期间已改变，必须重核'

evidence_paths = ['numerical/final_numerical_review.json', 'numerical/numerical_audit.json', 'numerical/evidence_and_claims.json', 'support/support_audit.json', 'rules/rules_final_audit.json', 'root_visual_review.json', 'geometry_audit.json', 'references_review.json']
report = {
    'checkpoint_id': 'FINAL_ACCURACY_20260913_CURRENT_PDF', 'generated_at': now,
    'audit_completed': True, 'status': 'FAIL', 'submission_readiness': 'ACTION_REQUIRED',
    'interpretation': '终审核查已完成；计算结果一致，但当前文件集合仍有已定位的提交问题。历史S8不覆盖本次新版PDF。',
    'input_files': inputs, 'input_snapshot_unchanged': True, 'findings': findings,
    'numerical_results_consistent': True, 'docx_result_cells_verified': 297, 'result_workbooks_byte_equal': 4,
    'major_claims_verified': 27, 'frozen_manifest_items_rehashed': 118,
    'historical_evidence_items_recoverable': 165, 'historical_moved_source_items': 1,
    'paper_pages': 186, 'abstract_pages': 1, 'body_including_AI_and_references_pages': 22,
    'body_starts_pdf_page': 2, 'AI_statement_pdf_page': 22, 'references_pdf_page': 23, 'appendix_starts_pdf_page': 24,
    'visual_review': {'paper_pages': list(range(1,187)), 'AI_detail_pages': list(range(1,6)), 'clipping_overlap_missing_glyphs_found': False, 'source_code_font': '密集、较小，需放大阅读', 'visible_content_findings': ['F03','F04','F05','F06','F07']},
    'support_files': 138, 'support_bytes': 42805705, 'zip_memory_estimate': support['zip_memory_estimate'],
    'submission_paper_md5_current_only': pdf['md5'], 'md5_registered_by_agent': False, 'upload_performed': False,
    'new_archive_created': False, 'submission_files_modified': False,
    'latest_notice': {'path': str(notice.relative_to(ROOT)), 'sha256': digest(notice), 'commitment_documents_required_now': False, 'identity_information_prohibited_in_both_deliverables': True},
    'human_review': '团队对核心代码和结论的核实仍待本人确认，区别于按最新通知赛后办理的队伍承诺书；本轮未冒充人工审查。',
    'limitations': ['本轮复核现存运行证据与文件字节，未新跑全量PDE。', 'CLI/沙盒/AI审阅不等于当前源码Visual Studio全量GUI复现或用户已审查。', '模型预测限定于气固映射、4h后平台延拓、有效热容量和同比收缩假设，无内部T/C实测精度。', '历史失败实验保持原状态；补件小网格验证不扩大为全部高网格实验重跑。', '35项完整附录源码34项相同、1项ROOT差异；第36项明确为主要部分，不能称36份全部逐字一致或单独可运行。'],
    'evidence_files': {p: digest(QA/p) for p in evidence_paths},
    'next_actions': ['处理F01–F06，建议同时处理F07', '重新导出PDF并复核改动页与全文页数', '最终文件集合与清单一致、匿名且压缩容量达标', '按说明会办理论文和支撑两项MD5，之后上传同一份文件'],
}
(QA/'final_readiness.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

lines = ['2026高教杯提交材料最终准确性核查', f'核查时间：{now}', '',
 '结论：核查已完成，当前状态ACTION_REQUIRED。已核对的核心数值、4个结果工作簿和运行证据一致；尚不能把当前论文与支撑文件集合认定为可直接提交。',
 '范围：根目录16:09《论文.pdf》186页、15:56附录修订版DOCX、16:06 AI详情PDF/DOCX与当前138项支撑。所有输入在本次审计结束时哈希仍一致。', '',
 '最新通知已执行到核查口径：论文从摘要开始；论文与支撑均不得有队伍信息；队伍承诺书等由校方赛后安排，不是本轮缺项；MD5继续严格依据赛前说明会。通知原文另存reference_materials/contest-admin。', '',
 '已验证的内容',
 '1. 7张结果表297格与7CSV逐格对应，PDF全部结果数值行可定位；4XLSX与final_v6a逐字节一致。',
 '2. 正文27项主要数值、百分比和表8误差指标与原精度证据一致；118项冻结运行账本哈希全部匹配。165项历史证据仍可追溯，其中1项旧MATLAB源码在同SHA归档中找到。',
 '3. 问题三严格报告57.4724 h、问题四51.0906 h，对应未舍入最大含水率0.14999989718225315和0.14999995339076624，均严格小于0.15。',
 '4. 两附件241/145条与清洗CSV逐值一致；03输入/运行证据、05三类适量检验、R绘图14CSV共4627行和6PNG均保持有效绑定。没有因本轮发现而需要改动模型数值。',
 '5. 论文首面摘要，正文22页（PDF2–23，含AI声明和参考），摘要至参考23页，附录从24页开始；AI声明在22页、参考在23页。全文页码连续1–186。',
 '6. 论文186页及AI详情5页全部视觉查看，无可见裁切、叠字、乱码。AI详情PDF和DOCX正文去除页脚后2639字符一致；两PDF及已查截图未见本队姓名/学校身份。',
 '7. 16XLSX、3NPZ、1DOCX通过CRC，7PDF可打开、6PNG完整；42Python静态解析通过。当前支撑没有JSON/MD/压缩包/隐藏IDE/空文件。',
 '8. 7条参考文献与当前书目核对一致，刊方、官方方法文档及注册/馆藏证据见references_review.json；并非宣称全部文献全文重新审读。', '',
 '具体问题与可直接执行的修改']
for f in findings:
    lines.extend([f"{f['id']} [{f['priority']}] {f['issue']}", f"位置：{f['location']}", f"核查事实：{f['evidence']}", f"处理：{f['action']}", ''])
lines.extend(['容量与哈希',
 '当前目录原始容量42,805,705 B；内存ZIP DEFLATE9测算21,891,321 B，约20.8772 MiB。未创建压缩包，未改动支撑；最终RAR/ZIP仍须实际检查。单个result2.xlsx的未压缩大小不是最终压缩包大小，不能以此单独判定失败。',
 f"当前论文PDF MD5：{pdf['md5']}（仅绑定本次核查版本；修改后必须重新计算，不能沿用）。",
 '截至本轮，没有办理MD5登记或上传，也没有生成新的最终支撑压缩包。',
 '按说明会执行北京时间9月13日19:00前登记为建议目标，20:00为硬截止；上传窗口9月13日20:30至9月14日14:00，上传必须与登记哈希对应同一文件。', '',
 '验收边界', *report['limitations'], report['human_review'], '',
 '本轮只保存内部审计、通知、记忆和备份记录，没有修改用户论文或支撑材料。承诺书/队伍签名材料不要求加入本次匿名提交。',
 '报告入口：paper_output/qa/final_accuracy_20260913/final_readiness.json；三个独立分报告见numerical、support、rules子目录。', '',
 '官方规则复核来源：',
 'https://www.mcm.edu.cn/html_cn/node/4cd596519c9eb9fbd866398f6df0caa3.html',
 'https://www.mcm.edu.cn/html_cn/node/fef94648f2836ab6cc81586f4c38512b.html'])
(QA/'最终提交材料核查报告.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')

memory_path = ROOT/'paper_output/context/workflow_memory.json'
memory = json.loads(memory_path.read_text(encoding='utf-8'))
memory['submission_readiness_recheck'] = {
    'checked_at': now, 'audit_status': 'COMPLETED_WITH_ACTION_ITEMS', 'submission_readiness': 'ACTION_REQUIRED',
    'paper_sha256': pdf['sha256'], 'paper_pages': 186, 'support_files': 138,
    'report': 'paper_output/qa/final_accuracy_20260913/最终提交材料核查报告.txt',
    'report_sha256': digest(QA/'最终提交材料核查报告.txt'),
    'machine_report': 'paper_output/qa/final_accuracy_20260913/final_readiness.json',
    'independent_of_historical_s8': True, 'remaining': [f['issue'] for f in findings],
    'commitment_documents_required_now': False, 'md5_registration_verified': False,
    'human_review': report['human_review']}
memory['submission_readiness'] = 'ACTION_REQUIRED'
memory['blockers'] = [f['issue'] for f in findings if f['priority'] != 'P3']
memory_path.write_text(json.dumps(memory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md = ROOT/'paper_output/context/workflow_memory.md'
md.write_text(md.read_text(encoding='utf-8')+'\n## 当前提交版本终审覆盖状态\n\n当前186页论文及138项支撑为ACTION_REQUIRED。上面的历史S8/COMPLETE不表示这份新稿可直接提交。详见final_accuracy_20260913/最终提交材料核查报告.txt；最新通知要求匿名，承诺书等赛后办理，不列为本轮缺项。\n',encoding='utf-8')

mp = ROOT/'memoryskill.md'
previous = mp.read_text(encoding='utf-8')
archive = ROOT/'memory_archive.md'
archive.write_text(archive.read_text(encoding='utf-8')+'\n\n## 2026-09-13 16时最终准确性终审前记忆快照\n\n'+previous+'\n',encoding='utf-8')
principles = previous.split('## 持续有效用户约束')[1].split('## 冻结模型与实际复现范围')[0]
principles = '\n'.join(s for s in principles.splitlines() if not s.startswith('- 用户自己编写独立AI详情'))
frozen = previous.split('## 冻结模型与实际复现范围')[1].split('## 历史交付定位')[0]
latest = '''# 2026 CUMCM 比赛记忆

仅适用于D:/Document/数学建模/2026CUMCM。当前A题《药材的烘干问题》，B题已停止。旧阶段和完整细节存memory_archive.md及各轮QA，不继承为当前提交PASS。

## 最新：2026-09-13 16时最终准确性核查

- 用户要求最后核实论文和所有提交材料。已完成三路独立审计及论文186页、AI详情5页全部视觉检查；状态ACTION_REQUIRED，详细报告paper_output/qa/final_accuracy_20260913/最终提交材料核查报告.txt及final_readiness.json。
- 本轮用户新增转发通知：论文从摘要开始；论文与支撑都不得含队伍信息；承诺书等由校方赛后统一安排，本轮忽略；MD5严格按赛前说明会。原文reference_materials/contest-admin/20260913提交前最新通知_用户转发.txt。不把承诺书或队伍签名材料列为当前缺项；模型/代码团队核实要求仍有效。
- 当前根论文.pdf为16:09、2,549,114B，SHA256 2bb7c6b3fff1151318a46d7a8884e4ad0ec99c202a5faf1ceaf24e893cea347b；DOCX为15:56、1,447,199B，SHA256 7eb8e9ef50e1645baddbf968e4cdd5e5fb48d9914119cc6a07101f4b45e7c757。PDF186页，正文2–23共22页，AI声明22页，参考23页，附录24页；首面摘要、连续页码、无裁切叠字乱码。
- 数值通过：7表297格、4XLSX、27主要数值与冻结一致；118冻结账本哈希全部匹配。165历史证据均可追溯，1旧MATLAB原路径已移但同SHA归档可用。当前03/04与真实沙盒全量证据仍匹配。无需因本轮发现重算模型；本轮没有新跑PDE/VS GUI或人工签核。
- 当前支撑138文件42,805,705B，只有AI DOCX改动和新增AI PDF，其余136项保持。内存ZIP DEFLATE9 21,891,321B，超过20,000,000及20MiB；未压缩。旧支撑材料临时.zip缺35项、55项旧内容、多6IDE，不能用于当前提交。
- 必修：支撑AI DOCX作者/最后修改者含本队姓名，须匿名或移出最终支撑仅留PDF；AI PDF第2页悬空实例3，部分“节选”与保存原文不同应恢复或标概述；两TXT及论文24页仍137/7漏AI PDF，补件说明仍6页/三实例等旧状态。
- 论文必修：164页9.2.32 method_comparison.py第11行应同步ROOT = pathlib.Path(__file__).resolve().parents[3]；正文5/7/9/13/16/19/20页旧附录A/C章节指引同步9.1.x；公式A.1–A.78保留。建议1页摘要问题三段结束后删重复问题四说明，保留独立问题四段。
- 附录源码实况：35份完整源码34份逐行同，1份ROOT一行差；第36份compareMatlab.mjs已标“主要部分”，省8行格式化函数，完整源码在支撑。不能沿用“36份完全相同/全部可独立运行”。
- 支撑完好性：16XLSX+3NPZ+1DOCX CRC、7PDF、6PNG、42Python静态通过；无JSON/MD/压缩包/隐藏IDE/空文件。05两输入及Matplotlib/三类小检验、06R+14CSV4627行+6PNG都继续绑定补件运行；历史失败不改PASS。
- AI详情当前16:06版5页，DOCX与PDF正文去页脚2639字符一致；PDF/内嵌截图无可见本队身份。新授权已允许依据真实记录生成独立AI详情，旧“禁止生成”不再适用于已授权补件；仍不得虚构对话或人工审核。
- 未修改用户论文/支撑、未代压缩、未登记/上传。当前论文MD5仅供绑定677a169b092a3f6817030cb213313092；修订后必须重算。修正后再次核查最终PDF和实际包，再按说明会两MD5登记和同文件上传。

## 持续有效用户约束
'''
mp.write_text(latest+principles+'\n\n## 冻结模型与实际复现范围\n'+frozen+'\n\n## 历史索引\n\n历次附录183/247页、补件137项等仅属旧版；完整快照和版本证据见memory_archive.md以及paper_output/qa。\n',encoding='utf-8')
assert len(mp.read_text(encoding='utf-8').splitlines()) <= 100
print(json.dumps({'status':report['submission_readiness'],'report':str(QA/'最终提交材料核查报告.txt'),'inputs_unchanged':True,'support_count':len(current_support),'memory_lines':len(mp.read_text(encoding='utf-8').splitlines())},ensure_ascii=False))
