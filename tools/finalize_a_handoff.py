"""Freeze local handoff metadata from observed GUI evidence; never rerun the model."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
assert Path.cwd().resolve() == ROOT
base = ROOT / 'notes/A-modeling/2026-09-10'
gui_dir = base / 'gui_final_v6a'
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

comparison = json.loads((gui_dir/'independent_comparison.json').read_text(encoding='utf-8'))
assert comparison['status'] == 'PASS_NUMERICAL_ARTIFACT_EQUIVALENCE'
assert comparison['check_count'] == 60 and not comparison['failed_checks']
run_path = ROOT/'paper_output/results/gui_reproduction/gui_final_v6a/review_result.json'
run = json.loads(run_path.read_text(encoding='utf-8'))
assert run['status'] == 'COMPUTED_PENDING_GUI_OBSERVATION'
evidence = {}
for path in sorted(gui_dir.iterdir()):
    if path.suffix in {'.png', '.txt'} or path.name in {'gui_observation.md','independent_comparison.md','independent_comparison.json'}:
        evidence[path.name] = {'bytes':path.stat().st_size,'sha256':digest(path)}
assert sum(name.endswith('.png') for name in evidence) >= 9
observation = {
    'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
    'status':'GUI_CORE_EXECUTION_AND_ARTIFACT_COMPARISON_COMPLETED',
    'gui_run':'gui_final_v6a',
    'source_production':'final_v6a',
    'gui_actual_exit_code':None,
    'exit_code_observation':'VS Debug Output did not display an exit code; do not infer 0.',
    'all_solves_and_exports_observed':True,
    'breakpoint_and_single_step_variables_observed':True,
    'debug_session_closed_after_completion':True,
    'independent_comparison_checks':60,
    'independent_comparison_passed':True,
    'human_review':'pending',
    'scope':'executed core solve/export/primary-figure/validation call chain; not every historical or supplementary helper',
    'run_started_at':run['started_at'],
    'run_finished_at':run['finished_at'],
    'original_run_record':{'path':run_path.relative_to(ROOT).as_posix(),'sha256':digest(run_path)},
    'evidence':evidence,
}
(gui_dir/'gui_observation.json').write_text(json.dumps(observation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

full = base/'A题_完整建模与公式推导.md'
brief = base/'A题_建模浓缩交接.md'
gui_text = ('Visual Studio 已通过 Computer Use 实际打开本轮核心源码，命中入口、Settings、RHS 与 Q4 断点并单步核对 T/C/D/ρ 和边界通量；'
            'N3200/N3200/N6400 三条轨迹、全部工作簿和四张主图已独立求解、导出完成。另一个代理实际核对 60 项，轨迹、原精度解压文本、全部工作表 XML、正文 CSV 和图数据逐值一致，工作簿仅创建/修改日期不同。'
            '完成标记已在 GUI 观察，之后关闭启动器等待；VS 输出窗口没有显示本次退出码，故 GUI 退出码保留未观察，不冒写为 0。正式命令行生产实际退出 0 有独立记录。'
            '**用户/团队人工代码和模型审查仍待确认。** 该证据只覆盖本轮实际执行调用链，不代表所有历史试验与新增补充工具都已分别通过 GUI 审查。')
for path in (full,brief):
    content=path.read_text(encoding='utf-8')
    assert content.count('<!-- GUI_STATUS_FINAL -->') == 1
    content,n=re.subn(r'(?<=<!-- GUI_STATUS_FINAL -->\n)[^\n]+',lambda _:gui_text,content,count=1)
    assert n==1
    if path==full:
        content=content.replace('按M50渐近展开作诊断','按M48的Richardson渐近展开作诊断')
        content=content.replace('本轮仍在进行的更细网格和存储重构验证','第十二节已完成的正式细网格和存储验证')
        addition='''
### 12.7 三张补充证据图

下列图只重绘已经运行并冻结的比较数据；新绘图驱动做了命令行生成、数组回读、PNG 与 PDF 视觉检查，未另做 GUI 复现，也未改动本轮正式图索引。来源和完整绘图值见[补充图审查](<D:/Document/数学建模/2026CUMCM/notes/A-modeling/2026-09-10/data/supplementary_figures/review.md>)。浓缩交接采用文字和数值，因此单独通过微信发送时不依赖这些本地图片。

![全整数秒与共同物理半径上的空间网格差](D:/Document/数学建模/2026CUMCM/notes/A-modeling/2026-09-10/data/supplementary_figures/fig_model_grid_convergence.png)

逐整数秒在 21 个固定物理半径上比较最大含水率差；Q4 仅比较同时位于材料内的有限值。Q1 使用 N800/1600/3200 的 v3 证据，Q23 此图只显示 v5 最终 N1600/3200 一对，Q4 使用 v5 N1600/3200/6400；样本秒数分别为 1801、206903、183929。右图为临界事件差绝对值。这些差是数值敏感性证据，单个 Q23 点不支持单独估计阶，所有点也不是连续解严格误差界。

![相同附录4物性下的收缩对照](D:/Document/数学建模/2026CUMCM/notes/A-modeling/2026-09-10/data/supplementary_figures/fig_q4_shrinkage_control.png)

同一 v2 源码、N200、附录4物性与参数，仅改变 shrink 开关：固定半径为 129.8452283470 h，采用给定收缩为 51.0909734198 h，时长下降约 60.65%。这是模型内的几何情景对照，不能用 Q3/Q4 同时改物性后的时间差隔离收缩作用，也不把这组 N200 值当作最终 N6400 正式值。

![四小时观测结束后的环境延拓情景](D:/Document/数学建模/2026CUMCM/notes/A-modeling/2026-09-10/data/supplementary_figures/fig_q3_physical_sensitivity.png)

同一 v2 源码、N200，基准为 4 h 后 50 °C/等效平衡含水率 0.05 平台。温度改成 49 °C、51 °C 而其余不变，临界时长分别改变 +3.24885%、−3.10681%；延续最后观测值为 −0.52708%，延续末 1 h 均值为 +0.0029529%。均值情景图中显示 +0.00% 只是两位小数舍入。情景变化不是统计置信区间，也不补足气相至固相平衡含水率映射的实测校准。

GUI 证据：[实际观察记录](<D:/Document/数学建模/2026CUMCM/notes/A-modeling/2026-09-10/gui_final_v6a/gui_observation.md>)、[60 项独立一致性审计](<D:/Document/数学建模/2026CUMCM/notes/A-modeling/2026-09-10/gui_final_v6a/independent_comparison.md>)。最终实验台账见[autoresearch 核验](<D:/Document/数学建模/2026CUMCM/notes/A-modeling/2026-09-10/data/autoresearch_final_review.md>)，S0—S6 的实际证据门禁范围见[S6 审查](<D:/Document/数学建模/2026CUMCM/notes/A-modeling/2026-09-10/data/s6_modeling_evidence_review.md>)。本次没有进入正式论文 S7/S8。
'''
        if '### 12.7 三张补充证据图' not in content:
            content=content.replace('<!-- ROOT_FINAL_RESULTS_END -->',addition+'\n<!-- ROOT_FINAL_RESULTS_END -->')
    path.write_text(content,encoding='utf-8')

snapshot={'created_at_utc':datetime.now(timezone.utc).isoformat(),
          'status':'FINAL_MODELING_HANDOFF_FILES_READY_FOR_REVIEW',
          'files':{p.name:{'bytes':p.stat().st_size,'sha256':digest(p)} for p in (full,brief)},
          'gui_observation_sha256':digest(gui_dir/'gui_observation.json'),
          'human_review':'pending',
          'planned_delivery':'Send the condensed MD only to the explicitly authorized recipient at 19:00 UTC; not sent by this script.'}
(base/'handoff_files_snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(snapshot,ensure_ascii=False,indent=2))
