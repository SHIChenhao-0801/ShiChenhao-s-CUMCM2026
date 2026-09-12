"""Record final-v4 citation review, v2 page review, v3 page-3 recheck and identical images."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
from zipfile import ZipFile
import hashlib, json, re
from lxml import etree

ROOT=Path('paper_output/qa/revision_20260913/references').resolve()
DOC=Path('paper_output/paper/药材热湿耦合模型与干燥时间计算_文献公式修订版.docx').resolve()
RENDER=Path('tmp/cache/paper_revision_20260913/v4').resolve()
PREVIOUS_RENDER=Path('tmp/cache/paper_revision_20260913/v2').resolve()
RECHECK_RENDER=Path('tmp/cache/paper_revision_20260913/v3').resolve()
EXPECTED='c872029841c907ba0155e09b53912d46c75547df4ed3a05921645f7ab2bb1f38'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(DOC)==EXPECTED
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS={'w':W}
with ZipFile(DOC) as z:
    xml=etree.fromstring(z.read('word/document.xml'))
    image_files=[n for n in z.namelist() if n.startswith('word/media/')]
paragraphs=xml.xpath('/w:document/w:body/w:p',namespaces=NS)
texts=[''.join(p.xpath('.//w:t/text()',namespaces=NS)) for p in paragraphs]
bib_starts=xml.xpath('//w:bookmarkStart[starts-with(@w:name,"bib_")]',namespaces=NS)
bookmarks={n.get(f'{{{W}}}name'):n.get(f'{{{W}}}id') for n in bib_starts}
fields=[]
for i,p in enumerate(paragraphs):
    for f in p.xpath('.//w:fldSimple',namespaces=NS):
        code=f.get(f'{{{W}}}instr','')
        if ' REF bib_' in code:
            target=re.search(r'REF\s+(bib_\d+)',code).group(1)
            visible=''.join(f.xpath('.//w:t/text()',namespaces=NS))
            fields.append({'paragraph_index':i,'target':target,'field':code.strip(),'visible':visible,'target_exists':target in bookmarks,'display_matches':int(visible)==int(target.split('_')[1]),'paragraph':texts[i]})
assert len(bookmarks)==7 and all(x['target_exists'] and x['display_matches'] for x in fields)
assert set(x['target'] for x in fields)==set(bookmarks)
expected=json.loads((ROOT/'references_verified.json').read_text(encoding='utf-8'))
actual_bibs=[t for t in texts if re.match(r'^\[[1-7]\]\s',t)]
bib_checks=[]
for ref in expected['references']:
    actual=next(t for t in actual_bibs if t.startswith('['+str(ref['number'])+']'))
    bib_checks.append({'number':ref['number'],'actual':actual,'matches_verified':actual==ref['bibliography']})
assert all(b['matches_verified'] for b in bib_checks)
notes={
1:'实际查看整页摘要，标题、段落、关键词及页脚完整，无文字截断或叠压。',
2:'实际查看背景与四问任务；[1]、[2]可读，二阶段明确为本题工况。页末2.1起段延续至下页正常。',
3:'v2实际查看后发现“烘焙”措辞，主代理在v3改为“烘干”。已再次实际打开v3第3页核实修复、正文和材料坐标显示完整；无视觉阻断。',
4:'实际查看假设与符号表前半，列对齐、底边完整，长表跨页到第5页。',
5:'实际查看符号表续表（表头重复）、5.1.1及公式(1)，无截断或遮挡。',
6:'实际查看有效热容量及气固闭合说明，引用[3]、[4]正常；公式(2)—(5)和相应式号可读。',
7:'实际查看公式(6)、(7)与有限体积/Kirchhoff/BDF说明；[5]、[4]、[6]、[7]可读，未把离散误差写成精确求解。',
8:'实际查看结果表1与表2，列标题、7行数据、边线均完整，无表格截列。',
9:'实际查看结果解释、黄色绘图位置1、数值检验与问题二开头及公式(8)，无叠压或截断。',
10:'实际查看公式(9)、(10)、延拓假设、黄色绘图位置2与算法段落，公式及式号完整可读。'
}
pages=[{'page':n,'path':str(RENDER/f'page-{n}.png'),'sha256':sha(RENDER/f'page-{n}.png'),'actually_viewed':True,'viewed_render':'v3' if n==3 else 'v2','v2_sha256':sha(PREVIOUS_RENDER/f'page-{n}.png'),'v3_sha256':sha(RECHECK_RENDER/f'page-{n}.png'),'pixel_file_identical_to_viewed_v2':sha(RENDER/f'page-{n}.png')==sha(PREVIOUS_RENDER/f'page-{n}.png'),'pixel_file_identical_to_v3':sha(RENDER/f'page-{n}.png')==sha(RECHECK_RENDER/f'page-{n}.png'),'finding':notes[n]} for n in range(1,11)]
assert all(p['pixel_file_identical_to_viewed_v2'] for p in pages if p['page']!=3)
assert all(p['pixel_file_identical_to_v3'] for p in pages)
result={
 'checked_utc':datetime.now(timezone.utc).isoformat(),
 'document':str(DOC),'document_sha256':EXPECTED,
 'pdf':str(next(RENDER.glob('*.pdf'))),'pdf_sha256':sha(next(RENDER.glob('*.pdf'))),
 'scope':'独立核查最终v4全部正文引文与7条书目支持范围；实际逐张查看v2渲染第1—10页，v3仅第3页变化并已实际重看，其余9页PNG哈希与实际看过的v2完全相同。v4第1—10页与v3的PNG哈希均完全相同。第11—31页由其他代理负责；不代替用户人工审查。',
 'previous_document_sha256':'11bdfd7bbd23203c0921617809dc4e2ea65d0bcbfc8976d19a6d73026f93c006',
 'citation_result':'PASS','visual_result':'PASS',
 'citation_fields':fields,'citation_counts':dict(Counter(x['target'] for x in fields)),
 'bibliography_checks':bib_checks,'pages':pages,
 'support_scope_review':[
  {'citations':'[1],[2]','result':'恰当支持研究背景；二阶段是题给工况独立陈述。'},
  {'citations':'[3]','result':'仅支持平衡含水率和等温线概念；Ceq=Y∞另行明确为本文假设。'},
  {'citations':'[4]','result':'支持常系数圆柱Bessel框架及浓度积分势；本文Ei公式和温度因子分离由自身推导，未声称全PDE精确。'},
  {'citations':'[5]','result':'支持共享面通量的守恒结构，不直接声称全套非线性移动域收敛定理已满足。'},
  {'citations':'[6]','result':'支持刚性方程的BDF一般积分框架。'},
  {'citations':'[7]','result':'支持SciPy BDF及稀疏Jacobian接口；没有引用文档证明本题实际耗时或实验精度。'}
 ],
 'resolved_notes':[{'page':3,'paragraph_index':22,'previous_text':'整个烘焙过程','corrected_text':'整个烘干过程','status':'v3实际重看已修复'}],
 'nonblocking_notes':[],
 'blocking_findings':[],
 'limitations':['未修改DOCX或任何模型/数值输出。','REF超链接字段按OOXML检查且PDF编号显示正确；本子任务未在Word GUI点击引用跳转。','科学数值有效性及后续页面不属于这10页视觉通过的证明范围。'],
 'media_count':len(image_files)
}
(ROOT/'final_citation_visual_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
md='''# 文献与前十页视觉终审（最终v4）

绑定DOCX：`药材热湿耦合模型与干燥时间计算_文献公式修订版.docx`。

SHA256：`'''+EXPECTED+'''`。

结论：**正文引用及7条参考文献一致性通过；前10页视觉通过，未发现文字/公式裁切、重叠、乱码、表格缺列等视觉阻断。** 已实际逐张打开v2第1—10页；主代理修改第3页措辞后，再实际打开v3第3页，确认“整个烘焙过程”已改为“整个烘干过程”。其余9页v3的PNG文件SHA256与实际看过的v2完全相同。最终v4的第1—10页与v3的PNG文件SHA256均相同，因此可以复用上述逐页视觉记录。

正文所有文献引用都通过Word的 `REF bib_00n \\h` 字段指向真实存在的书目书签，字段缓存数字与目标序号一致，7条书目均有正文引用。书目与本轮 `references_verified.json` 中逐条核定的作者、题名、出版信息、DOI/URL一致。原[1]的作者字、期号与页码已纠正；Byrne论文DOI已正确写为 `10.1145/355626.355636`。

支持范围复核：背景[1]、[2]与题给工况分开；[3]只支持平衡含水率及等温线的一般概念，气固数值等值映射明确是本文假设；Crank[4]用于常系数圆柱Bessel框架和浓度势构造；Eymard[5]用于共享面守恒；Byrne[6]用于BDF框架，SciPy[7]用于实现与稀疏Jacobian接口。没有发现以引用替代本题参数标定或数值/实验验证的表述。

实际逐页观察记录：

'''+ '\n'.join(f'- 第{n}页：{notes[n]}' for n in range(1,11))+'''

图1、图2对应位置仍是黄色绘图提示，符合用户“暂不插图，先核查”的安排。本次只负责1—10页视觉；11—31页由主代理及公式代理另行实际查看。本结论不等同Word GUI点击跳转测试、完整模型再计算或团队人工签核。全部输入、PDF、逐页图片哈希及字段清单保存在同名JSON中。
'''
(ROOT/'final_citation_visual_review.md').write_text(md,encoding='utf-8')
print(json.dumps({'hash':EXPECTED,'bibliography_count':len(bib_checks),'citation_fields':len(fields),'actual_viewed_v2_pages':len(pages),'actual_rechecked_v3_pages':[3],'identical_other_pages':9,'blocking_findings':0,'unresolved_note_count':0},ensure_ascii=False))
