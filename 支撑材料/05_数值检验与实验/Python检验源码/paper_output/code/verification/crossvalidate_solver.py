"""Cross-validation of the A-problem drying-time conclusion by independent methods.

Four independent blocks, all additive: no frozen model, setting, input or result
is modified. Everything is written under paper_output/results/crossvalidation/.

Block 1  time-integrator cross-validation   BDF vs Radau at fixed N
Block 2  water-flux face-scheme convergence Kirchhoff vs harmonic under refinement
Block 3  latent-heat model modification     surface evaporation-cooling scenarios
Block 4  threshold & scaling robustness     post-processing on the same solves

Sandbox note: disk_dense.DenseCache uses tempfile.mkdtemp, whose directories this
session's file sandbox cannot open. tempfile.mkdtemp is replaced by an equivalent
os.mkdir-based implementation before importing the solver. No solver logic changes.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile
import time
import traceback
import uuid
from dataclasses import replace
from datetime import datetime, timezone

ROOT = pathlib.Path(r"D:\Document\数学建模\2026CUMCM")
CODE = ROOT / "paper_output" / "code" / "modeling"


def _mkdtemp(suffix=None, prefix=None, dir=None):
    base = pathlib.Path(dir)
    for _ in range(200):
        candidate = base / ((prefix or "tmp") + uuid.uuid4().hex[:12] + (suffix or ""))
        if not candidate.exists():
            candidate.mkdir(parents=False)
            return str(candidate)
    raise FileExistsError("no unused temp name")


tempfile.mkdtemp = _mkdtemp

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.chdir(ROOT)
sys.dont_write_bytecode = True
sys.path.insert(0, str(CODE))

import numpy as np  # noqa: E402

import drying_core  # noqa: E402
from drying_core import Settings, solve_case  # noqa: E402

try:
    import q3_model  # noqa: E402

    completion = q3_model.completion
except Exception:  # pragma: no cover - fallback keeps the block self-contained
    completion = None

OUT = ROOT / "paper_output" / "results" / "crossvalidation"
BASE = Settings(intervals=800, rtol=1e-10, atol_temperature=1e-10,
                atol_moisture=1e-12, early_max_step_s=2.0, max_step_s=120.0,
                face_scheme="kirchhoff", jacobian_mode="analytic")


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def runCase(name, settings):
    started = time.perf_counter()
    record = {"case": name, "settings": {k: v for k, v in settings.__dict__.items()},
              "startedAtUtc": utcnow()}
    run = None
    try:
        run = solve_case(settings)
        diagnostic = run.diagnostics()
        record["diagnostics"] = diagnostic
        record["event_s"] = run.event_s
        record["event_h"] = None if run.event_s is None else run.event_s / 3600.0
        record["end_s"] = run.end_s
        if completion is not None and settings.question != "Q1":
            record["completion"] = completion(run)
        record["status"] = "computed"
    except Exception as error:  # keep the failure, never hide it
        record["status"] = "failed"
        record["error"] = f"{type(error).__name__}: {error}"
        record["traceback"] = traceback.format_exc()
    finally:
        if run is not None:
            try:
                run.close()
            except Exception:
                pass
    record["elapsedSeconds"] = time.perf_counter() - started
    print(json.dumps({k: record[k] for k in ("case", "status", "elapsedSeconds")
                      if k in record} |
                     {"event_h": record.get("event_h")}, ensure_ascii=False), flush=True)
    return record


def block1():
    """Independent time integrators at a fixed spatial discretisation.

    BDF/NDF (variable-order implicit) and Radau IIA (3-stage implicit Runge-Kutta)
    are different integration families with different truncation-error structure,
    so agreement at fixed N isolates the time integrator as an error source.

    LSODA was attempted and removed: SciPy's ODEPACK wrapper is dense, cannot
    consume the sparse analytic Jacobian, and with a dense finite-difference
    Jacobian at N = 200 it did not finish in a practical time. The third
    independent integrator is therefore the MATLAB ode15s implementation recorded
    under paper_output/qa/matlab_crosscheck_20260911, not a third SciPy method.
    """
    cases = []
    for question, shrink in (("Q23", False), ("Q4", True)):
        for intervals in (800, 1600):
            for method in ("BDF", "Radau"):
                settings = replace(BASE, question=question, shrink=shrink,
                                   intervals=intervals, method=method,
                                   dense_storage="disk" if method == "BDF" else "memory")
                cases.append((f"B1_{question}_{method}_N{intervals}", settings))
    return cases


def block2():
    """Water-flux face representation under grid refinement.

    A coarse grid separates the two schemes by a large factor; the test is whether
    they converge to the same answer as the mesh is refined, which is what makes the
    production Kirchhoff result grid-independent rather than scheme-dependent.
    """
    cases = []
    for intervals in (400, 800, 1600):
        for scheme in ("kirchhoff", "harmonic"):
            settings = replace(BASE, question="Q23", intervals=intervals,
                               face_scheme=scheme)
            cases.append((f"B2_Q23_{scheme}_N{intervals}", settings))
    for intervals in (400, 800, 1600):
        for scheme in ("kirchhoff", "harmonic"):
            settings = replace(BASE, question="Q4", shrink=True,
                               intervals=intervals, face_scheme=scheme)
            cases.append((f"B2_Q4_{scheme}_N{intervals}", settings))
    return cases


def block3():
    """Model modification: explicit surface evaporative cooling (latent heat).

    The fraction is a scenario parameter, not a calibrated physical constant:
    the problem provides no sorption isotherm that would close the surface vapour
    balance, so an envelope is reported instead of a single point prediction.
    """
    cases = []
    for question, shrink in (("Q23", False), ("Q4", True)):
        for fraction in (0.0, 0.25, 0.5, 1.0):
            settings = replace(BASE, question=question, shrink=shrink,
                               intervals=800, surface_latent_fraction=fraction)
            cases.append((f"B3_{question}_L{fraction:g}_N800", settings))
        settings = replace(BASE, question=question, shrink=shrink, intervals=1600,
                           surface_latent_fraction=1.0)
        cases.append((f"B3_{question}_L1_N1600", settings))
    return cases


BLOCKS = {"1": block1, "2": block2, "3": block3}


def main():
    wanted = sys.argv[1] if len(sys.argv) > 1 else "1"
    runId = sys.argv[2] if len(sys.argv) > 2 else "cv_" + wanted
    directory = OUT / runId
    directory.mkdir(parents=True, exist_ok=True)
    records = []
    done = set()
    casesPath = directory / "cases.json"
    if casesPath.exists():  # resume: never recompute a case that already succeeded
        records = json.loads(casesPath.read_text(encoding="utf-8"))
        done = {r["case"] for r in records if r.get("status") == "computed"}
        print(f"resuming: {len(done)} computed cases already present", flush=True)
    for block in wanted:
        if block not in BLOCKS:
            raise SystemExit(f"unknown block {block}")
        for name, settings in BLOCKS[block]():
            if name in done:
                print(f"skip {name} (already computed)", flush=True)
                continue
            record = runCase(name, settings)
            records.append(record)
            casesPath.write_text(json.dumps(records, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
    summary = {"runId": runId, "blocks": wanted,
               "solverCode": drying_core.file_record(pathlib.Path(drying_core.__file__)),
               "finishedAtUtc": utcnow(),
               "computed": sum(1 for r in records if r["status"] == "computed"),
               "failed": sum(1 for r in records if r["status"] == "failed")}
    (directory / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
