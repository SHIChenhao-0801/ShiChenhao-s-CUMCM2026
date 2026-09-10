# -*- coding: utf-8 -*-
"""check_figs.py —— SVG 插图结构化校验：XML 合法性、坐标越界、墨迹覆盖率。"""
import os
import re
import sys
import glob
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from raster import Canvas, render, _num, _parse_color, NS

FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out', 'figures')
PV = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out', 'preview')


def coords_of(root):
    xs, ys, n_el = [], [], 0
    bad = []
    for el in root.iter():
        tag = el.tag.replace(NS, '')
        n_el += 1
        vals = []
        if tag == 'rect':
            x, y, w, h = (_num(el.get('x')), _num(el.get('y')),
                          _num(el.get('width')), _num(el.get('height')))
            vals = [(x, y), (x + w, y + h)]
        elif tag == 'line':
            vals = [(_num(el.get('x1')), _num(el.get('y1'))),
                    (_num(el.get('x2')), _num(el.get('y2')))]
        elif tag == 'circle':
            cx, cy, r = _num(el.get('cx')), _num(el.get('cy')), _num(el.get('r'), 2)
            vals = [(cx - r, cy - r), (cx + r, cy + r)]
        elif tag == 'polyline':
            for pt in el.get('points', '').split():
                if ',' in pt:
                    a, b = pt.split(',')
                    try:
                        vals.append((float(a), float(b)))
                    except ValueError:
                        bad.append(pt)
        elif tag == 'text':
            vals = [(_num(el.get('x')), _num(el.get('y')))]
        for (a, b) in vals:
            if a != a or b != b:
                bad.append('NaN')
                continue
            xs.append(a)
            ys.append(b)
    return xs, ys, n_el, bad


def ink_stats(png):
    """统计 PNG 中非白像素比例与内容包围盒。"""
    import zlib, struct
    d = open(png, 'rb').read()
    pos = 8
    w = h = 0
    idat = b''
    while pos < len(d):
        ln = struct.unpack('>I', d[pos:pos + 4])[0]
        typ = d[pos + 4:pos + 8]
        data = d[pos + 8:pos + 8 + ln]
        if typ == b'IHDR':
            w, h = struct.unpack('>II', data[:8])
        elif typ == b'IDAT':
            idat += data
        pos += 12 + ln
    raw = zlib.decompress(idat)
    stride = w * 3
    n_ink = 0
    x0, y0, x1, y1 = w, h, -1, -1
    prev = bytearray(stride)
    i = 0
    for y in range(h):
        f = raw[i]
        i += 1
        line = bytearray(raw[i:i + stride])
        i += stride
        if f == 1:
            for k in range(3, stride):
                line[k] = (line[k] + line[k - 3]) & 255
        elif f == 2:
            for k in range(stride):
                line[k] = (line[k] + prev[k]) & 255
        elif f == 3:
            for k in range(stride):
                a = line[k - 3] if k >= 3 else 0
                line[k] = (line[k] + ((a + prev[k]) >> 1)) & 255
        elif f == 4:
            for k in range(stride):
                a = line[k - 3] if k >= 3 else 0
                b = prev[k]
                c = prev[k - 3] if k >= 3 else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[k] = (line[k] + pr) & 255
        prev = line
        for x in range(w):
            r, g, b = line[x * 3], line[x * 3 + 1], line[x * 3 + 2]
            if r < 245 or g < 245 or b < 245:
                n_ink += 1
                if x < x0:
                    x0 = x
                if x > x1:
                    x1 = x
                if y < y0:
                    y0 = y
                if y > y1:
                    y1 = y
    return w, h, n_ink / float(w * h), (x0, y0, x1, y1)


def main():
    os.makedirs(PV, exist_ok=True)
    files = sorted(glob.glob(os.path.join(FIG, 'fig*.svg')))
    print('%-46s %6s %6s %8s %8s %s' % ('file', 'W', 'H', 'ink%', 'els', 'bounds/status'))
    problems = []
    for f in files:
        try:
            root = ET.parse(f).getroot()
        except ET.ParseError as e:
            print('%-46s XML ERROR %s' % (os.path.basename(f), e))
            problems.append((f, 'xml'))
            continue
        W, H = _num(root.get('width')), _num(root.get('height'))
        xs, ys, n_el, bad = coords_of(root)
        png = os.path.join(PV, os.path.basename(f).replace('.svg', '.png'))
        render(f, png)
        w, h, ink, box = ink_stats(png)
        status = 'OK'
        msgs = []
        if bad:
            msgs.append('BAD_PTS=%d' % len(bad))
        if xs and (min(xs) < -2 or max(xs) > W + 2):
            msgs.append('X_OUT[%.0f,%.0f]/%.0f' % (min(xs), max(xs), W))
        if ys and (min(ys) < -2 or max(ys) > H + 2):
            msgs.append('Y_OUT[%.0f,%.0f]/%.0f' % (min(ys), max(ys), H))
        if ink < 0.01:
            msgs.append('TOO_EMPTY')
        if ink > 0.75:
            msgs.append('TOO_DENSE')
        if box[2] >= w - 1 or box[3] >= h - 1 or box[0] <= 0 or box[1] <= 0:
            msgs.append('CLIPPED')
        if msgs:
            status = ' '.join(msgs)
            problems.append((f, status))
        print('%-46s %6.0f %6.0f %7.2f%% %8d %s'
              % (os.path.basename(f), W, H, ink * 100, n_el, status))
    print()
    print('共 %d 张，异常 %d 张' % (len(files), len(problems)))
    for f, s in problems:
        print('  !! %s : %s' % (os.path.basename(f), s))


if __name__ == '__main__':
    main()
