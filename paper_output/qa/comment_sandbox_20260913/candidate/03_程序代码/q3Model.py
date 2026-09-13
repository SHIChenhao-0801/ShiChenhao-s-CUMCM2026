import math
import numpy as np


def completion(run):
    if run.eventS is None:
        raise ValueError('No full-domain drying event within the solved horizon')


    count = math.ceil(run.eventS / 3600. * 10000.)

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
