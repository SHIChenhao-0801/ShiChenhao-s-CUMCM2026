"""Bounded independent beta-by-grid/flux check using the frozen local core.

No peer code or pickle is imported. Each case runs in a serial child process,
saves the core's provenance immediately, and is killed if the total wall budget
is exhausted. Numerical execution is not VS GUI reproduction or human review.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import warnings

for _task_name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_task_name] = "1"

import numpy as np
import scipy
from drying_core import (ROOT, Settings, solve_case, save_run,
                         LOADED_CODE_SHA256 as CORE_SHA256)
import analytic_jacobian
from q3_model import completion

SOURCE = Path(__file__).resolve()
SOURCE_SHA256 = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
EXPECTED_CORE_SHA256 = "f113d965ce87a43ba86a95c291ce721120bf9543180bdcbd58e7c43f06eb76de"
RESULTS = ROOT / "paper_output/results/peer_beta_check"
GRID = (200, 400, 800)
SCHEMES = ("harmonic", "kirchhoff")
BETAS = (8e-7, 1.6e-6)
SAMPLE_SECONDS = np.array([0., 60., 300., 1800., 3600., 7200., 10800.,
                          14400., 21600., 43200., 86400., 129600.,
                          172800., 194400., 216000., 259200., 345600.,
                          432000., 648000.])


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False,
                               allow_nan=False), encoding="utf-8")


def verify_frozen():
    if CORE_SHA256 != EXPECTED_CORE_SHA256:
        raise RuntimeError("This check requires the declared frozen core v4")
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise RuntimeError("Check source changed after import")
    actual = hashlib.sha256(SOURCE.with_name("drying_core.py").read_bytes()).hexdigest()
    if actual != CORE_SHA256:
        raise RuntimeError("Core changed after import")
    actual_jac = hashlib.sha256(Path(analytic_jacobian.__file__).read_bytes()).hexdigest()
    if actual_jac != analytic_jacobian.LOADED_CODE_SHA256:
        raise RuntimeError("Analytic Jacobian changed after import")


def case_name(intervals, scheme, beta_factor):
    return f"N{intervals}_{scheme}_beta{beta_factor}"


def worker(intervals, scheme, beta_factor):
    verify_frozen()
    name = case_name(intervals, scheme, beta_factor)
    directory = RESULTS / name
    if directory.exists():
        raise FileExistsError(f"Refusing to overwrite existing case {directory}")
    started, cpu_started = time.perf_counter(), time.process_time()
    record = {"name": name, "started_utc": datetime.now(timezone.utc).isoformat(),
              "source_sha256": SOURCE_SHA256, "core_sha256": CORE_SHA256,
              "jacobian_sha256": analytic_jacobian.LOADED_CODE_SHA256,
              "gui_reproduced": False, "human_review_status": "pending"}
    captured = []
    try:
        settings = Settings(question="Q23", intervals=intervals, beta=8e-7*beta_factor,
                            face_scheme=scheme, jacobian_mode="analytic",
                            rtol=1e-8, atol_moisture=1e-10, atol_temperature=1e-8,
                            early_max_step_s=10., max_step_s=300., horizon_h=240.,
                            shrink=False, surface_latent_fraction=0.,
                            boundary_extension="nominal",
                            tail_temperature_C=50., tail_equilibrium=.05)
        record["settings"] = asdict(settings)
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            run = solve_case(settings)
            # Save the real input/core/Jacobian hash evidence before other analyses.
            summary = save_run(run, directory)
            report = completion(run) if run.event_s is not None else None
            times = np.unique(np.r_[SAMPLE_SECONDS[SAMPLE_SECONDS <= run.end_s],
                                    run.end_s])
            states = run.state(times)
            C, T = states[1:-1:2], states[:-1:2]
            environment = run.model.environment(times)
            np.savez_compressed(directory / "comparison_fields.npz",
                                times_s=times, x=run.model.x, C=C, T_K=T,
                                mean_C=2*run.model.w@C,
                                surface_excess=C[-1]-environment[1])
            diagnostics = summary["diagnostics"]
            finite = all(np.isfinite(piece.y).all() for piece in run.pieces)
        warning_records = [{"category": item.category.__name__, "message": str(item.message),
                            "filename": item.filename, "line": item.lineno}
                           for item in captured]
        checks = {
            "solver_success": bool(diagnostics["solver_success"]),
            "event_found": run.event_s is not None,
            "finite_accepted_states": bool(finite),
            "nonnegative_C": diagnostics["min_C"] >= -1e-10,
            "initial_C_upper_bound": diagnostics["max_C"] <= 2.55 + 1e-8,
            "positive_properties": bool(diagnostics["positive_properties"]),
            "mass_residual_below_1e-9": diagnostics["max_mass_balance_abs_kg_per_kg"] < 1e-9,
            "radial_nonincrease_tolerance_1e-8": diagnostics["max_radial_C_increase"] <= 1e-8,
            "strictly_dry_at_end": bool(diagnostics["strictly_dry_at_end"]),
            "strict_report_verified": report is not None and report["max_C_at_reported_time"] < .15,
            "no_warnings": not warning_records,
        }
        record.update(status="PASS" if all(checks.values()) else "QUALITY_FAIL",
                      diagnostics=diagnostics, completion=report, checks=checks,
                      warnings=warning_records,
                      min_sampled_surface_excess=float((C[-1]-environment[1]).min()))
        verify_frozen()
    except Exception as exc:
        directory.mkdir(parents=True, exist_ok=True)
        record.update(status="FAIL", error=f"{type(exc).__name__}: {exc}",
                      traceback=traceback.format_exc(),
                      warnings=[str(item.message) for item in captured])
    record["wall_elapsed_s"] = time.perf_counter() - started
    record["cpu_elapsed_s"] = time.process_time() - cpu_started
    write_json(directory / "record.json", record)
    print(json.dumps({"case": name, "status": record["status"],
                      "event_h": record.get("diagnostics", {}).get("event_h"),
                      "wall_s": record["wall_elapsed_s"]}), flush=True)
    return 0 if record["status"] == "PASS" else 1


def comparisons(records):
    lookup = {row["name"]: row for row in records
              if row.get("diagnostics", {}).get("event_s") is not None}
    pairs = []
    for intervals in GRID:
        for scheme in SCHEMES:
            names = [case_name(intervals, scheme, factor) for factor in (1, 2)]
            if not all(name in lookup for name in names):
                continue
            first, second = (lookup[name] for name in names)
            with np.load(RESULTS/names[0]/"comparison_fields.npz", allow_pickle=False) as a, \
                    np.load(RESULTS/names[1]/"comparison_fields.npz", allow_pickle=False) as b:
                times, ia, ib = np.intersect1d(a["times_s"], b["times_s"], return_indices=True)
                moisture_difference = b["C"][:, ib]-a["C"][:, ia]
                flat = int(np.argmax(moisture_difference))
                space_index, time_index = np.unravel_index(flat, moisture_difference.shape)
                row = {
                    "intervals": intervals, "scheme": scheme,
                    "beta1_event_h": first["diagnostics"]["event_h"],
                    "beta2_event_h": second["diagnostics"]["event_h"],
                    "delta_beta2_minus_beta1_s":
                        second["diagnostics"]["event_s"]-first["diagnostics"]["event_s"],
                    "delta_percent":
                        100*(second["diagnostics"]["event_s"]/first["diagnostics"]["event_s"]-1),
                    "common_sample_times_s": times.tolist(),
                    "max_sampled_C_beta2_minus_beta1": float(moisture_difference.max()),
                    "min_sampled_C_beta2_minus_beta1": float(moisture_difference.min()),
                    "positive_difference_location_x": float(a["x"][space_index]),
                    "positive_difference_time_s": float(times[time_index]),
                    "max_sampled_mean_C_beta2_minus_beta1":
                        float((b["mean_C"][ib]-a["mean_C"][ia]).max()),
                    "max_abs_sampled_temperature_difference_K":
                        float(np.max(np.abs(b["T_K"][:, ib]-a["T_K"][:, ia]))),
                }
                pairs.append(row)
    return pairs


def main(budget_s):
    verify_frozen()
    if not 0 < budget_s <= 480:
        raise ValueError("Total budget must be within 480 seconds")
    if RESULTS.exists():
        raise FileExistsError("Refusing to overwrite any existing beta check")
    RESULTS.mkdir(parents=True)
    started = time.perf_counter()
    planned = [(n, scheme, factor) for n in GRID for scheme in SCHEMES for factor in (1, 2)]
    records = []
    for intervals, scheme, factor in planned:
        name = case_name(intervals, scheme, factor)
        remaining = budget_s-(time.perf_counter()-started)
        if remaining <= 0:
            records.append({"name": name, "status": "NOT_RUN_BUDGET"})
            continue
        command = [sys.executable, "-B", str(SOURCE), "--worker", str(intervals),
                   scheme, str(factor)]
        try:
            result = subprocess.run(command, cwd=str(ROOT), timeout=remaining,
                                    capture_output=True, text=True, encoding="utf-8",
                                    errors="replace")
            directory = RESULTS/name
            directory.mkdir(parents=True, exist_ok=True)
            (directory/"stdout.log").write_text(result.stdout, encoding="utf-8")
            (directory/"stderr.log").write_text(result.stderr, encoding="utf-8")
            if (directory/"record.json").exists():
                record = json.loads((directory/"record.json").read_text(encoding="utf-8"))
            else:
                record = {"name": name, "status": "PROCESS_FAIL",
                          "returncode": result.returncode}
            records.append(record)
            print(result.stdout.strip() or json.dumps(record), flush=True)
        except subprocess.TimeoutExpired:
            directory = RESULTS/name
            directory.mkdir(parents=True, exist_ok=True)
            record = {"name": name, "status": "TIMEOUT_TOTAL_BUDGET",
                      "timeout_s": remaining}
            write_json(directory/"record.json", record)
            records.append(record)
            print(json.dumps(record), flush=True)
        write_json(RESULTS/"progress.json", {"records": records})
    pair_rows = comparisons(records)
    verify_frozen()
    result = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if len(records) == 12 and all(r["status"] == "PASS" for r in records)
                  else "INCOMPLETE_OR_FAILED",
        "source_sha256": SOURCE_SHA256, "core_sha256": CORE_SHA256,
        "jacobian_sha256": analytic_jacobian.LOADED_CODE_SHA256,
        "runtime": {"python": sys.version, "executable": sys.executable,
                    "numpy": np.__version__, "scipy": scipy.__version__,
                    "blas_thread_limit": 1},
        "budget_s": budget_s, "wall_elapsed_s": time.perf_counter()-started,
        "completed_child_cpu_s": sum(r.get("cpu_elapsed_s", 0.) for r in records),
        "planned_case_count": 12, "records": records, "paired_comparisons": pair_rows,
        "limitations": [
            "This is a local-core recomputation, not execution or reproduction of peer code.",
            "Only beta factors 1 and 2 and grids 200/400/800 are tested; no optimal beta is identified.",
            "Profile comparisons are at saved common times, not every continuous time.",
            "Quality checks and mass conservation do not prove event or field convergence.",
            "Full heat/moisture coupling is not automatically covered by a scalar comparison theorem.",
            "GUI reproduction and human review are pending; production choice is not changed."
        ],
    }
    write_json(RESULTS/"aggregate_summary.json", result)
    lines = ["# Beta/grid/flux independent check", "",
             "| N | face | beta 8e-7 event h | beta 1.6e-6 event h | beta2-beta1 s | change % |",
             "|---:|---|---:|---:|---:|---:|"]
    for row in pair_rows:
        lines.append(f"| {row['intervals']} | {row['scheme']} | {row['beta1_event_h']:.10f} | "
                     f"{row['beta2_event_h']:.10f} | {row['delta_beta2_minus_beta1_s']:.6f} | "
                     f"{row['delta_percent']:.6f} |")
    lines += ["", f"Status: {result['status']}. Wall seconds: {result['wall_elapsed_s']:.3f}.",
              "", "All values are conditional numerical events, not measured drying times.",
              "See aggregate_summary.json and each case's immediate summary.json for provenance."]
    (RESULTS/"numerical_table.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(json.dumps({"aggregate_status": result["status"],
                      "wall_s": result["wall_elapsed_s"]}), flush=True)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget-s", type=float, default=480.)
    parser.add_argument("--worker", nargs=3, metavar=("N", "SCHEME", "BETA_FACTOR"))
    arguments = parser.parse_args()
    if arguments.worker:
        n_value, scheme_value, factor_value = arguments.worker
        if int(n_value) not in GRID or scheme_value not in SCHEMES or int(factor_value) not in (1, 2):
            raise ValueError("Worker must belong to the preregistered 12 cases")
        raise SystemExit(worker(int(n_value), scheme_value, int(factor_value)))
    raise SystemExit(main(arguments.budget_s))
