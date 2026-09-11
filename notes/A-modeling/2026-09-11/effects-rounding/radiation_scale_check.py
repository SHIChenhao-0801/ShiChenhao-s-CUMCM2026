"""Bounded algebraic radiation audit; no new drying PDE or fitted parameters."""
from __future__ import annotations

import hashlib
import json
import math
import platform
from datetime import datetime, timezone
from pathlib import Path

from scipy.constants import Stefan_Boltzmann

projectRoot = Path.cwd().resolve()
assert projectRoot.name == "2026CUMCM"
outputDir = Path(__file__).resolve().parent
startTime = datetime.now(timezone.utc)
sigma = float(Stefan_Boltzmann)
wallKelvin = 323.15
convectiveCoefficient = 25.0
rows = []
for surfaceCelsius in (28.0, 40.0, 50.0):
    surfaceKelvin = surfaceCelsius + 273.15
    for emissivity in (0.1, 0.5, 0.9, 1.0):
        # Grey diffuse surface entirely surrounded by an isothermal black
        # radiative enclosure; wall temperature also equals air temperature.
        radiationCoefficient = emissivity * sigma * (wallKelvin + surfaceKelvin) * (
            wallKelvin**2 + surfaceKelvin**2)
        directFlux = emissivity * sigma * (wallKelvin**4 - surfaceKelvin**4)
        factoredFlux = radiationCoefficient * (wallKelvin - surfaceKelvin)
        assert math.isclose(directFlux, factoredFlux, rel_tol=3e-14, abs_tol=1e-12)
        rows.append({
            "surface_temperature_C": surfaceCelsius, "wall_temperature_C": 50.0,
            "scenario_emissivity_not_measured": emissivity,
            "radiation_coefficient_W_m2K": radiationCoefficient,
            "radiation_over_convective_coefficient": radiationCoefficient / convectiveCoefficient,
            "inward_radiation_W_m2": directFlux,
            "inward_convection_W_m2": convectiveCoefficient * (wallKelvin - surfaceKelvin),
            "flux_ratio_defined": surfaceKelvin != wallKelvin,
        })
sourceFiles = [
    Path("paper_output/code/modeling/drying_core.py"),
    Path("paper_output/code/review_delivery/dryingCore.py"),
    Path("paper_output/qa/recheck_20260910_1828/raw_problem_text.txt"),
]
sources = []
for relativePath in sourceFiles:
    sourcePath = projectRoot / relativePath
    content = sourcePath.read_bytes()
    sources.append({"path": relativePath.as_posix(), "bytes": len(content),
                    "sha256": hashlib.sha256(content).hexdigest()})
report = {
    "status": "SCENARIO_SCALE_CHECK_COMPLETE_NOT_EMPIRICAL_VALIDATION",
    "started_at_utc": startTime.isoformat(),
    "ended_at_utc": datetime.now(timezone.utc).isoformat(),
    "python_version": platform.python_version(), "new_PDE_solves": 0,
    "new_GUI_reproduction": False, "human_review": "pending",
    "sigma_W_m2K4": sigma, "convective_coefficient_W_m2K": convectiveCoefficient,
    "sources": sources, "rows": rows,
    "assumptions": [
        "Chosen emissivity values are scenario inputs, not measured properties of this herb.",
        "Isothermal black radiative enclosure fills the surface view; nonparticipating surroundings.",
        "Wall and air temperatures both set to 50 C solely for this scale comparison.",
        "Surface 28 C and wall 50 C is not asserted to be the actual initial state.",
        "At surface=wall=air, both net heat fluxes vanish; only the conductance ratio remains defined.",
    ],
    "conclusion": "At epsilon=0.9 and Ts=28 C the radiation/convection flux ratio is about 24.87%; 50 C alone does not justify negligible radiation. No inference of a 24.87% drying-time or temperature error is made.",
    "primary_sources": [
        "https://physics.nist.gov/cuu/Constants/Table/allascii.txt",
        "https://doc.comsol.com/6.3/doc/com.comsol.help.heat/heat_ug_ht_features.09.088.html",
        "https://doc.comsol.com/6.4/doc/com.comsol.help.heat/heat_ug_modeling.06.55.html",
    ],
}
(outputDir / "radiation-scale-results.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": report["status"], "rows": len(rows),
                  "epsilon_0_9_Ts_28": rows[2], "new_PDE_solves": 0},
                 ensure_ascii=False, indent=2))
