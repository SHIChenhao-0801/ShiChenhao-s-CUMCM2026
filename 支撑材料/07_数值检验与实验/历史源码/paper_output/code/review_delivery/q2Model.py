# 本文件为冻结求解源码的驼峰审查副本；来源、改名与 AST 核验见 tools/coreRenameReport.json。
"""Q2 uses Appendix 3 from t=0; it does not splice the Q1 trajectory."""
from dryingCore import Settings, solveCase


# Q2/Q3 从 t=0 采用附录 3，Q3 必须复用本次同一个 Run，不能拼接 Q1。
def solve(intervals=3200):
    return solveCase(Settings(question='Q23', intervals=intervals, faceScheme='kirchhoff',
        rtol=1e-10, atolTemperature=1e-10, atolMoisture=1e-12,
        earlyMaxStepS=2., maxStepS=120.))
