from dryingCore import Settings, solveCase


def solve(intervals=3200):
    return solveCase(Settings(question='Q23', intervals=intervals, faceScheme='kirchhoff',
        rtol=1e-10, atolTemperature=1e-10, atolMoisture=1e-12,
        earlyMaxStepS=2., maxStepS=120.))
