# -*- coding: utf-8 -*-
"""
raster.py —— 极简 SVG 光栅化器（仅支持 svgplot.py 使用的图元）
用途：把生成的 SVG 插图渲染成 PNG，供人工/视觉检查版式是否正确。
支持 rect / line / polyline / circle / text(以占位框表示文字范围) / rotate 变换。
"""
import sys
import os
import re
import math
import zlib
import struct
import xml.etree.ElementTree as ET

NS = '{http://www.w3.org/2000/svg}'


def _parse_color(c, default=(0, 0, 0)):
    if not c or c == 'none':
        return None
    c = c.strip()
    if c.startswith('#'):
        h = c[1:]
        if len(h) == 3:
            h = ''.join(ch * 2 for ch in h)
        try:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except ValueError:
            return default
    named = {'white': (255, 255, 255), 'black': (0, 0, 0), 'red': (255, 0, 0),
             'gray': (128, 128, 128), 'grey': (128, 128, 128)}
    return named.get(c.lower(), default)


def _num(v, d=0.0):
    if v is None:
        return d
    m = re.match(r'-?\d*\.?\d+(?:[eE][-+]?\d+)?', str(v).strip())
    return float(m.group(0)) if m else d


class Canvas(object):
    def __init__(self, w, h, bg=(255, 255, 255)):
        self.w, self.h = int(w), int(h)
        self.buf = bytearray(self.w * self.h * 3)
        for i in range(self.w * self.h):
            self.buf[i * 3] = bg[0]
            self.buf[i * 3 + 1] = bg[1]
            self.buf[i * 3 + 2] = bg[2]

    def px(self, x, y, col, alpha=1.0):
        xi, yi = int(x), int(y)
        if xi < 0 or yi < 0 or xi >= self.w or yi >= self.h:
            return
        i = (yi * self.w + xi) * 3
        if alpha >= 1.0:
            self.buf[i] = col[0]
            self.buf[i + 1] = col[1]
            self.buf[i + 2] = col[2]
        else:
            a = alpha
            self.buf[i] = int(self.buf[i] * (1 - a) + col[0] * a)
            self.buf[i + 1] = int(self.buf[i + 1] * (1 - a) + col[1] * a)
            self.buf[i + 2] = int(self.buf[i + 2] * (1 - a) + col[2] * a)

    def rect(self, x, y, w, h, col, alpha=1.0):
        if col is None:
            return
        x0, y0 = int(math.floor(x)), int(math.floor(y))
        x1, y1 = int(math.ceil(x + w)), int(math.ceil(y + h))
        for yy in range(max(0, y0), min(self.h, y1)):
            for xx in range(max(0, x0), min(self.w, x1)):
                i = (yy * self.w + xx) * 3
                if alpha >= 1.0:
                    self.buf[i], self.buf[i + 1], self.buf[i + 2] = col
                else:
                    a = alpha
                    self.buf[i] = int(self.buf[i] * (1 - a) + col[0] * a)
                    self.buf[i + 1] = int(self.buf[i + 1] * (1 - a) + col[1] * a)
                    self.buf[i + 2] = int(self.buf[i + 2] * (1 - a) + col[2] * a)

    def line(self, x0, y0, x1, y1, col, width=1.0, alpha=1.0):
        if col is None:
            return
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        n = min(n, 20000)
        r = max(0.5, width / 2.0)
        for i in range(n + 1):
            t = i / float(n) if n else 0.0
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            if width <= 1.2:
                self.px(x, y, col, alpha)
            else:
                for dy in range(-int(r), int(r) + 1):
                    for dx in range(-int(r), int(r) + 1):
                        if dx * dx + dy * dy <= r * r + 0.6:
                            self.px(x + dx, y + dy, col, alpha)

    def circle(self, cx, cy, r, col, alpha=1.0):
        if col is None:
            return
        R = int(math.ceil(r))
        for dy in range(-R, R + 1):
            for dx in range(-R, R + 1):
                if dx * dx + dy * dy <= r * r + 0.5:
                    self.px(cx + dx, cy + dy, col, alpha)

    def text_box(self, x, y, s, size, anchor, col=(120, 120, 120), rot=0):
        """用占位框表示文字范围（中文按 1.0em、西文按 0.55em 估算）。"""
        wsum = 0.0
        for ch in s:
            wsum += 1.0 if ord(ch) > 0x2000 else 0.55
        w = wsum * size * 0.95
        h = size * 1.0
        if rot == 0:
            if anchor == 'middle':
                x0 = x - w / 2.0
            elif anchor == 'end':
                x0 = x - w
            else:
                x0 = x
            y0 = y - h * 0.78
            self.rect(x0, y0, w, h * 0.82, (232, 232, 232))
            self.rect(x0, y0, w, 1.0, col)
            self.rect(x0, y0 + h * 0.82, w, 1.0, col)
        else:
            # 旋转 90 度：文字沿竖直方向延伸
            if anchor == 'middle':
                y0 = y - w / 2.0
            elif anchor == 'end':
                y0 = y - w
            else:
                y0 = y
            x0 = x - h * 0.78
            self.rect(x0, y0, h * 0.82, w, (232, 232, 232))
            self.rect(x0, y0, 1.0, w, col)
            self.rect(x0 + h * 0.82, y0, 1.0, w, col)

    def write_png(self, path):
        raw = bytearray()
        for y in range(self.h):
            raw.append(0)
            raw += self.buf[y * self.w * 3:(y + 1) * self.w * 3]

        def chunk(t, d):
            return (struct.pack('>I', len(d)) + t + d +
                    struct.pack('>I', zlib.crc32(t + d) & 0xffffffff))

        hdr = struct.pack('>IIBBBBB', self.w, self.h, 8, 2, 0, 0, 0)
        png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', hdr) +
               chunk(b'IDAT', zlib.compress(bytes(raw), 6)) + chunk(b'IEND', b''))
        d = os.path.dirname(os.path.abspath(path))
        if d:
            os.makedirs(d, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(png)
        return path


def _transform_of(el):
    tr = el.get('transform')
    if not tr:
        return None
    m = re.search(r'rotate\(\s*(-?[\d.]+)[,\s]+(-?[\d.]+)[,\s]+(-?[\d.]+)\s*\)', tr)
    if m:
        return ('rot', float(m.group(1)), float(m.group(2)), float(m.group(3)))
    return None


def _apply(tr, x, y):
    if tr is None or tr[0] != 'rot':
        return x, y
    a = math.radians(tr[1])
    cx, cy = tr[2], tr[3]
    dx, dy = x - cx, y - cy
    return (cx + dx * math.cos(a) - dy * math.sin(a),
            cy + dx * math.sin(a) + dy * math.cos(a))


def render(svg_path, png_path, scale=1.0):
    tree = ET.parse(svg_path)
    root = tree.getroot()
    w = _num(root.get('width'), 800)
    h = _num(root.get('height'), 600)
    cv = Canvas(w * scale, h * scale)
    g = {'stroke': None, 'fill': None, 'sw': 1.0, 'op': 1.0, 'font': 13}

    def walk(el, inherit):
        st = dict(inherit)
        for k in ('stroke', 'fill', 'stroke-width', 'stroke-opacity',
                  'fill-opacity', 'opacity', 'font-size'):
            v = el.get(k)
            if v is not None:
                st[k] = v
        tr = _transform_of(el)
        tag = el.tag.replace(NS, '')
        if tag == 'rect':
            col = _parse_color(st.get('fill'))
            op = _num(st.get('fill-opacity'), 1.0) * _num(st.get('opacity'), 1.0)
            if col:
                cv.rect(_num(el.get('x')) * scale, _num(el.get('y')) * scale,
                        _num(el.get('width')) * scale, _num(el.get('height')) * scale, col, op)
            sc = _parse_color(st.get('stroke'))
            if sc:
                x, y = _num(el.get('x')) * scale, _num(el.get('y')) * scale
                ww, hh = _num(el.get('width')) * scale, _num(el.get('height')) * scale
                sw = _num(st.get('stroke-width'), 1.0) * scale
                cv.line(x, y, x + ww, y, sc, sw)
                cv.line(x + ww, y, x + ww, y + hh, sc, sw)
                cv.line(x + ww, y + hh, x, y + hh, sc, sw)
                cv.line(x, y + hh, x, y, sc, sw)
        elif tag == 'line':
            col = _parse_color(st.get('stroke'))
            sw = _num(st.get('stroke-width'), 1.0) * scale
            p0 = _apply(tr, _num(el.get('x1')) * scale, _num(el.get('y1')) * scale)
            p1 = _apply(tr, _num(el.get('x2')) * scale, _num(el.get('y2')) * scale)
            cv.line(p0[0], p0[1], p1[0], p1[1], col, sw,
                    _num(st.get('stroke-opacity'), 1.0))
        elif tag == 'polyline':
            col = _parse_color(st.get('stroke'))
            sw = _num(st.get('stroke-width'), 1.0) * scale
            pts = el.get('points', '').split()
            prev = None
            for pt in pts:
                if ',' not in pt:
                    continue
                a, b = pt.split(',')
                cur = _apply(tr, float(a) * scale, float(b) * scale)
                if prev:
                    cv.line(prev[0], prev[1], cur[0], cur[1], col, sw)
                prev = cur
        elif tag == 'circle':
            col = _parse_color(st.get('fill'))
            c = _apply(tr, _num(el.get('cx')) * scale, _num(el.get('cy')) * scale)
            cv.circle(c[0], c[1], _num(el.get('r'), 2) * scale, col)
        elif tag == 'text':
            col = _parse_color(st.get('fill'), (60, 60, 60))
            size = _num(st.get('font-size'), 13) * scale
            x, y = _num(el.get('x')) * scale, _num(el.get('y')) * scale
            anchor = el.get('text-anchor', 'start')
            rot = 0
            if tr is not None and tr[0] == 'rot':
                x, y = _apply(tr, x, y)
                rot = 1 if abs(abs(tr[1]) - 90) < 1 else 0
            s = ''.join(el.itertext())
            cv.text_box(x, y, s, size, anchor, col or (60, 60, 60), rot)
        for ch in el:
            walk(ch, st)

    walk(root, g)
    return cv.write_png(png_path)


if __name__ == '__main__':
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src.rsplit('.', 1)[0] + '.png'
    p = render(src, dst)
    print('rendered ->', p, os.path.getsize(p), 'bytes')
