"""Read-only audit of the original submission ZIP; writes only this QA directory."""
from __future__ import annotations

import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import posixpath
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path.cwd().resolve()
OUT = ROOT / "paper_output/qa/portability_20260912"
ZIP = ROOT / "paper_output/submission/支撑材料/A题_支撑材料.zip"
EXPECTED_SHA = "6460f3299e012c2728385b1f78212386ba98b30a1acad926b9c446cc890c5b91"
blob = ZIP.read_bytes()
zip_sha = hashlib.sha256(blob).hexdigest()
if zip_sha != EXPECTED_SHA:
    raise RuntimeError("Original package changed; do not mix audit versions: " + zip_sha)
manifest = json.loads((ZIP.parent / "pack_manifest.json").read_text(encoding="utf-8"))
findings = [
    {"id": "P01", "severity": "blocking", "title": "包内目录与核心根目录推导不一致",
     "locations": ["code/runDelivery.py:29", "code/runDelivery.py:230", "code/dryingCore.py:27", "code/exportOutputs.py:40", "code/matlab/runCrossCheck.m:10"],
     "detail": "ZIP将交付代码放到code/，但Python仍向上取parents[3]，MATLAB仍向上四层。解压根目录启动时会触发cwd检查；绕过该检查也会读写解压目录外的错误根目录。主求解、导出和MATLAB入口均受影响。"},
    {"id": "P02", "severity": "blocking", "title": "入口无条件依赖未打包的冻结工程",
     "locations": ["code/runDelivery.py:110", "code/runDelivery.py:115", "code/runDelivery.py:253", "code/runDelivery.py:159", "code/runDelivery.py:176"],
     "detail": "final和audit均调用verifyFrozenBaseline，要求paper_output/results/production/final_v6a/run_manifest.json及账本中107项输入输出存在并逐字节匹配。包中只有重定位到evidence/final_v6a_run的部分账本/摘要，没有全量NPZ、原精度gz与原目录树。final还要求新解、事件、原精度CSV与冻结结果精确相等；此回归模式不能作为无历史工程的独立生产入口，也不能据此保证不同平台浮点逐位相等。"},
    {"id": "P03", "severity": "blocking", "title": "输入CSV存放位置不匹配，原始附件和输出模板缺失",
     "locations": ["code/dryingCore.py:35", "code/exportOutputs.py:43", "code/exportOutputs.py:105", "code/matlab/runCrossCheck.m:64", "code/data/prepare_a_data.py:39"],
     "detail": "两份清洗数据存在于figures/A_*_observed.csv，求解器读取paper_output/data_cleaned。题面附件1/2原始XLSX与附件3四个空白模板均未打包；顶层result1—4.xlsx是正式结果，不能冒称原始模板。仅修正根目录仍不能完成求解和导出，也不能完整重跑数据准备。"},
    {"id": "P04", "severity": "blocking", "title": "交叉验证代码仍绑定作者磁盘路径",
     "locations": ["code/modeling/validate_bessel.py:291", "code/verification/analytic_metric_check.py:24", "code/verification/crossvalidate_solver.py:28", "code/verification/isotherm_activity_closure.py:59"],
     "detail": "14个code/verification脚本直接将ROOT绑定D:/Document/数学建模/2026CUMCM；validate_bessel还强制cwd等于该绝对路径。另一设备或另一解压位置会读不到源码/数据，甚至误读同名旧工程，无法依靠ZIP独立复现。"},
    {"id": "P05", "severity": "blocking_for_extended_pipeline", "title": "扩展管线依赖未列全且绘图强制本机字体",
     "locations": ["code/requirements.txt:2", "code/modeling/publication_plots.py:25", "code/modeling/publication_plots.py:32", "code/modeling/run_modeling.py:65", "code/data/prepare_a_data.py:23"],
     "detail": "实际ZIP包含19个旧建模脚本、14个验证脚本及数据准备程序；requirements仅列numpy/scipy/openpyxl，遗漏实际导入的matplotlib。publication_plots在C:/Windows/Fonts/msyh.ttc不存在时直接raise，run_modeling无条件stat该字体。精确依赖是否能在目标平台安装应另作干净环境实测；本次不把语法通过当成安装验证。"},
    {"id": "P06", "severity": "blocking_for_documented_commands", "title": "运行说明和监督器保留本机启动方式",
     "locations": ["code/README.md:27", "code/README.md:40", "code/README.md:45", "code/runLogged.ps1:4", "code/runLogged.ps1:7"],
     "detail": "README让接收者打开未打包的A_CodeReview.sln，并切到作者D盘目录，以包内不存在的paper_output/code/review_delivery路径启动。监督器默认C:/Python314/python.exe。README全部6个本地Markdown链接在包中无法解析；需要面向解压根目录的安装、运行、预期输出与失败判定说明。"},
    {"id": "P07", "severity": "blocking_for_historical_tools", "title": "重命名和旧修复验证工具的历史依赖缺失",
     "locations": ["code/tools/verifyCamelCopies.py:17", "code/tools/buildCamelCopies.py:16", "code/tools/verifyExportPathFix.py:32", "code/tools/verifyExportPathFix.py:40", "code/tools/verifyExportPathFix.py:66"],
     "detail": "旧代码实际在code/modeling，但工具仍找paper_output/code/modeling。verifyExportPathFix另外读取明确排除的tools/exportPathFixBefore和camel_final_v1失败目录。这些文件可用作开发历史证据，当前无法作为随包可执行复现程序。"},
    {"id": "P08", "severity": "assurance_gap", "title": "打包通过仅证明容器完整，未证明运行闭包完整",
     "locations": ["paper_output/submission/支撑材料/build_support_package.py:406", "paper_output/submission/支撑材料/build_support_package.py:477"],
     "detail": "附录目录项仅检查any(n.startswith(item))，并未验证其中程序的输入、依赖、路径或调用链。退出条件只检查压缩大小与身份词零命中，missing_sources/附录完整性也未纳入返回码。现有178项CRC/SHA一致和体积合规可确认，但不能推出独立运行通过。"},
]

with zipfile.ZipFile(io.BytesIO(blob)) as archive:
    names = archive.namelist()
    name_set = set(names)
    records = []
    py_checks = []
    imports = {}
    identity_hits = []
    hard_tokens = ["Chenhao", "chenhao", "SHICHE", "ShiChenhao", "施陈浩", "福州", "厦门", "lin_yuxiang", "C:\\Users", "C:/Users"]
    for name in names:
        data = archive.read(name)
        records.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        if name.endswith(".py"):
            source = data.decode("utf-8-sig")
            try:
                tree = ast.parse(source, filename=name)
                compile(tree, name, "exec")
                py_checks.append({"path": name, "syntax": "PASS", "executed": False})
                imports[name] = sorted({n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module} | {alias.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for alias in n.names})
            except SyntaxError as error:
                py_checks.append({"path": name, "syntax": "FAIL", "error": str(error), "executed": False})
        if name.startswith("code/") and Path(name).suffix in {".py", ".m", ".ps1", ".md", ".json", ".txt"}:
            for line_no, line in enumerate(data.decode("utf-8-sig").splitlines(), 1):
                for token in hard_tokens:
                    if token in line:
                        identity_hits.append({"path": name, "line": line_no, "token": token})
    links = []
    for line_no, line in enumerate(archive.read("code/README.md").decode("utf-8-sig").splitlines(), 1):
        for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", line):
            target = match.group(1)
            if "://" not in target:
                resolved = posixpath.normpath(posixpath.join("code", target))
                links.append({"line": line_no, "target": target, "resolved": resolved, "exists": resolved in name_set})
    baseline = json.loads(archive.read("evidence/final_v6a_run/run_manifest.json"))["runs"][0]
    manifest_by_path = {item["path"]: item for item in manifest["entries"]}
    hash_mismatches = [r["path"] for r in records if r["path"] not in manifest_by_path or manifest_by_path[r["path"]]["sha256"] != r["sha256"]]
    result = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "audit_type": "independent read-only archive/static dependency audit",
        "verdict": "FAIL_PORTABILITY_ORIGINAL_PACKAGE",
        "audited_archive": {"path": str(ZIP.relative_to(ROOT)), "sha256": zip_sha, "bytes": len(blob), "entries": len(names), "crc_bad_entry": archive.testzip()},
        "source_mutated": False, "production_executed": False, "gui_executed": False, "human_review_signed": False,
        "counts": {"python_total": len(py_checks), "python_in_code": sum(n.startswith("code/") and n.endswith(".py") for n in names), "python_in_evidence": sum(n.startswith("evidence/") and n.endswith(".py") for n in names), "matlab": sum(n.endswith(".m") for n in names), "powershell": sum(n.endswith(".ps1") for n in names), "cpp": sum(n.endswith((".cpp", ".cc", ".cxx")) for n in names)},
        "duplicate_entries": [n for n, count in Counter(names).items() if count > 1],
        "manifest_hash_mismatches": hash_mismatches,
        "baseline_inventory_required_by_entrypoint": len(baseline["input_files"]) + len(baseline["output_artifacts"]),
        "readme_local_links": links,
        "independent_code_identity_token_hits": identity_hits,
        "identity_scope": "limited code text token scan, not full PDF metadata/privacy certification",
        "findings": findings, "python_syntax_checks": py_checks, "imports": imports, "archive_inventory": records,
        "limits": ["No claim of second physical device execution", "No dependency installation or numerical solve in this sub-audit", "CLI syntax checks do not satisfy Visual Studio GUI or user code review", "This verdict binds only the audited original ZIP SHA256; later repaired packages require a new audit"]}

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "package_review.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
lines = ["# 原始提交包完整性与可移植性独立审计", "", "结论：**原始ZIP不具备脱离作者工程的独立运行条件（FAIL_PORTABILITY_ORIGINAL_PACKAGE）**。这是对本报告绑定的原始版本的只读审计；修复后的新包应单独验收。", "", f"- ZIP：`{result['audited_archive']['path']}`", f"- SHA256：`{zip_sha}`", f"- 体积：{len(blob):,}字节；178项；CRC通过；178项与打包清单SHA256一致；无重复项。", "- 包含55个Python文件，其中code下46个、evidence下9个；另有1个MATLAB和1个PowerShell；无C++。55个Python均通过语法解析/编译检查，本子审计未执行这些生产或历史程序。", "- 独立代码身份词扫描未命中所列人名/学校/用户目录词；该结果仅是限定文本扫描，不等于完整匿名终审。", "", "## 运行阻断与补齐项", ""]
for finding in findings:
    lines += [f"### {finding['id']} {finding['title']}（{finding['severity']}）", "", finding["detail"], "", "包内定位：" + "；".join("`" + loc + "`" for loc in finding["locations"]), ""]
lines += ["## 验证边界", "", "本报告仅证明原包容器/文件指纹和静态依赖问题；未安装新环境、未执行数值求解、未操作MATLAB/Visual Studio、未替用户人工签核。实际隔离重跑由主代理另存证据。不得将旧本机GUI成功、CRC/SHA通过、或Python语法通过合并称为另一设备已独立复现。", "", "修复应提供解压根目录入口、完整输入与模板、可安装的依赖和平台说明、可选的历史回归模式、可运行的验证/绘图入口及包内有效链接。最终以不接触作者源工程的解压副本实际运行、全量导出回读和预期数值比较为验收依据。", ""]
(OUT / "package_review.md").write_text("\n".join(lines), encoding="utf-8")
print(json.dumps({"verdict": result["verdict"], "sha256": zip_sha, "python_syntax_pass": sum(p["syntax"] == "PASS" for p in py_checks), "counts": result["counts"], "findings": len(findings), "reports": [str(OUT / "package_review.md"), str(OUT / "package_review.json")]}, ensure_ascii=False, indent=2))
