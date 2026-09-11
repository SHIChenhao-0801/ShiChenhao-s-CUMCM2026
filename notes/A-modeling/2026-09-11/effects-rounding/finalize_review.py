"""Check references and unchanged numerical sources, then index the screenshot audit."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

root = Path.cwd().resolve()
assert root.name == "2026CUMCM"
folder = Path(__file__).resolve().parent


def record(path):
    path = Path(path)
    with path.open("rb") as stream:
        sha = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size,
            "sha256": sha}


def readJson(name):
    return json.loads((folder / name).read_text(encoding="utf-8"))


reports = ["截图七项物理机制与四位小数复核.md", "四张易错点截图逐条对照与判断.md",
           "physics-effects-review.md", "rounding-review.md",
           "截图易错点_题意与输出复核.md", "截图易错点_物理与数值复核.md"]
linkChecks = []
for name in reports:
    path = folder / name
    text = path.read_text(encoding="utf-8")
    assert text.count(r"\[") == text.count(r"\]"), name
    for match in re.finditer(r"\]\((?:<([^>]+)>|([^\s)]+))\)", text):
        target = unquote(match.group(1) or match.group(2))
        if target.startswith(("https://", "http://", "#")):
            continue
        cleanTarget = re.sub(r":\d+$", "", target)
        local = Path(cleanTarget)
        if not local.is_absolute():
            local = path.parent / local
        assert local.exists(), (name, target)
        linkChecks.append({"document": name, "target": target, "exists": True})

mainText = (folder / reports[1]).read_text(encoding="utf-8")
itemIds = re.findall(r"^\| ((?:I|II|III|IV|V|VI)-\d+) ", mainText, re.M)
assert len(itemIds) == len(set(itemIds)) == 20, itemIds
localChecks = readJson("截图易错点_物理与数值复核.json")
assert localChecks["process_exit_code"] == 0
assert len(localChecks["checks"]) == 7 and all(c["pass"] for c in localChecks["checks"])
assert localChecks["warnings"] == []
radiation = readJson("radiation-scale-results.json")
assert len(radiation["rows"]) == 12 and radiation["new_PDE_solves"] == 0

sourceChecks = []
for data in [radiation, localChecks]:
    for old in data["sources"]:
        now = record(root / old["path"])
        assert now["sha256"] == old["sha256"], old["path"]
        sourceChecks.append(now)

screens = readJson("input-screenshots/source-records.json")
for source in screens["files"]:
    assert record(root / source["project_copy"])["sha256"] == source["sha256"]
assert len(screens["files"]) == 5

core = root / "paper_output/code/review_delivery/dryingCore.py"
lines = core.read_text(encoding="utf-8").splitlines()
assert "原始环境时间" in lines[31]
errata = {
    "status": "COMMENT_ERRATUM_RECORDED_FROZEN_SOURCE_NOT_EDITED",
    "source": record(core), "line": 32, "current_comment": lines[31],
    "corrected_comment_proposed": "# 读取清洗后的环境表：time_s单位s，temperature_K单位K；环境水分列保留题给kg/kg数值，并按等效Ceq使用，真实气相质量基准与气固映射待核；记录输入哈希。",
    "numerical_behavior_changed": False,
    "reason_to_retain_old_source": "The exact frozen source remains paired with its completed CLI/GUI run evidence; this task is a read-only review, and the corrected wording is delivered as an explicit erratum.",
}
(folder / "source-comment-erratum.json").write_text(
    json.dumps(errata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

summary = {
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SEVEN_EFFECTS_AND_TWENTY_PITFALLS_REVIEW_COMPLETE_WITH_EXPLICIT_CORRECTIONS",
    "user_scope": "All seven physical items, four-decimal output and all four added screenshots",
    "original_seven_effects": 7, "unique_pitfall_items": itemIds,
    "user_images_byte_preserved": 5, "local_algebra_checks_passed": 7,
    "radiation_algebra_scenarios": 12, "new_PDE_solves": 0,
    "frozen_core_results_modified": False, "new_GUI_reproduction": False,
    "human_review": "pending",
    "physical_prediction_accuracy": "not established without independent measurements",
    "Q4_template_correction": "Original is a single Sheet1 with 0,0.1,0.2,ellipsis,surface. The present 0..2 cm rectangular union and auxiliary radius sheet are declared export choices, not explicitly mandated original columns/sheets.",
    "Q2_original_requirement": "Whole-process Appendix 3 from t=0; six first-three-hour paper times, not Appendix 2/3 stage switching.",
    "Q3_rounding": "critical approximation 57.4723h; separately checked strictly feasible 4-decimal report 57.4724h",
    "Q4_rounding": "both displayed critical approximation and strictly feasible report 51.0906h",
    "source_comment_erratum": record(folder / "source-comment-erratum.json"),
    "linked_local_files_checked": linkChecks,
    "unchanged_numeric_sources_checked": sourceChecks,
    "artifacts": [record(folder / name) for name in reports + [
        "physics-effects-review.json", "rounding-review.json",
        "截图易错点_题意与输出复核.json", "截图易错点_物理与数值复核.json",
        "radiation-scale-results.json", "radiation_scale_check.py", "readback-rounding.py",
        "input-screenshots/source-records.json"]],
    "independent_text_review": "physics and template subagents reviewed respective root explanations; root corrected the Q4 template claim and six Q2 paper times before this snapshot",
    "helper": record(Path(__file__).resolve()),
}
(folder / "review_manifest.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": summary["status"], "items": len(itemIds),
                  "local_links": len(linkChecks), "checks": len(localChecks["checks"]),
                  "manifest": record(folder / "review_manifest.json")},
                 ensure_ascii=False, indent=2))
