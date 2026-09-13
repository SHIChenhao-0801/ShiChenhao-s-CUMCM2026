# 本文件为冻结求解源码的驼峰审查副本；本次便携路径调整见 docs/源码变更说明.txt。
"""Q3 is a threshold functional of the exact same Run used by Q2."""
import math
import numpy as np


# Q3 是 Q2 场解的阈值泛函；先连续定位，再向上取 0.0001 h 并验原精度 max(C)<0.15。
def completion(run):
    if run.eventS is None:
        raise ValueError('No full-domain drying event within the solved horizon')
    # At the continuous root the maximum equals 0.15. Report upward on the
    # required 0.0001-hour grid and verify the unrounded state there.
    count = math.ceil(run.eventS / 3600. * 10000.)
    # 即使四位显示为 0.1500，也只能依据未舍入含水率判定严格干燥。
    while True:
        reportH = count/10000.
        t = reportH*3600.
        if t > run.endS:
            raise RuntimeError('Four-decimal reporting time is outside the verified trajectory')
        values = run.state([t])[1:-1:2,0]
        if float(np.max(values)) < .15:
            break
        count += 1
    return {'critical_event_s':run.eventS,'critical_event_h':run.eventS/3600.,
        'reported_drying_time_h':reportH,'reported_time_s':t,
        'max_C_at_reported_time':float(np.max(values)),
        'slowest_material_coordinate':float(run.model.x[np.argmax(values)]),
        'conservative_post_verification_s':run.endS,
        'rounding_convention':'upward on 0.0001 h grid, followed by actual strict threshold check',
        'interpretation':'A conditional numerical event, not a confidence bound on physical drying time.'}
