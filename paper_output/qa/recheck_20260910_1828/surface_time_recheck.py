"""Read frozen material-coordinate samples only; no PDE or model imports."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import numpy as np

ROOT=Path.cwd().resolve()
OUT=Path(__file__).resolve().parent
assert ROOT.name=='2026CUMCM' and OUT.is_relative_to(ROOT)

def record(p):
    p=Path(p)
    return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,
            'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def arrays(p):
    with np.load(p,allow_pickle=False) as z:
        return {k:z[k] for k in z.files}

results=[]
for q,tag in [('Q1','final_v6'),('Q23','final_v6_Q23'),('Q4','final_v6_Q4')]:
    folder=ROOT/'paper_output/results/time_accuracy'/tag
    paths=[folder/name/'sampled_solution.npz' for name in ['baseline','tight']]
    baseline,tight=map(arrays,paths)
    common,bi,ti=np.intersect1d(baseline['times_s'],tight['times_s'],return_indices=True)
    regular=(np.mod(common,60.)==0.)
    times=common[regular];bi=bi[regular];ti=ti[regular]
    assert np.array_equal(baseline['material_x'],tight['material_x'])
    assert baseline['material_x'][-1]==1.
    assert np.array_equal(baseline['radius_m'][bi],tight['radius_m'][ti])
    assert np.all(np.diff(times)==60.)
    fields={}
    for key in ['T_K','C']:
        a=baseline[key][bi];b=tight[key][ti]
        difference=np.abs(a-b)
        surface=difference[:,-1]
        index=int(np.argmax(surface))
        full_index=np.unravel_index(np.argmax(difference),difference.shape)
        pairs=[]
        for j in range(len(times)):
            av=float(a[j,-1]-(273.15 if key=='T_K' else 0.))
            bv=float(b[j,-1]-(273.15 if key=='T_K' else 0.))
            if round(av,4)!=round(bv,4):
                pairs.append({'time_s':float(times[j]),'radius_m':float(baseline['radius_m'][bi[j]]),
                   'baseline':av,'tight':bv,'baseline_4dp':f'{round(av,4):.4f}',
                   'tight_4dp':f'{round(bv,4):.4f}'})
        fields[key]={
            'surface_max_absolute_difference':float(surface[index]),
            'surface_max_location':{'time_s':float(times[index]),'material_x':1.,
                                    'radius_m':float(baseline['radius_m'][bi[index]])},
            'surface_values_at_max':{'baseline':float(a[index,-1]),'tight':float(b[index,-1])},
            'all_21_material_points_max_absolute_difference':float(difference[full_index]),
            'all_21_material_points_max_location':{'time_s':float(times[full_index[0]]),
                'material_x':float(baseline['material_x'][full_index[1]]),
                'radius_m':float(baseline['radius_m'][bi[full_index[0]]]*baseline['material_x'][full_index[1]])},
            'surface_4dp_difference_count':len(pairs),'surface_4dp_differences':pairs}
    results.append({'question':q,'sources':list(map(record,paths)),
        'common_regular_time_count':len(times),'first_s':float(times[0]),'last_s':float(times[-1]),
        'time_interval_s':60,'material_point_count':len(baseline['material_x']),
        'source_time_counts':[len(baseline['times_s']),len(tight['times_s'])],
        'excluded_common_non_60s_times':common[~regular].tolist(),'fields':fields})

space_paths=[ROOT/'paper_output/results/convergence/Q4_final_resolution_v5'/f'N{n}'/'sampled_solution.npz' for n in [3200,6400]]
coarse,fine=map(arrays,space_paths)
times,ci,fi=np.intersect1d(coarse['times_s'],fine['times_s'],return_indices=True)
assert np.array_equal(coarse['material_x'],fine['material_x'])
assert np.array_equal(coarse['radius_m'][ci],fine['radius_m'][fi])
space_fields={}
for key in ['T_K','C']:
    difference=np.abs(coarse[key][ci,-1]-fine[key][fi,-1])
    index=int(np.argmax(difference))
    space_fields[key]={'surface_max_absolute_difference':float(difference[index]),
        'location':{'time_s':float(times[index]),'material_x':1.,'radius_m':float(coarse['radius_m'][ci[index]])},
        'coarse':float(coarse[key][ci[index],-1]),'fine':float(fine[key][fi[index],-1])}
space={'question':'Q4','coarse_N':3200,'fine_N':6400,'sources':list(map(record,space_paths)),
    'common_saved_time_count':len(times),'scope':'x=1 actual moving surface at common saved times; ordinary samples every 60 s with common extra times; no full-second surface archive.',
    'extra_non_60s_times':times[np.mod(times,60.)!=0.].tolist(),'fields':space_fields}

report={'status':'SAVED_SURFACE_TIME_COMPARISON_COMPLETE','created_at':datetime.now(timezone.utc).isoformat(),
        'scope':'Same final N, baseline versus tight tolerances and step caps; actual x=1 surface at common regular 60 s times only. Not all seconds or a continuous error bound.',
        'new_PDE_solves':0,'code':record(__file__),'results':results,'Q4_spatial_saved_surface':space}
path=OUT/'surface_time_recheck.json'
path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
