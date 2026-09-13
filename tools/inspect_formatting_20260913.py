from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import json, hashlib, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
root=Path.cwd(); assert root.as_posix()=='D:/Document/数学建模/2026CUMCM'
qa=root/'paper_output/qa/formatting_20260913';qa.mkdir(parents=True,exist_ok=True)
source=root/'paper_output/paper/药材热湿耦合模型与干燥时间计算_文献公式修订版.docx'
snapshot=qa/'source.docx'
if not snapshot.exists():shutil.copy2(source,snapshot)
assert source.read_bytes()==snapshot.read_bytes()
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing','a':'http://schemas.openxmlformats.org/drawingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
def tx(el):return ''.join(el.xpath('.//w:t/text()|.//m:t/text()',namespaces=ns))
with ZipFile(source) as z:
 doc=E.fromstring(z.read('word/document.xml'));body=doc.find('w:body',ns)
 blocks=[{'index':i,'type':E.QName(e).localname,'text':tx(e),'drawings':len(e.findall('.//w:drawing',ns)),'section':bool(e.findall('.//w:sectPr',ns))} for i,e in enumerate(body)]
 (qa/'source_blocks.json').write_text(json.dumps(blocks,ensure_ascii=False,indent=2),encoding='utf-8')
 (qa/'source_text.txt').write_text('\n\n'.join(f"[{b['index']}] {b['text']}" for b in blocks),encoding='utf-8')
 pictures=[]
 for i,e in enumerate(body):
  if e.findall('.//w:drawing',ns):
   pictures.append({'index':i,'context':blocks[max(0,i-2):i+3],'xml':E.tostring(e,encoding='unicode')})
 (qa/'source_figures.json').write_text(json.dumps(pictures,ensure_ascii=False,indent=2),encoding='utf-8')
 sections=[E.tostring(s,encoding='unicode') for s in doc.findall('.//w:sectPr',ns)]
 (qa/'source_sections.json').write_text(json.dumps(sections,ensure_ascii=False,indent=2),encoding='utf-8')
 footers={n:z.read(n).decode('utf-8') for n in z.namelist() if n.startswith('word/footer') and n.endswith('.xml')}
 (qa/'source_footers.json').write_text(json.dumps(footers,ensure_ascii=False,indent=2),encoding='utf-8')
 media=qa/'source_media';media.mkdir(exist_ok=True)
 for n in z.namelist():
  if n.startswith('word/media/'):(media/Path(n).name).write_bytes(z.read(n))
 print(json.dumps({'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'blocks':len(blocks),'drawings':pictures,'sections':sections,'footerNames':list(footers)},ensure_ascii=False))
