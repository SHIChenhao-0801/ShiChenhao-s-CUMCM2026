from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.special import j0, j1, jn_zeros


FloatArray = NDArray[np.float64]


def _vector(value: ArrayLike, name: str) -> FloatArray:
    a = np.atleast_1d(np.asarray(value, dtype=float))
    if a.ndim != 1 or a.size == 0 or not np.all(np.isfinite(a)):
        raise ValueError(f"{name} must be a nonempty finite 1-D array")
    return a


@lru_cache(maxsize=24)
def _eigen_cached(biot: float, n_terms: int) -> tuple[FloatArray, FloatArray]:
    if not np.isfinite(biot) or biot <= 0:
        raise ValueError("Biot must be finite and positive")
    if not isinstance(n_terms, (int, np.integer)) or n_terms < 1:
        raise ValueError("n_terms must be a positive integer")


    upper = jn_zeros(0, n_terms)
    lower = np.r_[0.0, jn_zeros(1, n_terms-1)] if n_terms > 1 else np.array([0.0])
    roots = np.array([
        brentq(lambda z: z*j1(z)-biot*j0(z), lo, hi, xtol=1e-13, rtol=1e-14)
        for lo, hi in zip(lower, upper)
    ])
    a = 2*j1(roots) / (roots*(j0(roots)**2+j1(roots)**2))
    roots.setflags(write=False)
    a.setflags(write=False)
    return roots, a


def robin_eigenpairs(biot: float, n_terms: int = 120) -> tuple[FloatArray, FloatArray]:

    mu, a = _eigen_cached(float(biot), int(n_terms))
    return mu.copy(), a.copy()


def _validate_inputs(times_s, env_t, env_values, radius, diffusivity, biot):
    t = _vector(times_s, "times_s")
    knots = _vector(env_t, "env_t")
    values = _vector(env_values, "env_values")
    if len(knots) != len(values) or len(knots) < 2:
        raise ValueError("Boundary needs matching arrays with at least two knots")
    if abs(knots[0]) > 1e-12 or np.any(np.diff(knots) <= 0):
        raise ValueError("Boundary knots must start at t=0 and strictly increase")
    if np.any(t < 0):
        raise ValueError("Negative evaluation times are not permitted")
    if np.max(t) > knots[-1] + 1e-10:
        raise ValueError("Evaluation exceeds boundary observations: supply an explicit extension")
    if not np.isfinite(radius) or radius <= 0 or not np.isfinite(diffusivity) or diffusivity <= 0:
        raise ValueError("radius and diffusivity must be finite and positive")
    if not np.isfinite(biot) or biot < 0:
        raise ValueError("Biot must be finite and nonnegative")
    return t, knots, values


def _modal_history(
    times: FloatArray, knots: FloatArray, values: FloatArray,
    rates: FloatArray, initial_value: float,
) -> FloatArray:


    z = (initial_value-values[0])*np.exp(-times[:, None]*rates[None, :])
    slopes = np.diff(values)/np.diff(knots)
    for lo, hi, slope in zip(knots[:-1], knots[1:], slopes):
        if slope == 0:
            continue
        selected = times > lo
        ts = times[selected]
        end = np.minimum(ts, hi)
        duration = end-lo
        contribution = (
            np.exp(-(ts-end)[:, None]*rates[None, :])
            * (-np.expm1(-duration[:, None]*rates[None, :]))
            / rates[None, :]
        )
        z[selected] -= slope*contribution
    return z


def _space_modes(mu: FloatArray, radii_m: ArrayLike, radius: float, cell_edges_m=None) -> FloatArray:
    if cell_edges_m is None:
        x = _vector(radii_m, "radii_m")/radius
        if np.any(x < 0) or np.any(x > 1+1e-12):
            raise ValueError("radii must lie inside the cylinder")
        return j0(mu[:, None]*x[None, :])
    edges = _vector(cell_edges_m, "cell_edges_m")/radius
    if len(edges) < 2 or np.any(np.diff(edges) <= 0) or edges[0] < 0 or edges[-1] > 1+1e-12:
        raise ValueError("cell edges must strictly increase inside [0,radius]")
    lo, hi = edges[:-1], edges[1:]
    return 2*(hi[None, :]*j1(mu[:, None]*hi[None, :])
              - lo[None, :]*j1(mu[:, None]*lo[None, :])) / (mu[:, None]*(hi*hi-lo*lo)[None, :])


def bessel_diffusion(
    times_s: ArrayLike, radii_m: ArrayLike, env_t: ArrayLike,
    env_values: ArrayLike, *, radius: float, diffusivity: float,
    biot: float, initial_value: float, n_terms: int = 120,
    cell_edges_m: ArrayLike | None = None,
) -> FloatArray:


    t, knots, values = _validate_inputs(times_s, env_t, env_values, radius, diffusivity, biot)
    if not np.isfinite(initial_value):
        raise ValueError("initial_value must be finite")
    if not isinstance(n_terms, (int, np.integer)) or n_terms < 1:
        raise ValueError("n_terms must be a positive integer")
    if biot == 0:

        nspace = len(_vector(cell_edges_m, "cell_edges_m"))-1 if cell_edges_m is not None else len(_vector(radii_m, "radii_m"))
        _space_modes(np.array([1.0]), radii_m, radius, cell_edges_m)
        return np.full((len(t), nspace), initial_value)
    mu, a = _eigen_cached(float(biot), int(n_terms))
    rates = diffusivity*mu*mu/(radius*radius)
    spatial = _space_modes(mu, radii_m, radius, cell_edges_m)
    history = _modal_history(t, knots, values, rates, initial_value)
    result = np.interp(t, knots, values)[:, None] + (history*a[None, :]) @ spatial


    result[t == 0] = initial_value
    return result


def bessel_temperature(
    times_s: ArrayLike, radii_m: ArrayLike, env_t: ArrayLike,
    env_T: ArrayLike, radius: float = 0.02, h: float = 25.0,
    k: float = 0.36, rho: float = 820.0, cp: float = 2600.0,
    n_terms: int = 120, initial_temperature_K: float = 301.15,
    cell_edges_m: ArrayLike | None = None,
) -> FloatArray:

    if any(not np.isfinite(v) or v <= 0 for v in (k,rho,cp)) or h < 0:
        raise ValueError("k,rho,cp must be positive and h nonnegative")
    return bessel_diffusion(
        times_s, radii_m, env_t, env_T, radius=radius,
        diffusivity=k/(rho*cp), biot=h*radius/k,
        initial_value=initial_temperature_K, n_terms=n_terms,
        cell_edges_m=cell_edges_m,
    )


def bessel_moisture(
    times_s: ArrayLike, radii_m: ArrayLike, env_t: ArrayLike,
    env_Ceq: ArrayLike, diffusion_coefficient: float,
    radius: float = 0.02, beta: float = 8e-7,
    initial_moisture: float = 2.55, n_terms: int = 240,
    cell_edges_m: ArrayLike | None = None,
) -> FloatArray:

    if diffusion_coefficient <= 0 or beta < 0:
        raise ValueError("Frozen diffusion coefficient must be positive, beta nonnegative")
    return bessel_diffusion(
        times_s, radii_m, env_t, env_Ceq, radius=radius,
        diffusivity=diffusion_coefficient, biot=beta*radius/diffusion_coefficient,
        initial_value=initial_moisture, n_terms=n_terms,
        cell_edges_m=cell_edges_m,
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def selfcheck(env_t: FloatArray, env_T: FloatArray) -> dict:


    bi = 25*.02/.36
    mu, a = robin_eigenpairs(bi, 120)
    residual = mu*j1(mu)-bi*j0(mu)
    relative_eigen_residual = np.max(np.abs(residual)/(1+np.abs(mu*j1(mu))+np.abs(bi*j0(mu))))


    knots = np.array([0.,17.,52.,130.])
    boundary = np.array([301.15,305.,303.,303.])
    targets = np.array([8.,17.,40.,78.,130.])
    rates = np.array([1e-6,.002,.2])
    z = _modal_history(targets,knots,boundary,rates,299.)
    independent = np.empty_like(z)
    for i,t in enumerate(targets):
        for j,lam in enumerate(rates):
            integral = 0.
            for lo,hi,gl,gh in zip(knots[:-1],knots[1:],boundary[:-1],boundary[1:]):
                if t > lo:
                    slope = (gh-gl)/(hi-lo)
                    integral += quad(lambda s: slope*np.exp(-lam*(t-s)),lo,min(t,hi),epsabs=1e-12,epsrel=1e-12)[0]
            independent[i,j] = (299.-boundary[0])*np.exp(-lam*t)-integral
    convolution_error = float(np.max(np.abs(z-independent)))


    edges = np.array([0.,.001,.006,.02])
    averaged = _space_modes(mu[:8], [0.], .02,edges)
    quad_average = np.empty_like(averaged)
    for n,m in enumerate(mu[:8]):
        for i,(lo,hi) in enumerate(zip(edges[:-1]/.02,edges[1:]/.02)):
            quad_average[n,i] = 2*quad(lambda x: x*j0(m*x),lo,hi,epsabs=1e-12)[0]/(hi*hi-lo*lo)
    average_error = float(np.max(np.abs(averaged-quad_average)))


    alpha=.36/(820*2600)
    lam=alpha*mu**2/.02**2
    e=np.exp(-100*lam)
    mean_basis=2*j1(mu)/mu
    dmean=np.sum(a*(-lam)*(-20)*e*mean_basis)
    surface=321.15+np.sum(a*(-20)*e*j0(mu))
    influx=2*25/(820*2600*.02)*(321.15-surface)
    energy_error=abs(dmean-influx)

    ts=np.array([0.,1.,10.,100.,300.,600.,900.,1200.,1500.,1800.])
    rs=np.linspace(0,.02,41)
    t120=bessel_temperature(ts,rs,env_t,env_T,n_terms=120)
    t240=bessel_temperature(ts,rs,env_t,env_T,n_terms=240)
    t480=bessel_temperature(ts,rs,env_t,env_T,n_terms=480)
    error120_240=float(np.max(np.abs(t120-t240)))
    error240_480=float(np.max(np.abs(t240-t480)))
    equilibrium=bessel_temperature([0.,1.,100.],[0.,.01,.02],[0.,100.],[301.15,301.15])
    equilibrium_error=float(np.max(np.abs(equilibrium-301.15)))
    insulating=bessel_temperature([0.,50.,100.],[0.,.01,.02],[0.,100.],[301.15,323.15],h=0)
    insulation_error=float(np.max(np.abs(insulating-301.15)))

    checks = [
        ("robin_eigen_relative_residual",float(relative_eigen_residual),1e-10,"1"),
        ("piecewise_convolution_vs_adaptive_quadrature",convolution_error,1e-10,"K"),
        ("annular_average_vs_adaptive_quadrature",average_error,1e-10,"1"),
        ("constant_boundary_step_energy_identity",float(energy_error),1e-10,"K/s"),
        ("Q1_observed_boundary_120_vs_240_terms",error120_240,1e-4,"K"),
        ("Q1_observed_boundary_240_vs_480_terms",error240_480,1e-4,"K"),
        ("uniform_equilibrium",equilibrium_error,1e-12,"K"),
        ("insulating_boundary",insulation_error,1e-12,"K"),
    ]
    return {
        "status":"PASS" if all(v<=limit for _,v,limit,_ in checks) else "FAIL",
        "scope":"analytic benchmark implementation selfcheck; production FVM comparison is separate",
        "checks":[{"name":name,"value":v,"tolerance":limit,"unit":unit,"passed":v<=limit} for name,v,limit,unit in checks],
        "series_note":"120/240/480 differences estimate truncation sensitivity at sampled locations and times, not a rigorous uniform error bound.",
        "no_internal_experimental_validation":True,
        "visual_studio_gui":"pending",
        "human_review":"pending",
    }


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment-csv",default="paper_output/data_cleaned/A_environment_observed.csv")
    parser.add_argument("--output-dir",default="paper_output/results/bessel_validation")
    args=parser.parse_args()
    root=Path.cwd().resolve()
    if root != Path(r"D:\Document\数学建模\2026CUMCM").resolve():
        raise RuntimeError("Run only from the 2026CUMCM workspace root")
    source=(root/args.environment_csv).resolve()
    with source.open(encoding="utf-8-sig",newline="") as fh:
        rows=list(csv.DictReader(fh))
    env_t=np.array([float(r["time_s"]) for r in rows])
    env_T=np.array([float(r["temperature_K"]) for r in rows])
    env_C=np.array([float(r["air_moisture_kg_per_kg"]) for r in rows])
    report=selfcheck(env_t,env_T)
    out=(root/args.output_dir).resolve()
    if not out.is_relative_to(root):
        raise RuntimeError("Output must remain inside the competition workspace")
    out.mkdir(parents=True,exist_ok=True)
    paper_t=np.array([100.,300.,600.,900.,1200.,1500.,1800.])
    paper_r=np.array([0.,.005,.01,.015,.02])
    temperature=bessel_temperature(paper_t,paper_r,env_t,env_T,n_terms=240)
    frozen_D=7e-9*np.exp(-.89/2.55)
    frozen_water=bessel_moisture(paper_t,paper_r,env_t,env_C,float(frozen_D),n_terms=240)
    artifacts=[]
    for filename,field,label in [
        ("q1_exact_heat_paper_points.csv",temperature-273.15,"temperature_C"),
        ("frozen_D_moisture_benchmark_points.csv",frozen_water,"moisture_kg_per_kg"),
    ]:
        path=out/filename
        with path.open("w",encoding="utf-8",newline="") as fh:
            writer=csv.writer(fh)
            writer.writerow(["time_s","radius_m",label])
            for i,t in enumerate(paper_t):
                for j,r in enumerate(paper_r):
                    writer.writerow([format(t,".17g"),format(r,".17g"),format(field[i,j],".17g")])
        artifacts.append({"path":path.relative_to(root).as_posix(),"bytes":path.stat().st_size,"sha256":_sha256(path)})
    report.update({
        "schema_version":"1.0", "question_id":"Q1",
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "generated_by":"paper_output/code/modeling/validate_bessel.py",
        "frozen_moisture_diffusion_coefficient_m2_s":float(frozen_D),
        "frozen_moisture_note":"This table is a constant-D algorithm benchmark and must not replace nonlinear Q1 result1 moisture values.",
        "execution_provenance":{
            "source_code_path":Path(__file__).resolve().relative_to(root).as_posix(),
            "source_code_sha256":_sha256(Path(__file__)),
            "run_command":sys.executable+" -B "+" ".join(sys.argv),
            "run_exit_code":0 if report["status"]=="PASS" else 1,
            "python_version":platform.python_version(),
            "input_artifacts":[{"path":source.relative_to(root).as_posix(),"sha256":_sha256(source)}],
            "output_artifacts":artifacts,
        },
    })
    report_path=out/"bessel_selfcheck.json"
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"checks":report["checks"],"report":str(report_path)},ensure_ascii=False,indent=2))
    return 0 if report["status"]=="PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
