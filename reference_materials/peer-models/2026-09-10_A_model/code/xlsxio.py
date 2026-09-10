# -*- coding: utf-8 -*-
"""
xlsxio.py —— 纯标准库实现的 xlsx 读写（无需 numpy/openpyxl）

读：解析 sharedStrings / workbook / worksheet XML
写：直接生成最小合规的 OOXML 包（含 0.0000 数字格式与加粗表头）

用途：读取赛题附件与结果模板，生成 result1~result4.xlsx
"""
import zipfile
import re
import os
import xml.etree.ElementTree as ET

_NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
_RNS = '{http://schemas.openxmlformats.org/package/2006/relationships}'
_RID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


# ----------------------------------------------------------------------
# 读取
# ----------------------------------------------------------------------
def _col_to_idx(ref):
    m = re.match(r'([A-Z]+)', ref)
    n = 0
    for ch in m.group(1):
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def read_workbook(path):
    """返回 {sheet_name: [[cell, ...], ...]}，数值以 float 返回，文本以 str 返回。"""
    z = zipfile.ZipFile(path)
    shared = []
    if 'xl/sharedStrings.xml' in z.namelist():
        root = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in root.findall(_NS + 'si'):
            shared.append(''.join(t.text or '' for t in si.iter(_NS + 't')))

    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    rid2t = {r.get('Id'): r.get('Target') for r in rels.findall(_RNS + 'Relationship')}

    out = {}
    for sh in wb.find(_NS + 'sheets').findall(_NS + 'sheet'):
        name = sh.get('name')
        tgt = rid2t[sh.get(_RID)]
        if not tgt.startswith('xl/'):
            tgt = 'xl/' + tgt.lstrip('/')
        root = ET.fromstring(z.read(tgt))
        rows = []
        for row in root.iter(_NS + 'row'):
            cells = {}
            for c in row.findall(_NS + 'c'):
                ci = _col_to_idx(c.get('r'))
                t = c.get('t')
                v = c.find(_NS + 'v')
                isel = c.find(_NS + 'is')
                if t == 's' and v is not None:
                    val = shared[int(v.text)]
                elif t == 'inlineStr' and isel is not None:
                    val = ''.join(x.text or '' for x in isel.iter(_NS + 't'))
                elif v is not None:
                    try:
                        val = float(v.text)
                    except (TypeError, ValueError):
                        val = v.text
                else:
                    val = None
                cells[ci] = val
            rows.append([cells.get(i) for i in range(max(cells) + 1)] if cells else [])
        out[name] = rows
    return out


# ----------------------------------------------------------------------
# 写入
# ----------------------------------------------------------------------
def _esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;').replace("'", '&apos;'))


def _col_name(i):
    s = ''
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


_STYLES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<numFmts count="1"><numFmt numFmtId="164" formatCode="0.0000"/></numFmts>
<fonts count="2">
<font><sz val="11"/><name val="宋体"/></font>
<font><b/><sz val="11"/><name val="宋体"/></font>
</fonts>
<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="3">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/>
<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>
</cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>'''


def _sheet_xml(rows, style_map=None):
    """style_map: None 表示全部用 General；或 'auto' 表示第1行与A列用加粗、数据用0.0000。"""
    parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
             '<sheetData>']
    for ri, row in enumerate(rows, start=1):
        parts.append('<row r="%d">' % ri)
        for ci, val in enumerate(row):
            if val is None or val == '':
                continue
            ref = '%s%d' % (_col_name(ci), ri)
            if style_map == 'auto':
                if ri == 1 or ci == 0:
                    st = ' s="1"'
                else:
                    st = ' s="2"'
            else:
                st = ''
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                parts.append('<c r="%s"%s><v>%.10g</v></c>' % (ref, st, val))
            else:
                parts.append('<c r="%s"%s t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>'
                             % (ref, st, _esc(val)))
        parts.append('</row>')
    parts.append('</sheetData></worksheet>')
    return ''.join(parts)


def write_workbook(path, sheets, style_map='auto'):
    """sheets: [(name, rows), ...]；rows 为 list of list，元素为 str/float/int/None。"""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    n = len(sheets)
    ct = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
          '<Default Extension="xml" ContentType="application/xml"/>',
          '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
          '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>']
    for i in range(1, n + 1):
        ct.append('<Override PartName="/xl/worksheets/sheet%d.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' % i)
    ct.append('</Types>')

    wb = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
          '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>']
    rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
    for i, (name, _) in enumerate(sheets, start=1):
        wb.append('<sheet name="%s" sheetId="%d" r:id="rId%d"/>' % (_esc(name), i, i))
        rels.append('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet%d.xml"/>' % (i, i))
    wb.append('</sheets></workbook>')
    rels.append('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>' % (n + 1))
    rels.append('</Relationships>')

    root_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                 '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                 '</Relationships>')

    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ''.join(ct))
        z.writestr('_rels/.rels', root_rels)
        z.writestr('xl/workbook.xml', ''.join(wb))
        z.writestr('xl/_rels/workbook.xml.rels', ''.join(rels))
        z.writestr('xl/styles.xml', _STYLES)
        for i, (name, rows) in enumerate(sheets, start=1):
            z.writestr('xl/worksheets/sheet%d.xml' % i, _sheet_xml(rows, style_map))
    return path


if __name__ == '__main__':
    import sys
    p = sys.argv[1]
    for name, rows in read_workbook(p).items():
        print('sheet', name, len(rows), 'rows')
