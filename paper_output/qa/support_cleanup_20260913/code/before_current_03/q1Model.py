# 本文件为冻结求解源码的驼峰审查副本；本次便携路径调整见 docs/source_changes.json。
"""Q1 uses Appendix 2 throughout its 1800-second interval."""
from dryingCore import Settings, solveCase


# Q1 全部 1800 秒均采用附录 2 参数，正式空间区间数默认 3200。
def solve(intervals=3200):
    return solveCase(Settings(question='Q1', intervals=intervals, faceScheme='kirchhoff',
        rtol=1e-10, atolTemperature=1e-10, atolMoisture=1e-12,
        earlyMaxStepS=2., maxStepS=120.))
