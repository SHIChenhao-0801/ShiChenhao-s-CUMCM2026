from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import json,re,hashlib,ast

ROOT=Path.cwd(); OUT=ROOT/'paper_output/qa/revision_20260913/formulas'; QA=OUT.parent
SOURCE=QA/'user_source.docx'; FINAL=ROOT/'paper_output/paper/药材热湿耦合模型与干燥时间计算_文献公式修订版.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
def root(path):
    with ZipFile(path) as z:return E.fromstring(z.read('word/document.xml'))
def text(node):return ''.join(node.xpath('.//w:t/text()|.//m:t/text()',namespaces=NS))
def plain(node):return ''.join(node.xpath('.//w:t/text()',namespaces=NS))
def math(e):
    tag=E.QName(e).localname
    def sub(n):
        c=e.find('m:'+n,NS);return math(c) if c is not None else ''
    if tag.endswith('Pr'):return ''
    if tag=='t':return e.text or ''
    if tag=='f':return r'\frac{'+sub('num')+'}{'+sub('den')+'}'
    if tag=='sSub':return '{'+sub('e')+'}_{'+sub('sub')+'}'
    if tag=='sSup':return '{'+sub('e')+'}^{'+sub('sup')+'}'
    if tag=='sSubSup':return '{'+sub('e')+'}_{'+sub('sub')+'}^{'+sub('sup')+'}'
    if tag=='rad':return r'\sqrt['+sub('deg')+']{'+sub('e')+'}'
    if tag=='acc':
        c=e.find('m:accPr/m:chr',NS); ch=c.get('{'+NS['m']+'}val','') if c is not None else ''
        return {'̇':r'\dot','˙':r'\dot','̂':r'\hat','^':r'\hat','̅':r'\bar'}.get(ch,r'\accent['+ch+']')+'{'+sub('e')+'}'
    if tag=='d':
        def v(k,default):
            n=e.find('m:dPr/m:'+k,NS);return n.get('{'+NS['m']+'}val',default) if n is not None else default
        return v('begChr','(')+sub('e')+v('endChr',')')
    if tag=='nary':
        ch=e.find('m:naryPr/m:chr',NS)
        return (ch.get('{'+NS['m']+'}val') if ch is not None else '∫')+'_{'+sub('sub')+'}^{'+sub('sup')+'} '+sub('e')
    if tag=='limLow':return sub('e')+'_{'+sub('lim')+'}'
    if tag=='limUpp':return sub('e')+'^{'+sub('lim')+'}'
    if tag=='func':return sub('fName')+sub('e')
    return ''.join(math(c) for c in e)
src=root(SOURCE); dst=root(FINAL)
sp=src.findall('w:body/w:p',NS); dp=dst.findall('w:body/w:p',NS)
build=json.loads((QA/'revision_build.json').read_text(encoding='utf-8'))
bm=dst.xpath('.//w:bookmarkStart',namespaces=NS)
names=[e.get('{'+NS['w']+'}name') for e in bm]
ids=[e.get('{'+NS['w']+'}id') for e in bm]
endids=[e.get('{'+NS['w']+'}id') for e in dst.xpath('.//w:bookmarkEnd',namespaces=NS)]
fields=[]
for i,p in enumerate(dp):
    for f in p.xpath('.//w:fldSimple',namespaces=NS):
        fields.append({'p':i,'instr':f.get('{'+NS['w']+'}instr',''),'value':plain(f),'context':text(p)})
seq=[f for f in fields if re.match(r'\s*SEQ Equation\b',f['instr'])]
bibseq=[f for f in fields if re.match(r'\s*SEQ Bibliography\b',f['instr'])]
refs=[f for f in fields if re.match(r'\s*REF ',f['instr'])]
ref_checks=[]
for f in refs:
    target=re.search(r'REF\s+(\S+)',f['instr']).group(1)
    ref_checks.append({**f,'target':target,'exists':target in names,'display_matches_target':f['value']==str(int(target[-3:]))})
eq_records=[]
for new,record in enumerate(build['equations'],1):
    matches=[p for p in dp if p.xpath('.//w:bookmarkStart[@w:name="eq_%03d"]'%new,namespaces=NS)]
    assert len(matches)==1
    p=matches[0]; before=sp[record['sourceParagraph']].find('m:oMath',NS);after=p.find('m:oMath',NS)
    eq_records.append({'number':new,'sourceParagraph':record['sourceParagraph'],'original':math(before),'final':math(after),'math_text_unchanged':math(before)==math(after),'intentional_replacement':new in(14,18,37)})
tables_src=src.findall('w:body/w:tbl',NS);tables_dst=dst.findall('w:body/w:tbl',NS)
def cell_text(tbl):return [[text(c) for c in row.findall('w:tc',NS)] for row in tbl.findall('w:tr',NS)]
table_checks=[{'index':i,'same':cell_text(a)==cell_text(b),'cells':sum(len(row) for row in cell_text(a))} for i,(a,b) in enumerate(zip(tables_src,tables_dst)) if i>0]
sidx=next(i for i,p in enumerate(sp) if text(p)=='附录 D 必要算法片段')
didx=next(i for i,p in enumerate(dp) if text(p)=='附录 D 必要算法片段')
tail_same=[text(p) for p in sp[sidx:]]==[text(p) for p in dp[didx:]]
styles={}
for p in sp[sidx:]:
    style=p.find('w:pPr/w:pStyle',NS);name=style.get('{'+NS['w']+'}val','') if style is not None else ''
    styles[name]=styles.get(name,0)+1

# Test only the pure delimiter function using AST extraction, without importing builder.
builder=(ROOT/'tools/revise_paper_references_20260913.py').read_text(encoding='utf-8')
module=ast.parse(builder)
fn=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='inline_math_delimiters')
namespace={'re':re};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<delimiter-audit>','exec'),namespace)
examples=['式(14)及式(16)—(20)','[1]、[7]','(x=r/R(t))','([0,1])',r'(0.15\ \mathrm{kg/kg})',r'(\Delta t=0.36\ \mathrm s=10^{-4}\ \mathrm h)',r'(t_{\mathrm c}\approx57.472302\ \mathrm h)','(0.1500)','(kg/kg)']
delimiter_checks=[{'source':s,'converted':namespace['inline_math_delimiters'](s)} for s in examples]

# Inspect every final body paragraph with its native math and references for human semantic review.
blocks=[]
for i,p in enumerate(dp):
    blocks.append({'paragraph':i,'plain':plain(p),'visible':text(p),'math':[math(m) for m in p.findall('m:oMath',NS)],'refs':[r for r in ref_checks if r['p']==i]})
(OUT/'final_extracted_paragraphs.json').write_text(json.dumps(blocks,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'final_extracted_paragraphs.txt').write_text('\n\n'.join(f"[{b['paragraph']}] {b['visible']}\n"+'\n'.join('MATH '+s for s in b['math']) for b in blocks),encoding='utf-8')
report={
    'source_docx':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'output_docx':str(FINAL),'output_sha256':hashlib.sha256(FINAL.read_bytes()).hexdigest(),
    'builder_output_hash_matches':hashlib.sha256(FINAL.read_bytes()).hexdigest()==build['outputSha256'],
    'equation_seq_count':len(seq),'equation_numbers_ordered': [f['value'] for f in seq]==list(map(str,range(1,38))),
    'equation_bookmark_count':len([s for s in names if s.startswith('eq_')]),
    'bibliography_seq_count':len(bibseq),'bibliography_ref_count':len([r for r in refs if 'bib_' in r['instr']]),
    'bibliography_bookmark_count':len([s for s in names if s.startswith('bib_')]),
    'bookmark_ids_unique':len(ids)==len(set(ids)), 'bookmark_pairs_match':sorted(ids)==sorted(endids),
    'ref_checks':ref_checks,'all_refs_resolve_and_match':all(r['exists'] and r['display_matches_target'] for r in ref_checks),
    'equation_math_comparison':eq_records,'unchanged_equations_preserved':all(r['math_text_unchanged'] for r in eq_records if not r['intentional_replacement']),
    'result_table_checks':table_checks,'all_result_table_cells_unchanged':all(t['same'] for t in table_checks),
    'appendix_D_all_paragraph_text_unchanged':tail_same,'appendix_D_paragraph_styles':styles,
    'symbol_table_final':cell_text(tables_dst[0]),'inline_delimiter_examples':delimiter_checks,
    'human_semantic_review':'PENDING','status':'PENDING_SEMANTIC_REVIEW'
}
(QA/'final_semantic_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in('ref_checks','equation_math_comparison','result_table_checks','symbol_table_final')},ensure_ascii=False,indent=2))
print('equation refs:')
for r in ref_checks:
    if 'eq_' in r['target']: print(r['p'],r['target'],r['context'])
