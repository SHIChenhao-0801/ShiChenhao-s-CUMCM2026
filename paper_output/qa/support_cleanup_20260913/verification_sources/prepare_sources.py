"""Copy selected original numerical-check sources; do not execute any model."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, shutil, sys

ROOT=Path.cwd().resolve()
assert ROOT.name=='2026CUMCM'
TARGET=ROOT/'支撑材料/05_数值检验与实验'
QA=ROOT/'paper_output/qa/support_cleanup_20260913/verification_sources'
QA.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
matlab=TARGET/'MATLAB对照证据/runCrossCheck.m'
matlab_before=sha(matlab)
assert matlab_before=='54cdebf6941ed139efc00ff75e43b2c5fd5a3d73d2ec095829d7bc31aae3aeda'
original_matlab=ROOT/'paper_output/code/review_delivery/matlab/runCrossCheck.m'
assert not original_matlab.exists(), 'Do not restore the MATLAB source moved by the user.'

groups={
'modeling':{
 'drying_core.py':'原径向热湿方程、材料坐标、Kirchhoff水通量与求解器；检验共同依赖',
 'analytic_jacobian.py':'解析稀疏Jacobian与有限差分自检；原求解器依赖',
 'disk_dense.py':'BDF稠密多项式磁盘保存和查询；原求解器依赖',
 'q1_model.py':'问题一参数封装；时间误差检验依赖',
 'q2_model.py':'问题二/三共享轨迹参数封装；时间误差检验依赖',
 'q3_model.py':'全域含水率达标及严格报告格点；灵敏度等检验依赖',
 'q4_model.py':'问题四附录4物性与径向收缩参数封装；时间误差检验依赖',
 'validate_bessel.py':'常热物性圆柱Robin边界和时变环境卷积的Bessel解析基准',
 'compare_analytic.py':'有限体积结果与独立Bessel基准的数值对照',
 'verify_convergence.py':'网格加密、公共投影及解析特例的空间收敛检查',
 'verify_time_accuracy.py':'固定物理条件下基准/紧容差对照和监督执行',
 'verify_dense_storage.py':'BDF稠密输出存储/查询的一致性检查',
 'run_experiments.py':'带明确预算的网格、参数、物理情景实验入口',
 'production_provenance.py':'时间检验需要的源码/输入快照、执行监督和退出记录工具',
 'run_modeling.py':'production_provenance自检引用的原监督/求解入口；依赖补齐',
 'export_outputs.py':'run_modeling动态加载的原结果导出/回读模块；依赖补齐',
 'publication_plots.py':'run_modeling动态加载的原绘图模块；依赖补齐',
 'axisymmetric_check.py':'轴对称二维含端面情景的适用性检查源代码'
},
'verification':{
 'analytic_metric_check.py':'对解析基准的评估指标、共同点与体平均差异核查',
 'crossvalidate_solver.py':'数值求解器实现、物理边界与诊断的交叉检查',
 'crossvalidate_series.py':'已有时间序列、阶段特征与质量变化分析',
 'method_comparison.py':'BDF、Radau等适用数值方法的小网格比较',
 'sensitivity_analysis.py':'参数敏感性；包括已修正的Kirchhoff通量尺度注入',
 'threshold_and_scaling_checks.py':'阈值、量纲标度、缩放与响应解释检查',
 'isotherm_activity_closure.py':'吸附/水活度边界闭合的经验情景求解',
 'isotherm_diagnose.py':'上述闭合的物理量、初值及通量诊断',
 'isotherm_jacobian_probe.py':'上述闭合Jacobian和数值扰动的诊断',
 'energy_balance_check.py':'有效热容量和显热收支检查',
 'energy_balance_diagnose.py':'能量残差构成及容量项的补充诊断',
 'energy_balance_diagnose2.py':'能量表达式/容量功解释的进一步诊断',
 'latent_heat_scenarios.py':'潜热负荷压力情景；非生产基准替换'
}}
records=[]
for group,files in groups.items():
    for name,purpose in files.items():
        source=ROOT/'paper_output/code'/group/name
        target=TARGET/'Python检验源码/paper_output/code'/group/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
        assert source.read_bytes()==target.read_bytes()
        ast.parse(target.read_text(encoding='utf-8-sig'),filename=name)
        records.append({'file':target.relative_to(TARGET).as_posix(),'source':source.relative_to(ROOT).as_posix(),
         'purpose':purpose,'bytes':target.stat().st_size,'source_sha256':sha(source),'packaged_sha256':sha(target),'byte_identical':True})

source=ROOT/'paper_output/code/review_delivery/tools/compareMatlab.mjs'
target=TARGET/'MATLAB对照证据/compareMatlab.mjs'
shutil.copyfile(source,target)
records.append({'file':target.relative_to(TARGET).as_posix(),'source':source.relative_to(ROOT).as_posix(),
 'purpose':'原MATLAB与Python共同时间/材料坐标样点、事件的对照程序；Node.js自带库',
 'bytes':target.stat().st_size,'source_sha256':sha(source),'packaged_sha256':sha(target),'byte_identical':source.read_bytes()==target.read_bytes()})
records.append({'file':'MATLAB对照证据/runCrossCheck.m','source':'现有支撑目录内由用户移入的MATLAB原文件；保持原位，未恢复原目录',
 'purpose':'实际使用的独立MATLAB N40热湿求解和共同样点导出',
 'bytes':matlab.stat().st_size,'source_sha256':matlab_before,'packaged_sha256':sha(matlab),'byte_identical':sha(matlab)==matlab_before})
assert all(r['byte_identical'] for r in records)

all_local={p.stem for folder in ['modeling','verification'] for p in (ROOT/'paper_output/code'/folder).glob('*.py')}
included={Path(r['file']).stem for r in records if r['file'].endswith('.py')}
local_edges=[]
for r in records:
    if not r['file'].endswith('.py'):continue
    tree=ast.parse((TARGET/r['file']).read_text(encoding='utf-8-sig'))
    modules=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):modules.extend(a.name.split('.')[0] for a in node.names)
        elif isinstance(node,ast.ImportFrom) and node.module:modules.append(node.module.split('.')[0])
    for name in sorted(set(modules)&all_local):
        local_edges.append({'source_file':r['file'],'imports':name,'included':name in included})
assert all(e['included'] for e in local_edges)

readme='''数值检验与实验程序说明
====================

本目录保存本题实际使用的数值检验源代码，供阅读和追溯。共有31个Python源文件、1个MATLAB源文件和1个Node.js源文件；没有用报告文件代替程序，也没有恢复此前整个历史版本目录。

一、从哪里看

Python检验源码/paper_output/code/modeling：原模型、问题参数、Bessel解析基准、网格/时间/稠密输出检验和实验入口。相互调用的本地Python源码已经补齐，文件名和代码内容保持原样。
Python检验源码/paper_output/code/verification：求解器/方法对照、敏感性、阈值标度、经验闭合、能量和潜热情景的检验源码。
MATLAB对照证据/runCrossCheck.m：用户已经移入本目录的独立MATLAB实现，原位保留；未改任何字节，未移回原工作区。
MATLAB对照证据/compareMatlab.mjs：读取已有MATLAB/Python共同样点和事件、按预先设定容差比较的原Node.js程序。
逐文件用途、原来源和SHA256见“源码文件与校验值.txt”。

二、运行前提

这些是实际使用过的原检验源码，仍保留当时的路径、输出结构和数据读取约定。当前生产模型的独立运行入口请查看支撑材料03程序目录；本目录不宣称所有历史检验可以在任意位置直接双击运行。

Python基本依赖为NumPy和SciPy；compare_analytic、crossvalidate_series、latent_heat_scenarios及publication_plots的绘图部分还需要Matplotlib；原export_outputs依赖openpyxl。实际生产依赖版本以03目录的requirements和运行说明为准。disk_dense调用SciPy的BDF内部接口，换版本后须重新验证。

modeling代码按自身所在位置寻找Python检验源码根目录，并读取paper_output/data_cleaned下的A_environment_observed.csv和A_radius_observed.csv；这些是本题已有的环境/半径数据。verify_time_accuracy还会读取本目录已提供的问题参数和监督器源码。运行前须在独立实验目录准备所需输入、核对路径及磁盘预算。

verification中的若干程序把原本届工作区写为绝对ROOT路径；crossvalidate_series等还读取final_v6a的采样NPZ。compareMatlab.mjs读取历史MATLAB/Python运行输出，并核对来源哈希；本次交付按要求移除了JSON报告，因此这些历史输出不在本目录。它们需要重新生成相应运行输出或从原工作区读取既有证据；不能以缺少历史报告的当前目录冒称已独立复现。

runCrossCheck.m包含全部MATLAB局部函数，以N40作独立对照。该原文件按所在目录向上四级推断项目路径，移动后这一推断与当前目录层级不再相符。阅读源码时须特别检查projectRoot及输入路径；本轮保留原文件，不自动修补它或恢复用户移走的原路径。MATLAB运行应按团队既定GUI复现流程进行。

本轮只复制与静态核对源码，没有重新求解PDE、运行全部实验或代替核心代码人工审查。运行这些原程序可能新产生JSON等过程输出；本次交付目录本身不保存JSON或Markdown报告。新生成的过程输出应另放实验目录。

三、采用范围

生产基准仍为final_v6a：Q1/Q23使用N3200，Q4使用N6400。N40方法或MATLAB对照用于实现检查，不能代替正式网格。

常数序列的旧M-K伪越界、无效的旧Morris扩散参数注入和未完成Sobol不作为结论。这里提供的sensitivity_analysis.py包含对Kirchhoff面通量的实际缩放修正；代码存在不等于原全部历史输出均已重算。

经验吸附/水活度、潜热、端面和能量诊断是有限假设下的对照或压力情景。它们不构成真实药材等温线标定、内部温湿实测精度或真实工艺时长下界。累积显热解释需保留有效热容量及容量功限制。

四、文件整理方式

本目录原有12个JSON及1个Markdown说明按用户要求删除。说明以人工可读TXT重新编写，并非把JSON简单改后缀。原本届paper_output内的源程序和证据没有修改；runCrossCheck.m保留用户当前放置位置及原字节。
'''
(TARGET/'数值检验说明.txt').write_text(readme,encoding='utf-8-sig')
lines=['数值检验源码文件与SHA256校验值','==============================','',
 '以下33项均为真实源代码。新复制文件与所列本届来源逐字节一致；runCrossCheck.m与整理前的现有文件逐字节一致。','']
for index,r in enumerate(records,1):
    lines.extend([f'{index:02d}. {r["file"]}',f'用途：{r["purpose"]}',f'来源：{r["source"]}',f'大小：{r["bytes"]} 字节',f'SHA256：{r["packaged_sha256"]}',''])
(TARGET/'源码文件与校验值.txt').write_text('\n'.join(lines),encoding='utf-8-sig')
remove=[{'file':p.relative_to(TARGET).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in TARGET.rglob('*') if p.is_file() and p.suffix.lower() in ['.json','.md']]
report={'created_at_utc':datetime.now(timezone.utc).isoformat(),'sources':records,'source_count':len(records),
 'python_count':31,'matlab_count':1,'mjs_count':1,'all_source_sha256_match':all(r['byte_identical'] for r in records),
 'python_ast_parse_count':31,'local_import_edges':local_edges,'local_import_dependencies_present':True,
 'existing_matlab_sha256_before':matlab_before,'existing_matlab_sha256_after':sha(matlab),'original_matlab_path_restored':original_matlab.exists(),
 'remove_plan':remove,'removed_yet':False,'model_runs':0,'copied_code_modified':False}
(QA/'preparation_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'source_count':len(records),'python_count':31,'all_source_sha_match':True,'remove_plan':remove,'matlab_unchanged':sha(matlab)==matlab_before,'original_matlab_path_restored':original_matlab.exists()},ensure_ascii=False,indent=2))
