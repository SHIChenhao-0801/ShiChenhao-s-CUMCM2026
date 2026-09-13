from drying_core import Settings, solve_case


def solve(intervals=6400):
    return solve_case(Settings(question='Q4', intervals=intervals, face_scheme='kirchhoff',
        shrink=True, rtol=1e-10, atol_temperature=1e-10, atol_moisture=1e-12,
        early_max_step_s=2., max_step_s=120.))
