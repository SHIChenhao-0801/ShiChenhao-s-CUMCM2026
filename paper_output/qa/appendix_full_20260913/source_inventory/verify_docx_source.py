from __future__ import annotations
import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import tokenize
import zipfile
from lxml import etree

OUT=Path(__file__).resolve().parent
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS={'w':W}
qn=lambda name:'{'+W+'}'+name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
jread=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))

def paragraph_text(paragraph):
    values=[]
    for node in paragraph.iter():
        if node.tag==qn('t'):
            values.append(node.text or '')
        elif node.tag==qn('tab'):
            values.append('\t')
        elif node.tag==qn('cr'):
            values.append('\n')
        elif node.tag==qn('br') and node.get(qn('type'),'textWrapping')=='textWrapping':
            values.append('\n')
        elif node.tag==qn('noBreakHyphen'):
            values.append('\u2011')
        elif node.tag==qn('softHyphen'):
            values.append('\u00ad')
    return ''.join(values)

def normalized_sha(lines):
    return hashlib.sha256(('\n'.join(lines)+'\n').encode('utf-8')).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--docx',required=True,type=Path)
    parser.add_argument('--index',required=True,type=Path)
    parser.add_argument('--manifest',default=OUT/'source_manifest.json',type=Path)
    parser.add_argument('--out',default=OUT/'docx_source_audit.json',type=Path)
    args=parser.parse_args()
    manifest=jread(args.manifest);index=jread(args.index)
    initial_docx_sha=sha(args.docx)
    if isinstance(index,dict) and index.get('docx_sha256'):
        assert index['docx_sha256']==initial_docx_sha,'Index is bound to a different DOCX version'
    sources=manifest['entries'];records=index if isinstance(index,list) else index['entries']
    assert len(sources)==47 and manifest['total_source_lines']==9917
    by_id={r['id']:r for r in records}
    assert len(records)==len(by_id)==len(sources),'Duplicate/missing code-index entries'
    assert set(by_id)=={e['id'] for e in sources},'Unexpected code-index scope'
    with zipfile.ZipFile(args.docx) as z:
        xml=etree.fromstring(z.read('word/document.xml'))
    body=xml.find('w:body',NS)
    paragraphs=body.findall('w:p',NS)
    positions={id(p):i for i,p in enumerate(paragraphs)}
    bookmarks={}
    for bookmark in xml.findall('.//w:bookmarkStart',NS):
        name=bookmark.get(qn('name'))
        if not name or not name.startswith('CODE_SRC'):
            continue
        assert name not in bookmarks,'Duplicate code bookmark '+name
        p=bookmark.getparent()
        while p is not None and p.tag!=qn('p'):
            p=p.getparent()
        assert p is not None and p.getparent() is body,'Code bookmark not in main body'
        bookmarks[name]=paragraphs.index(p)
    extracted_dir=OUT/'extracted_from_docx'
    extracted_dir.mkdir(exist_ok=True)
    results=[];covered=set()
    for source in sources:
        code_id=source['id'];record=by_id[code_id]
        start=record['start_paragraph_index'];end=record['end_paragraph_index']
        assert isinstance(start,int) and isinstance(end,int) and 0<=start<=end<len(paragraphs)
        assert bookmarks['CODE_'+code_id+'_BEGIN']==start,'BEGIN bookmark disagrees: '+code_id
        assert bookmarks['CODE_'+code_id+'_END']==end,'END bookmark disagrees: '+code_id
        code_range=set(range(start,end+1))
        assert not covered.intersection(code_range),'Overlapping source spans'
        covered.update(code_range)
        path=Path(source['appendix_source_path'])
        assert sha(path)==source['sha256'],'Source file changed since frozen manifest: '+code_id
        expected=path.read_text(encoding=source['source_text_encoding']).splitlines()
        actual=[paragraph_text(p) for p in paragraphs[start:end+1]]
        forbidden=[]
        for offset,p in enumerate(paragraphs[start:end+1]):
            for name in ['drawing','object','instrText','delText','altChunk']:
                if p.find('.//w:'+name,NS) is not None:
                    forbidden.append((offset+1,name))
        mismatch=[]
        for line in range(max(len(actual),len(expected))):
            wanted=expected[line] if line<len(expected) else None
            got=actual[line] if line<len(actual) else None
            if wanted!=got:
                mismatch.append({'source_line':line+1,'expected':wanted,'actual':got})
        assert len(expected)==source['lines']
        extracted_path=extracted_dir/(code_id+'_'+path.name)
        extracted_path.write_text('\n'.join(actual)+'\n',encoding='utf-8')
        checks={'exact_lines_equal':not mismatch,'forbidden_noncode_elements':forbidden,
                'start_and_end_bookmarks_equal_index':True,'overlap':False,
                'original_source_sha256':source['sha256'],
                'expected_normalized_text_sha256':normalized_sha(expected),
                'docx_extracted_normalized_text_sha256':normalized_sha(actual)}
        if source['language']=='Python' and not mismatch and not forbidden:
            text='\n'.join(actual)+'\n'
            compile(text,str(extracted_path),'exec')
            tree=ast.parse(text)
            comments=[t for t in tokenize.generate_tokens(io.StringIO(text).readline) if t.type==tokenize.COMMENT]
            standalone=[n for n in ast.walk(tree) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str)]
            assert not comments and not standalone
            assert ast.dump(tree,include_attributes=False)==ast.dump(ast.parse('\n'.join(expected)+'\n'),include_attributes=False)
            checks.update(python_compile='PASS',python_ast_equal_to_frozen_source=True,remaining_comments=0,remaining_standalone_docstrings=0)
        results.append({'id':code_id,'language':source['language'],'path':source['relative_path'],
                        'start_paragraph_index':start,'end_paragraph_index':end,
                        'expected_lines':len(expected),'extracted_lines':len(actual),
                        'mismatches':mismatch[:20],'mismatch_count':len(mismatch),
                        'status':'PASS' if not mismatch and not forbidden else 'FAIL','checks':checks,
                        'extracted_file':str(extracted_path)})
    assert sha(args.docx)==initial_docx_sha,'DOCX changed during extraction'
    passed=all(r['status']=='PASS' for r in results)
    report={'status':'PASS' if passed else 'FAIL','created_utc':datetime.now(timezone.utc).isoformat(),
            'docx_path':str(args.docx.resolve()),'docx_sha256':sha(args.docx),
            'index_path':str(args.index.resolve()),'index_sha256':sha(args.index),
            'manifest_path':str(args.manifest.resolve()),'manifest_sha256':sha(args.manifest),
            'sources':len(results),'total_source_lines':sum(r['expected_lines'] for r in results),
            'total_extracted_lines':sum(r['extracted_lines'] for r in results),
            'languages':dict(Counter(r['language'] for r in results)),
            'source_bookmarks':len(bookmarks),'method':'Read actual word/document.xml, reconstruct text/tabs/line-breaks, verify inclusive paragraph ranges and two zero-width bookmarks per source independently; exact line comparison preserves all spaces and blank lines; final physical newline/BOM excluded from line equivalence',
            'new_model_execution':False,'entries':results}
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['status','sources','total_source_lines','total_extracted_lines','languages','source_bookmarks','docx_sha256']},ensure_ascii=False))
    if not passed:
        raise SystemExit(1)

if __name__=='__main__':
    main()
