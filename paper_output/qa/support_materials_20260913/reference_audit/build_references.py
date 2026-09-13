"""Build a traceable, portable reference archive without changing source evidence."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET
import json, hashlib, shutil, csv, re, html
import pymupdf
from html.parser import HTMLParser

class ReadableHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output=[]
        self.skip=[]
    def handle_starttag(self,tag,attrs):
        if tag in {'script','style','nav','header','footer','form','iframe'}:
            self.skip.append(tag)
        if self.skip: return
        if tag in {'p','h1','h2','h3','h4','h5','h6','ul','ol','li','table','tr','th','td','pre','code','blockquote','br','em','strong','sub','sup','a','div','span'}:
            attrs=''.join(' '+k+'="'+html.escape(v or '',quote=True)+'"' for k,v in attrs if tag=='a' and k=='href')
            self.output.append('<'+tag+attrs+'>')
    def handle_endtag(self,tag):
        if self.skip:
            if tag==self.skip[-1]:self.skip.pop()
            return
        if tag in {'p','h1','h2','h3','h4','h5','h6','ul','ol','li','table','tr','th','td','pre','code','blockquote','em','strong','sub','sup','a','div','span'}:self.output.append('</'+tag+'>')
    def handle_data(self,data):
        if not self.skip:self.output.append(html.escape(data))

ROOT = Path.cwd().resolve()
assert ROOT.name == '2026CUMCM'
OUT = ROOT/'支撑材料/02_参考文献与网络资料'
AUDIT = ROOT/'paper_output/qa/support_materials_20260913/reference_audit'
OLD = ROOT/'paper_output/qa/revision_20260913/references'
RAW = AUDIT/'raw_downloads'
NOW = datetime.now(timezone(timedelta(hours=8))).isoformat()
OUT.mkdir(parents=True, exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
refs=json.loads((OLD/'references_verified.json').read_text(encoding='utf-8'))['references']
current=ROOT/'paper_output/paper/药材热湿耦合模型与干燥时间计算_文献公式修订版.docx'
with ZipFile(current) as z: xml=ET.fromstring(z.read('word/document.xml'))
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
paras=[''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in xml.findall('.//w:p',ns)]
current_bib=[p for p in paras if re.match(r'^\[[1-7]\] ',p)]
assert len(current_bib)==7
assert current_bib==[r['bibliography'] for r in refs]
manifest=[]
old_retrieval=json.loads((OLD/'retrieval_evidence.json').read_text(encoding='utf-8'))
old_lookup={r['name']:r for r in old_retrieval}
new_lookup={r['file']:r for r in json.loads((AUDIT/'retrieval_evidence.json').read_text(encoding='utf-8'))}

def record(src, dest, key, url, status, scope, retrieved=None, original_sha=None, derivative=False):
    target=OUT/dest
    target.parent.mkdir(parents=True,exist_ok=True)
    if src is not None:
        shutil.copyfile(src,target)
    supplement_titles={'fao_drying':'Grain storage techniques - Drying principles and general considerations','scipy_solve_ivp':'scipy.integrate.solve_ivp','shampine1997':'The MATLAB ODE Suite'}
    manifest.append({'reference_key':key,'file':dest,'title':next((r['title'] for r in refs if r['key']==key),supplement_titles.get(key,key)),
        'url':url,'retrieved_at':retrieved or NOW,'archived_at_beijing':NOW,'material_status':status,'supports':scope,
        'bytes':target.stat().st_size,'sha256':sha(target),'original_sha256':original_sha or (None if derivative else sha(target)),
        'is_derivative':derivative})
    return target

def downloaded(name,dest,key,status,scope):
    r=new_lookup[name]
    assert r['accepted']
    return record(RAW/name,dest,key,r['url'],status,scope,r['retrieved_utc'])

def cached(name,dest,key,status,scope,url=None):
    r=old_lookup.get(name,{})
    return record(OLD/'source_cache'/name,dest,key,url or r.get('url',''),status,scope,r.get('retrieved_utc','2026-09-12 (exact download time not recorded in existing evidence)'))

downloaded('wang2024_full.pdf','01_王乐意2024/刊方全文_28页.pdf','wang2024','刊方完整PDF，28页；仅核读所需背景范围','摘要、引言及干燥过程；支持干燥影响脱水速率与品质的一般背景')
downloaded('wang2024_publisher.html','01_王乐意2024/刊方书目与摘要_原始网页.html','wang2024','刊方书目及摘要原始HTML','标题、作者、卷期页码、DOI及背景摘要')
downloaded('wang2023_pubmed.xml','02_王晓辉2023/PubMed_书目与英文摘要_原始XML.xml','wang2023','PubMed官方书目与摘要XML；不是论文全文','题名、8位作者、48(13):3440-3447、DOI；数值模拟的一般背景')
cached('mujumdar_2014.crossref.json','03_Mujumdar2014/Crossref_原始书目.json','mujumdar2014','注册元数据','发行年2014、书名、出版社、DOI')

# Preserve actual page objects; omit unrelated preview pages. Render equality is audited.
source=OLD/'source_cache/mujumdar_preview.pdf'
dest=OUT/'03_Mujumdar2014/公开预览节选_题名版权与正文13至15页.pdf'
srcdoc=pymupdf.open(source)
indices=[3,4,43,44,45]
excerpt=pymupdf.open()
for i in indices: excerpt.insert_pdf(srcdoc,from_page=i,to_page=i)
excerpt.set_metadata({'title':'Handbook of Industrial Drying, 4th edition - public preview excerpt', 'subject':'Original preview PDF pages 4, 5, 44, 45, 46; printed text pages 13-15. Not the complete book.'})
excerpt.save(dest,garbage=4,deflate=True)
excerpt.close()
record(None,str(dest.relative_to(OUT)).replace('\\','/'),'mujumdar2014',old_lookup['mujumdar_preview.pdf']['url'],'公开预览的5页无损节选；不是全书','题名版权页与正文13-15页：平衡含水率、等温线及温度影响',old_lookup['mujumdar_preview.pdf']['retrieved_utc'],sha(source),True)
render_dir=AUDIT/'preview_validation'
render_dir.mkdir(exist_ok=True)
ex=pymupdf.open(dest)
page_checks=[]
for j,i in enumerate(indices):
    a=srcdoc[i].get_pixmap(matrix=pymupdf.Matrix(1.0,1.0),alpha=False)
    b=ex[j].get_pixmap(matrix=pymupdf.Matrix(1.0,1.0),alpha=False)
    a_hash=hashlib.sha256(a.samples).hexdigest()
    b_hash=hashlib.sha256(b.samples).hexdigest()
    assert a_hash==b_hash
    b.save(render_dir/f'excerpt_page_{j+1}.png')
    page_checks.append({'excerpt_page':j+1,'source_pdf_page':i+1,'pixel_sha256':b_hash,'pixel_identical':True})

catalog=OUT/'04_Crank1975/官方馆藏书目核验.md'
catalog.parent.mkdir(exist_ok=True)
catalog.write_text('''# Crank 第二版官方馆藏书目核验

本文件是官方页面书目信息的人工整理摘录，不是原网页HTML或原书全文。

- 官方来源：[日本国立国会图书馆](https://ndlsearch.ndl.go.jp/books/R100000074-IALIS_QQ00223544)
- 本次网页核验：'''+NOW+'''
- 标题：The mathematics of diffusion / by J. Crank.
- 作者：Crank, John
- 版本：2d ed.
- 出版地与出版社：Oxford, [Eng] : Clarendon Press
- 出版年：1975
- 页数：viii, 414 p.
- ISBN-10：0198533446；对应ISBN-13：9780198533443
- NDL书目ID：000006163481；馆藏号：PA41-31

本次原始HTML直接下载超时；网页检索工具实际打开上述官方页面并核实以上字段。未取得原版整书PDF。既有核查对原书OCR转录中正文2-5、79-80、107页作了范围核读，用于Fick扩散、圆柱Robin边界Bessel解、浓度势变换；转录没有作为出版社原件收入本包。

可定位的原书旧链接：https://staff.bath.ac.uk/ensdasr/PAPERS/Crank-The-Mathematics-of-Diffusion.pdf 。既有核查记录该链接重定向首页，不能视作已下载文件。书目核验本身不能替代上述数学内容的原书逐式核对。
''',encoding='utf-8')
record(None,'04_Crank1975/官方馆藏书目核验.md','crank1975',refs[3]['primary_urls'][0],'官方书目摘录；未取得原始HTML或整书PDF','第二版、出版社、年份、ISBN及馆藏记录；不等于原书全文',derivative=True)
cached('eymard_author.pdf','05_Eymard2000/作者完整更新稿_2019_254页.pdf','eymard2000','作者2019完整更新稿254页；不是2000刊方排印版','实际核读PDF第1、7、23页：控制体守恒、共用面通量及调和平均')
cached('eymard_2000.crossref.json','05_Eymard2000/Crossref_原始书目.json','eymard2000','出版社注册元数据','2000年书章，713-1018页与正确DOI')
cached('byrne_1975.crossref.json','06_Byrne1975/Crossref_原始书目.json','byrne1975','ACM注册元数据；论文全文未取得','作者、标题、1975、1(1):71-96及正确DOI',url='https://api.crossref.org/works/10.1145/355626.355636')
downloaded('sundials_references.html','06_Byrne1975/SUNDIALS_官方书目交叉核对.html','byrne1975','SUNDIALS v7.1.0官方书目网页','该论文书目交叉核对；不是论文全文')
downloaded('scipy_bdf.html','07_SciPy_BDF/BDF_官方完整API网页.html','scipy_bdf','SciPy官方API完整网页','隐式BDF、1-5阶、稀疏Jacobian接口及dense_output；网页版本1.18.0不代替本地安装证据')
downloaded('fao_drying.html','08_实际使用的补充网络资料/FAO_干燥原理_官方网页.html','fao_drying','FAO官方章节网页；最终正文未单独引用','平衡含水率与材料、温湿度有关；粮食对象的数值不可直接移植为本题药材参数')
downloaded('scipy_solve_ivp.html','08_实际使用的补充网络资料/SciPy_solve_ivp_官方API网页.html','scipy_solve_ivp','SciPy官方API完整网页；最终正文未单独引用','BDF刚性积分、事件与Jacobian接口核查；不替代本题运行证据')
cached('shampine_1997.crossref.json','08_实际使用的补充网络资料/Shampine1997_Crossref书目.json','shampine1997','核查过的补充书目；最终正文未独立引用','SciPy准定步长/NDF文献来源追查；曾取得扫描但未全文OCR或通读')
cached('shampine_byu.pdf','08_实际使用的补充网络资料/Shampine1997_BYU原始扫描_35页.pdf','shampine1997','已取得35页原始扫描；不是正式刊物1-22页排印版，未全文已读','SciPy准定步长/NDF文献来源追查；本次目视抽查题名摘要首面与最后书目页，未全文OCR或通读')

# A small self-contained readable view is included for each HTML source.
for item in list(manifest):
    if not item['file'].endswith('.html'): continue
    p=OUT/item['file']
    raw_html=p.read_text(encoding='utf-8',errors='replace')
    body=re.search(r'<body\b[^>]*>(.*)</body>',raw_html,re.I|re.S)
    parser=ReadableHTML()
    parser.feed(body.group(1) if body else raw_html)
    content=''.join(parser.output)
    readable=p.with_name(p.stem+'_离线文本.html')
    readable.write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>'+html.escape(item['title'])+'</title><style>body{max-width:980px;margin:40px auto;padding:0 20px;font:16px/1.65 sans-serif;color:#18212b}pre{white-space:pre-wrap}table{border-collapse:collapse}td,th{border:1px solid #bbb;padding:6px}a{overflow-wrap:anywhere}</style><body><p>离线文本整理版，移除脚本、导航和图片；原始HTML另存。来源：<a href="'+html.escape(item['url'])+'">'+html.escape(item['url'])+'</a></p>'+str(content)+'</body></html>',encoding='utf-8')
    record(None,str(readable.relative_to(OUT)).replace('\\','/'),item['reference_key'],item['url'],'原网页离线文本整理版；不是原始HTML',item['supports'],item['retrieved_at'],item['original_sha256'],True)

# Record title-level material, reading, and inference limits without internal chat content.
statuses={
 'wang2024':('刊方完整PDF已取得，28页','摘要、引言及正文第1节按所需范围核读；未声称逐页通读'),
 'wang2023':('官方书目和英文摘要已取得；全文未取得','刊方首面检索与PubMed书目/摘要已核；本次刊方PDF返回0字节'),
 'mujumdar2014':('公开预览实际使用页节选已归档；全书未取得','题名版权页与正文13-15页；原134页公开预览保留于工作区'),
 'crank1975':('官方书目已核；整书PDF未取得','既有核查读原书OCR转录2-5、79-80、107页；当前包不含该转录原件'),
 'eymard2000':('作者2019完整更新稿已取得；2000刊方排印版未取得','作者稿PDF第1、7、23页按所需范围核读；未声称254页通读'),
 'byrne1975':('原始书目及官方软件文档交叉核对已取得；全文未取得','ACM Crossref书目、SUNDIALS书目和SciPy方法文档；不声称论文全文已读'),
 'scipy_bdf':('官方完整API网页已取得','BDF说明、参数、Jacobian、dense_output及参考文献已读')}
reference_records=[]
for r in refs:
    state,read=statuses[r['key']]
    record_r={k:r[k] for k in ['key','number','title','bibliography','primary_urls','supports','does_not_support']}
    record_r.update(material_status=state,read_scope=read,doi=r.get('doi'),files=[x['file'] for x in manifest if x['reference_key']==r['key']])
    reference_records.append(record_r)
    note=OUT/f'{r["number"]:02d}_{["王乐意2024","王晓辉2023","Mujumdar2014","Crank1975","Eymard2000","Byrne1975","SciPy_BDF"][r["number"]-1]}'/'资料说明.md'
    links='\n'.join('- ['+u+']('+u+')' for u in r['primary_urls'])
    note.write_text('# '+r['title']+'\n\n'+r['bibliography']+'\n\n**取得状态：** '+state+'。\n\n**实际已读范围：** '+read+'。\n\n**用于论文：** '+'；'.join(r['supports'])+'。\n\n**支持边界：** '+ '；'.join(r['does_not_support'])+'，均不能由本条文献直接推出。\n\n来源链接：\n\n'+links+'\n\n文件级下载时间、来源和SHA256见根目录“来源清单.csv”。\n',encoding='utf-8')

bibtex='''% UTF-8. Same seven references as the current manuscript. No invented DOI for Crank.
@article{wang2024,
  author = {{王乐意} and {李长河} and {刘明政} and others},
  title = {中药材干燥技术与装备研究现状},
  journal = {农业工程学报}, year = {2024}, volume = {40}, number = {2}, pages = {1--28},
  doi = {10.11975/j.issn.1002-6819.202306104}
}
@article{wang2023,
  author = {{王晓辉} and {王学成} and {唐培渝} and {伍志成} and {伍振峰} and {王雅琪} and {刘振峰} and {杨明}},
  title = {数值模拟仿真研究现状及其在中药干燥领域应用展望},
  journal = {中国中药杂志}, year = {2023}, volume = {48}, number = {13}, pages = {3440--3447},
  doi = {10.19540/j.cnki.cjcmm.20230331.301}
}
@book{mujumdar2014,
  editor = {Mujumdar, Arun S.}, title = {Handbook of Industrial Drying}, edition = {4},
  address = {Boca Raton}, publisher = {CRC Press}, year = {2014}, doi = {10.1201/b17208}, isbn = {9781466596658}
}
@book{crank1975,
  author = {Crank, John}, title = {The Mathematics of Diffusion}, edition = {2},
  address = {Oxford}, publisher = {Clarendon Press}, year = {1975}, isbn = {9780198533443}
}
@incollection{eymard2000,
  author = {Eymard, Robert and Gallouët, Thierry and Herbin, Raphaèle},
  title = {Finite Volume Methods}, editor = {Ciarlet, P. G. and Lions, J. L.},
  booktitle = {Handbook of Numerical Analysis}, volume = {7}, pages = {713--1018},
  address = {Amsterdam}, publisher = {North-Holland}, year = {2000}, doi = {10.1016/S1570-8659(00)07005-8}
}
@article{byrne1975,
  author = {Byrne, G. D. and Hindmarsh, A. C.}, title = {A Polyalgorithm for the Numerical Solution of Ordinary Differential Equations},
  journal = {ACM Transactions on Mathematical Software}, year = {1975}, volume = {1}, number = {1}, pages = {71--96},
  doi = {10.1145/355626.355636}
}
@misc{scipy_bdf,
  author = {{The SciPy community}}, title = {scipy.integrate.BDF},
  url = {https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.BDF.html},
  urldate = {2026-09-12}, note = {Manuscript access date; local public page snapshot additionally archived on 2026-09-13, Beijing time.}
}
'''
(OUT/'正文七条参考文献.bib').write_text(bibtex,encoding='utf-8')
(OUT/'正文七条参考文献.txt').write_text('\n\n'.join(current_bib)+'\n',encoding='utf-8-sig')
(OUT/'正文文献核实与用途.json').write_text(json.dumps({'compiled_at_beijing':NOW,'manuscript_filename':current.name,'manuscript_sha256':sha(current),'reference_count':7,'references':reference_records},ensure_ascii=False,indent=2),encoding='utf-8')
fields=['reference_key','title','url','retrieved_at','archived_at_beijing','file','material_status','supports','bytes','sha256','original_sha256','is_derivative']
with (OUT/'来源清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(manifest)
(OUT/'来源清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
supp=OUT/'08_实际使用的补充网络资料/补充资料说明.md'
supp.write_text('''# 实际使用但未在最终正文单列的资料

这些资料仅记录真实检索/方法核查过程，不增加正文引用编号。

1. FAO 的 Grain storage techniques 中 Drying principles and general considerations 章节：既有稿件用来核查材料平衡含水率、环境湿度和温度关系。本包保存官方网页及离线文本。对象是粮食；没有直接移植其经验参数到本题药材。
2. SciPy solve_ivp 官方文档：实现阶段与既有文稿核查过 BDF、Jacobian、事件等接口。本包保存官方完整API网页及离线文本。网页展示版本不能取代计算环境运行记录。
3. Shampine L F, Reichelt M W. The MATLAB ODE Suite. SIAM Journal on Scientific Computing, 1997, 18(1):1-22. DOI: https://doi.org/10.1137/S1064827594276424 。该文在SciPy方法文档中作为准定步长/NDF出处，曾核对书目并取得BYU扫描文件；本次目视抽查题名摘要首面与最后书目页，没有全文OCR或逐页通读。最终正文未对NDF另设独立论述，本包保存原始书目、公开链接与35页扫描原件，扫描文件不计入正文全文覆盖数量。

Shampine扫描公开链接：https://www.et.byu.edu/~beard/papers/library/MatlabOdeSuite.pdf 。扫描文件为35页、1,974,378字节，SHA256为 '''+sha(OLD/'source_cache/shampine_byu.pdf')+'''。保持下载原件不重排，不将扫描页数35与正式刊物页码1-22混同。
''',encoding='utf-8')
readme=['# 参考文献与网络资料索引','',
'本目录对应当前《'+current.name+'》中的7条参考文献。整理时间（北京时间）：'+NOW+'。当前文稿SHA256：`'+sha(current)+'`。', '',
'正文书目逐条从当前实际文件抽取并与既有核实表比对一致。仅归档来源与用途，本轮未修改论文或重算模型。','',
'| 正文编号 | 资料 | 已归档状态 |', '|---|---|---|']
for r in reference_records:
    readme.append(f'| [{r["number"]}] | {r["title"]} | {r["material_status"]} |')
readme += ['',
'建议先看各编号目录的“资料说明.md”，再打开PDF或标有“离线文本”的HTML。原始HTML可能引用网络样式或图片；离线文本删除脚本、导航与图片，方便离线阅读文字，原件同时保留。', '',
'**完整覆盖与缺口。** 已收入王2024刊方完整论文和Eymard作者完整更新稿、SciPy完整API文档。Mujumdar为公开预览的题名/版权/正文13–15页节选，并非全书。王2023、Crank、Byrne未取得原版全文，分别以官方书目/摘要或元数据及范围说明归档；不得把这三项计为全文已读。Eymard作者2019更新稿也不冒充2000刊方排印版。', '',
'**版本差异。** Mujumdar版权页标2015，出版社发行与Crossref年为2014，正文沿用已核实的2014发行年。Eymard作者稿封面书目可能写713–1020，当前出版社注册页码是713–1018，正文与BibTeX采用后者。SciPy归档页面显示1.18.0，实际计算依赖版本须查代码运行证据。', '',
'**使用边界。** 文献支持背景和方法的一般出处；不替代题目参数、Ceq=Y∞闭合假设、生产代码正确性、真实干燥精度或实验验证。本目录不包含参赛人员身份、聊天记录或校内规则材料。文献作者和其公开单位属书目原件内容，不是参赛身份。', '',
'**文件索引。** “正文七条参考文献.txt”和“.bib”可用于论文维护；“正文文献核实与用途.json”逐条列出支持范围、限制与文件；“来源清单.csv/json”含URL、取得时间、材料类型、文件哈希及原件哈希；“文件SHA256清单.csv”覆盖本目录其他全部文件。附加网络资料单列于08目录，不与正文编号混排。', '',
'公开预览节选的来源页映射：节选第1–5页分别为原公开预览PDF第4、5、44、45、46页，其中后3页为原书正文13、14、15页。逐页重新渲染与源页像素SHA256一致，图文未改写或降质。', '']
(OUT/'README_文献与网络资料索引.md').write_text('\n'.join(readme),encoding='utf-8')
all_files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='文件SHA256清单.csv')
with (OUT/'文件SHA256清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['文件','字节数','SHA256'])
    for p in all_files:w.writerow([p.relative_to(OUT).as_posix(),p.stat().st_size,sha(p)])
pdf_checks=[]
for p in OUT.rglob('*.pdf'):
    doc=pymupdf.open(p)
    pdf_checks.append({'file':p.relative_to(OUT).as_posix(),'pages':len(doc),'bytes':p.stat().st_size,'sha256':sha(p),'first_page_text':doc[0].get_text()[:150]})
zip_path=AUDIT/'reference_compression_check.zip'
with ZipFile(zip_path,'w',ZIP_DEFLATED,compresslevel=9) as z:
    for p in OUT.rglob('*'):
        if p.is_file():z.write(p,p.relative_to(OUT).as_posix())
report={'manuscript_sha256':sha(current),'references_match_current_manuscript':True,'reference_count':7,'source_item_count':len(manifest),
 'file_count':len(list(OUT.rglob('*')))-len([p for p in OUT.rglob('*') if p.is_dir()]),
 'bytes':sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),'zip_bytes':zip_path.stat().st_size,
 'pdf_checks':pdf_checks,'excerpt_pixel_checks':page_checks,'full_original_unavailable':['wang2023','crank1975','byrne1975'],
 'preview_only':['mujumdar2014'],'author_revision_instead_of_publisher_typeset':['eymard2000'],
 'visual_review':'PASS: all 5 created excerpt pages actually inspected; original PDF spot checks only',
 'original_pdf_visual_spot_checks':{'wang2024':[1,28],'eymard2019_author':[1,7,23],'shampine_scan':[1,35]},
 'source_originals_modified':False}
(AUDIT/'reference_package_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
