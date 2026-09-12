"""Audit dependency installation in a fresh, isolated venv; never run model PDEs."""
from __future__ import annotations

import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[3]
QA = ROOT / "paper_output/qa/portability_20260912"
PROBE = ROOT / "tmp/cache/portability_20260912/dependency_probe"
VENV = PROBE / "venv"
REQ = ROOT / "paper_output/code/review_delivery/requirements.txt"
ZIP = ROOT / "paper_output/submission/支撑材料/A题_支撑材料.zip"
QA.mkdir(parents=True, exist_ok=True)
PROBE.mkdir(parents=True, exist_ok=True)

env = os.environ.copy()
for key in list(env):
    if key.upper().startswith("PIP_") or key.upper() in {"PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"}:
        del env[key]
env.update(PIP_CONFIG_FILE=os.devnull, PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")

report = {
    "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "scope": "Fresh venv with include-system-site-packages=false; official PyPI only; no model PDE executed",
    "root": str(ROOT), "venv": str(VENV), "host_python": sys.executable,
    "requirements_sha256": hashlib.sha256(REQ.read_bytes()).hexdigest(),
    "requirements": REQ.read_text(encoding="utf-8-sig"),
    "zip_sha256": hashlib.sha256(ZIP.read_bytes()).hexdigest(),
    "steps": [],
}

def run(name, args, timeout):
    started = time.monotonic()
    try:
        proc = subprocess.run(args, cwd=PROBE, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        output = proc.stdout + proc.stderr
        step = {"name": name, "exit_code": proc.returncode, "elapsed_seconds": time.monotonic() - started, "timeout": False}
    except subprocess.TimeoutExpired as exc:
        output = "TIMEOUT\n" + (exc.stdout or b"").decode("utf-8", errors="replace") + (exc.stderr or b"").decode("utf-8", errors="replace")
        step = {"name": name, "exit_code": None, "elapsed_seconds": time.monotonic() - started, "timeout": True}
    logfile = QA / (name + ".log")
    logfile.write_text(output, encoding="utf-8")
    step["log"] = str(logfile.relative_to(ROOT))
    report["steps"].append(step)
    print(json.dumps(step), flush=True)
    return step, output

if VENV.exists():
    raise RuntimeError("Probe venv already exists: refusing to reuse it as a fresh install")
creation, _ = run("dependency_venv_create", [sys.executable, "-I", "-m", "venv", str(VENV)], 120)
PY = VENV / "Scripts/python.exe"
if creation["exit_code"] == 0:
    report["pyvenv_cfg"] = (VENV / "pyvenv.cfg").read_text(encoding="utf-8")
    installed, _ = run("dependency_pypi_install", [str(PY), "-I", "-m", "pip", "--isolated", "--disable-pip-version-check", "--no-cache-dir", "install", "--index-url", "https://pypi.org/simple", "--timeout", "20", "--retries", "1", "--only-binary=:all:", "--report", str(QA / "dependency_pip_report.json"), "-r", str(REQ)], 480)
    if installed["exit_code"] == 0:
        run("dependency_pip_check", [str(PY), "-I", "-m", "pip", "--isolated", "--disable-pip-version-check", "check"], 60)
        run("dependency_pip_freeze", [str(PY), "-I", "-m", "pip", "--isolated", "--disable-pip-version-check", "freeze", "--all"], 60)
        imported, output = run("dependency_import_probe", [str(PY), "-I", "-c", "import sys,json,numpy,scipy,openpyxl; from scipy.integrate._ivp.bdf import BDF,BdfDenseOutput; from scipy.integrate._ivp.base import DenseOutput; print(json.dumps(dict(executable=sys.executable,python=sys.version,base_prefix=sys.base_prefix,prefix=sys.prefix,modules={m.__name__:dict(version=m.__version__,file=m.__file__) for m in (numpy,scipy,openpyxl)},BDF_module=BDF.__module__,BdfDenseOutput_module=BdfDenseOutput.__module__,DenseOutput_module=DenseOutput.__module__),indent=2))"], 60)
        if imported["exit_code"] == 0:
            report["imports"] = json.loads(output)

with zipfile.ZipFile(ZIP) as zf:
    pyfiles = [n for n in zf.namelist() if n.endswith(".py")]
    local_modules = {Path(n).stem for n in pyfiles}
    all_imports = {}
    external_imports = {}
    syntax_errors = []
    for name in pyfiles:
        source = zf.read(name).decode("utf-8-sig")
        try:
            tree = ast.parse(source, filename=name)
        except SyntaxError as exc:
            syntax_errors.append({"file": name, "error": str(exc)})
            continue
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        all_imports[name] = sorted(imports)
        external = sorted(imports - sys.stdlib_module_names - local_modules - {"__future__"})
        if external:
            external_imports[name] = external
    report["zip_import_audit"] = {"python_files": len(pyfiles), "syntax_errors": syntax_errors, "imports_by_file": all_imports, "external_imports_by_file": external_imports, "external_top_level_modules": sorted({x for xs in external_imports.values() for x in xs})}

report["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
(QA / "dependency_review.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"report": str(QA / "dependency_review.json"), "external_imports": report["zip_import_audit"]["external_top_level_modules"]}, ensure_ascii=False), flush=True)
