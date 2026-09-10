# -*- coding: utf-8 -*-
"""
results.py —— 由求解结果生成比赛要求的 result1~result4.xlsx 与论文表格

结果文件格式（严格对齐赛题模板）
    result1.xlsx : 工作表「温度」「水分浓度」
                   A 列 = 时间 / s（1,2,...,1800），第 1 行 = 到药材中心距离 0,0.1,...,2 cm
    result2.xlsx : 同上，时间 1..10800 s
    result3.xlsx : 工作表「Sheet1」，时间 60,120,...,烘干结束时间
    result4.xlsx : 同上，末列增加「药材表面」
所有数值保留四位小数。
"""
import os
import pickle
import math
import sys

from physics import OUT_DIR, C_TARGET, R0
from solver import find_crossing
from xlsxio import write_workbook

PKL_DIR = os.path.join(OUT_DIR, 'pkl')
TAB_DIR = os.path.join(OUT_DIR, 'tables')

RAD_CM = [round(i * 0.1, 10) for i in range(21)]      # 0, 0.1, ..., 2.0


def load(q, N, sub):
    p = os.path.join(PKL_DIR, 'q%d_N%d_sub%d.pkl' % (q, N, sub))
    with open(p, 'rb') as f:
        return pickle.load(f)


def _r4(v):
    return None if v is None else round(v + 0.0, 4)


# ----------------------------------------------------------------------
# result1 / result2：双工作表，时间步 1 s
# ----------------------------------------------------------------------
def build_result12(res, q):
    header = ['时间\\到药材中心的距离'] + RAD_CM
    sheets = []
    for which, name in (('T', '温度'), ('C', '水分浓度')):
        rows = [header]
        for k, t in enumerate(res.times):
            if t < 0.5:
                continue                     # 模板从 t=1 s 起
            line = [int(round(t))]
            for r_cm in RAD_CM:
                xq = r_cm * 1e-2 / res.R[k]
                v = res.interp_T(k, xq) if which == 'T' else res.interp_C(k, xq)
                line.append(_r4(v))
            rows.append(line)
        sheets.append((name, rows))
    path = os.path.join(OUT_DIR, 'result%d.xlsx' % q)
    write_workbook(path, sheets)
    return path, len(sheets[0][1]) - 1


# ----------------------------------------------------------------------
# result3 / result4：单工作表，时间步 60 s
# ----------------------------------------------------------------------
def build_result34(res, q, with_surface):
    header = ['时间\\到药材中心的距离'] + RAD_CM + (['药材表面'] if with_surface else [])
    rows = [header]
    t_end = res.times[-1]
    for k, t in enumerate(res.times):
        if t < 59.5:
            continue
        line = [int(round(t))]
        Rk = res.R[k]
        for r_cm in RAD_CM:
            r = r_cm * 1e-2
            if r > Rk + 1e-12:
                line.append(None)             # 该半径已超出当前材料表面
            else:
                line.append(_r4(res.interp_C(k, r / Rk)))
        if with_surface:
            line.append(_r4(res.C[k][-1]))
        rows.append(line)
    path = os.path.join(OUT_DIR, 'result%d.xlsx' % q)
    write_workbook(path, [('Sheet1', rows)])
    return path, len(rows) - 1, t_end


# ----------------------------------------------------------------------
# 论文表格（赛题表1—表6 格式）
# ----------------------------------------------------------------------
def _md_table(caption, header, rows, note=''):
    out = ['**%s**' % caption, '']
    out.append('| ' + ' | '.join(str(h) for h in header) + ' |')
    out.append('|' + '|'.join(['---'] * len(header)) + '|')
    for r in rows:
        out.append('| ' + ' | '.join('' if v is None else (('%g' % v) if isinstance(v, float) else str(v))
                                     for v in r) + ' |')
    if note:
        out.append('')
        out.append(note)
    out.append('')
    return '\n'.join(out)


def table_q1(res):
    """表1 温度 / 表2 水分浓度：100,300,600,900,1200,1500,1800 s；r = 0,0.5,1,1.5,2 cm"""
    ts = [100, 300, 600, 900, 1200, 1500, 1800]
    rs = [0.0, 0.5, 1.0, 1.5, 2.0]
    idx = {int(round(t)): k for k, t in enumerate(res.times)}
    hdr = ['时间 / s'] + ['%g' % r for r in rs]
    out = {}
    for which, name in (('T', '表1  30 分钟内药材的温度（单位：°C）'),
                        ('C', '表2  30 分钟内药材的水分浓度（单位：kg/kg）')):
        rows = []
        for t in ts:
            k = idx[t]
            line = [t]
            for r_cm in rs:
                xq = r_cm * 1e-2 / res.R[k]
                v = res.interp_T(k, xq) if which == 'T' else res.interp_C(k, xq)
                line.append(_r4(v))
            rows.append(line)
        out[name] = _md_table(name + '（到药材中心的距离 / cm）', hdr, rows)
    return out


def table_q2(res):
    """表3 温度 / 表4 水分浓度：0.5,1.0,...,3.0 h；r = 0,0.5,1,1.5,2 cm"""
    hs = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    rs = [0.0, 0.5, 1.0, 1.5, 2.0]
    idx = {int(round(t)): k for k, t in enumerate(res.times)}
    hdr = ['时间 / h'] + ['%g' % r for r in rs]
    out = {}
    for which, name in (('T', '表3  3 小时内药材的温度（单位：°C）'),
                        ('C', '表4  3 小时内药材的水分浓度（单位：kg/kg）')):
        rows = []
        for h in hs:
            k = idx[int(round(h * 3600))]
            line = ['%g' % h]
            for r_cm in rs:
                xq = r_cm * 1e-2 / res.R[k]
                v = res.interp_T(k, xq) if which == 'T' else res.interp_C(k, xq)
                line.append(_r4(v))
            rows.append(line)
        out[name] = _md_table(name + '（到药材中心的距离 / cm）', hdr, rows)
    return out


def table_q34(res, cap, with_surface=False):
    """表5/表6：每隔 6 h、距离每隔 0.5 cm 的水分浓度，末行为烘干结束时间。
    with_surface=True 时额外给出「药材表面」列（问题4 收缩后表面位置随时间变化）。"""
    rs = [0.0, 0.5, 1.0, 1.5, 2.0]
    t_end = find_crossing(res, C_TARGET) or res.times[-1]
    ts = []
    h = 6.0
    while h * 3600 < t_end:
        ts.append(h)
        h += 6.0
    idx = {int(round(t)): k for k, t in enumerate(res.times)}
    hdr = ['时间 / h'] + ['%g' % r for r in rs] + (['药材表面', '当前半径 R/cm'] if with_surface else [])
    rows = []

    def line_for(k, label):
        line = [label]
        for r_cm in rs:
            r = r_cm * 1e-2
            line.append(None if r > res.R[k] + 1e-12 else _r4(res.interp_C(k, r / res.R[k])))
        if with_surface:
            line.append(_r4(res.C[k][-1]))
            line.append(_r4(res.R[k] * 100.0))
        return line

    for h in ts:
        t = int(round(h * 3600))
        if t not in idx:
            continue
        rows.append(line_for(idx[t], '%g' % h))
    kf = len(res.times) - 1
    for k, t in enumerate(res.times):
        if t >= t_end - 1e-9:
            kf = k
            break
    rows.append(line_for(kf, '烘干结束时间(%.4f h)' % (t_end / 3600.0)))
    note = '（到药材中心的距离 / cm'
    note += '；空白表示该半径已超出当前药材表面' if with_surface else ''
    note += '）\n\n> 注：末行为烘干判据 $\\max_r C=0.15$ 被满足的临界时刻，'
    note += '故该行中心处数值按定义恰为 0.1500；'
    note += '结果文件 result%d.xlsx 记录至 60 s 网格上最大含水率**严格低于** 0.15 的首个时刻。' % (4 if with_surface else 3)
    return _md_table(cap + note, hdr, rows)


# ----------------------------------------------------------------------
def main():
    q1f = load(1, 400, 4)
    q2f = load(2, 400, 2)
    q3f = load(3, 400, 12)
    q4f = load(4, 400, 12)

    p1, n1 = build_result12(q1f, 1)
    p2, n2 = build_result12(q2f, 2)
    p3, n3, te3 = build_result34(q3f, 3, False)
    p4, n4, te4 = build_result34(q4f, 4, True)

    print('result1.xlsx : %d 行 × 21 列 × 2 表' % n1)
    print('result2.xlsx : %d 行 × 21 列 × 2 表' % n2)
    print('result3.xlsx : %d 行（60 s 步长，至 %.1f s = %.4f h）' % (n3, te3, te3 / 3600.0))
    print('result4.xlsx : %d 行（60 s 步长，至 %.1f s = %.4f h，含药材表面列）' % (n4, te4, te4 / 3600.0))
    print('  ->', OUT_DIR)

    os.makedirs(TAB_DIR, exist_ok=True)
    parts = []
    parts.append('# 论文表格（由模型计算结果直接生成）\n')
    t1 = table_q1(q1f)
    t2 = table_q2(q2f)
    parts.append('## 问题 1\n')
    parts.append(t1['表1  30 分钟内药材的温度（单位：°C）'])
    parts.append(t1['表2  30 分钟内药材的水分浓度（单位：kg/kg）'])
    parts.append('## 问题 2\n')
    parts.append(t2['表3  3 小时内药材的温度（单位：°C）'])
    parts.append(t2['表4  3 小时内药材的水分浓度（单位：kg/kg）'])
    parts.append('## 问题 3\n')
    parts.append(table_q34(q3f, '表5  药材烘干过程的水分浓度（单位：kg/kg）'))
    parts.append('## 问题 4\n')
    parts.append(table_q34(q4f, '表6  药材烘干过程的水分浓度（单位：kg/kg）', with_surface=True))
    tp = os.path.join(TAB_DIR, '论文表格_表1-表6.md')
    with open(tp, 'w', encoding='utf-8') as f:
        f.write('\n'.join(parts))
    print('  ->', tp)

    tc = find_crossing(q3f, C_TARGET)
    td = find_crossing(q4f, C_TARGET)
    print()
    print('问题3 烘干时间 T* = %.4f s = %.6f h = %.4f d' % (tc, tc / 3600.0, tc / 86400.0))
    print('问题4 烘干时间 T* = %.4f s = %.6f h = %.4f d' % (td, td / 3600.0, td / 86400.0))
    print('收缩使烘干时间缩短 %.2f%%' % ((tc - td) / tc * 100.0))


def selftest():
    """用已完成的算例快速验证 xlsx 生成与回读，不必等全部生产算例。"""
    q1f = load(1, 400, 4)
    p1, n1 = build_result12(q1f, 1)
    print('result1.xlsx : %d 行' % n1)
    q3f = load(3, 200, 12)
    p3, n3, te3 = build_result34(q3f, 3, False)
    print('result3.xlsx : %d 行, 至 %.1f s' % (n3, te3))
    q4f = load(4, 200, 12)
    p4, n4, te4 = build_result34(q4f, 4, True)
    print('result4.xlsx : %d 行, 至 %.1f s' % (n4, te4))

    from xlsxio import read_workbook
    for p in (p1, p3, p4):
        wb = read_workbook(p)
        for nm, rows in wb.items():
            print('  [%s] %s : %d 行 × %d 列 | 首行 %s | 末行 %s'
                  % (os.path.basename(p), nm, len(rows), len(rows[0]),
                     rows[0][:4], rows[-1][:4]))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'selftest':
        selftest()
    else:
        main()
