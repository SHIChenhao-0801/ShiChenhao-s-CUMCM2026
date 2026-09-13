from pathlib import Path
from datetime import datetime, timezone
import json

qa = Path(__file__).resolve().parent
root = qa.parents[2]
final = json.loads((qa/'final_delivery_audit.json').read_text(encoding='utf-8'))
assert final['status']=='FINALIZED'
record = {
    'updatedUtc':datetime.now(timezone.utc).isoformat(),
    'task':'Remove all source comments in the current support package and verify independent sandbox execution',
    'scope':['支撑材料/03_程序代码','支撑材料/05_数值检验与实验'],
    'status':'COMMENT_REMOVAL_COMPLETE_AND_SANDBOX_AUDIT_COMPLETE',
    'sourceFiles':44,'pythonSources':41,'commentsRemoved':274,'docstringsRemoved':106,
    'coreFormalVm':'PASS','coreExternalSeconds':final['core']['elapsedSeconds'],
    'workbookCells':sum(final['workbookCells'].values()),'paperCells':final['paperCells'],
    'savedArraysExactlyEqual':21,'strictHours':[57.4724,51.0906],
    'historical05AllRunnable':False,'historicalPythonTasks':29,'historicalPythonZeroExit':24,
    'historicalPythonNonzeroExit':5,'historicalPythonVmSourceCoverage':31,
    'rootPathAdaptationsInExperimentalCopyOnly':14,
    'nodeVm':'EXIT_2_MISSING_HISTORICAL_INPUTS','matlabVm':'NOT_EXECUTED_RUNTIME_UNAVAILABLE',
    'powershellVm':'PASS_FULL_QUICK_AFTER_OBSERVER_CONSOLE_CORRECTION',
    'visualStudioGui':'SOURCE_BREAKPOINT_STEP_AND_VARIABLES_VERIFIED_NOT_FULL_SOLVE',
    'humanReview':'PENDING_USER_REVIEW',
    'userArchiveSha256':'e65deebaaeb87ec542b0972d8fa655796612413e94a1cb256f99e48f40638159',
    'userArchivePreserved':True,'desktopSandboxKeptOpen':True,
    'finalReport':'支撑材料/源码去注释与沙盒核查.txt',
    'qa':'paper_output/qa/comment_sandbox_20260913/final_delivery_audit.json',
    'scopeLimitation':'No new physical accuracy, other operating system, human review or general historical batch PASS is established.'
}
wechat_file=qa/'gui/wechat_sent_verified.json'
if wechat_file.exists():
    wechat=json.loads(wechat_file.read_text(encoding='utf-8'))
    assert wechat['status']=='SENT_VERIFIED_IN_CHAT'
    record['wechatNotificationStatus']=wechat['status']
    record['wechatNotificationEvidence']=str(wechat_file.relative_to(root))
desktop_file=qa/'vm_output/desktop_delivery.json'
if desktop_file.exists():
    record['sandboxDesktopDelivery']={k:v for k,v in json.loads(desktop_file.read_text(encoding='utf-8')).items() if k!='files'}
workflow_file=root/'paper_output/context/workflow_memory.json'
workflow=json.loads(workflow_file.read_text(encoding='utf-8-sig'))
workflow['support_comment_sandbox_review']=record
workflow_file.write_text(json.dumps(workflow,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
memory=root/'memoryskill.md'
text=memory.read_text(encoding='utf-8-sig')
section=(
    '## 支撑源码去注释及真实Windows Sandbox核查（2026-09-13）\n\n'
    '- 当前修改范围仅用户支撑材料03/05，44源＝41 Python+MATLAB+Node+PowerShell；删除274词法注释、106说明性docstring，全部Python非注释AST/编译及Node AST、PowerShell token核验，MATLAB保留计算语句/格式符。实际支撑目录已发布，before快照保留。reference_data.py仅删说明并同步input_manifest.csv，12项清单回读通过。\n'
    '- 用户宿主及VM桌面“支撑材料临时.zip”20,542,720B，SHA e65deebaaeb87ec542b0972d8fa655796612413e94a1cb256f99e48f40638159；CRC及44源与before全部相同，原ZIP保留。以当前未压缩支撑材料为去注释交付。\n'
    f'- 真正Windows Sandbox Win11禁网，原D盘工作区不可见；独立C:/Runtime Python3.14.7/NumPy2.5.2/SciPy1.18.1/openpyxl3.1.5。03正式N3200/N3200/N6400实际exit0、内部PASS，外部{final["core"]["elapsedSeconds"]:.3f}秒；9335598工作簿格、297正文格核验，21保存数组直接与冻结NPZ逐值相同，Q3/Q4严格57.4724h/51.0906h。四份04冻结Excel未改。\n'
    '- 05共33源已读；31 Python在VM原入口/函数调用覆盖，29任务24exit0/5exit1。原路径先实际失败，再仅在实验副本做14处根路径适配、明示复制必需输入。首轮6旧输出目录干扰在空目录复测，5通过、run_modeling缺model_route；不把HOST旧结果计VM。旧B接口、_extract转置、Jacobian注入0调用、M-K常数伪趋势、N400解析误差超限、analytic_metric解释矛盾仍列问题，模型算法未因此改变。Node VM exit2缺MATLAB旧结果；MATLAB在VM无runtime未实算。\n'
    '- 原PS辅助quick内部首轮数值PASS，观察器600秒退出使控制台恢复报错、真实父进程exit1。使用独立隐藏控制台/保持观察器的新目录完整复测，原PS脚本最终exit0+内部PASS；不隐去首轮准备问题。\n'
    '- VS当前无注释candidate已实际打开、dryingCore.py:19断点/22行单步、初值和加载SHA验证；未在VS全量求解，人审仍待用户。WindowsSandbox保持打开，用户ZIP及解压原件保留。正式源码和TXT清单与用户VS生成的.vs缓存分开计数，不再无条件声称整目录JSON为零。\n'
    '- 交付入口支撑材料/源码去注释与沙盒核查.txt，05独立沙盒逐源码核查.txt及CSV矩阵；内部QA在paper_output/qa/comment_sandbox_20260913，final_delivery_audit绑定core/05/PS/去注释证据SHA。旧S8/物理精度/其他系统与人审状态不扩大。本轮未编辑论文或正式冻结结果。\n\n'
)
title=section.splitlines()[0]
if title not in text:
    anchor='## 最新论文格式、六图命名与专业措辞修订（2026-09-13）'
    assert anchor in text
    memory.write_text(text.replace(anchor,section+anchor,1),encoding='utf-8')
if wechat_file.exists():
    current=memory.read_text(encoding='utf-8')
    notification='- 微信通知已完成：2026-09-13向唯一私人联系人“乐乐”仅发送一次完成说明，聊天显示10:30；02:33:41 UTC实际核到完整绿色气泡、进度标记消失、无失败标记。证据gui/wechat_sent_verified.json，SENT_VERIFIED_IN_CHAT；未发文件/其他消息，未声称对方已读。此前文献修订轮次的UNSENT已由此项实际完成。\n'
    if notification not in current:
        memory.write_text(current.replace(title+'\n\n',title+'\n\n'+notification,1),encoding='utf-8')
print(json.dumps({'status':record['status'],'coreFormalVm':record['coreFormalVm'],'historical05AllRunnable':False},ensure_ascii=False))
