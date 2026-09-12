"""Audit the submitted ZIP without changing its source or the frozen results.

These are CLI packaging probes, not Visual Studio or another physical device
verification. Every child process is supervised and its actual exit is saved.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--label", default="installed_environment")
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[3]
    report_dir = Path(__file__).resolve().parent
    cache = project / "tmp/cache/portability_20260912" / args.label
    cache.mkdir(parents=True, exist_ok=False)
    archive = project / "paper_output/submission/支撑材料/A题_支撑材料.zip"
    archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
    extracted = cache / "original_case/extracted"
    with zipfile.ZipFile(archive) as package:
        crc_failure = package.testzip()
        if crc_failure:
            raise RuntimeError(crc_failure)
        for member in package.infolist():
            target = (extracted / member.filename).resolve()
            if not target.is_relative_to(extracted.resolve()):
                raise RuntimeError("Unsafe archive member")
        package.extractall(extracted)
        member_count = len(package.infolist())
    relocated = cache / "layout_diagnostic"
    relocated_code = relocated / "paper_output/code/review_delivery"
    shutil.copytree(extracted / "code", relocated_code)
    # Only the directory shape changes. No source/input/reference is borrowed
    # from the original working project, and no package code is patched.
    copied_sources = []
    for source in sorted((extracted / "code").rglob("*")):
        if source.is_file():
            relative = source.relative_to(extracted / "code")
            left = hashlib.sha256(source.read_bytes()).hexdigest()
            right = hashlib.sha256((relocated_code / relative).read_bytes()).hexdigest()
            if left != right:
                raise AssertionError(str(relative))
            copied_sources.append({"path": relative.as_posix(), "sha256": left})
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    environment.update(PYTHONNOUSERSITE="1", PYTHONIOENCODING="utf-8",
                       PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
    cases = []

    def run_case(name, command, cwd):
        started = datetime.now(timezone.utc).isoformat()
        timer = time.perf_counter()
        try:
            result = subprocess.run(command, cwd=cwd, env=environment,
                                    capture_output=True, timeout=60)
            stdout, stderr = result.stdout, result.stderr
            exit_code, timed_out = result.returncode, False
        except subprocess.TimeoutExpired as error:
            stdout, stderr = error.stdout or b"", error.stderr or b""
            exit_code, timed_out = None, True
        prefix = args.label + "_" + name
        (report_dir / (prefix + ".stdout.log")).write_bytes(stdout)
        (report_dir / (prefix + ".stderr.log")).write_bytes(stderr)
        record = {"name": name, "command": command, "cwd": str(cwd),
                  "startedAtUtc": started, "actualExitCode": exit_code,
                  "elapsedSeconds": time.perf_counter() - timer,
                  "timedOut": timed_out, "stdoutLog": prefix + ".stdout.log",
                  "stderrLog": prefix + ".stderr.log"}
        cases.append(record)
        print(json.dumps(record, ensure_ascii=False), flush=True)

    python = str(Path(args.python).resolve())
    run_case("environment", [python, "-X", "utf8", "-B", "-c",
             "import sys,json,site,importlib.metadata as m; "
             "print(json.dumps({'executable':sys.executable,'version':sys.version,"
             "'prefix':sys.prefix,'basePrefix':sys.base_prefix,"
             "'userSiteEnabled':site.ENABLE_USER_SITE,"
             "'libraries':{x:m.version(x) for x in ['numpy','scipy','openpyxl']}},ensure_ascii=False))"],
             extracted)
    for profile in ("final", "audit"):
        run_case("as_unzipped_" + profile,
                 [python, "-X", "utf8", "-B", str(extracted / "code/runDelivery.py"),
                  "--profile", profile, "--run-id", "portability_" + profile], extracted)
        run_case("layout_only_" + profile,
                 [python, "-X", "utf8", "-B", str(relocated_code / "runDelivery.py"),
                  "--profile", profile, "--run-id", "portability_" + profile], relocated)
    run_case("load_inputs", [python, "-X", "utf8", "-B", "-c",
             "import sys; sys.path.insert(0,sys.argv[1]); "
             "import dryingCore; dryingCore.loadInputs()", str(relocated_code)], relocated)
    report = {"createdAtUtc": datetime.now(timezone.utc).isoformat(),
              "scope": "CLI startup/input probes; no PDE executed; no new GUI/human/physical-device verification",
              "sourceZip": archive.relative_to(project).as_posix(),
              "sourceZipSha256": archive_hash, "zipCrc": "PASS", "members": member_count,
              "label": args.label, "extractedRoot": str(extracted),
              "layoutDiagnosticRoot": str(relocated), "copiedSourceHashes": copied_sources,
              "cases": cases,
              "unchangedZipSha256": hashlib.sha256(archive.read_bytes()).hexdigest()}
    (report_dir / (args.label + "_execution.json")).write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
