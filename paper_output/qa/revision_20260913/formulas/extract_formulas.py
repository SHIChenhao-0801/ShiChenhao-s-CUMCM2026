from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import json, re, hashlib

BASE=Path(__file__).resolve().parents[4]
SRC=BASE/'paper_output/paper/药材热湿耦合模型与干燥时间计算.docx'
OUT=Path(__file__).parent
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
def math(e):
    tag=E.QName(e).localname
    def sub(n):
        c=e.find('m:'+n,NS)
        return math(c) if c is not None else ''
    if tag.endswith('Pr'): return ''
    if tag=='t': return e.text or ''
    if tag=='f': return r'\frac{'+sub('num')+'}{'+sub('den')+'}'
    if tag=='sSub': return '{'+sub('e')+'}_{'+sub('sub')+'}'
    if tag=='sSup': return '{'+sub('e')+'}^{'+sub('sup')+'}'
    if tag=='sSubSup': return '{'+sub('e')+'}_{'+sub('sub')+'}^{'+sub('sup')+'}'
    if tag=='rad': return r'\sqrt['+sub('deg')+']{'+sub('e')+'}'
    if tag=='acc':
        c=e.find('m:accPr/m:chr',NS)
        ch=c.get('{'+NS['m']+'}val','') if c is not None else ''
        return {'̇':r'\dot','̂':r'\hat','̅':r'\bar'}.get(ch,r'\accent['+ch+']')+'{'+sub('e')+'}'
    if tag=='d':
        def v(k,default):
            n=e.find('m:dPr/m:'+k,NS)
            return n.get('{'+NS['m']+'}val',default) if n is not None else default
        return v('begChr','(')+sub('e')+v('endChr',')')
    if tag=='nary':
        ch=e.find('m:naryPr/m:chr',NS)
        return (ch.get('{'+NS['m']+'}val') if ch is not None else '∫')+'_{'+sub('sub')+'}^{'+sub('sup')+'} '+sub('e')
    if tag=='limLow': return sub('e')+'_{'+sub('lim')+'}'
    if tag=='limUpp': return sub('e')+'^{'+sub('lim')+'}'
    if tag=='func': return sub('fName')+sub('e')
    if tag in ('eqArr','m'): return ' | '.join(math(c) for c in e if not E.QName(c).localname.endswith('Pr'))
    return ''.join(math(c) for c in e)

with ZipFile(SRC) as z:
    root=E.fromstring(z.read('word/document.xml'))
blocks=[]
for i,b in enumerate(root.find('w:body',NS)):
    txt=''.join(b.xpath('.//w:t/text()',namespaces=NS))
    formulas=[math(x) for x in b.xpath('.//m:oMath[not(ancestor::m:oMath)]',namespaces=NS)]
    blocks.append({'index':i,'tag':E.QName(b).localname,'text':txt,'formulas':formulas})
    if formulas: (OUT/f'block_{i:03d}.xml').write_bytes(E.tostring(b,pretty_print=True,encoding='utf-8'))
(OUT/'extracted_blocks.json').write_text(json.dumps({'source':str(SRC),'sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'blocks':blocks},ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'extracted_text.txt').write_text('\n\n'.join(f"[{b['index']}] {b['tag']}: {b['text']}\n"+'\n'.join('MATH '+s for s in b['formulas']) for b in blocks),encoding='utf-8')
print(OUT/'extracted_text.txt')
