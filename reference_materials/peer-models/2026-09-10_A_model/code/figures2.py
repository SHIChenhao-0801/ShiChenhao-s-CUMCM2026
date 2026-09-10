# -*- coding: utf-8 -*-
"""
figures2.py —— 收敛性、敏感度与模型对比插图（图17—图20）
依赖 sensitivity.json 与 conv_tstar 的结果（若尚未生成则自动跳过）。
"""
import os
import sys
import json
import pickle
import math

from physics import OUT_DIR, FIG_DIR, C_TARGET, PROPS_Q23, PROPS_Q4, R_TAB, R0
from solver import find_crossing
from svgplot import Plot, PALETTE

PKL = os.path.join(OUT_DIR, 'pkl')
MADE = []


def load(tag):
    with open(os.path.join(PKL, tag + '.pkl'), 'rb') as f:
        return pickle.load(f)


def save(p, name):
    MADE.append((name, p))
    return p


def fig17_convergence():
    """图17 烘干时间 T* 的网格与时间步收敛性"""
    sens = _load_json('sensitivity.json')
    if not sens:
        print('  跳过图17：sensitivity.json 尚未生成')
        return
    rows = sens.get('rows', [])
    grid = [(r['name'], r['T_star_h']) for r in rows if r['cat'] == 'num' and 'N=' in r['name']]
    subs = [(r['name'], r['T_star_h']) for r in rows if r['cat'] == 'num' and 'sub=' in r['name']]
    if not grid:
        print('  跳过图17：缺少网格数据')
        return

    p = Plot(800, 450, title='图17a  烘干时间 T* 的网格收敛性（问题3）',
             xlabel='径向节点数 N', ylabel='烘干时间 T* / h',
             xlim=(60, 860), legend_loc='upper right')
    Ns = [int(g[0].replace('网格 ', '').replace('N=', '')) for g in grid]
    Ts = [g[1] for g in grid]
    p.add(Ns, Ts, label='数值计算 T*(N)', color='#1f4e9c', width=2.4, marker='o', msize=4.5)
    rich = Ts[-1] + (Ts[-1] - Ts[-2]) / 3.0
    p.add([60, 860], [rich, rich], label='二阶 Richardson 外推 %.4f h' % rich,
          color='#c0392b', width=1.8, dash='6,4')
    for n, v in zip(Ns, Ts):
        p.text(n + 22, v + 0.35, '%.4f' % v, color='#333', size=11)
    save(p.save(os.path.join(FIG_DIR, 'fig17_conv_grid.svg')), '图17a T*网格收敛')

    if subs:
        p2 = Plot(800, 450, title='图17b  烘干时间 T* 的时间步收敛性（问题3, N=200）',
                  xlabel='时间子步 sub（Δt = 60/sub 秒）', ylabel='烘干时间 T* / h',
                  xlim=(0, len(subs) + 1))
        p2.bar([s[0].split('(')[0].replace('时间子步 ', '') for s in subs],
               [s[1] for s in subs], width=0.5, value_fmt='%.5f')
        save(p2.save(os.path.join(FIG_DIR, 'fig17_conv_sub.svg')), '图17b T*时间步收敛')


def fig18_tornado():
    """图18 参数敏感度龙卷风图"""
    sens = _load_json('sensitivity.json')
    if not sens:
        print('  跳过图18：sensitivity.json 尚未生成')
        return
    rows = [r for r in sens.get('rows', []) if r['cat'] in ('beta', 'h', 'D', 'Ceq')]
    if not rows:
        print('  跳过图18：缺少敏感度数据')
        return
    base = sens['baseline']['T_star_h']
    rows.sort(key=lambda r: abs(r['T_star_h'] - base))
    names = [r['name'] for r in rows]
    vals = [(r['T_star_h'] - base) / base * 100.0 for r in rows]

    lo = min(vals + [0.0]) * 1.25
    hi = max(vals + [0.0]) * 1.25
    if hi - lo < 1e-9:
        hi = lo + 1.0
    p = Plot(820, 520, title='图18  关键参数对烘干时间 T* 的敏感度（相对基准 %+.4f h）' % base,
             xlabel='T* 相对变化 / %', ylabel='', xlim=(lo, hi),
             legend_loc='lower right')
    yy = [len(rows) - i for i in range(len(rows))]
    for i, (nm, v) in enumerate(zip(names, vals)):
        p.add([0.0, v], [yy[i], yy[i]], label=(nm if i < 10 else ''),
              color=('#c0392b' if v > 0 else '#1f4e9c'), width=7.0)
    for i, (nm, v) in enumerate(zip(names, vals)):
        p.text(v, yy[i] + 0.28, '%s  %+.2f%%' % (nm, v), color='#333',
               size=11, anchor='start' if v >= 0 else 'end')
    p.vline(0.0, color='#333', dash='', width=1.4)
    save(p.save(os.path.join(FIG_DIR, 'fig18_tornado.svg')), '图18 敏感度龙卷风图')


def fig19_shrink_models():
    """图19 问题4 收缩口径对比"""
    sens = _load_json('sensitivity.json')
    if not sens:
        print('  跳过图19：sensitivity.json 尚未生成')
        return
    rows = [r for r in sens.get('rows', []) if r['cat'] == 'shrink']
    if not rows:
        return
    names = [r['name'] for r in rows]
    vals = [r['T_star_h'] for r in rows]
    p = Plot(860, 460, title='图19  问题4 收缩口径与物性组合对烘干时间的影响',
             xlabel='', ylabel='烘干时间 T* / h', xlim=(0, len(vals)),
             legend_loc='lower right')
    p.bar([''] * len(vals), vals, width=0.55)
    for i, (nm, v) in enumerate(zip(names, vals)):
        p.text(i + 0.5, v * 0.5, nm, color='#fff', size=10, anchor='middle')
    save(p.save(os.path.join(FIG_DIR, 'fig19_shrink_models.svg')), '图19 收缩口径对比')


def fig20_rate_compare():
    """图20 问题3 与问题4 干燥速率特征曲线对比"""
    try:
        q3 = load('q3_N400_sub12')
        q4 = load('q4_N400_sub12')
    except Exception:
        print('  跳过图20：缺少 Q3/Q4 结果')
        return
    p = Plot(820, 470, title='图20  问题3 与问题4 干燥速率特征曲线对比',
             xlabel='平均干基含水率 C_avg / (kg/kg)',
             ylabel='干燥速率 (−dM/dt)/A / (kg/(m²·s))', xlim=(0, 2.6), ylim=(0, None))
    for res, tag, col in ((q3, '问题3 无收缩', '#1f4e9c'), (q4, '问题4 含收缩', '#c0392b')):
        mean = [m / 2.0 for m in res.mass]
        xs, ys = [], []
        for k in range(1, len(res.times) - 1):
            dt = res.times[k + 1] - res.times[k - 1]
            if dt <= 0:
                continue
            rho_d = res.mass[k] and 0.0
            rho_d = (PROPS_Q23.rho(mean[k]) if tag.startswith('问题3')
                     else PROPS_Q4.rho(mean[k])) / (1.0 + mean[k])
            dM = (res.mass[k + 1] - res.mass[k - 1]) / dt
            xs.append(mean[k])
            ys.append(-dM * rho_d * res.R[k] / 2.0)
        p.add(xs, ys, label=tag, color=col, width=2.2)
    p.hline(0.0, color='#999')
    p.vline(0.15, color='#333', dash='5,4', label='C = 0.15 判据')
    save(p.save(os.path.join(FIG_DIR, 'fig20_rate_compare.svg')), '图20 干燥速率对比')


def _load_json(name):
    p = os.path.join(OUT_DIR, name)
    if not os.path.exists(p):
        return None
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    os.makedirs(FIG_DIR, exist_ok=True)
    fig17_convergence()
    fig18_tornado()
    fig19_shrink_models()
    fig20_rate_compare()
    print()
    print('新增插图 %d 张：' % len(MADE))
    for n, p in MADE:
        print('  %-26s %s' % (n, os.path.basename(p)))


if __name__ == '__main__':
    main()
