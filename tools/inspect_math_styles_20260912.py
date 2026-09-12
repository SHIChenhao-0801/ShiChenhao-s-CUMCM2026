from zipfile import ZipFile
from lxml import etree as E
import sys
sys.stdout.reconfigure(encoding='utf-8')
z=ZipFile('paper_output/paper/A题_论文_公式规范与精简附录版.docx')
d=E.fromstring(z.read('word/document.xml'))
ns={'m':'http://schemas.openxmlformats.org/officeDocument/2006/math','w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
for query in ['//m:sub[.//m:t="eff"]','//m:sub[.//m:t="f"]','//m:r[./m:t="exp"]','//m:r[./m:t="K"]']:
    matches=d.xpath(query,namespaces=ns)
    print(query,len(matches))
    if matches:
        r=E.fromstring(E.tostring(matches[-1]));E.cleanup_namespaces(r)
        print(E.tostring(r,encoding='unicode'))
