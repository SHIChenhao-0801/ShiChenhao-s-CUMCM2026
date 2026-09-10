# -*- coding: utf-8 -*-
"""
svgplot.py —— 纯标准库 SVG 科学绘图库（用于生成论文级矢量插图）

支持
    * 多序列折线 / 散点 / 误差棒
    * 双 Y 轴（左右）
    * 对数坐标
    * 网格、图例、中文标注（SimSun / Microsoft YaHei）
    * 矩形网格热力图 + Marching Squares 等值线
输出为矢量 SVG，可无损缩放到论文任意尺寸；浏览器/Word 均直接支持。
"""
import math
import os

FONT = "'Times New Roman','SimSun','Microsoft YaHei',serif"
FONT_CJK = "'SimSun','Microsoft YaHei','Times New Roman',serif"

PALETTE = ['#1f4e9c', '#c0392b', '#1e8449', '#b7791f', '#6c3483',
           '#00838f', '#d35400', '#2c3e50', '#7f8c8d', '#a93226']


# ----------------------------------------------------------------------
# 刻度
# ----------------------------------------------------------------------
def nice_ticks(lo, hi, target=6, log=False):
    if log:
        a = int(math.floor(math.log10(lo)))
        b = int(math.ceil(math.log10(hi)))
        step = max(1, (b - a) // max(1, target - 1))
        out = []
        e = a
        while e <= b:
            for m in (1, 2, 5):
                v = m * (10.0 ** e)
                if lo <= v <= hi:
                    out.append(v)
            e += step
        return sorted(set(out)) or [lo, hi]
    if not (hi > lo):
        return [lo]
    raw = (hi - lo) / float(target)
    e = math.floor(math.log10(raw))
    f = raw / (10.0 ** e)
    if f <= 1.0:
        nice = 1.0
    elif f <= 2.0:
        nice = 2.0
    elif f <= 2.5:
        nice = 2.5
    elif f <= 5.0:
        nice = 5.0
    else:
        nice = 10.0
    step = nice * (10.0 ** e)
    start = math.floor(lo / step) * step
    out = []
    v = start
    while v <= hi + step * 1e-9:
        if v >= lo - step * 1e-9:
            out.append(round(v, 12))
        v += step
    return out


def fmt_tick(v, step=None):
    if v == 0:
        return '0'
    a = abs(v)
    if step is not None and step >= 1:
        return '%d' % round(v)
    if a >= 1e5 or a < 1e-3:
        s = '%.1e' % v
        m, e = s.split('e')
        e = int(e)
        return '%s×10<tspan baseline-shift="super" font-size="8">%d</tspan>' % (m, e)
    if a >= 100:
        return '%.0f' % v
    if a >= 1:
        return ('%.2f' % v).rstrip('0').rstrip('.')
    if a >= 0.01:
        return ('%.3f' % v).rstrip('0').rstrip('.')
    return ('%.4f' % v).rstrip('0').rstrip('.')


def _esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


# ----------------------------------------------------------------------
# 折线图
# ----------------------------------------------------------------------
class Plot(object):
    def __init__(self, w=760, h=500, title='', xlabel='', ylabel='', ylabel2='',
                 xlim=None, ylim=None, ylim2=None,
                 logx=False, logy=False, legend_loc='upper right',
                 nxtick=7, nytick=6, fs=13):
        self.w, self.h = w, h
        self.title, self.xlabel, self.ylabel, self.ylabel2 = title, xlabel, ylabel, ylabel2
        self.xlim, self.ylim, self.ylim2 = xlim, ylim, ylim2
        self.logx, self.logy = logx, logy
        self.legend_loc = legend_loc
        self.nxtick, self.nytick = nxtick, nytick
        self.fs = fs
        self.series = []
        self.vlines = []
        self.hlines = []
        self.texts = []
        self.dual = ylabel2 != ''
        self.ml, self.mr, self.mt, self.mb = 82, (82 if self.dual else 26), 52, 74

    # ---- 数据 ----
    def add(self, xs, ys, label='', color=None, width=2.0, dash=None,
            marker=None, msize=3.2, axis=1, alpha=1.0, smooth=None):
        if color is None:
            color = PALETTE[len(self.series) % len(PALETTE)]
        self.series.append(dict(xs=list(xs), ys=list(ys), label=label, color=color,
                                width=width, dash=dash, marker=marker,
                                msize=msize, axis=axis, alpha=alpha))
        return self

    def bar(self, labels, values, colors=None, width=0.6, label='', axis=1,
            value_fmt='%.4g'):
        """竖排柱状图；labels 为类目名（等距排布），values 为高度。"""
        n = len(values)
        pos = [i + 0.5 for i in range(n)]
        self._bars = getattr(self, '_bars', [])
        for i, (p, v) in enumerate(zip(pos, values)):
            c = (colors[i] if colors else PALETTE[i % len(PALETTE)])
            self._bars.append((p, v, c, width, axis, value_fmt,
                               labels[i] if labels else ''))
        if self.xlim is None:
            self.xlim = (0.0, float(n))
        return self

    def vline(self, x, color='#888', dash='4,3', width=1.2, label=''):
        self.vlines.append((x, color, dash, width, label))
        return self

    def hline(self, y, color='#888', dash='4,3', width=1.2, label='', axis=1):
        self.hlines.append((y, color, dash, width, label, axis))
        return self

    def text(self, x, y, s, color='#222', size=None, anchor='start', axis=1):
        self.texts.append((x, y, s, color, size or self.fs, anchor, axis))
        return self

    # ---- 坐标系 ----
    def _ranges(self):
        xs, ys, ys2 = [], [], []
        for s in self.series:
            if s['axis'] == 1:
                xs += [v for v in s['xs'] if v is not None]
                ys += [v for v in s['ys'] if v is not None]
            else:
                ys2 += [v for v in s['ys'] if v is not None]
                xs += [v for v in s['xs'] if v is not None]
        for (p, v, c, bw, ax, vf, lab) in getattr(self, '_bars', []):
            xs.append(p)
            if ax == 1:
                ys.append(v)
            else:
                ys2.append(v)

        def fix(lim, vals, padfrac=0.06):
            lo_v, hi_v = (min(vals), max(vals)) if vals else (0.0, 1.0)
            if hi_v == lo_v:
                hi_v = lo_v + 1.0
            lo0 = lim[0] if lim is not None and lim[0] is not None else lo_v - padfrac * (hi_v - lo_v)
            hi0 = lim[1] if lim is not None and lim[1] is not None else hi_v + padfrac * (hi_v - lo_v)
            return (lo0, hi0)

        if self.xlim is None or self.xlim[0] is None or self.xlim[1] is None:
            self.xlim = fix(self.xlim, xs, 0.02)
        if self.ylim is None or self.ylim[0] is None or self.ylim[1] is None:
            self.ylim = fix(self.ylim, ys)
        if self.ylim2 is None or self.ylim2[0] is None or self.ylim2[1] is None:
            self.ylim2 = fix(self.ylim2, ys2 or ys)
        # 柱状图必须含 0，否则"数值几乎相同"时 y 轴范围退化成近零区间而柱高爆炸
        if getattr(self, '_bars', None) and not self.dual:
            a, b = self.ylim
            vals = [v for (_, v, _, _, ax, _, _) in self._bars if ax == 1]
            if vals:
                lo0 = min(0.0, min(vals))
                hi0 = max(0.0, max(vals))
                if hi0 == lo0:
                    hi0 = lo0 + 1.0
                pad = 0.06 * (hi0 - lo0)
                self.ylim = (lo0, hi0 + pad)

    def _px(self, x):
        pw = self.w - self.ml - self.mr
        a, b = self.xlim
        if self.logx:
            return self.ml + (math.log10(x) - math.log10(a)) / (math.log10(b) - math.log10(a)) * pw
        return self.ml + (x - a) / (b - a) * pw

    def _py(self, y, axis=1):
        ph = self.h - self.mt - self.mb
        lim = self.ylim if axis == 1 else self.ylim2
        a, b = lim
        if self.logy and axis == 1:
            return self.h - self.mb - (math.log10(y) - math.log10(a)) / (math.log10(b) - math.log10(a)) * ph
        return self.h - self.mb - (y - a) / (b - a) * ph

    # ---- 渲染 ----
    def svg(self):
        self._ranges()
        pw = self.w - self.ml - self.mr
        ph = self.h - self.mt - self.mb
        o = ['<?xml version="1.0" encoding="UTF-8"?>']
        o.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
                 'viewBox="0 0 %d %d" font-family="%s" font-size="%d">'
                 % (self.w, self.h, self.w, self.h, FONT_CJK, self.fs))
        o.append('<rect width="%d" height="%d" fill="#ffffff"/>' % (self.w, self.h))
        if self.title:
            o.append('<text x="%.1f" y="27" text-anchor="middle" font-size="%d" '
                     'font-weight="bold">%s</text>' % (self.w / 2.0, self.fs + 2, _esc(self.title)))

        # 网格 + 刻度
        xt = nice_ticks(self.xlim[0], self.xlim[1], self.nxtick, self.logx)
        yt = nice_ticks(self.ylim[0], self.ylim[1], self.nytick, self.logy)
        g = ['<g stroke="#dddddd" stroke-width="0.8">']
        for v in xt:
            if self.logx and v <= 0:
                continue
            X = self._px(v)
            g.append('<line x1="%.2f" y1="%d" x2="%.2f" y2="%d"/>' % (X, self.mt, X, self.mt + ph))
        for v in yt:
            if self.logy and v <= 0:
                continue
            Y = self._py(v)
            g.append('<line x1="%d" y1="%.2f" x2="%d" y2="%.2f"/>' % (self.ml, Y, self.ml + pw, Y))
        g.append('</g>')
        o += g

        # 坐标框
        o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="#333" '
                 'stroke-width="1.2"/>' % (self.ml, self.mt, pw, ph))

        # X 轴刻度
        for v in xt:
            if self.logx and v <= 0:
                continue
            X = self._px(v)
            o.append('<line x1="%.2f" y1="%d" x2="%.2f" y2="%d" stroke="#333" stroke-width="1.2"/>'
                     % (X, self.mt + ph, X, self.mt + ph + 5))
            o.append('<text x="%.2f" y="%d" text-anchor="middle" font-size="%d">%s</text>'
                     % (X, self.mt + ph + 20, self.fs - 1,
                        fmt_tick(v, xt[1] - xt[0] if len(xt) > 1 else None)))
        for v in yt:
            if self.logy and v <= 0:
                continue
            Y = self._py(v)
            o.append('<line x1="%d" y1="%.2f" x2="%d" y2="%.2f" stroke="#333" stroke-width="1.2"/>'
                     % (self.ml - 5, Y, self.ml, Y))
            o.append('<text x="%d" y="%.2f" text-anchor="end" font-size="%d">%s</text>'
                     % (self.ml - 9, Y + 4, self.fs - 1,
                        fmt_tick(v, yt[1] - yt[0] if len(yt) > 1 else None)))
        if self.dual:
            yt2 = nice_ticks(self.ylim2[0], self.ylim2[1], self.nytick, False)
            for v in yt2:
                Y = self._py(v, 2)
                o.append('<line x1="%d" y1="%.2f" x2="%d" y2="%.2f" stroke="#333" stroke-width="1.2"/>'
                         % (self.ml + pw, Y, self.ml + pw + 5, Y))
                o.append('<text x="%d" y="%.2f" text-anchor="start" font-size="%d">%s</text>'
                         % (self.ml + pw + 9, Y + 4, self.fs - 1,
                            fmt_tick(v, yt2[1] - yt2[0] if len(yt2) > 1 else None)))

        # 参考线
        for (x, c, d, w, lab) in self.vlines:
            X = self._px(x)
            o.append('<line x1="%.2f" y1="%d" x2="%.2f" y2="%d" stroke="%s" stroke-width="%.1f" '
                     'stroke-dasharray="%s"/>' % (X, self.mt, X, self.mt + ph, c, w, d))
            if lab:
                # 靠近右边界时改为右对齐，避免标注文字溢出画布
                if X > self.ml + pw * 0.55:
                    o.append('<text x="%.2f" y="%d" font-size="%d" fill="%s" '
                             'text-anchor="end">%s</text>'
                             % (X - 5, self.mt + 16, self.fs - 2, c, _esc(lab)))
                else:
                    o.append('<text x="%.2f" y="%d" font-size="%d" fill="%s">%s</text>'
                             % (X + 5, self.mt + 16, self.fs - 2, c, _esc(lab)))
        for (y, c, d, w, lab, ax) in self.hlines:
            Y = self._py(y, ax)
            o.append('<line x1="%d" y1="%.2f" x2="%d" y2="%.2f" stroke="%s" stroke-width="%.1f" '
                     'stroke-dasharray="%s"/>' % (self.ml, Y, self.ml + pw, Y, c, w, d))
            if lab:
                o.append('<text x="%d" y="%.2f" font-size="%d" fill="%s" text-anchor="end">%s</text>'
                         % (self.ml + pw - 5, Y - 5, self.fs - 2, c, _esc(lab)))

        # 数据
        for (p, v, c, bw, ax, vf, lab) in getattr(self, '_bars', []):
            X0 = self._px(p - bw / 2.0)
            X1 = self._px(p + bw / 2.0)
            Yv = self._py(v, ax)
            Y0 = self._py(0.0 if ax == 1 else min(0.0, v), ax)
            o.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s" '
                     'fill-opacity="0.85" stroke="%s" stroke-width="1.0"/>'
                     % (min(X0, X1), min(Yv, Y0), abs(X1 - X0), abs(Y0 - Yv) or 1.0, c, c))
            o.append('<text x="%.2f" y="%.2f" text-anchor="middle" font-size="%d" fill="%s">%s</text>'
                     % ((X0 + X1) / 2.0, min(Yv, Y0) - 5, self.fs - 2, '#222', vf % v))
            if lab:
                o.append('<text x="%.2f" y="%d" text-anchor="middle" font-size="%d">%s</text>'
                         % ((X0 + X1) / 2.0, self.mt + ph + 20, self.fs - 2, _esc(lab)))

        for s in self.series:
            pts = []
            for x, y in zip(s['xs'], s['ys']):
                if x is None or y is None:
                    continue
                if self.logx and x <= 0:
                    continue
                if self.logy and s['axis'] == 1 and y <= 0:
                    continue
                pts.append((self._px(x), self._py(y, s['axis'])))
            if not pts:
                continue
            da = ' stroke-dasharray="%s"' % s['dash'] if s['dash'] else ''
            op = ' opacity="%.2f"' % s['alpha'] if s['alpha'] < 1.0 else ''
            o.append('<polyline fill="none" stroke="%s" stroke-width="%.2f" '
                     'stroke-linejoin="round" stroke-linecap="round"%s%s points="%s"/>'
                     % (s['color'], s['width'], da, op,
                        ' '.join('%.2f,%.2f' % p for p in pts)))
            if s['marker']:
                for (X, Y) in pts[::max(1, len(pts) // 40)]:
                    o.append('<circle cx="%.2f" cy="%.2f" r="%.1f" fill="%s"/>'
                             % (X, Y, s['msize'], s['color']))

        # 轴标题
        o.append('<text x="%.1f" y="%d" text-anchor="middle" font-size="%d">%s</text>'
                 % ((self.ml + self.ml + pw) / 2.0, self.h - 26, self.fs + 1, _esc(self.xlabel)))
        o.append('<text x="18" y="%.1f" text-anchor="middle" font-size="%d" '
                 'transform="rotate(-90,18,%.1f)">%s</text>'
                 % (self.mt + ph / 2.0, self.fs + 1, self.mt + ph / 2.0, _esc(self.ylabel)))
        if self.dual:
            o.append('<text x="%d" y="%.1f" text-anchor="middle" font-size="%d" '
                     'transform="rotate(90,%d,%.1f)">%s</text>'
                     % (self.w - 18, self.mt + ph / 2.0, self.fs + 1,
                        self.w - 18, self.mt + ph / 2.0, _esc(self.ylabel2)))

        # 自由文本
        for (x, y, s, c, sz, an, ax) in self.texts:
            o.append('<text x="%.2f" y="%.2f" font-size="%d" fill="%s" text-anchor="%s">%s</text>'
                     % (self._px(x), self._py(y, ax), sz, c, an, _esc(s)))

        # 图例
        lab_series = [s for s in self.series if s['label']]
        if lab_series:
            bw = max(140, 10 + max(len(s['label']) for s in lab_series) * (self.fs - 1))
            bh = 16 * len(lab_series) + 10
            if 'upper right' in self.legend_loc:
                bx, by = self.ml + pw - bw - 10, self.mt + 10
            elif 'upper left' in self.legend_loc:
                bx, by = self.ml + 12, self.mt + 10
            elif 'lower left' in self.legend_loc:
                bx, by = self.ml + 12, self.mt + ph - bh - 10
            else:
                bx, by = self.ml + pw - bw - 10, self.mt + ph - bh - 10
            o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#ffffff" fill-opacity="0.88" '
                     'stroke="#bbbbbb" stroke-width="0.8"/>' % (bx, by, bw, bh))
            for i, s in enumerate(lab_series):
                yy = by + 16 + 16 * i
                o.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="%.2f"%s/>'
                         % (bx + 8, yy - 4, bx + 34, yy - 4, s['color'], s['width'],
                            ' stroke-dasharray="%s"' % s['dash'] if s['dash'] else ''))
                o.append('<text x="%d" y="%d" font-size="%d">%s</text>'
                         % (bx + 40, yy, self.fs - 2, _esc(s['label'])))
        o.append('</svg>')
        return '\n'.join(o)

    def save(self, path):
        d = os.path.dirname(os.path.abspath(path))
        if d:
            os.makedirs(d, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.svg())
        return path


# ----------------------------------------------------------------------
# 热力图 + 等值线
# ----------------------------------------------------------------------
def _colormap(t):
    """blue -> cyan -> green -> yellow -> red 的连续色标。"""
    t = 0.0 if t < 0 else (1.0 if t > 1 else t)
    stops = [(0.00, (8, 29, 88)), (0.20, (34, 94, 168)), (0.40, (29, 145, 192)),
             (0.60, (120, 198, 121)), (0.80, (253, 219, 119)), (1.00, (215, 48, 39))]
    for i in range(len(stops) - 1):
        a, ca = stops[i]
        b, cb = stops[i + 1]
        if a <= t <= b:
            w = (t - a) / (b - a)
            r = int(ca[0] + (cb[0] - ca[0]) * w)
            g = int(ca[1] + (cb[1] - ca[1]) * w)
            bl = int(ca[2] + (cb[2] - ca[2]) * w)
            return '#%02x%02x%02x' % (r, g, bl)
    return '#d73027'


def heatmap_svg(path, xs, ys, zs, title='', xlabel='', ylabel='',
                cblabel='', levels=None, w=820, h=470, ncb=6, fs=13,
                contour=True, ncont=9):
    """
    xs   : 列坐标（递增，长度 nx）
    ys   : 行坐标（递增，长度 ny）
    zs   : zs[iy][ix]
    """
    nx, ny = len(xs), len(ys)
    vals = [v for r in zs for v in r if v is not None]
    zmin = min(vals)
    zmax = max(vals)
    if zmax == zmin:
        zmax = zmin + 1.0
    ml, mr, mt, mb = 88, 120, 52, 74
    pw, ph = w - ml - mr, h - mt - mb
    cw, ch = pw / float(nx), ph / float(ny)

    def PX(x):
        return ml + (x - xs[0]) / (xs[-1] - xs[0]) * pw

    def PY(y):
        return h - mb - (y - ys[0]) / (ys[-1] - ys[0]) * ph

    o = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
         'font-family="%s" font-size="%d">' % (w, h, w, h, FONT_CJK, fs),
         '<rect width="%d" height="%d" fill="#ffffff"/>' % (w, h)]
    if title:
        o.append('<text x="%.1f" y="27" text-anchor="middle" font-size="%d" font-weight="bold">%s</text>'
                 % (w / 2.0, fs + 2, _esc(title)))

    for iy in range(ny):
        for ix in range(nx):
            if zs[iy][ix] is None:
                continue
            t = (zs[iy][ix] - zmin) / (zmax - zmin)
            X = PX(xs[ix]) - cw / 2.0
            Y = PY(ys[iy]) - ch / 2.0
            o.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s"/>'
                     % (X, Y, cw + 0.6, ch + 0.6, _colormap(t)))

    if contour and levels:
        segs = marching_squares(xs, ys, zs, levels)
        for lev, seg in zip(levels, segs):
            c = _colormap((lev - zmin) / (zmax - zmin))
            for (x1, y1, x2, y2) in seg:
                o.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#111111" '
                         'stroke-width="0.7" stroke-opacity="0.55"/>' % (PX(x1), PY(y1), PX(x2), PY(y2)))

    o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="#333" stroke-width="1.1"/>'
             % (ml, mt, pw, ph))

    xt = nice_ticks(xs[0], xs[-1], 6)
    for v in xt:
        X = PX(v)
        o.append('<line x1="%.2f" y1="%d" x2="%.2f" y2="%d" stroke="#333"/>' % (X, mt + ph, X, mt + ph + 5))
        o.append('<text x="%.2f" y="%d" text-anchor="middle" font-size="%d">%s</text>'
                 % (X, mt + ph + 20, fs - 1, fmt_tick(v)))
    yt = nice_ticks(ys[0], ys[-1], 6)
    for v in yt:
        Y = PY(v)
        o.append('<line x1="%d" y1="%.2f" x2="%d" y2="%.2f" stroke="#333"/>' % (ml - 5, Y, ml, Y))
        o.append('<text x="%d" y="%.2f" text-anchor="end" font-size="%d">%s</text>'
                 % (ml - 9, Y + 4, fs - 1, fmt_tick(v)))

    o.append('<text x="%.1f" y="%d" text-anchor="middle" font-size="%d">%s</text>'
             % (ml + pw / 2.0, h - 26, fs + 1, _esc(xlabel)))
    o.append('<text x="18" y="%.1f" text-anchor="middle" font-size="%d" '
             'transform="rotate(-90,18,%.1f)">%s</text>'
             % (mt + ph / 2.0, fs + 1, mt + ph / 2.0, _esc(ylabel)))

    bx = ml + pw + 26
    for i in range(ncb):
        Y = mt + ph - (i + 1) * ph / float(ncb)
        o.append('<rect x="%d" y="%.2f" width="20" height="%.2f" fill="%s"/>'
                 % (bx, Y, ph / ncb + 0.6, _colormap(1.0 - (i + 0.5) / ncb)))
    o.append('<rect x="%d" y="%d" width="20" height="%d" fill="none" stroke="#333" stroke-width="0.9"/>'
             % (bx, mt, ph))
    for i in range(ncb + 1):
        t = i / float(ncb)
        Y = mt + ph - t * ph
        v = zmin + (zmax - zmin) * t
        o.append('<text x="%d" y="%.2f" font-size="%d">%s</text>' % (bx + 26, Y + 4, fs - 2, fmt_tick(v)))
    if cblabel:
        o.append('<text x="%d" y="%.1f" text-anchor="middle" font-size="%d" '
                 'transform="rotate(90,%d,%.1f)">%s</text>'
                 % (w - 22, mt + ph / 2.0, fs, w - 22, mt + ph / 2.0, _esc(cblabel)))
    o.append('</svg>')
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(o))
    return path


def marching_squares(xs, ys, zs, levels):
    """对每个 level 返回线段列表 [(x1,y1,x2,y2), ...]。"""
    out = []
    ny, nx = len(ys), len(xs)
    for lev in levels:
        segs = []
        for iy in range(ny - 1):
            for ix in range(nx - 1):
                x0, x1 = xs[ix], xs[ix + 1]
                y0, y1 = ys[iy], ys[iy + 1]
                v00 = zs[iy][ix]
                v10 = zs[iy][ix + 1]
                v11 = zs[iy + 1][ix + 1]
                v01 = zs[iy + 1][ix]
                if None in (v00, v10, v11, v01):
                    continue
                pts = []

                def interp(pa, pb, va, vb):
                    if va == vb:
                        return None
                    w = (lev - va) / (vb - va)
                    if w < 0.0 or w > 1.0:
                        return None
                    return (pa[0] + (pb[0] - pa[0]) * w, pa[1] + (pb[1] - pa[1]) * w)

                edges = [interp((x0, y0), (x1, y0), v00, v10),
                         interp((x1, y0), (x1, y1), v10, v11),
                         interp((x1, y1), (x0, y1), v11, v01),
                         interp((x0, y1), (x0, y0), v01, v00)]
                for p in edges:
                    if p is not None:
                        pts.append(p)
                if len(pts) >= 2:
                    segs.append((pts[0][0], pts[0][1], pts[1][0], pts[1][1]))
        out.append(segs)
    return out


if __name__ == '__main__':
    import math
    p = Plot(title='SVG 绘图库自检', xlabel='x', ylabel='sin(x)', ylabel2='cos(x)')
    xs = [i * 0.05 for i in range(200)]
    p.add(xs, [math.sin(v) for v in xs], label='sin x', color='#1f4e9c')
    p.add(xs, [math.cos(v) for v in xs], label='cos x', color='#c0392b', dash='6,3', axis=2)
    p.hline(0.0, color='#999')
    p.vline(math.pi, label='x=pi')
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out', 'figures', '_selftest_line.svg')
    p.save(out)
    print('line ->', os.path.abspath(out))

    gx = [i * 0.05 for i in range(41)]
    gy = [j * 0.1 for j in range(21)]
    gz = [[math.sin(3 * a) * math.cos(2 * b) for a in gx] for b in gy]
    out2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out', 'figures', '_selftest_heat.svg')
    heatmap_svg(out2, gx, gy, gz, title='热力图自检', xlabel='x', ylabel='y', cblabel='z',
                levels=[-0.8, -0.4, 0.0, 0.4, 0.8])
    print('heat ->', os.path.abspath(out2))
