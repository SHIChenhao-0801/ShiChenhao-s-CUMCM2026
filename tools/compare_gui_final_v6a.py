"""Read-only numerical artifact comparison; never imports or runs model code.

The GUI process exit and human acceptance are supplied by separate observed
evidence. Equal ZIP/GZIP data need not have equal container timestamps.
"""
from pathlib import Path
from datetime import datetime, timezone
import csv
import gzip
import hashlib
import json
import time
import xml.etree.ElementTree as ET
import zipfile
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "paper_output/results/production/final_v6a"
GUI = ROOT / "paper_output/results/gui_reproduction/gui_final_v6a"
OUT = ROOT / "notes/A-modeling/2026-09-10/gui_final_v6a"
BLOCK = 1024 * 1024


def stream_hash(stream):
    digest, count = hashlib.sha256(), 0
    while block := stream.read(BLOCK):
        digest.update(block)
        count += len(block)
    return {"uncompressed_bytes": count, "uncompressed_sha256": digest.hexdigest()}


def record(path):
    before = path.stat()
    with path.open("rb") as stream:
        value = stream_hash(stream)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError("File changed while reading: " + str(path))
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": after.st_size,
            "sha256": value["uncompressed_sha256"]}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def npz_comparison(left, right):
    records = []
    with np.load(left, allow_pickle=False) as a, np.load(right, allow_pickle=False) as b:
        keys_equal = sorted(a.files) == sorted(b.files)
        for key in sorted(set(a.files) & set(b.files)):
            x, y = a[key], b[key]
            same_shape_dtype = x.shape == y.shape and x.dtype == y.dtype
            same = same_shape_dtype and np.array_equal(x, y, equal_nan=True)
            maximum = None
            if same_shape_dtype and x.dtype.kind in "fiu":
                finite = np.isfinite(x) & np.isfinite(y)
                maximum = float(np.max(np.abs(x[finite] - y[finite]))) if finite.any() else 0.0
            records.append({"key": key, "shape": list(x.shape), "dtype": str(x.dtype),
                            "equal_including_nan_positions": bool(same),
                            "max_finite_absolute_difference": maximum})
    return {"keys_equal": keys_equal, "arrays": records,
            "equal": keys_equal and all(x["equal_including_nan_positions"] for x in records),
            "left": record(left), "right": record(right)}


def core_without_dates(data):
    root = ET.fromstring(data)
    for child in list(root):
        if child.tag in {"{http://purl.org/dc/terms/}created",
                         "{http://purl.org/dc/terms/}modified"}:
            root.remove(child)
    return ET.tostring(root)


def xlsx_comparison(left, right):
    entries, allowed_dates = [], []
    with zipfile.ZipFile(left) as a, zipfile.ZipFile(right) as b:
        same_names = sorted(a.namelist()) == sorted(b.namelist())
        for name in sorted(set(a.namelist()) & set(b.namelist())):
            with a.open(name) as aa, b.open(name) as bb:
                ah, bh = stream_hash(aa), stream_hash(bb)
            equal = ah == bh
            permissible = False
            if not equal and name == "docProps/core.xml":
                permissible = core_without_dates(a.read(name)) == core_without_dates(b.read(name))
                if permissible:
                    allowed_dates.append(name)
            entries.append({"entry": name, "left": ah, "right": bh,
                            "decompressed_bytes_equal": equal,
                            "only_allowed_created_modified_dates_differ": permissible})
    return {"left": record(left), "right": record(right),
            "entry_names_equal": same_names, "entries": entries,
            "allowed_metadata_date_differences": allowed_dates,
            "worksheet_xml_entries_equal": all(e["decompressed_bytes_equal"] for e in entries
                                               if e["entry"].startswith("xl/worksheets/")),
            "equal_numeric_and_format_payloads": same_names and all(
                e["decompressed_bytes_equal"] or e["only_allowed_created_modified_dates_differ"]
                for e in entries)}


def main():
    if Path.cwd().resolve() != ROOT:
        raise RuntimeError("Run from the competition workspace")
    if not (GUI / "review_result.json").exists():
        raise RuntimeError("GUI review_result.json is not present; final audit must wait")
    started = time.perf_counter()
    result = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "Independent CLI/GUI numerical artifact equality; no model solve and no GUI-exit certification.",
              "cli_version": CLI.name, "gui_version": GUI.name,
              "gui_observed_process_exit": "Not certified by this audit; see separate Visual Studio Output evidence.",
              "human_review": "pending", "performance_comparison": "Not made; GUI duration includes breakpoint pauses.",
              "source": record(Path(__file__).resolve()), "checks": []}
    checks = result["checks"]
    def check(name, passed, detail=None):
        item = {"name": name, "passed": bool(passed)}
        if detail is not None:
            item["detail"] = detail
        checks.append(item)
    a, b = read_json(CLI / "launch.json"), read_json(GUI / "launch.json")
    check("source_input_inventories_equal", a["input_files"] == b["input_files"])
    check("runtime_equal", a["runtime"] == b["runtime"])
    check("font_equal", a["font"] == b["font"])
    result["inputs"] = a["input_files"]
    for expected in a["input_files"]:
        actual = record(ROOT / expected["path"])
        check("current_input:" + expected["path"],
              actual["sha256"] == expected["sha256"] and actual["bytes"] == expected["bytes"])
    review = read_json(GUI / "review_result.json")
    result["review_result"] = record(GUI / "review_result.json")
    result["review_result_status"] = review["status"]
    check("review_has_three_complete_trajectories", set(review["summaries"]) == {"Q1", "Q23", "Q4"})
    result["trajectories"] = []
    for question in ("Q1", "Q23", "Q4"):
        x, y = read_json(CLI / question / "summary.json"), read_json(GUI / question / "summary.json")
        fields = ("settings", "code", "jacobian_code", "dense_storage_code", "inputs",
                  "completion", "reproduction_samples", "metric_samples")
        field_checks = {k: x.get(k) == y.get(k) for k in fields}
        # elapsed_s includes debugger pauses; comparing it as numerical data would be wrong.
        dx = {k: v for k, v in x["diagnostics"].items() if k != "elapsed_s"}
        dy = {k: v for k, v in y["diagnostics"].items() if k != "elapsed_s"}
        field_checks["diagnostics_except_elapsed_time"] = dx == dy
        field_checks["review_summary_matches_saved_summary"] = review["summaries"][question] == y
        field_checks["both_zero_solver_warnings"] = x["solver_warning_count"] == y["solver_warning_count"] == 0
        saved = npz_comparison(CLI / question / "sampled_solution.npz",
                               GUI / question / "sampled_solution.npz")
        check("trajectory:" + question, all(field_checks.values()) and saved["equal"])
        result["trajectories"].append({"question": question, "field_checks": field_checks,
                                      "completion": y.get("completion"), "sampled_npz": saved,
                                      "cli_summary": record(CLI / question / "summary.json"),
                                      "gui_summary": record(GUI / question / "summary.json")})
        print("COMPARED trajectory " + question, flush=True)
    result["exports"] = []
    for q in range(1, 5):
        name = "result" + str(q)
        vp, vg = read_json(CLI / "outputs" / (name + ".validation.json")), read_json(
            GUI / "outputs" / (name + ".validation.json"))
        check("both_live_export_validation:" + name,
              vp["status"] == vg["status"] == "PASS" and
              vp["fully_verified_with_live_Run"] and vg["fully_verified_with_live_Run"] and
              vp["checked_cells"] == vg["checked_cells"])
        lp, lg = CLI / "outputs" / (name + "_unrounded.csv.gz"), GUI / "outputs" / (name + "_unrounded.csv.gz")
        with gzip.open(lp, "rb") as fp, gzip.open(lg, "rb") as fg:
            gp, gg = stream_hash(fp), stream_hash(fg)
        check("unrounded_gzip_payload:" + name, gp == gg)
        wb = xlsx_comparison(CLI / "outputs" / (name + ".xlsx"), GUI / "outputs" / (name + ".xlsx"))
        check("workbook_payload:" + name, wb["equal_numeric_and_format_payloads"])
        result["exports"].append({"question": "Q" + str(q), "checked_cells_each_run": vp["checked_cells"],
                                  "gzip": {"cli": record(lp), "gui": record(lg), "cli_payload": gp,
                                           "gui_payload": gg, "decoded_content_equal": gp == gg},
                                  "xlsx": wb, "gui_validation": record(GUI / "outputs" / (name + ".validation.json"))})
        print("COMPARED complete gzip/XLSX " + name, flush=True)
    result["paper_csvs"] = []
    csv_names = sorted(p.name for p in (CLI / "outputs").glob("q*_paper_*.csv"))
    check("seven_csv_names", len(csv_names) == 7 and csv_names ==
          sorted(p.name for p in (GUI / "outputs").glob("q*_paper_*.csv")))
    for name in csv_names:
        lp, lg = CLI / "outputs" / name, GUI / "outputs" / name
        with lp.open(encoding="utf-8-sig", newline="") as fp, lg.open(encoding="utf-8-sig", newline="") as fg:
            cp, cg = list(csv.reader(fp)), list(csv.reader(fg))
        check("paper_csv:" + name, cp == cg)
        result["paper_csvs"].append({"name": name, "data_rows": len(cp) - 1, "equal": cp == cg,
                                     "cli": record(lp), "gui": record(lg)})
    result["figure_arrays"] = []
    for name in ("fig_q1_profiles", "fig_q2_profiles", "fig_q3_drying", "fig_q4_drying"):
        compared = npz_comparison(CLI / "figures" / (name + "_data.npz"),
                                  GUI / "figures" / (name + "_data.npz"))
        check("figure_arrays:" + name, compared["equal"])
        result["figure_arrays"].append({"figure_id": name, **compared})
    # The completion gate is read again after all large payload reads.
    check("review_result_unchanged", result["review_result"] == record(GUI / "review_result.json"))
    result["status"] = "PASS_NUMERICAL_ARTIFACT_EQUIVALENCE" if all(x["passed"] for x in checks) else "FAIL"
    result["check_count"] = len(checks)
    result["failed_checks"] = [x for x in checks if not x["passed"]]
    result["audit_elapsed_seconds"] = time.perf_counter() - started
    result["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "independent_comparison.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": len(checks),
                      "failed": result["failed_checks"], "audit_seconds": result["audit_elapsed_seconds"]},
                     ensure_ascii=False), flush=True)
    return 0 if not result["failed_checks"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
