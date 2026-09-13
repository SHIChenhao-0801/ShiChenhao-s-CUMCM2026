# 本文件为冻结求解源码的驼峰审查副本；本次便携路径调整见 docs/source_changes.json。
"""Q4 switches all properties to Appendix 4 and follows observed radial shrinkage."""
from dryingCore import Settings, solveCase


# Q4 从 t=0 使用整组附录 4 系数，并按观测 R(t) 同比径向收缩，固定长度。
def solve(intervals=6400):
    return solveCase(Settings(question='Q4', intervals=intervals, faceScheme='kirchhoff',
        shrink=True, rtol=1e-10, atolTemperature=1e-10, atolMoisture=1e-12,
        earlyMaxStepS=2., maxStepS=120.))
