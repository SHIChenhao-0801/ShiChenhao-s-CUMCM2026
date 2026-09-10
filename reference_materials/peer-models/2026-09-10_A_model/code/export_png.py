# -*- coding: utf-8 -*-
"""export_png.py —— 把全部 SVG 插图导出为高分辨率 PNG（便于插入 Word/PPT）。"""
import os
import glob
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from raster import render

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, '..', 'out', 'figures')
OUT = os.path.join(HERE, '..', 'out', 'png')

if __name__ == '__main__':
    scale = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
    os.makedirs(OUT, exist_ok=True)
    files = sorted(glob.glob(os.path.join(FIG, 'fig*.svg')))
    for f in files:
        dst = os.path.join(OUT, os.path.basename(f).replace('.svg', '.png'))
        render(f, dst, scale=scale)
        print('%-42s %8.1f KB' % (os.path.basename(dst), os.path.getsize(dst) / 1024.0))
    print('\n共 %d 张，输出目录 %s' % (len(files), os.path.abspath(OUT)))
