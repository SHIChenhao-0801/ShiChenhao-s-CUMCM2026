"""Verify the amended handoff against archived text and freeze this audit's index.

No PDE solve, result changes, network, GUI, or human approval is performed here.
Run from the 2026CUMCM project root with Python -B.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

ROOT = Path.cwd().resolve()
assert ROOT.name == "2026CUMCM", ROOT
QA = ROOT / "paper_output/qa/recheck_20260910_1828"
DOC = ROOT / "notes/A-modeling/2026-09-10"


def record(path: Path) -> dict:
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size, "sha256": digest}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def tables(text: str) -> list[str]:
    return re.findall(r"(?:^\|[^\n]*\n)+", text, re.M)


names = ["A题_完整建模与公式推导.md", "A题_建模浓缩交接.md"]
documents = []
for name, expected_count in zip(names, [98, 20]):
    before_path = QA / "documents_before" / name
    current_path = DOC / name
    before = before_path.read_text(encoding="utf-8")
    current = current_path.read_text(encoding="utf-8")
    old_math = re.findall(r"\\\[(.*?)\\\]", before, re.S)
    new_math = re.findall(r"\\\[(.*?)\\\]", current, re.S)
    assert old_math == new_math and len(new_math) == expected_count, name
    original_tables = tables(before)
    assert all(table in current for table in original_tables), name
    tags = re.findall(r"\\tag\{([^}]+)\}", current)
    if name == names[0]:
        assert len(tags) == len(set(tags)) == 92
        assert len(re.findall(r"^\| E0[1-9] \|", current, re.M)) == 9
    documents.append({"before": record(before_path), "current": record(current_path),
                      "display_math_blocks_unchanged": len(new_math),
                      "all_original_tables_unchanged": True,
                      "original_table_count": len(original_tables),
                      "registered_tags": len(tags)})

report_path = DOC / "A题_成果与重新核验报告.md"
all_documents = [DOC / n for n in names] + [report_path]
links = []
for path in all_documents:
    text = path.read_text(encoding="utf-8")
    for match in re.finditer(r"\]\((?:<([^>]+)>|([^\s)]+))\)", text):
        target = unquote(match.group(1) or match.group(2))
        if target.startswith(("https://", "http://", "#")):
            continue
        without_line = re.sub(r":\d+$", "", target)
        local = Path(without_line)
        if not local.is_absolute():
            local = path.parent / local
        assert local.exists(), (path.name, target)
        links.append({"document": path.name, "target": target, "exists": True})

agent_json = {name: read_json(QA / name) for name in [
    "data_scale_recheck.json", "physics_recheck.json", "numerical_recheck.json",
    "surface_time_recheck.json"]}
assert agent_json["data_scale_recheck.json"]["all_inputs_hash_unchanged"]
assert agent_json["physics_recheck.json"]["all_checked_display_formulas_unchanged"]
numeric = agent_json["numerical_recheck.json"]
assert len(numeric["production_current_hash_checks"]) == 107
assert all(item["matches"] for item in numeric["production_current_hash_checks"])

# Only files relevant to final text consistency are hashed again here. The
# independent numerical audit has already freshly checked all 107 production entries.
selected_sources = []
for item in numeric["production_current_hash_checks"]:
    rel = item["path"]
    if rel.startswith("paper_output/code/modeling/") or rel.endswith(".xlsx"):
        actual = record(ROOT / rel)
        assert actual["sha256"] == item["expected_sha256"], rel
        selected_sources.append(actual)
manifest = record(ROOT / "paper_output/results/production/final_v6a/run_manifest.json")
assert manifest["sha256"] == numeric["production_manifest"]["sha256"]
gate_path = ROOT / "paper_output/qa/evidence_gate_report.json"
assert read_json(gate_path)["status"] == "PASS"
assert record(gate_path)["sha256"] == record(QA / "evidence_gate_after.json")["sha256"]

now = datetime.now(timezone.utc).isoformat()
summary = {
    "schema_version": "1.0", "created_at_utc": now,
    "status": "CONDITIONAL_MODEL_RECHECK_COMPLETE_WITH_DISCLOSED_PHYSICAL_GAPS",
    "scope": "Fresh raw-data, algebra, saved-array and analytic-baseline audit; explanatory amendments only.",
    "new_production_PDE_solves": 0, "formal_S7_S8_started_by_this_audit": False,
    "new_core_algebra_defects_found_in_checked_model": 0,
    "physical_predictive_accuracy": "NOT_ESTABLISHED_NO_INTERNAL_OBSERVATIONS",
    "continuous_domain_strict_error_bound": "NOT_ESTABLISHED",
    "all_four_decimal_last_digits_stable": False,
    "human_approval": "pending", "new_audit_helpers_GUI_reproduced": False,
    "documents": documents, "unified_report": record(report_path),
    "document_links_checked": links, "production_manifest": manifest,
    "final_selected_source_hashes_match_independent_audit": selected_sources,
    "independent_agent_statuses": {name: value["status"] for name, value in agent_json.items()},
    "evidence": [record(QA / name) for name in [
        "data_scale_recheck.md", "data_scale_recheck.json", "physics_recheck.md",
        "physics_recheck.json", "physics_small_checks.json", "numerical_recheck.md",
        "numerical_recheck.json", "surface_time_recheck.json", "explanatory_corrections.json",
        "recovered_historical_source/reconstruction_record.json"]],
    "evidence_gate": {**record(gate_path), "status": "PASS",
                      "meaning": "provenance and artifact contract only; not empirical physical validation"},
    "independent_final_text_review": {
        "reviewer": "physics_derivations", "substantive_issues_found": 0,
        "minor_issue": "Two purpose/variable descriptions should precede their formulas",
        "minor_issue_corrected": True},
    "unresolved_physical_inputs": [
        "air humidity basis, transfer-coefficient basis and material sorption equilibrium",
        "effective versus component volumetric heat capacity and empirical density basis",
        "latent heat, phase transport, saturation and deformation closure",
        "environment beyond four hours and internal temperature/moisture validation"],
    "reproducibility_limit": "Historical coarse full-second spatial arrays were not retained; this audit rereads their reports and rechecks saved material samples, not every historical spatial sample.",
    "helper": record(Path(__file__).resolve())
}
save_json(QA / "recheck_summary.json", summary)

snapshot = {
    "created_at_utc": now, "status": summary["status"],
    "files": {path.name: {k: v for k, v in record(path).items() if k != "path"}
              for path in all_documents},
    "latest_recheck": record(QA / "recheck_summary.json"),
    "human_review": "pending",
    "delivery": "Not sent; user cancelled wake action and stopped Computer Use with Escape."
}
save_json(DOC / "handoff_files_snapshot.json", snapshot)
print(json.dumps({"status": summary["status"], "completed_at_utc": now,
                  "display_formula_counts": [d["display_math_blocks_unchanged"] for d in documents],
                  "original_tables_unchanged": [d["original_table_count"] for d in documents],
                  "links_checked": len(links), "selected_sources_rehashed": len(selected_sources),
                  "report": record(report_path), "summary": record(QA / "recheck_summary.json")},
                 ensure_ascii=False, indent=2))
