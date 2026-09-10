"""Update only local A-task memory from verified production/QA and GUI evidence."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--gui-complete', action='store_true')
args = parser.parse_args()
assert Path.cwd().resolve() == ROOT
stamp = datetime.now(timezone.utc).isoformat()
base = ROOT / 'notes/A-modeling/2026-09-10'
manifest = json.loads((ROOT/'paper_output/results/run_manifest.json').read_text(encoding='utf-8'))
gate = json.loads((ROOT/'paper_output/qa/evidence_gate_report.json').read_text(encoding='utf-8'))
assert manifest['status'] == 'PASS' and gate['status'] == 'PASS'
if args.gui_complete:
    observation=json.loads((base/'gui_final_v6a/gui_observation.json').read_text(encoding='utf-8'))
    assert observation['status']=='GUI_CORE_EXECUTION_AND_ARTIFACT_COMPARISON_COMPLETED'
    assert observation['independent_comparison_checks']==60 and observation['all_solves_and_exports_observed']
gui = '核心独立GUI求解、全部导出与60项逐值核验完成；GUI退出码未在Output观察，记录null；用户人工代码审查待确认' if args.gui_complete else '已实际打开核心源码、命中入口/Settings/RHS断点并单步查看变量；完整求解和导出仍在运行'
state_path = base/'state.json'
state = json.loads(state_path.read_text(encoding='utf-8'))
state.update(status='results_validated_gui_complete_awaiting_deadline' if args.gui_complete else 'production_and_final_accuracy_pass_gui_reproduction_running',
             last_memory_update_utc=stamp,
             production_run='final_v6a',
             numerical_audit='notes/A-modeling/2026-09-10/data/final_numerical_audit.md',
             workflow_evidence_gate='S6_PASS',
             final_time_accuracy='ALL_THREE_FINAL_GRIDS_PASS',
             gui_reproduction={'run':'gui_final_v6a','status':gui,'completed':args.gui_complete,'actual_gui_exit_code':None,'observation_report':'notes/A-modeling/2026-09-10/gui_final_v6a/gui_observation.md'},
             human_code_review='pending')
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
memory = ROOT/'memoryskill.md'
text = memory.read_text(encoding='utf-8')
replacements = {
'- S1/S2/S3已完成': '- 正式生产 final_v6a 于UTC16:20:48—16:31:52实际完成，worker退出0，107项输入/输出哈希核验通过；S0—S6证据门禁已实际PASS。当前交付为完整建模及浓缩MD，未运行正式论文S7/S8。',
'- 已验证基准约Q3': '- 最终空间网格Q1/Q23 N3200、Q4 N6400；全整数秒×21物理半径最细相邻网格最大C差分别4.690332349e-5、3.830289061e-5、1.979947177e-5。Q3连续临界57.47230195056044h，严格上取报告57.4724h；Q4连续临界51.09057478683054h，严格报告51.0906h。是条件模型预测，不是实测。',
'- 两个v4高网格': '- 两个v4高网格并行尝试因虚拟内存压力主动中止，N3200不作有效结果。v5磁盘BDF仅改存储；v6修正精确accepted断点左右选择和异常清理。三个完整N40内存/磁盘全断点、左右nextafter及随机查询逐字节零差。最细空间历史证据保留版本链，最终保存场与生产逐字节相同，不宣称所有旧检查在v6重跑。',
'- 最终生产入口正在修复': '- 正式四XLSX共9335598格完整回读通过，正文7CSV共297格从live Run独立查询通过，Q2全206903行0—206902s；Q4域外23173空白、实际表面独立列。四工作簿合计30218400B，含完整工作簿等93文件无损数值候选ZIP14382321B，解压哈希一致；最终AI说明/复现README/匿名性仍需论文阶段补齐。',
}
lines = text.splitlines()
for index, line in enumerate(lines):
    for prefix, replacement in replacements.items():
        if line.startswith(prefix):
            lines[index] = replacement
            break
lines = [line for line in lines if not line.startswith('- 最终同N时间检查：') and not line.startswith('- 本轮VS GUI：')]
lines += ['- 最终同N时间检查：Q1/Q23/Q4基准与紧容差6次真实退出0、零警告，最大C差3.619134326e-9/9.941051204e-9/9.818015290e-10；Q23/Q4事件差+3.975728760e-6/-3.415538231e-6s。相邻网格与容差敏感性不是严格连续误差上界或实测准确率。', '- 本轮VS GUI：'+gui+'。启动元数据将无效ScriptArguments改为PTVS实际读取的CommandLineArguments，并加-B；首次缺参数退出2记录保留，模型Python源码未改。']
memory.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'updated_at':stamp,'state':state['status'],'gui':gui},ensure_ascii=False))
