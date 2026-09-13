"""Independent grid/time checks on the adopted equations; no experimental fitting."""
from __future__ import annotations
import argparse
from dataclasses import replace
from datetime import datetime, timezone
import gc
import json
from pathlib import Path
import warnings
import numpy as np
from drying_core import ROOT, Settings, solve_case, save_run, file_record
from validate_bessel import bessel_temperature, bessel_moisture


def project_run(run, points, full_seconds):
    """Evaluate every comparison point from full BDF states before releasing Run."""
    if full_seconds:
        times = np.arange(0., np.floor(run.end_s)+1.)
    else:
        times = np.unique(np.r_[np.arange(0., min(10800., run.end_s)+1.),
                               np.arange(10860., run.end_s, 60.)])
    T = np.empty((len(times), len(points)))
    C = np.empty_like(T)
    for first in range(0, len(times), 128):
        T[first:first+128], C[first:first+128] = run.fields(times[first:first+128], radii_m=points)
    return {'times':times,'T':T,'C':C,'end_s':run.end_s,'event_s':run.event_s,
            'N':run.model.settings.intervals}


def compare_projections(coarse, fine, points, block=1000):
    common_count = min(len(coarse['times']), len(fine['times']))
    times = coarse['times'][:common_count]
    if not np.array_equal(times, fine['times'][:common_count]):
        raise ValueError('Only identical physical time queries may be compared')
    maxima = {'T_K':0., 'C':0.}
    locations = {}
    for first in range(0, len(times), block):
        tt = times[first:first+block]
        fields_a = [coarse[k][first:first+len(tt)] for k in ['T','C']]
        fields_b = [fine[k][first:first+len(tt)] for k in ['T','C']]
        for label, aa, bb in zip(['T_K', 'C'], fields_a, fields_b):
            error = np.abs(aa-bb)
            if np.any(np.isfinite(error)):
                index = np.unravel_index(np.nanargmax(error), error.shape)
                value = float(error[index])
                if value > maxima[label]:
                    maxima[label] = value
                    locations[label] = {'time_s':float(tt[index[0]]),
                                        'radius_m':float(points[index[1]])}
    return {'max_absolute_difference':maxima, 'locations':locations,
            'compared_time_count':len(times), 'radial_count':len(points),
            'convention':'Only finite values at common physical points are compared.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--question', choices=['Q1','Q23','Q4'], required=True)
    parser.add_argument('--grids', type=int, nargs='+', required=True)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--full-second-comparison', action='store_true')
    parser.add_argument('--frozen-d', type=float)
    args = parser.parse_args()
    out = ROOT/'paper_output/results/convergence'/args.tag
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    settings = Settings(question=args.question, face_scheme='kirchhoff',
        shrink=args.question=='Q4', rtol=1e-10, atol_temperature=1e-10,
        atol_moisture=1e-12, max_step_s=120., early_max_step_s=2.,
        constant_D=args.frozen_d)
    report = {'created_at':datetime.now(timezone.utc).isoformat(),
              'question':args.question, 'runs':[], 'comparisons':[],
              'driver_code':file_record(__file__), 'human_review':'pending'}
    previous = None
    radii = np.linspace(0,.02,21)
    for n in args.grids:
        print(f'START {args.tag} N={n}', flush=True)
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter('always')
            run = solve_case(replace(settings, intervals=n))
            summary = save_run(run, out/f'N{n}')
        projection = project_run(run, radii, args.full_second_comparison or args.question=='Q1')
        summary['warnings'] = [str(item.message) for item in captured]
        report['runs'].append(summary)
        if captured:
            raise RuntimeError(f'Production solver warnings at N={n}: {summary["warnings"]}')
        if previous is not None:
            comparison = compare_projections(previous, projection, radii)
            comparison.update({'coarse_N':previous['N'], 'fine_N':n,
                'event_difference_s':None if run.event_s is None else run.event_s-previous['event_s']})
            report['comparisons'].append(comparison)
            print(json.dumps(comparison), flush=True)
        if args.question=='Q1':
            times = np.arange(0.,1801.)
            numeric_T, numeric_C = projection['T'], projection['C']
            env = run.model.env
            exact_T = bessel_temperature(times, radii, env['time_s'], env['temperature_K'], n_terms=240)
            error_T = np.abs(numeric_T-exact_T)
            analytic = {'N':n,'max_heat_error_K':float(error_T.max()),
                        'scope':'All 1801 integer seconds and 21 requested radii'}
            if args.frozen_d is not None:
                exact_C = bessel_moisture(times, radii, env['time_s'],
                    env['air_moisture_kg_per_kg'], diffusion_coefficient=args.frozen_d, n_terms=480)
                error_C = np.abs(numeric_C-exact_C)
                at = np.unravel_index(np.argmax(error_C), error_C.shape)
                analytic.update({'max_frozen_D_water_error':float(error_C.max()),
                                 'water_error_time_s':float(times[at[0]]),
                                 'water_error_radius_m':float(radii[at[1]])})
            summary['analytic_comparison'] = analytic
            print(json.dumps(analytic), flush=True)
        previous = projection
        run.close()
        del run
        (out/'convergence_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        gc.collect()
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    report['status'] = 'computed_and_zero_solver_warnings'
    (out/'convergence_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('COMPLETED '+args.tag, flush=True)


if __name__=='__main__':
    main()
