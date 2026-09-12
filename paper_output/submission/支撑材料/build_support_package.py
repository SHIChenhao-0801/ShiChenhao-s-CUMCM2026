# -*- coding: utf-8 -*-
r"""按论文附录 A 的 10 项清单组装 A 题支撑材料压缩包，并做完整性与匿名性校验。

用法（工作目录固定为比赛根目录 D:\Document\数学建模\2026CUMCM）：

    $env:PYTHONPYCACHEPREFIX='D:\Document\数学建模\2026CUMCM\tmp\cache\python'
    python -B paper_output\submission\支撑材料\build_support_package.py

可选参数：
    --include-legacy-pipeline   额外纳入 paper_output/code 下蛇形命名的
                                数据准备/建模/验证原始实现（默认不纳入，交付版为
                                review_delivery 的驼峰版本）

设计约束（脚本自身保证）：
  * 不改动任何源文件：所有文件先复制到 tmp/cache/support_package_stage 再打包；
  * 禁止把 final_v6a/outputs 整目录打包，禁止 result*_unrounded.csv.gz、
    tmp/、cache/、solver_runs/、.vs/、.git/、__pycache__/ 进入包内（硬守卫）；
  * 打包后解压回读：逐条 CRC 校验、统计条目数与解压后总字节、核对压缩包 <= 20 MB，
    并对 result1—4.xlsx 计算 SHA256，与源文件 SHA256 逐一比对。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_PATH = Path(__file__).resolve()
OUT_DIR = SCRIPT_PATH.parent                       # paper_output/submission/支撑材料
ROOT = SCRIPT_PATH.parents[3]                      # 比赛根目录
STAGE = ROOT / "tmp" / "cache" / "support_package_stage"
ZIP_PATH = OUT_DIR / "A题_支撑材料.zip"
MANIFEST_PATH = OUT_DIR / "pack_manifest.json"
AI_PDF = OUT_DIR / "AI工具使用详情.pdf"
LIMIT_BYTES = 20 * 1024 * 1024                     # 20,971,520
FINAL_OUT = "paper_output/results/production/final_v6a/outputs"
FINAL_ROOT = "paper_output/results/production/final_v6a"
DELIVERY = "paper_output/code/review_delivery"

# ---------------------------------------------------------------- 清单定义 ---
# 附录 A 第 1—5 项：支撑材料根目录
TOP_FILES = [
    (FINAL_OUT + "/result1.xlsx", "result1.xlsx"),
    (FINAL_OUT + "/result2.xlsx", "result2.xlsx"),
    (FINAL_OUT + "/result3.xlsx", "result3.xlsx"),
    (FINAL_OUT + "/result4.xlsx", "result4.xlsx"),
]

# 附录 A 第 6—8 项：源码与文档
CODE_FILES = [
    (DELIVERY + "/runDelivery.py", "code/runDelivery.py"),
    (DELIVERY + "/dryingCore.py", "code/dryingCore.py"),
    (DELIVERY + "/analyticJacobian.py", "code/analyticJacobian.py"),
    (DELIVERY + "/diskDense.py", "code/diskDense.py"),
    (DELIVERY + "/exportOutputs.py", "code/exportOutputs.py"),
    (DELIVERY + "/q1Model.py", "code/q1Model.py"),
    (DELIVERY + "/q2Model.py", "code/q2Model.py"),
    (DELIVERY + "/q3Model.py", "code/q3Model.py"),
    (DELIVERY + "/q4Model.py", "code/q4Model.py"),
    (DELIVERY + "/README.md", "code/README.md"),
    (DELIVERY + "/requirements.txt", "code/requirements.txt"),
    (DELIVERY + "/runLogged.ps1", "code/runLogged.ps1"),
    (DELIVERY + "/tools/buildCamelCopies.py", "code/tools/buildCamelCopies.py"),
    (DELIVERY + "/tools/verifyCamelCopies.py", "code/tools/verifyCamelCopies.py"),
    (DELIVERY + "/tools/verifyExportPathFix.py", "code/tools/verifyExportPathFix.py"),
    (DELIVERY + "/tools/coreChangeLog.md", "code/tools/coreChangeLog.md"),
    (DELIVERY + "/tools/coreRenameReport.json", "code/tools/coreRenameReport.json"),
    (DELIVERY + "/matlab/runCrossCheck.m", "code/matlab/runCrossCheck.m"),
    (DELIVERY + "/matlab/README.md", "code/matlab/README.md"),
]

DOC_FILES = [
    (DELIVERY + "/docs/公式与算法说明.md", "docs/公式与算法说明.md"),
    (DELIVERY + "/docs/人工审查清单.md", "docs/人工审查清单.md"),
    (DELIVERY + "/docs/独立代码审查.md", "docs/独立代码审查.md"),
    ("notes/A-modeling/2026-09-12/当前方法与数值求解步骤.md", "docs/当前方法与数值求解步骤.md"),
]

# 附录 A 第 9 项：正文图件的矢量版本与绘图数据（6 张正式图件，见
# final_v6a/published_contracts/figure_index.json）
FIGURE_FILES = [
    ("paper_output/figures/fig_A_environment.pdf", "figures/fig_A_environment.pdf"),
    ("paper_output/figures/fig_A_environment.svg", "figures/fig_A_environment.svg"),
    ("paper_output/figures/fig_A_radius.pdf", "figures/fig_A_radius.pdf"),
    ("paper_output/figures/fig_A_radius.svg", "figures/fig_A_radius.svg"),
    ("paper_output/data_cleaned/A_environment_observed.csv", "figures/A_environment_observed.csv"),
    ("paper_output/data_cleaned/A_radius_observed.csv", "figures/A_radius_observed.csv"),
    (FINAL_ROOT + "/figures/fig_q1_profiles.pdf", "figures/fig_q1_profiles.pdf"),
    (FINAL_ROOT + "/figures/fig_q1_profiles.svg", "figures/fig_q1_profiles.svg"),
    (FINAL_ROOT + "/figures/fig_q1_profiles.json", "figures/fig_q1_profiles.json"),
    (FINAL_ROOT + "/figures/fig_q1_profiles_data.npz", "figures/fig_q1_profiles_data.npz"),
    (FINAL_ROOT + "/figures/fig_q2_profiles.pdf", "figures/fig_q2_profiles.pdf"),
    (FINAL_ROOT + "/figures/fig_q2_profiles.svg", "figures/fig_q2_profiles.svg"),
    (FINAL_ROOT + "/figures/fig_q2_profiles.json", "figures/fig_q2_profiles.json"),
    (FINAL_ROOT + "/figures/fig_q2_profiles_data.npz", "figures/fig_q2_profiles_data.npz"),
    (FINAL_ROOT + "/figures/fig_q3_drying.pdf", "figures/fig_q3_drying.pdf"),
    (FINAL_ROOT + "/figures/fig_q3_drying.svg", "figures/fig_q3_drying.svg"),
    (FINAL_ROOT + "/figures/fig_q3_drying.json", "figures/fig_q3_drying.json"),
    (FINAL_ROOT + "/figures/fig_q3_drying_data.npz", "figures/fig_q3_drying_data.npz"),
    (FINAL_ROOT + "/figures/fig_q4_drying.pdf", "figures/fig_q4_drying.pdf"),
    (FINAL_ROOT + "/figures/fig_q4_drying.svg", "figures/fig_q4_drying.svg"),
    (FINAL_ROOT + "/figures/fig_q4_drying.json", "figures/fig_q4_drying.json"),
    (FINAL_ROOT + "/figures/fig_q4_drying_data.npz", "figures/fig_q4_drying_data.npz"),
]

# 附录 A 第 10 项：运行记录、校验输出、交叉验证结果
EVIDENCE_FILES = [
    (FINAL_ROOT + "/run_manifest.json", "evidence/final_v6a_run/run_manifest.json"),
    (FINAL_ROOT + "/launch.json", "evidence/final_v6a_run/launch.json"),
    (FINAL_ROOT + "/export_validation.json", "evidence/final_v6a_run/export_validation.json"),
    (FINAL_ROOT + "/metric_evidence_validation.json", "evidence/final_v6a_run/metric_evidence_validation.json"),
    (FINAL_ROOT + "/numerical_summaries.json", "evidence/final_v6a_run/numerical_summaries.json"),
    (FINAL_ROOT + "/process_result.json", "evidence/final_v6a_run/process_result.json"),
    (FINAL_ROOT + "/stdout.log", "evidence/final_v6a_run/stdout.log"),
    (FINAL_ROOT + "/outputs/result1.validation.json", "evidence/workbook_validation/result1.validation.json"),
    (FINAL_ROOT + "/outputs/result2.validation.json", "evidence/workbook_validation/result2.validation.json"),
    (FINAL_ROOT + "/outputs/result3.validation.json", "evidence/workbook_validation/result3.validation.json"),
    (FINAL_ROOT + "/outputs/result4.validation.json", "evidence/workbook_validation/result4.validation.json"),
    (FINAL_ROOT + "/outputs/result1.export.json", "evidence/workbook_validation/result1.export.json"),
    (FINAL_ROOT + "/outputs/result2.export.json", "evidence/workbook_validation/result2.export.json"),
    (FINAL_ROOT + "/outputs/result3.export.json", "evidence/workbook_validation/result3.export.json"),
    (FINAL_ROOT + "/outputs/result4.export.json", "evidence/workbook_validation/result4.export.json"),
    ("paper_output/results/code_delivery/交付与运行记录.md", "evidence/交付与运行记录.md"),
    (DELIVERY + "/runtime/coreRenameVerification.json", "evidence/code_runtime/coreRenameVerification.json"),
    (DELIVERY + "/runtime/exportPathFix_v2/verification.json", "evidence/code_runtime/exportPathFix_v2/verification.json"),
    (DELIVERY + "/runtime/exportPathFix_v2/artifactManifest.json", "evidence/code_runtime/exportPathFix_v2/artifactManifest.json"),
    (DELIVERY + "/runtime/exportPathFix_v2/process-exit.json", "evidence/code_runtime/exportPathFix_v2/process-exit.json"),
    (DELIVERY + "/runtime/exportPathFix_v2_console.log", "evidence/code_runtime/exportPathFix_v2_console.log"),
    ("paper_output/qa/evidence_gate_report.json", "evidence/qa/evidence_gate_report.json"),
    ("paper_output/qa/evidence_gate_report.md", "evidence/qa/evidence_gate_report.md"),
    ("paper_output/qa/workflow_guard_report.json", "evidence/qa/workflow_guard_report.json"),
    ("paper_output/qa/workflow_guard_report.md", "evidence/qa/workflow_guard_report.md"),
]

# 目录扫描条目：(源目录, 包内目录, 允许扩展名, 追加排除的正则)
SWEEPS = [
    ("paper_output/results/crossvalidation", "evidence/crossvalidation",
     {".json", ".md", ".csv", ".pdf"}, r"$^"),
    ("paper_output/qa/matlab_crosscheck_20260911", "evidence/matlab_crosscheck_20260911",
     {".json", ".md", ".csv", ".txt", ".jsonl"}, r"$^"),
    ("paper_output/qa/recheck_20260910_1828", "evidence/recheck_20260910_1828",
     {".json", ".md", ".py", ".txt", ".log", ".csv"},
     r"(^|/)documents_before/"),          # 内部文档快照，不作为外发证据
]

LEGACY_PIPELINE = [
    ("paper_output/code/data", "code/data", {".py"}),
    ("paper_output/code/modeling", "code/modeling", {".py"}),
    ("paper_output/code/verification", "code/verification", {".py"}),
]

# 附录 A 交叉核对用的 10 项（名称与说明逐字取自论文定稿附录 A）
APPENDIX_A = [
    ("AI工具使用详情.pdf", "按 AI 规定第 4 条撰写的详情说明"),
    ("result1.xlsx", "问题一完整结果（1800 s 内每 1 s、每 0.1 cm）"),
    ("result2.xlsx", "问题二完整结果（全过程每 1 s、每 0.1 cm）"),
    ("result3.xlsx", "问题三完整结果（每 60 s、每 0.1 cm）"),
    ("result4.xlsx", "问题四完整结果（每 60 s、每 0.1 cm，含药材表面列）"),
    ("code/", "建模与求解全部 Python 源程序（正式入口、核心模块、解析 Jacobian、绘图与导出脚本）"),
    ("code/matlab/", "MATLAB 独立交叉核验脚本"),
    ("docs/", "公式与算法说明、参数与运行设置说明"),
    ("figures/", "正文图件的矢量版本（PDF/SVG）与绘图数据"),
    ("evidence/", "运行记录、校验输出、交叉验证结果"),
]

# ------------------------------------------------------------ 硬守卫与扫描 ---
FORBIDDEN_ENTRY_RE = re.compile(
    r"(unrounded\.csv\.gz$)"
    r"|(^|/)(tmp|cache|solver_runs|__pycache__|\.vs|\.git)(/|$)"
    r"|\.pyc$|\.suo$|\.vsidx$|\.db(-shm|-wal)?$",
    re.IGNORECASE,
)
HARD_TOKENS = [
    "Chenhao", "chenhao", "SHICHE", "ShiChenhao", "施陈浩",
    "旗山", "福建", "福州", "厦门", "lin_yuxiang", "linyuxiang",
    "C:\\Users", "C:/Users", "Users\\", "Administrator",
]
REVIEW_TOKENS = ["参赛队", "队号", "赛区", "学校", "学院", "用户名"]
TEXT_EXTS = {".py", ".md", ".json", ".csv", ".txt", ".jsonl", ".m", ".ps1",
             ".log", ".svg", ".xml", ".yml", ".yaml", ".toml", ".ini", ".cfg"}
BINARY_EXTS = {".pdf", ".docx", ".xlsx"}   # 文档属性/元数据按字节与 docProps 抽查

SKIP_REASONS = [
    ("paper_output/results/production/final_v6a/outputs/*_unrounded.csv.gz",
     "未舍入原精度中间文件（gzip 已压缩，约 44 MB），题目只要求四位小数工作簿；进包会直接超 20 MB"),
    ("paper_output/results/production/final_v6a/outputs/ 整目录",
     "整目录实测 55.85 MB，含未舍入中间文件，禁止整目录打包"),
    ("paper_output/code/review_delivery/.vs/**",
     "Visual Studio 本机索引与 Copilot 聊天缓存，含本机环境信息，不入包"),
    ("paper_output/code/review_delivery/A_CodeReview.sln / *.pyproj",
     "Visual Studio 解决方案文件，任务书明确可不纳入（本机绝对路径，无复现价值）"),
    ("paper_output/code/review_delivery/tools/exportPathFixBefore/**",
     "修复前旧导出器与旧映射归档，已被 exportPathFix_v2 取代"),
    ("paper_output/code/review_delivery/runtime/exportPathFix_v2/Q3,Q4/**",
     "N40 定向验证的中间工作簿与 gz，与 final_v6a 正式产物重复"),
    ("paper_output/code/{data,modeling,verification}/**.py（蛇形命名原始实现）",
     "非人工审查交付版；交付版为 review_delivery 驼峰命名八个核心模块。"
     "论文附录 B 另列 prepareData.py/publicationPlots.py/validateBessel.py 等 8 个脚本，"
     "工作区内只有这些蛇形命名原件，未纳入（可用 --include-legacy-pipeline 追加）"),
    ("**/*.png（图件位图版本、MATLAB/GUI 截图）",
     "附录 A 第 9 项只要求矢量版本（PDF/SVG）与绘图数据；位图与本机 GUI 截图不入包"),
    ("notes/A-modeling/2026-09-10/gui_final_v6a/**, data/final_visual_assets/**",
     "内部过程材料与体积预检包，含未匿名的内部证据路径"),
    ("final_v6a/{worker_started,worker_success,launch_claim}.json, publication_previous/, published_contracts/",
     "编排状态与历史发布快照，非外发运行记录必需项"),
]


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def build_plan(include_legacy: bool):
    """返回 [(源相对路径, 包内相对路径)]，并做存在性与守卫检查。"""
    plan, missing_sources = [], []
    if AI_PDF.is_file():                      # 由 AI 工具使用详情 PDF 生成方提供
        plan.append(("paper_output/submission/支撑材料/AI工具使用详情.pdf",
                     "AI工具使用详情.pdf"))
    for src, dst in TOP_FILES + CODE_FILES + DOC_FILES + FIGURE_FILES + EVIDENCE_FILES:
        plan.append((src, dst))

    sweeps = list(SWEEPS)
    if include_legacy:
        sweeps += [(s, d, e, r"$^") for s, d, e in LEGACY_PIPELINE]

    for src_dir, dst_dir, exts, exclude_re in sweeps:
        base = ROOT / src_dir
        if not base.is_dir():
            missing_sources.append(src_dir + "/  (目录不存在)")
            continue
        for cur, dirs, files in os.walk(base):
            dirs[:] = sorted(d for d in dirs if d not in ("__pycache__", ".vs", ".git"))
            rel_dir = Path(cur).relative_to(base).as_posix()
            for name in sorted(files):
                if Path(name).suffix.lower() not in exts:
                    continue
                rel = name if rel_dir == "." else rel_dir + "/" + name
                if exclude_re != r"$^" and re.search(exclude_re, rel):
                    continue
                plan.append((src_dir + "/" + rel, dst_dir + "/" + rel))

    seen, deduped = set(), []
    for src, dst in plan:
        if dst in seen:
            raise SystemExit("包内路径重复: " + dst)
        seen.add(dst)
        if FORBIDDEN_ENTRY_RE.search(dst):
            raise SystemExit("硬守卫拦截（禁止入包）: " + dst)
        if not (ROOT / src).is_file():
            missing_sources.append(src)
            continue
        deduped.append((src, dst))
    return deduped, missing_sources


def stage_copy(plan):
    """复制到暂存目录（不改动源文件），返回 [(src, dst, staged, bytes, sha)]。"""
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    staged = []
    for src_rel, dst_rel in plan:
        src = ROOT / src_rel
        dst = STAGE / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        n_src, n_dst = src.stat().st_size, dst.stat().st_size
        if n_src != n_dst:
            raise SystemExit("复制字节数不一致: " + src_rel)
        staged.append((src_rel, dst_rel, dst, n_dst, sha256_file(dst)))
    return staged


def write_zip(staged):
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for _src, dst_rel, staged_path, _n, _h in sorted(staged, key=lambda r: r[1]):
            zf.write(staged_path, arcname=dst_rel)
    return ZIP_PATH.stat().st_size


def readback(staged):
    """解压回读：逐条 CRC 校验、条目数、解压后总字节、条目 SHA256。"""
    staged_by_name = {dst: (src, staged_path, n, h)
                      for src, dst, staged_path, n, h in staged}
    entries, total_uncompressed, total_compressed = [], 0, 0
    with zipfile.ZipFile(ZIP_PATH) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise SystemExit("CRC 校验失败: " + bad)
        for info in sorted(zf.infolist(), key=lambda i: i.filename):
            blob = zf.read(info.filename)          # 触发 CRC 校验
            h = hashlib.sha256(blob).hexdigest()
            total_uncompressed += len(blob)
            total_compressed += info.compress_size
            src, staged_path, n_staged, h_staged = staged_by_name[info.filename]
            entries.append({
                "path": info.filename,
                "bytes": len(blob),
                "compressed_bytes": info.compress_size,
                "sha256": h,
                "source": src,
                "source_sha256": h_staged,
                "source_sha256_match": h == h_staged,
                "source_bytes_match": len(blob) == n_staged,
                "crc": "%08X" % info.CRC,
            })
    return entries, total_uncompressed, total_compressed


def identity_scan(entries):
    """检查包内路径名与文本内容是否出现身份字符串。"""
    hard, review, scanned = [], [], 0
    for e in entries:
        name = e["path"]
        for tok in HARD_TOKENS:
            if tok in name:
                hard.append({"where": "entry-name", "path": name, "token": tok})
        for tok in REVIEW_TOKENS:
            if tok in name:
                review.append({"where": "entry-name", "path": name, "token": tok})
        if Path(name).suffix.lower() not in TEXT_EXTS or e["bytes"] > 8 * 1024 * 1024:
            continue
        scanned += 1
        blob = (STAGE / name)
        try:
            text = blob.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for tok in HARD_TOKENS:
                if tok in line:
                    hard.append({"where": "content", "path": name, "line": lineno,
                                 "token": tok, "context": line.strip()[:160]})
            for tok in REVIEW_TOKENS:
                if tok in line:
                    review.append({"where": "content", "path": name, "line": lineno,
                                   "token": tok, "context": line.strip()[:160]})
    binary, props = [], []
    for e in entries:
        suf = Path(e["path"]).suffix.lower()
        if suf not in BINARY_EXTS:
            continue
        blob = (STAGE / e["path"]).read_bytes()
        for tok in HARD_TOKENS:
            for enc in ("utf-8", "utf-16-be"):
                try:
                    pat = tok.encode(enc)
                except UnicodeEncodeError:
                    continue
                if pat and pat in blob:
                    binary.append({"path": e["path"], "token": tok, "encoding": enc})
                    break
        if suf in (".docx", ".xlsx") and zipfile.is_zipfile(STAGE / e["path"]):
            with zipfile.ZipFile(STAGE / e["path"]) as zz:
                for nm in zz.namelist():
                    if not nm.startswith("docProps/"):
                        continue
                    text = zz.read(nm).decode("utf-8", "replace")
                    for tok in HARD_TOKENS:
                        if tok in text:
                            props.append({"path": e["path"], "part": nm, "token": tok})
    return {"scanned_text_entries": scanned, "hard_hits": hard, "review_hits": review,
            "binary_metadata_hits": binary, "docprops_hits": props,
            "binary_note": "PDF/Office 二进制按 utf-8 与 utf-16-be 逐字节抽查；"
                           "PDF 正文流通常已压缩，元数据（Info/XMP）一般未压缩，"
                           "docProps 为解压后解析结果"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-legacy-pipeline", action="store_true",
                    help="额外纳入 paper_output/code 下蛇形命名的原始实现")
    args = ap.parse_args()

    os.chdir(ROOT)
    plan, missing_sources = build_plan(args.include_legacy_pipeline)
    staged = stage_copy(plan)
    zip_bytes = write_zip(staged)
    entries, total_uncompressed, total_compressed = readback(staged)
    scan = identity_scan(entries)

    names = {e["path"] for e in entries}
    result_sha = {e["path"]: e["sha256"] for e in entries
                  if re.fullmatch(r"result[1-4]\.xlsx", e["path"])}
    ai_pdf_entry = next((e for e in entries if e["path"] == "AI工具使用详情.pdf"), None)

    appendix_status = []
    for item, desc in APPENDIX_A:
        if item.endswith("/"):
            present = any(n.startswith(item) for n in names)
        else:
            present = item in names
        appendix_status.append({
            "item": item, "description": desc, "packaged": present,
            "note": "" if present else ("待补：由 AI 工具使用详情 PDF 生成方补齐"
                                        if item.endswith(".pdf") else "缺失"),
        })

    dt_utc = datetime.now(timezone.utc)
    dt_bj = dt_utc.astimezone(timezone(timedelta(hours=8)))
    manifest = {
        "schema_version": "1.0",
        "generated_by": "paper_output/submission/支撑材料/build_support_package.py",
        "generated_at_utc": dt_utc.isoformat(timespec="seconds"),
        "generated_at_beijing": dt_bj.strftime("%Y-%m-%d %H:%M:%S"),
        "zip_path": "paper_output/submission/支撑材料/A题_支撑材料.zip",
        "zip_bytes": zip_bytes,
        "limit_bytes": LIMIT_BYTES,
        "under_limit": zip_bytes <= LIMIT_BYTES,
        "entry_count": len(entries),
        "total_uncompressed_bytes": total_uncompressed,
        "total_compressed_bytes": total_compressed,
        "crc_check": "pass",
        "appendix_a_check": {"all_packaged": all(a["packaged"] for a in appendix_status),
                             "items": appendix_status},
        "result_xlsx_sha256": result_sha,
        "ai_pdf": ({"present": True, "bytes": ai_pdf_entry["bytes"],
                    "sha256": ai_pdf_entry["sha256"]} if ai_pdf_entry
                   else {"present": False, "status": "待补：打包时 AI工具使用详情.pdf 尚未生成"}),
        "missing_sources": missing_sources,
        "skipped": [{"path_or_pattern": p, "reason": r} for p, r in SKIP_REASONS],
        "identity_scan": scan,
        "source_files_unmodified": True,
        "staging_dir": "tmp/cache/support_package_stage",
        "entries": entries,
    }
    hard_total = len(scan["hard_hits"]) + len(scan["binary_metadata_hits"]) + len(scan["docprops_hits"])
    scan["hard_hits_total"] = hard_total
    if hard_total == 0:
        scan["conclusion"] = "硬身份词零命中（文件名/夹名、文本内容、PDF/Office 元数据与 docProps）"
    else:
        scan["conclusion"] = "存在硬身份词命中，需人工处理"

    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                             encoding="utf-8")

    print("=" * 74)
    print("压缩包: %s" % ZIP_PATH)
    print("压缩包字节: %d  (上限 %d, <=20MB: %s)" % (zip_bytes, LIMIT_BYTES,
                                                "是" if zip_bytes <= LIMIT_BYTES else "否"))
    print("条目数: %d   解压后总字节: %d   压缩后总字节: %d" % (len(entries), total_uncompressed, total_compressed))
    print("附录 A 十项齐全: %s" % ("是" if manifest["appendix_a_check"]["all_packaged"] else "否"))
    for a in appendix_status:
        if not a["packaged"]:
            print("   [缺失] %s  %s" % (a["item"], a["note"]))
    for r in sorted(result_sha):
        print("   %-14s %s  %d B" % (r, result_sha[r][:16] + "...",
                                     next(e["bytes"] for e in entries if e["path"] == r)))
    print("身份词扫描: 文本条目 %d 个, 硬命中 %d (文本 %d + 二进制元数据 %d + docProps %d), 待目视 %d" % (
        scan["scanned_text_entries"], hard_total, len(scan["hard_hits"]),
        len(scan["binary_metadata_hits"]), len(scan["docprops_hits"]), len(scan["review_hits"])))
    for h in (scan["hard_hits"] + scan["binary_metadata_hits"] + scan["docprops_hits"])[:10]:
        print("   [硬命中] %s" % h)
    for h in scan["review_hits"][:10]:
        print("   [待目视] %s:%s %s ..." % (h["path"], h.get("line", "-"), h["token"]))
    if missing_sources:
        print("源文件缺失: %d" % len(missing_sources))
        for m in missing_sources:
            print("   " + m)
    print("清单: %s" % MANIFEST_PATH)
    return 0 if (zip_bytes <= LIMIT_BYTES and hard_total == 0) else 2


if __name__ == "__main__":
    raise SystemExit(main())
