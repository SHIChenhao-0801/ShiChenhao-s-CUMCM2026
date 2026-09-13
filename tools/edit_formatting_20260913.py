from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from copy import deepcopy
import hashlib,json,sys,re,difflib
sys.stdout.reconfigure(encoding='utf-8')
root=Path.cwd();assert root.as_posix()=='D:/Document/数学建模/2026CUMCM'
qa=root/'paper_output/qa/formatting_20260913'
source=qa/'source.docx'
output=root/'paper_output/paper/药材热湿耦合模型与干燥时间计算_格式与语言修订版.docx'
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing','pic':'http://schemas.openxmlformats.org/drawingml/2006/picture','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
W=ns['w'];qn=lambda n:'{'+W+'}'+n
def tx(el):return ''.join(el.xpath('.//w:t/text()|.//m:t/text()',namespaces=ns))
def xml(el):return E.tostring(el,xml_declaration=True,encoding='UTF-8',standalone=True)
def setchild(parent,name,attrs):
 e=parent.find(qn(name))
 if e is None:e=E.SubElement(parent,qn(name))
 for k,v in attrs.items():e.set(qn(k),str(v))
 return e
def ppr(p):
 e=p.find(qn('pPr'))
 if e is None:e=E.Element(qn('pPr'));p.insert(0,e)
 return e
changes=[]
def replace(p,old,new,block):
 nodes=p.xpath('.//w:t|.//m:t',namespaces=ns)
 text=''.join(n.text or '' for n in nodes)
 assert text.count(old)==1,(block,old,text)
 base=text.index(old)
 for tag,i,j,a,b in reversed(difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes()):
  if tag=='equal':continue
  start=base+i;end=base+j;offset=0;written=False
  for node in nodes:
   value=node.text or '';left=offset;right=left+len(value);offset=right
   if start==end:
    if not written and left<=start<=right:
     assert node.tag==qn('t'),(block,'math insertion')
     node.text=value[:start-left]+new[a:b]+value[start-left:];written=True
    continue
   if right<=start or left>=end:continue
   assert node.tag==qn('t'),(block,'math mutation',old,new)
   prefix=value[:max(0,start-left)];suffix=value[max(0,end-left):] if end<right else ''
   node.text=prefix+(new[a:b] if left<=start<right else '')+suffix
   node.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
 assert tx(p)==text.replace(old,new,1),(block,'replacement mismatch')
 changes.append({'block':block,'old':old,'new':new})
def plain(p,text,template=None):
 if template is not None:
  pr=p.find(qn('pPr'))
  if pr is not None:p.remove(pr)
  p.insert(0,deepcopy(template))
 for e in list(p):
  if e.tag!=qn('pPr'):p.remove(e)
 r=E.SubElement(p,qn('r'));rp=E.SubElement(r,qn('rPr'))
 setchild(rp,'rFonts',{'ascii':'Times New Roman','hAnsi':'Times New Roman','eastAsia':'宋体','cs':'Times New Roman'})
 setchild(rp,'sz',{'val':'24'});setchild(rp,'color',{'val':'000000'})
 E.SubElement(r,qn('t')).text=text
titles=[
 '问题一不同时刻的径向温度与干基含水率分布',
 '烘房温度与空气水分指标的观测插值及平台延拓',
 '问题二中心与表面的温度及干基含水率变化',
 '问题三全域含水率达标过程及临界时刻局部放大',
 '问题四半径收缩过程与域内干基含水率分布',
 '经验边界阻力参数对临界烘干时长的影响（N=800）',
]
with ZipFile(source) as z:
 payload={n:z.read(n) for n in z.namelist()}
 doc=E.fromstring(payload['word/document.xml']);original=deepcopy(doc);body=doc.find('w:body',ns);blocks=list(body)
 recommendations=json.loads((qa/'language_recommendations.json').read_text(encoding='utf-8'))
 entries=recommendations if isinstance(recommendations,list) else recommendations['replacements']
 for entry in entries:
  if entry.get('apply',True):replace(blocks[entry['block_index']],entry['old'],entry['new'],entry['block_index'])
 replace(blocks[16],'计算出药材内部水分浓度每隔60s、到药材中心距离每隔0.1cm的药材水分浓度以及烘干结束时间','以60 s为时间间隔、0.1 cm为径向距离间隔输出水分浓度，并确定烘干结束时间',16)
 for index in (83,101):setchild(ppr(blocks[index]),'widowControl',{'val':'1'})
 # Match the final symbol description cell to the existing table typography.
 rows=blocks[35].findall(qn('tr'));description=rows[-1].findall(qn('tc'))[1]
 assert tx(description)=='全域含水率阈值的临界时刻'
 donor=rows[-2].findall(qn('tc'))[1].find(qn('p'))
 target=description.find(qn('p'));targetpr=ppr(target);target.remove(targetpr);target.insert(0,deepcopy(ppr(donor)))
 setchild(ppr(target),'jc',{'val':'center'});setchild(ppr(target),'ind',{'firstLine':'0','left':'0','right':'0'})
 for attr in ('firstLineChars','leftChars','rightChars','hanging','hangingChars'):ppr(target).find(qn('ind')).attrib.pop(qn(attr),None)
 donor_rpr=donor.find('.//'+qn('rPr'))
 for run in target.findall(qn('r')):
  oldrp=run.find(qn('rPr'))
  if oldrp is not None:run.remove(oldrp)
  if donor_rpr is not None:run.insert(0,deepcopy(donor_rpr))
 for index in (76,94):
  assert tx(blocks[index]) in ('图1：','图2：');body.remove(blocks[index])
 descriptions={
  93:'图2展示烘房温度与空气水分指标在0—4 h内的观测及分段线性插值，并区分4 h之后的假设平台延拓；平台值分别为50°C和0.05 kg/kg。',
  110:'图3分别展示中心与表面在前4 h内的温度响应及从初始状态至达标时刻的干基含水率变化，以不同时间尺度呈现传热与脱水过程。',
 }
 for index,text in descriptions.items():
  old=tx(blocks[index]);plain(blocks[index],text,ppr(blocks[108]));changes.append({'block':index,'old':old,'new':text})
 for number,index in enumerate((77,95,111,139,172,180),1):
  picture=blocks[index];pr=ppr(picture)
  setchild(pr,'jc',{'val':'center'});ind=setchild(pr,'ind',{'firstLine':'0','left':'0','right':'0'})
  for key in ('firstLineChars','leftChars','rightChars','hanging','hangingChars'):ind.attrib.pop(qn(key),None)
  setchild(pr,'keepNext',{'val':'1'});setchild(pr,'keepLines',{'val':'1'})
  setchild(pr,'spacing',{'before':'100','after':'0','line':'240','lineRule':'auto'})
  for high in picture.findall('.//w:highlight',ns):high.getparent().remove(high)
  for dp in picture.xpath('.//wp:docPr|.//pic:cNvPr',namespaces=ns):
   dp.set('title',f'图{number} {titles[number-1]}');dp.set('descr',titles[number-1])
  caption=E.Element(qn('p'));cp=E.SubElement(caption,qn('pPr'))
  setchild(cp,'jc',{'val':'center'});setchild(cp,'ind',{'firstLine':'0','left':'0','right':'0'})
  setchild(cp,'keepNext',{'val':'0'});setchild(cp,'keepLines',{'val':'1'})
  setchild(cp,'spacing',{'before':'60','after':'140','line':'240','lineRule':'auto'})
  plain(caption,f'图{number}  {titles[number-1]}')
  picture.addnext(caption)
 for highlight in doc.findall('.//w:highlight',ns):highlight.getparent().remove(highlight)
 # Explicit automatic numbering; the source already starts on the abstract page.
 sects=doc.findall('.//w:sectPr',ns)
 assert len(sects)==1
 sect=sects[0]
 number_format=E.Element(qn('pgNumType'));number_format.set(qn('fmt'),'decimal');number_format.set(qn('start'),'1')
 cols=sect.find(qn('cols'));sect.insert(list(sect).index(cols) if cols is not None else len(sect),number_format)
 mode=sys.argv[1] if len(sys.argv)>1 else 'continuous'
 if mode=='no_appendix':
  before=deepcopy(sect);setchild(before,'type',{'val':'nextPage'})
  boundary=E.Element(qn('p'));bp=E.SubElement(boundary,qn('pPr'));bp.append(before)
  blocks[217].addprevious(boundary)
  pagebreak=ppr(blocks[217]).find(qn('pageBreakBefore'))
  if pagebreak is not None:pagebreak.getparent().remove(pagebreak)
  relns='http://schemas.openxmlformats.org/package/2006/relationships'
  rel=E.fromstring(payload['word/_rels/document.xml.rels']);newid='rIdFormattingEmptyFooter'
  E.SubElement(rel,'{'+relns+'}Relationship',Id=newid,Type=ns['r']+'/footer',Target='footerFormattingEmpty.xml')
  for ref in sect.findall(qn('footerReference')):sect.remove(ref)
  ref=E.Element(qn('footerReference'));ref.set(qn('type'),'default');ref.set('{'+ns['r']+'}id',newid);sect.insert(0,ref)
  empty=E.Element(qn('ftr'),nsmap={'w':W});E.SubElement(empty,qn('p'))
  payload['word/footerFormattingEmpty.xml']=xml(empty);payload['word/_rels/document.xml.rels']=xml(rel)
  ct=E.fromstring(payload['[Content_Types].xml']);E.SubElement(ct,'{'+ct.nsmap[None]+'}Override',PartName='/word/footerFormattingEmpty.xml',ContentType='application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml');payload['[Content_Types].xml']=xml(ct)
 footer=E.fromstring(payload['word/footer1.xml'])
 for p in footer.findall('.//w:p',ns):setchild(ppr(p),'jc',{'val':'center'})
 # Materialize a visible initial cache while keeping the real PAGE field live.
 sep=next(n for n in footer.findall('.//w:fldChar',ns) if n.get(qn('fldCharType'))=='separate')
 cache=E.Element(qn('r'));E.SubElement(cache,qn('t')).text='1';sep.getparent().addnext(cache)
 payload['word/footer1.xml']=xml(footer);payload['word/document.xml']=xml(doc)
 # Prove the local prose/format edits did not alter equations, tables, code or media.
 beforemath=[E.tostring(x,method='c14n') for x in original.findall('.//m:oMath',ns)]
 aftermath=[E.tostring(x,method='c14n') for x in doc.findall('.//m:oMath',ns)]
 assert beforemath==aftermath
 assert [tx(x) for x in original.findall('.//w:tbl',ns)]==[tx(x) for x in doc.findall('.//w:tbl',ns)]
 assert [E.tostring(x,method='c14n') for x in original.findall('.//w:tbl',ns)[1:]]==[E.tostring(x,method='c14n') for x in doc.findall('.//w:tbl',ns)[1:]]
 assert [E.tostring(x,method='c14n') for x in list(original.find('w:body',ns))[286:-1]]==[E.tostring(x,method='c14n') for x in blocks[286:-1]]
 instructions=lambda d:d.xpath('//w:instrText/text()|//w:fldSimple/@w:instr',namespaces=ns)
 assert instructions(doc)==instructions(original)
 assert not re.search(r'【绘图位置|我们|你们|笔者',tx(doc))
 with ZipFile(output,'w') as out:
  for info in z.infolist():out.writestr(info,payload.pop(info.filename))
  for name,data in payload.items():out.writestr(name,data)
 audit={'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'outputSha256':hashlib.sha256(output.read_bytes()).hexdigest(),'pageNumberMode':mode,'captions':titles,'languageEdits':changes,'layoutEdits':['symbol tc description cell typography','widow control at source blocks 83,101','remove drawing instruction highlights, including empty paragraph'],'unchanged':{'math':len(beforemath),'allTableCellContents':len(doc.findall('.//w:tbl',ns)),'eightResultTablesXml':True,'codeAppendixXml':True,'fieldInstructions':True,'imageFiles':True},'output':str(output)}
 (qa/'build_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(audit,ensure_ascii=False))
