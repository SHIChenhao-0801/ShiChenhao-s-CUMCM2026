from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import csv
import hashlib
import json
import shutil

qa = Path(__file__).resolve().parent
root = qa.parents[2]
support = root / '支撑材料'
vm = qa / 'vm_output'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

core = read(vm/'core_final_result.json')
assert core['accepted'] and core['returncode']==0 and core['sourceAndInputHashesUnchanged']
run = read(vm/'core_results/vm_final/runResult.json')
assert run['status']=='PASS' and run['profile']=='final'
matrix = read(qa/'verification_work/windows_sandbox_verification_matrix.json')
assert matrix['pythonSourcesWithVmExecutionCoverage']==31
wrapper = read(vm/'wrapper_stable/result.json')
assert wrapper['accepted'] and wrapper['actualExitCode']==0 and wrapper['programStatus']=='PASS'
assert wrapper['profile']=='quick' and set(wrapper['questions'])=={'Q1','Q23','Q4'}
strip = read(qa/'strip_final_audit.json')
for entry in strip['records']:
    if Path(entry['path']).suffix in {'.py','.m','.mjs','.ps1'} or entry['path'] in {'03_程序代码/requirements.txt','03_程序代码/input_manifest.csv'}:
        assert sha(support/entry['path'])==entry['after_sha256'], entry['path']
cells = {}
paper_cells = 0
saved_arrays_equal = True
for question, comparisons in run['comparisons'].items():
    reference = comparisons['referenceComparison']
    assert reference['status']=='PASS'
    saved_arrays_equal &= all(reference['supplementaryExactEqualityOfAllSavedArrays'].values())
    for group in comparisons['exports']:
        assert group['status']=='PASS' and group['fully_verified_with_live_Run']
        for export in group['exports']:
            cells[export['question_id']] = export['checked_cells']
            paper_cells += export['paper_CSV_live_Run_validation']['checked_cells']
assert sum(cells.values())==9335598 and paper_cells==297
assert saved_arrays_equal
q3 = run['summaries']['Q23']['completion']
q4 = run['summaries']['Q4']['completion']
assert q3['reported_drying_time_h']==57.4724 and q4['reported_drying_time_h']==51.0906
assert q3['max_C_at_reported_time']<0.15 and q4['max_C_at_reported_time']<0.15
drafts = read(qa/'strip_txt_drafts_manifest.json')
backup = qa/'txt_before_final'
backup.mkdir(exist_ok=False)
for entry in drafts:
    target = support/entry['target']
    assert sha(target)==entry['currentTargetSha256'], entry['target']
    assert sha(Path(entry['draft']))==entry['draftSha256']
    dest = backup/entry['target']
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(target,dest)
for entry in drafts:
    shutil.copyfile(entry['draft'],support/entry['target'])

gui_text = '当前去注释源码已在Visual Studio实际打开、命中dryingCore.py第19行断点并单步到第22行，核对初值和加载SHA；本轮未在VS完成全量求解，用户人工审查仍待本人完成。'
runtime_text = (
    '当前去注释源码的Windows Sandbox正式重算（2026-09-13）\n'
    '实际沙盒为独立Windows 11环境，配置关闭网络，原宿主D盘工作区不可见。\n'
    'Python3.14.7、NumPy2.5.2、SciPy1.18.1、openpyxl3.1.5；运行库显式提供且不继承宿主site-packages。\n'
    f'Q1/Q23 N3200、Q4 N6400正式全量，实际退出码0，程序内部PASS，程序耗时{run["elapsedSeconds"]:.3f}秒。\n'
    f'四份工作簿逐格回读{sum(cells.values()):,}格，全部正文CSV共{paper_cells}格与当前求解对象逐格核对通过。\n'
    '三轨迹21个保存数组与冻结参照逐值相同；运行前后源码及输入SHA不变。\n'
    f'Q3连续事件{q3["critical_event_h"]:.15g} h，严格报告{q3["reported_drying_time_h"]:.4f} h，未舍入maxC={q3["max_C_at_reported_time"]:.17g}。\n'
    f'Q4连续事件{q4["critical_event_h"]:.15g} h，严格报告{q4["reported_drying_time_h"]:.4f} h，未舍入maxC={q4["max_C_at_reported_time"]:.17g}。\n'
    '原runLogged.ps1也在沙盒Windows PowerShell5.1完成N40三轨迹、四表导出和回读，实际退出码0，内部PASS。\n'
    '辅助入口首轮内部数值PASS，但观察器提前退出造成控制台状态错误；改用独立隐藏控制台、保持监督进程至结束后，原脚本重新完整运行通过。\n'
    + gui_text+'\n'
    '本结论只证明所测Windows环境的数值复现，不表示真实物理预测精度、其他系统通过或人工签核。\n'
)
acceptance = support/'03_程序代码/docs/运行验收说明.txt'
history = acceptance.read_text(encoding='utf-8-sig')
history = history.replace('当前版本的正式独立运行结论应由本轮实际运行记录单列，包含环境、实际退出码、内部检查状态和源码SHA；本静态说明不代填尚未完成的运行结果。', '当前版本的实际沙盒结果见本文件最前面的独立运行记录。')
history = history.replace('新版Visual Studio工程仅完成静态检查，GUI打开、断点和运行未在本次实测；用户人工审查仍待本人完成。', '以上历史版本的GUI范围以当时记录为准；本轮去注释版本的GUI范围见文件开头。')
history = history.replace('当前交付目录已清除JSON和Markdown文件，说明统一为TXT。','正式源码/输入和说明不依赖附带JSON或Markdown；用户打开VS产生的.vs缓存另计，说明统一为TXT。')
acceptance.write_text(runtime_text+'\n以下保留版本历史，避免把旧运行当作本轮运行：\n\n'+history,encoding='utf-8-sig')
readme = support/'03_程序代码/README.txt'
content = readme.read_text(encoding='utf-8-sig').replace('本次交付中没有JSON或Markdown文件。','正式源码/输入及说明不附带JSON或Markdown；打开VS产生的.vs机器缓存另计。')
content = content.replace('新版工程的GUI打开、断点和运行尚未在本轮实测，用户人工审查仍待本人完成。',gui_text)
content += '\n7. 本轮独立运行结果\n\n'+runtime_text+'\n05历史检验的实际结果见支撑材料根目录“源码去注释与沙盒核查.txt”。\n'
readme.write_text(content,encoding='utf-8-sig')
organization = support/'00_整理验收说明.txt'
content = organization.read_text(encoding='utf-8-sig').replace('本说明不填入尚未结束的虚拟机成功声明；最终实际运行范围与结果由对应记录补充。','当前03正式全量在Windows Sandbox实际退出0且内部PASS；05历史检验未全部通过，具体见“源码去注释与沙盒核查.txt”。')
organization.write_text(content,encoding='utf-8-sig')
shutil.copyfile(qa/'verification_work/05源码独立运行核查_WINDOWS_SANDBOX.txt',support/'05_数值检验与实验/独立沙盒逐源码核查.txt')
shutil.copyfile(qa/'verification_work/05源码独立运行矩阵_WINDOWS_SANDBOX.csv',support/'05_数值检验与实验/独立沙盒运行矩阵.csv')
summary = (
    '源码去注释与独立Windows Sandbox核查\n\n'
    '结论：44份源码去注释已完成。03正式四问可在本次独立Windows Sandbox运行并通过数值回读；05历史检验源码不能全部判为可原样独立运行。\n\n'
    '一、文件与去注释范围\n'
    '范围为03_程序代码与05_数值检验与实验全部源码：41份Python、1份MATLAB、1份Node.js和1份PowerShell。\n'
    '删除274处词法注释和106处Python说明性docstring；Python非注释AST相同并全部编译通过，Node非注释AST相同，PowerShell非注释token流相同；MATLAB计算语句、字符串格式符和转置保留。\n'
    'requirements依赖项不变。reference_data.py的说明文字删除后，仅同步input_manifest.csv对应项的字节数和SHA；12项输入清单通过。\n'
    '7个使用__doc__作为argparse介绍的入口，其--help不再显示原介绍段，选项和计算行为保持一致。VS方案中的格式标识不是程序注释。\n'
    '用户沙盒桌面“支撑材料临时.zip”通过CRC和来源核对，44份源码与去注释前快照相同；ZIP原件保留。ZIP SHA256：e65deebaaeb87ec542b0972d8fa655796612413e94a1cb256f99e48f40638159。当前去注释文件以本支撑材料目录为准。\n\n'
    '二、03正式独立运行\n'+runtime_text+'\n'
    '三、05历史检验实际范围与问题\n'
    '31份Python均已在真实VM进行入口或函数级调用。29项Python任务24项退出0、5项退出1；退出0的任务仍逐项检查内部数值报告。\n'
    '原样路径探测实际失败；数值检验在实验副本中仅对14处根目录路径进行适配，并明确补入两CSV、四模板及描述性序列使用的Q23参考NPZ。适配未写入当前05源码。\n'
    '首次6项启动因测试准备时带入旧输出而被禁止覆盖；保留首轮记录，在新的空目录重跑后5项通过，另一项确认缺少model_route.json。\n'
    '主要未通过项：\n'
    '  run_modeling.py：缺少paper_output/plan/model_route.json。\n'
    '  isotherm_diagnose.py：旧B参数与当前ActivityModel接口不匹配，实际TypeError。\n'
    '  isotherm_activity_closure.py：原_extract把时间×空间数组按相反方向取值，实际IndexError。\n'
    '  isotherm_jacobian_probe.py：计算虽完成，numJacCalls=0，不能判定替代Jacobian测试有效。\n'
    '  crossvalidate_series.py：常数序列被旧M-K算法判出伪趋势，负例不通过。\n'
    '  compare_analytic.py：程序完成但内部REVIEW_REQUIRED；N400含水率误差约2.87508e-4超过1e-4门槛，N800约7.15866e-5。\n'
    '  analytic_metric_check.py：误差随网格细化减小，原固定解释文字却称不减小。\n'
    '  compareMatlab.mjs：Node v24.20.0在VM实际退出2，缺少历史MATLAB runSummary.json等对照文件。\n'
    '  runCrossCheck.m：沙盒没有MATLAB运行环境，未实算；其原根路径推导及输入位置也需调整。\n'
    '解析Jacobian、Bessel基准、稠密输出、部分网格与时间误差、方法对照、阈值事件、导出和有限情景实算的逐项证据见05“独立沙盒逐源码核查.txt”。没有运行全部默认高网格/数百情景批次，也没有把旧能量诊断的大残差写成守恒通过。\n\n'
    '四、复现和证据\n'
    '03运行：在该目录按README安装requirements，然后运行 python -X utf8 -B runDelivery.py --profile final。每次使用新run-id。\n'
    '无注释前后源码快照、修改审计、实际VM配置/环境/日志、进程退出码和结果回读证据保存在本届工作区paper_output/qa/comment_sandbox_20260913。说明及矩阵用TXT/CSV放在支撑材料，原始运行JSON留在内部QA。\n'
    '本次仅删除注释及同步相应清单，未以放宽阈值、改变模型或填造历史输入使检验通过。\n'
)
(support/'源码去注释与沙盒核查.txt').write_text(summary,encoding='utf-8-sig')
main = support/'00_支撑材料总说明.txt'
main.write_text(main.read_text(encoding='utf-8-sig')+'\n2026-09-13更新：全部44份源码已去注释；03在真实Windows Sandbox完成正式全量重算，05保留未通过及未实算状态。详见“源码去注释与沙盒核查.txt”。\n',encoding='utf-8-sig')
formal_files = sorted(p for p in support.rglob('*') if p.is_file() and '.vs' not in p.parts and p.name!='UpgradeLog.htm')
local_files = sorted(p for p in support.rglob('*') if p.is_file() and ('.vs' in p.parts or p.name=='UpgradeLog.htm'))
counts = Counter(p.relative_to(support).parts[0] if len(p.relative_to(support).parts)>1 else '根目录说明' for p in formal_files)
listing = ['支撑材料文件清单','',f'正式材料共{len(formal_files)}个文件，包含本清单。保留未压缩文件夹。',
           f'用户VS运行产生的本机工程缓存/升级日志{len(local_files)}个另列，不计入正式材料。','', '分类文件数：']
listing += [f'  {name}：{count}个文件' for name,count in sorted(counts.items())]
listing += ['', '逐文件相对路径：','']+[p.relative_to(support).as_posix() for p in formal_files]
listing += ['', '另列本机IDE文件（会随VS操作变化）：','']+[p.relative_to(support).as_posix() for p in local_files]
(support/'00_文件清单.txt').write_text('\n'.join(listing)+'\n',encoding='utf-8-sig')
report = {'status':'FINALIZED','utc':datetime.now(timezone.utc).isoformat(),'core':core,'workbookCells':cells,'paperCells':paper_cells,
          'savedArraysExactlyEqual':saved_arrays_equal,'q3':q3,'q4':q4,'sourceCount':44,'formalFileCount':len(formal_files),
          'localIdeFileCount':len(local_files),'sourceRemovalPublished':True,'allHistoricalProgramsPassed':False,
          'formalJsonOrMarkdown':[p.relative_to(support).as_posix() for p in formal_files if p.suffix.lower() in {'.json','.jsonl','.md'}],
          'formalFiles':[{'path':p.relative_to(support).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in formal_files]}
assert not report['formalJsonOrMarkdown']
evidence_files = [qa/'verification_work/windows_sandbox_verification_matrix.json',
                  qa/'verification_work/05源码独立运行核查_WINDOWS_SANDBOX.txt',
                  qa/'verification_work/05源码独立运行矩阵_WINDOWS_SANDBOX.csv',
                  vm/'wrapper_stable/result.json',vm/'extra_entries/wrapper_external_exit.json',
                  vm/'core_final_result.json',qa/'strip_final_audit.json',*qa.glob('strip_publish_apply_*.json')]
report['evidenceBindings']=[{'path':p.relative_to(root).as_posix(),'sha256':sha(p)} for p in evidence_files]
report['frozenWorkbooks']=[]
for q in range(1,5):
    current=support/f'04_结果表格/result{q}.xlsx'
    frozen=root/f'paper_output/results/production/final_v6a/outputs/result{q}.xlsx'
    assert sha(current)==sha(frozen)
    report['frozenWorkbooks'].append({'question':q,'sha256':sha(current),'matchesFrozen':True})
(qa/'final_delivery_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':report['status'],'formalFiles':len(formal_files),'cells':sum(cells.values()),'paperCells':paper_cells},ensure_ascii=False))
