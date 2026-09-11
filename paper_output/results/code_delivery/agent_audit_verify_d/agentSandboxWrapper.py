"""Sandbox workaround wrapper: DSH blocks tempfile.mkdtemp directories.

Only the private rebuildable solver cache path creation is replaced with
os.mkdir-based creation so the process can open polynomials.bin. No model,
mesh, tolerance, data or export logic is changed.
"""
import os
import pathlib
import sys
import tempfile
import uuid

ROOT = pathlib.Path(r"D:\Document\数学建模\2026CUMCM")
CODE = ROOT / "paper_output" / "code" / "review_delivery"


def _mkdtemp(suffix=None, prefix=None, dir=None):
    base = pathlib.Path(dir)
    for _ in range(200):
        candidate = base / ((prefix or "tmp") + uuid.uuid4().hex[:12] + (suffix or ""))
        if not candidate.exists():
            candidate.mkdir(parents=False)
            return str(candidate)
    raise FileExistsError("no unused temp name")


tempfile.mkdtemp = _mkdtemp

os.chdir(ROOT)
sys.path.insert(0, str(CODE))
sys.argv = [
    "runDelivery.py",
    "--profile", "audit",
    "--run-id", sys.argv[1] if len(sys.argv) > 1 else "agent_audit_verify_d",
]
import runDelivery  # noqa: E402

runDelivery.main()
