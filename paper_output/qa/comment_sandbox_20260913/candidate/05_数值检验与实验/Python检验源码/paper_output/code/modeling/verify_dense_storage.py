from dataclasses import replace
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import warnings
import numpy as np
from drying_core import ROOT, Settings, solve_case, file_record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', default='paper_output/results/dense_storage_verification_v6')
    args = parser.parse_args()
    output = ROOT/args.output_dir
    output.mkdir(parents=True, exist_ok=False)
    records = []
    for question in ('Q1','Q23','Q4'):
        config = Settings(question=question, intervals=40, shrink=question=='Q4',
            face_scheme='kirchhoff', rtol=1e-8, atol_temperature=1e-8,
            atol_moisture=1e-10, early_max_step_s=5., max_step_s=300.)
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter('always')
            memory = solve_case(replace(config, dense_storage='memory'))
            disk = solve_case(replace(config, dense_storage='disk'))
        try:
            same_steps = len(memory.pieces)==len(disk.pieces) and all(
                np.array_equal(a.t,b.t) and np.array_equal(a.y,b.y)
                for a,b in zip(memory.pieces,disk.pieces))
            rng = np.random.default_rng(20260910)
            times = np.r_[0., memory.end_s, np.arange(0,min(1800,memory.end_s)+1),
                          rng.uniform(0,memory.end_s,400)]

            if memory.event_s is not None:
                times = np.r_[times,memory.event_s,memory.event_s-.01,memory.event_s+.01]
            knots = np.unique(np.concatenate([piece.t[1:-1] for piece in memory.pieces]))
            times = np.r_[times,knots,np.nextafter(knots,-np.inf),np.nextafter(knots,np.inf)]
            difference = 0.
            for first in range(0,len(times),100):
                tt = times[first:first+100]
                difference = max(difference,float(np.max(np.abs(memory.state(tt)-disk.state(tt)))))
            same_event = memory.event_s==disk.event_s and memory.end_s==disk.end_s
            record = {'question':question,'accepted_times_and_states_bitwise_equal':same_steps,
                'event_and_endpoint_bitwise_equal':same_event,'dense_query_max_difference':difference,
                'query_count':len(times),'warnings':[str(w.message) for w in captured],
                'internal_knot_count':len(knots),
                'covers_all_internal_knots_and_adjacent_representable_times':True,
                'disk_diagnostics':disk.diagnostics(),'memory_diagnostics':memory.diagnostics()}
            if not same_steps or not same_event or difference!=0 or captured:
                raise AssertionError(record)
            records.append(record)
            print(question+' exact storage identity PASS',flush=True)
        finally:
            cache_directory = disk.cache.directory
            memory.close();disk.close()
        record['private_cache_removed_after_close'] = not cache_directory.exists()
        if not record['private_cache_removed_after_close']:
            raise AssertionError('Private cache cleanup failed')
    report = {'status':'PASS','at_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'Storage-only identity check on three complete N40 trajectories; not spatial accuracy validation',
        'runs':records,'sources':[file_record(__file__),file_record(Path(__file__).with_name('drying_core.py')),
                                 file_record(Path(__file__).with_name('disk_dense.py'))]}
    (output/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
