"""Assemble actual contest supporting materials without changing frozen inputs/results."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "支撑材料"
QA = ROOT / "paper_output/qa/support_materials_20260913"
FROZEN = ROOT / "paper_output/results/production/final_v6a"
MANIFEST = QA / "assembly_source_manifest.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def assemble():
    records = []

    def copy(src, rel, *, sanitize=False, role=""):
        src = ROOT / src if not isinstance(src, Path) else src
        target = DEST / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        changes = []
        if sanitize:
            value = src.read_text(encoding="utf-8-sig")
            for before in [str(ROOT).replace("\\", "\\\\"), str(ROOT), ROOT.as_posix()]:
                if before in value:
                    value = value.replace(before, ".")
                    changes.append("本届工作区绝对路径改为相对路径标记")
            for before in ["C:\\\\Users\\\\Shi Chenhao", "C:\\Users\\Shi Chenhao", "C:/Users/Shi Chenhao", "SHIChenhao-0801"]:
                if before in value:
                    value = value.replace(before, "ANONYMIZED_LOCAL_USER")
                    changes.append("移除本机用户或账号标识")
            write(target, value)
        else:
            shutil.copy2(src, target)
        records.append({"source": src.relative_to(ROOT).as_posix(), "destination": target.relative_to(DEST).as_posix(), "source_sha256": sha(src), "packaged_sha256": sha(target), "bytes": target.stat().st_size, "transformation": sorted(set(changes)), "role": role})

    # The official problem and all A-problem attachments, including blank templates.
    official = ROOT / "problem_files/CUMCM2026Problems/A题"
    for src in sorted(official.rglob("*")):
        if src.is_file():
            copy(src, Path("01_赛题与原始数据") / src.relative_to(official), role="官方原始输入；原件不改动")
    for src in (ROOT / "paper_output/data_cleaned").glob("*"):
        if src.suffix == ".csv" or src.name == "load_report.json":
            copy(src, Path("01_赛题与原始数据/清洗后数据") / src.name, sanitize=src.suffix == ".json", role="实际数值输入或清洗审计")
    write(DEST / "01_赛题与原始数据/数据说明.md", """# 数据说明

本目录保留 A 题题面、附件1/2原始Excel及附件3的四个空白结果模板。原件均逐字节复制，哈希可查总清单。填好的结果在 `../04_结果表格/`，避免与空白模板混淆。

- 附件1：0–4 h 共241条环境观测。温度单位°C，空气水分指标单位kg/kg；4 h后的50°C、0.05 kg/kg平台属于模型延拓假设，不是额外实测数据。
- 附件2：0–72 h 共145条半径观测，按题目单位换算使用。
- 清洗后数据：2份CSV由原附件转换，实际程序使用同样的数据；读取、单位和缺失情况见 `清洗后数据/load_report.json`。
- 气相水分指标映射为材料平衡含水率属于模型闭合假设，不能据此声称两者物理定义相同。

本题采用的定量外部实测输入为空；论文外部文献用于背景和方法依据，保存于 `../02_参考文献与网络资料/`。无题意关联的新闻、其他赛题及赛前练习不纳入本包。
""")
    for src in sorted((FROZEN / "outputs").iterdir()):
        if src.suffix in {".xlsx", ".csv", ".json"}:
            copy(src, Path("04_结果表格") / src.name, sanitize=src.suffix == ".json", role="final_v6a冻结结果；Excel/正文CSV不改动")
    for name in ["numerical_summaries.json", "export_validation.json", "process_result.json", "run_manifest.json"]:
        copy(FROZEN / name, Path("07_数值检验与实验/冻结运行证据") / name, sanitize=True, role="历史实际生产运行证据，路径匿名化副本")
    write(DEST / "04_结果表格/结果表说明.md", """# 四问结果表

| 文件 | 对应问题 | 冻结计算 |
|---|---|---|
| result1.xlsx | 问题一的径向温度和含水率 | 附录2物性，固定半径，N=3200 |
| result2.xlsx | 问题二时空温度和含水率大表 | 附录3物性，固定半径，N=3200，与问题三共享同一条从t=0开始的轨迹 |
| result3.xlsx | 问题三干燥达标时刻及含水率 | 连续临界根57.47230195056044 h；严格报告57.4724 h |
| result4.xlsx | 问题四收缩材料的达标及含水率 | 附录4物性，径向收缩，N=6400；连续临界根51.09057478683054 h；严格报告51.0906 h |

四份工作簿是 final_v6a 原件的逐字节副本；完整保留问题二约29MB的大表，没有删行或降低精度。7份 `q*_paper_*.csv` 是正文297格结果的来源。本次按用户要求直接交付文件夹。

显示四位小数不等于数值精度。严格时刻基于未舍入的全域最大含水率检验，不能只凭单元格四位显示判断达标。问题四固定列域外空白、表面列独立，不能用零填充。

`*.export.json` 与 `*.validation.json` 记录旧冻结导出和回读；其中绝对工作区路径已匿名化，数值保留。完整未舍入逐时空CSV体积较大、属于可重建中间导出，本包保留生产采样NPZ（在程序包的frozen_reference或相应参考数据目录）和完整复现入口，可重新生成。

这些时长为给定参数及闭合假设下的模型预测。没有药材内部温度/含水率实测数据，不构成实测准确率或已验证工艺时长。
""")

    # Six reviewed figures and their full 14 CSV tables; no nested handoff ZIP.
    figs = ROOT / "paper_output/figures/review_20260913"
    for src in sorted(figs.rglob("*")):
        if src.is_file() and (src.suffix.lower() in {".png", ".pdf", ".svg", ".csv"} or src.name in {"source_manifest.json", "plot_checks.csv", "axis_range_checks.csv", "R_session_info.txt"}):
            copy(src, Path("05_绘图与数据") / src.relative_to(figs), sanitize=src.suffix == ".json", role="已实际绘制六图与全部绘图CSV；未经重算")
    rsrc = figs / "draw_figures.R"
    rcode = rsrc.read_text(encoding="utf-8")
    rcode = rcode.replace("# Run from D:/Document/数学建模/2026CUMCM with Rscript --vanilla.", "# Portable copy: Rscript --vanilla draw_figures.R [output-directory].")
    rcode = rcode.replace('root <- normalizePath("paper_output/figures/review_20260913", winslash = "/", mustWork = TRUE)\ninput <- file.path(root, "input_data", "CSV")', '''script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
if (length(script_arg) != 1L) stop("Use Rscript --vanilla draw_figures.R [output-directory]")
source_dir <- dirname(normalizePath(sub("^--file=", "", script_arg), winslash = "/", mustWork = TRUE))
out_args <- commandArgs(trailingOnly = TRUE)
root <- if (length(out_args)) out_args[[1L]] else file.path(source_dir, "generated_figures")
dir.create(root, recursive = TRUE, showWarnings = FALSE)
root <- normalizePath(root, winslash = "/", mustWork = TRUE)
input <- file.path(source_dir, "input_data", "CSV")''')
    target = DEST / "05_绘图与数据/draw_figures.R"
    write(target, rcode)
    records.append({"source": rsrc.relative_to(ROOT).as_posix(), "destination": target.relative_to(DEST).as_posix(), "source_sha256": sha(rsrc), "packaged_sha256": sha(target), "bytes": target.stat().st_size, "transformation": ["只改输入/输出目录定位为脚本相对路径；输出另存generated_figures"], "role": "R绘图便携副本；绘图与数值逻辑不变"})
    guide = (figs / "README_六图核查.md").read_text(encoding="utf-8")
    guide = guide.replace('这六张图按用户最新论文《药材热湿耦合模型与干燥时间计算.docx》的六处绘图说明制作，暂未插入论文。', '本目录保存与《药材热湿耦合模型与干燥时间计算_文献公式修订版.docx》六图要求对应的图像与数据。最终插入、版式及选用以团队当前稿为准。')
    guide = guide[:guide.index("## 复现与数据来源")] + """## 复现与数据来源

已附全部14份CSV，共4627数据行；每图的PNG/PDF/SVG和六图合并PDF已实际生成、核看。正式论文是否使用这些图，以团队最终插入稿为准。

安装R并使Rscript可调用后，在本目录运行：

```text
Rscript --vanilla draw_figures.R
```

脚本以自身位置寻找输入，输出到新建的 `generated_figures/`，支持把输出目录作为最后一个参数。只调整路径，未修改绘图逻辑。历史实际环境R4.6.1、Windows、Cairo设备，字体Microsoft YaHei及Times New Roman；其他系统可调整字体，但须重新检查中文字形及布局。无需额外R包。

图2的平台延拓是假设；图4中心曲线与全域最大值真实重合；图5各曲线止于真实半径；图6全部采用N800。不得把旧图6的情景网格替换为生产网格后混比。
"""
    write(DEST / "05_绘图与数据/绘图说明.md", guide)

    # Complete sources used in the paper's production/verification lineage.
    original_paths = set()
    roles = {}
    for name in ["code_appendix_manifest.json", "verification_code_appendix_manifest.json"]:
        data = json.loads((ROOT / "paper_output/qa/manuscript_20260912" / name).read_text(encoding="utf-8"))
        for f in data["files"]:
            original_paths.add(f["path"])
            roles[f["path"]] = f.get("role", "生产源码")
    original_paths.add("paper_output/code/review_delivery/exportOutputs.py")
    original_paths.add("paper_output/code/data/prepare_a_data.py")
    for code_dir in ["modeling", "verification", "versions", "data", "contracts", "a_restart"]:
        for src in (ROOT / "paper_output/code" / code_dir).glob("*"):
            if src.suffix.lower() in {".py", ".r", ".m", ".mjs", ".ps1"}:
                original_paths.add(src.relative_to(ROOT).as_posix())
    for src in sorted(original_paths):
        copy(src, Path("07_数值检验与实验/历史源码") / src, role=roles.get(src, "补齐历史数据/导出入口"))
    for name in ["crossvalidation", "experiments", "convergence", "time_accuracy", "bessel_validation", "analytic_comparison", "jacobian_validation"]:
        for src in sorted((ROOT / "paper_output/results" / name).rglob("*")):
            if src.suffix in {".json", ".jsonl", ".csv"}:
                copy(src, Path("07_数值检验与实验/历史结果") / src.relative_to(ROOT / "paper_output/results"), sanitize=src.suffix in {".json", ".jsonl"}, role="实际检验/实验记录，采用范围见核验说明")
    for src in (ROOT / "paper_output/qa/matlab_crosscheck_20260911").glob("*.json"):
        copy(src, Path("07_数值检验与实验/MATLAB对照证据") / src.name, sanitize=True, role="历史MATLAB独立GUI对照记录")
    write(DEST / "07_数值检验与实验/数值检验说明.md", """# 数值检验与实验的使用范围

本目录保留生产/检验所用原始源码及实际运行的JSON/CSV证据。历史源码按原层级保存，逐字节不改，以便追溯论文的真实计算；部分入口依赖原工程的绝对路径、配置和历史版本，不能把这些审计存档当成本次便携入口。当前跨目录复现请从 `../03_程序代码/README.md` 开始。

历史源码包括原论文生产11文件、检验及历史依赖31文件，并补齐现存建模、交叉验证、清洗、契约及历史版本目录中的全部脚本。不能将其中旧版本全部当作当前生产代码执行。历史JSON内本机绝对路径作匿名化替换，数据、状态和数字不变；精确源哈希与转换记录见总清单。

当前采用基线：final_v6a，Q1/Q23为N3200，Q4为N6400，Kirchhoff水通量、解析稀疏Jacobian。检验包括网格/时间误差、解析特例、其他数值方法、阈值/标度、参数情景和MATLAB独立实现。不同网格和不同物理情景不可混作同一模型的精度。

采纳边界与已否决结果：

- `experiments/trials.jsonl` 留存42条历史试验；后续复核报告456项机器检查。新包组装不等于重跑这42条试验。
- 常数序列的旧M-K伪越界、Morris中D参数未有效注入、未完成的Sobol结果不作为论文结论；历史记录保留是为追踪失败，不代表采纳。
- 经验边界阻力参数族未用实测等温线标定，不能称真实工艺时间下界。图6统一N800、零潜热负荷。
- 累积热量解释存在容量功与有效热容量闭合限制，速率形式自洽不能扩大为真实全局能量模型完备性。
- D4/D3=0.175 exp(0.15/C)会在C约0.08606处反转，不能说D4全程更小。固定物性收缩对照和Q3/Q4综合差异应分开。
- 历史VS/MATLAB实际执行证据绑定当时源码；新的包装版本需单独验收。CLI、GUI、团队人工审查是三个状态，人工审查不能由机器检查代签。

未纳入重复中间产物：完整42轮状态轨迹、可重建稠密缓存、同一结果的旧图像和重复失败解压目录；题目所需4个大工作簿、正式采样参考、图表数据、源码和主要检验证据已经纳入。
""")
    for audit_rel in [
        'r_portability_audit.json',
        'reference_audit/independent_package_review.json',
        'reference_audit/reference_package_audit.json',
        'code_validation/code_package_audit.json',
        'ai_disclosure/final_audit.json',
    ]:
        audit_source = QA / audit_rel
        if audit_source.is_file():
            copy(audit_source, Path('07_数值检验与实验/本次整理核验') / audit_source.name, sanitize=True, role='本次实际材料、代码或披露核验；详情及限制见报告')
    # Rebuild the copied handoff index so its current file paths resolve in this package.
    idx_path = DEST / "05_绘图与数据/source_manifest.json"
    idx = json.loads(idx_path.read_text(encoding="utf-8"))
    source_lookup = {r['source']: r['destination'] for r in records}
    for table in idx['tables']:
        table['csv'] = 'input_data/' + table['csv'].replace('\\', '/')
    for source in idx['sources']:
        original_handoff = source.pop('file')
        source['original_handoff_path'] = original_handoff
        source['original_source_sha256'] = source.pop('sha256')
        current = []
        if source['source'] in source_lookup:
            current = ['../' + source_lookup[source['source']]]
        elif source['source'].endswith('/sampled_solution.npz'):
            case = Path(source['source']).parent.name
            current = [f'../03_程序代码/reference/{case}/sampled_solution.npz']
        elif source['source'].endswith('/summary.json'):
            current = ['../03_程序代码/reference/numerical_reference.json']
            source['representation_note'] = '生产数值摘要已按问题汇入此JSON；非原summary文件逐字节副本。'
        else:
            current = [t['csv'] for t in idx['tables'] if original_handoff in t['source']]
            source['representation_note'] = '原绘图NPZ的实际使用字段已逐值导出为下列CSV；旧NPZ是可重建中间数据，原工作区保留。'
        source['packaged_files'] = []
        for relative in dict.fromkeys(current):
            physical = (idx_path.parent / relative).resolve()
            if physical.is_file():
                source['packaged_files'].append({'file':relative, 'sha256':sha(physical)})
            else:
                raise FileNotFoundError('Current figure source mapping: '+relative)
    idx['purpose'] = '当前支撑材料六图CSV与原始来源映射；所有packaged_files及tables.csv相对本文件目录。'
    idx['source_root_note'] = 'source/original_handoff_path仅为历史追溯描述，不是当前包内运行路径；实际文件位置与哈希见packaged_files。绘图只需input_data/CSV。'
    write(idx_path, json.dumps(idx, ensure_ascii=False, indent=2))
    for filename in ['input_sha256.csv', 'output_sha256.csv']:
        base = DEST / '05_绘图与数据'
        targets = sorted((base/'input_data/CSV').rglob('*.csv')) if filename.startswith('input') else sorted(p for p in base.rglob('*') if p.is_file() and p.name not in {'input_sha256.csv','output_sha256.csv'})
        with (base/filename).open('w', encoding='utf-8-sig', newline='') as stream:
            out = csv.writer(stream)
            out.writerow(['file','sha256','bytes'])
            out.writerows([p.relative_to(base).as_posix(),sha(p),p.stat().st_size] for p in targets)
    for record in records:
        if record['destination'] in {'05_绘图与数据/source_manifest.json','05_绘图与数据/input_sha256.csv','05_绘图与数据/output_sha256.csv'}:
            file = DEST / record['destination']
            record['packaged_sha256'] = sha(file)
            record['bytes'] = file.stat().st_size
            record['transformation'].append('重建当前包内来源路径或文件校验，原来源哈希另存')
    QA.mkdir(parents=True, exist_ok=True)
    write(MANIFEST, json.dumps({"created_at_utc": datetime.now(timezone.utc).isoformat(), "records": records}, ensure_ascii=False, indent=2))
    print(json.dumps({"copied_files": len(records), "copied_bytes": sum(r["bytes"] for r in records), "source_manifest": str(MANIFEST)}, ensure_ascii=False))


if __name__ == "__main__":
    assemble()
