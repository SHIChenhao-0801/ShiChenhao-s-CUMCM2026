from drying_core import Settings, solve_case


def solve(intervals=3200):
    return solve_case(Settings(question='Q23', intervals=intervals, face_scheme='kirchhoff',
        rtol=1e-10, atol_temperature=1e-10, atol_moisture=1e-12,
        early_max_step_s=2., max_step_s=120.))
