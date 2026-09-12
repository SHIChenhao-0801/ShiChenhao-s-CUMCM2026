from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from collections import Counter
import hashlib,json,shutil,sys
sys.stdout.reconfigure(encoding='utf-8')
root=Path.cwd(); assert root.as_posix()=='D:/Document/数学建模/2026CUMCM'
qa=root/'paper_output/qa/manuscript_revision_20260912';qa.mkdir(parents=True,exist_ok=True)
src=root/'paper_output/paper/A题_完整论文_保留原文_含附录.docx'
snapshot=qa/'user_edited_source.docx'
if not snapshot.exists():shutil.copy2(src,snapshot)
assert hashlib.sha256(src.read_bytes()).digest()==hashlib.sha256(snapshot.read_bytes()).digest()
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
text=lambda x:''.join(x.xpath('.//w:t/text()|.//m:t/text()',namespaces=ns))
with ZipFile(snapshot) as z:
    doc=etree.fromstring(z.read('word/document.xml'))
    body=doc.find('w:body',ns)
    boundary=next(i for i,p in enumerate(body) if text(p).strip()=='附录')
    blocks=[{'index':i,'type':etree.QName(p).localname,'text':text(p)} for i,p in enumerate(body[:boundary])]
    maths=[{'text':text(m),'xml':etree.tostring(m,encoding='unicode')} for p in body[:boundary] for m in p.findall('.//m:oMath',ns)]
    (qa/'user_body_blocks.json').write_text(json.dumps(blocks,ensure_ascii=False,indent=2),encoding='utf-8')
    (qa/'user_body_math.json').write_text(json.dumps(maths,ensure_ascii=False,indent=2),encoding='utf-8')
    (qa/'user_body_text.txt').write_text('\n\n'.join(f"[{b['index']}] {b['text']}" for b in blocks),encoding='utf-8')
    for p in list(body)[boundary:]:
        if p.tag!='{'+ns['w']+'}sectPr':body.remove(p)
    base=qa/'baseline_body.docx'
    with ZipFile(base,'w') as out:
        for info in z.infolist():
            out.writestr(info,etree.tostring(doc,xml_declaration=True,encoding='UTF-8',standalone=True) if info.filename=='word/document.xml' else z.read(info.filename))
    fonts=Counter(doc.xpath('//w:rFonts/@w:ascii',namespaces=ns))
    print(json.dumps({'sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),'bodyBlocks':len(blocks),'bodyMath':len(maths),'fonts':dict(fonts),'mathSamples':maths[:2]},ensure_ascii=False))
(qa/'artifact.md').write_text('''# 本轮编辑契约

正文权威为用户修改后的452310字节DOCX快照，原稿继续保留；新交付另存文件。IEEE模板及厦大规范只参考数学符号、字体、下标和公式编号，不替换数模的A4单栏和正文页数口径。

本轮明确授权公式/符号排版、代码附录精简、标明绘图说明。附录采用核心推导、数值过程和必要算法片段，原生产源码及既有全量代码版保留。该明确用户要求覆盖旧附录全量源码的排版安排。原正文内容仅作必要排版、绘图标记、可核实笔误处理及批注维护；不重新改写正文、不恢复用户删除的文献、不重算模型。

输出：A题_论文_公式规范与精简附录版.docx。保留公式可编辑性；变量采用Times New Roman斜体，数值/单位/函数/说明性下标正体；可伸缩运算符须保持可读。6个绘图位置正文醒目标识，并单独提供定位清单。真实渲染全部页检查后交付，最后Computer Use播放Apple Music。
''',encoding='utf-8')
