"""Bounded reproducible batches; each scenario has independent physical assumptions."""
from __future__ import annotations
import argparse
from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import traceback

from drying_core import ROOT, Settings, solve_case, save_run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', choices=['baseline', 'grids', 'temporal', 'physical'], default='baseline')
    parser.add_argument('--n', type=int, default=100)
    parser.add_argument('--tag', default='')
    args = parser.parse_args()
    base = Settings(intervals=args.n)
    if args.batch in ('baseline', 'grids'):
        candidates = [('Q1', replace(base, question='Q1')), ('Q23', base),
                      ('Q4', replace(base, question='Q4', shrink=True))]
    elif args.batch == 'temporal':
        candidates = [('Q23_tight', replace(base, rtol=1e-9, atol_moisture=1e-11,
                        atol_temperature=1e-9, max_step_s=150., early_max_step_s=10.)),
                      ('Q4_tight', replace(base, question='Q4', shrink=True, rtol=1e-9,
                        atol_moisture=1e-11, atol_temperature=1e-9, max_step_s=150., early_max_step_s=10.))]
    else:
        candidates = [('Q4_fixed', replace(base, question='Q4', shrink=False)),
                      ('Q23_last', replace(base, boundary_extension='last')),
                      ('Q23_mean', replace(base, boundary_extension='tail_mean')),
                      ('Q23_T49', replace(base, tail_temperature_C=49.)),
                      ('Q23_T51', replace(base, tail_temperature_C=51.)),
                      ('Q23_eq045', replace(base, tail_equilibrium=.045)),
                      ('Q23_eq055', replace(base, tail_equilibrium=.055)),
                      ('Q4_T49', replace(base, question='Q4', shrink=True, tail_temperature_C=49.)),
                      ('Q4_T51', replace(base, question='Q4', shrink=True, tail_temperature_C=51.)),
                      ('Q23_beta08', replace(base, beta=6.4e-7)),
                      ('Q23_beta12', replace(base, beta=9.6e-7)),
                      ('Q23_latent', replace(base, surface_latent_fraction=1.)),
                      ('Q4_latent', replace(base, question='Q4', shrink=True, surface_latent_fraction=1.))]
    out = ROOT/'paper_output/results/experiments'
    out.mkdir(parents=True, exist_ok=True)
    failed = 0
    for name, settings in candidates:
        trial_id = f'{args.batch}_{name}_N{args.n}{args.tag}'
        folder = out/trial_id
        if (folder/'summary.json').exists():
            raise FileExistsError(f'Refusing to overwrite previous trial: {trial_id}')
        folder.mkdir(parents=True, exist_ok=True)
        start = datetime.now(timezone.utc).isoformat()
        print(f'START {trial_id} {start}', flush=True)
        try:
            run = solve_case(settings)
            summary = save_run(run, folder)
            record = {'trial_id':trial_id, 'started_at':start,
                      'finished_at':datetime.now(timezone.utc).isoformat(),
                      'status':'computed', 'exit_code':0, **summary['diagnostics']}
        except Exception as exc:
            failed += 1
            (folder/'failure.txt').write_text(traceback.format_exc(), encoding='utf-8')
            record = {'trial_id':trial_id, 'started_at':start, 'status':'failed',
                      'exit_code':1, 'error':str(exc)}
        (folder/'trial_record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
        with (out/'trials.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(record, ensure_ascii=False)+'\n')
        print(json.dumps(record, ensure_ascii=False), flush=True)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
