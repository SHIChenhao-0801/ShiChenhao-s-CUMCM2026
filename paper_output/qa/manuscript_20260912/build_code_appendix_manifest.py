"""List the complete, actually imported final_v6a source closure; no PDE runs."""
from __future__ import annotations
import ast
import hashlib
import json
import pathlib
from datetime import datetime, timezone
ROOT=pathlib.Path(r"D:/Document/数学建模/2026CUMCM")
assert pathlib.Path.cwd().resolve()==ROOT.resolve()
OUT=ROOT/"paper_output/qa/manuscript_20260912"
manifest_path=ROOT/"paper_output/results/production/final_v6a/run_manifest.json"
original=json.loads(manifest_path.read_text(encoding="utf-8-sig"))["runs"][0]
roles={
"run_modeling.py":("总入口、实际进程监督、版本隔离与结果发布",["production_provenance.py","drying_core.py","q1_model.py","q2_model.py","q3_model.py","q4_model.py","export_outputs.py","publication_plots.py"]),
"q1_model.py":("问题一正式参数入口",["drying_core.py"]),
"q2_model.py":("问题二/三共用轨迹参数入口",["drying_core.py"]),
"q3_model.py":("全域阈值、四位小时上取与严格可行复核",[]),
"q4_model.py":("问题四附录4物性与收缩开关入口",["drying_core.py"]),
"drying_core.py":("读取输入、有限体积、水热物性、通量、ODE事件和稠密轨迹查询",["analytic_jacobian.py","disk_dense.py"]),
"analytic_jacobian.py":("全部状态交叉导数与解析稀疏Jacobian",[]),
"disk_dense.py":("BDF原精度多项式磁盘存储、分段边界与生命周期",[]),
"export_outputs.py":("模板识别、完整Excel/未舍入CSV导出、回读和活轨迹采样核验",[]),
"publication_plots.py":("正式入口直接调用的主题图生成及图源指纹",[]),
"production_provenance.py":("源文件/输入指纹、运行元数据、监督进程和发布事务",[]),
}
records={pathlib.Path(x["path"]).name:x for x in original["imported_model_modules"]}
order=list(roles)
files=[]
for index,name in enumerate(order,1):
    record=records[name];p=ROOT/record["path"];data=p.read_bytes();text=data.decode("utf-8-sig")
    sha=hashlib.sha256(data).hexdigest();assert sha==record["sha256"],f"frozen source changed: {p}"
    tree=ast.parse(text)
    imports=set()
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):imports.update(x.name for x in node.names)
        elif isinstance(node,ast.ImportFrom) and node.module:imports.add(node.module)
    files.append({"appendixOrder":index,"path":record["path"],"absolutePath":str(p),"name":name,
        "role":roles[name][0],"embedCompleteSource":True,"sha256":sha,"frozenProductionSha256":record["sha256"],
        "matchesFrozenProduction":True,"bytes":len(data),"lineCount":len(text.splitlines()),
        "productionLocalDependencies":roles[name][1],"allStaticImportsIncludingSelfchecks":sorted(imports),
        "note":"Embed the complete UTF-8 source; retain all functions. Do not concatenate files into one runnable script. Existing comments/state flags are historical and do not certify current human review."})
required=[]
for record in original["input_files"]:
    if record["path"].endswith(".py"):continue
    p=ROOT/record["path"];data=p.read_bytes();sha=hashlib.sha256(data).hexdigest()
    assert sha==record["sha256"],f"frozen noncode input changed: {p}"
    required.append({**record,"currentSha256":sha,"matchesFrozenProduction":True,
        "usage":"runtime numerical input" if record["path"].endswith(".csv") else "original layout, template or provenance inventory input"})
result={"generatedAtUtc":datetime.now(timezone.utc).isoformat(),"basis":"Actual imported_model_modules in frozen final_v6a run_manifest; current bytes independently matched to recorded hashes.",
"sourceManifest":{"path":str(manifest_path.relative_to(ROOT)),"sha256":hashlib.sha256(manifest_path.read_bytes()).hexdigest()},
"appendixPolicy":"The 11 files below form the original production source closure and must be fully embedded in file order. Validation trial scripts, old model versions, faulty sequential-MK and unavailable Sobol are excluded. publication_plots is retained because the original production entry imports it, not as a request for extra manuscript figures.",
"files":files,"totalSourceFiles":len(files),"totalSourceLines":sum(x["lineCount"] for x in files),
"nonCodeInputsRequiredByOriginalLayout":required,
"historicalRuntime":original["python"],
"requiredDirectoryLayout":["paper_output/code/modeling/<each of the 11 source files>","paper_output/data_cleaned/A_environment_observed.csv","paper_output/data_cleaned/A_radius_observed.csv","paper_output/plan/model_route.json","problem_files/CUMCM2026Problems/A题/附件/附件1.xlsx","problem_files/CUMCM2026Problems/A题/附件/附件2.xlsx","problem_files/CUMCM2026Problems/A题/附件/附件3/result1.xlsx ... result4.xlsx","tmp/cache/ (created at runtime)","paper_output/results/gui_reproduction/ or production/ (new version output)"],
"environmentPrerequisites":["Run from the original competition workspace root; each module locates that root through its original parents[3] file depth.","Python 3.14.7; NumPy 2.5.2; SciPy 1.18.1; openpyxl 3.1.5; Matplotlib 3.11.1 were the historical runtime. SciPy private BDF/OdeSolution APIs are used; do not assume an untested version is equivalent.","The original supervised entry checks C:/Windows/Fonts/msyh.ttc; original publication plots require this Windows font.","Allow writable per-run output and tmp/cache directories and sufficient disk for original-precision dense coefficients. CPU single-thread task environment is set by the entry.","Do not reuse final_v6a or any existing run version label. --review avoids publishing new global numerical contracts; it still performs real new solves when a user executes it.","This manifest certifies recorded source identity and documents prerequisites, not that an existing ZIP is standalone or portable. No new clean-room execution or GUI validation was performed in this task."],
"documentedCommandsNotExecuted":[
{"purpose":"Read-only explanation of the historical production entry; execution would create a new reviewed solve/export directory", "cwd":"D:/Document/数学建模/2026CUMCM", "command":"C:/Python314/python.exe -B paper_output/code/modeling/run_modeling.py --version appendix_review_unique --n1 3200 --n23 3200 --n4 6400 --blas-threads 1 --review --review-exports", "writes":"new paper_output/results/gui_reproduction/<version> plus temporary cache; does not by itself mean Visual Studio was used"},
{"purpose":"Original supervised production route; supplied for source comprehension, not run here", "cwd":"D:/Document/数学建模/2026CUMCM", "command":"C:/Python314/python.exe -B paper_output/code/modeling/run_modeling.py --version new_unique_version --n1 3200 --n23 3200 --n4 6400 --blas-threads 1", "writes":"new version outputs and publishes global model/result/table/figure contracts after verification"}],
"excludedSources":{"reason":"Not required by the original production dependency closure or unsuitable scientific claims", "examples":["paper_output/code/verification/crossvalidate_series.py","paper_output/code/verification/sensitivity_analysis.py","paper_output/code/verification/energy_balance_check.py","paper_output/code/verification/isotherm_activity_closure.py","paper_output/code/versions/*","paper_output/code/modeling/run_experiments.py"],"note":"Independent verification results may be cited with their proper scope; exclusion from this source appendix does not erase their historical evidence."},
"machineScope":"AST parse, byte hashes, line counts, declared/runtime-import dependency reconciliation. No PDE, no code alteration, no package repair, no Git.",
"humanReviewStatus":"pending","newVisualStudioExecution":False}
OUT.mkdir(parents=True,exist_ok=True)
(OUT/"code_appendix_manifest.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"sourceFiles":len(files),"sourceLines":result["totalSourceLines"],"nonCodeInputs":len(required),"allFrozenHashesMatch":True,"pdeRuns":0},ensure_ascii=False))
