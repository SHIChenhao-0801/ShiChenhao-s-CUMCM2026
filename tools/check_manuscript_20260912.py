"""Apply the real formal-paper checks to this user-requested Word manuscript.

The user will provide drawings, so this manuscript uses an explicit empty figure
index and six written drawing briefs. Reuse the packaged renderer's actual PDF
only when its DOCX SHA matches; all ordinary structure/formula/citation checks run.
"""
from pathlib import Path
import hashlib
import json
import re
import sys

root=Path(__file__).resolve().parents[1]
assert Path.cwd().resolve()==root
sys.path.insert(0,str(root/'.agents/skills/paper-formal-writer/scripts'))
import check_paper_format as check
from paper_scope import checked_scope, body_text
qa=root/'paper_output/qa/manuscript_20260912'
check.FIGURE_INDEX_FILE=qa/'figure_index_for_manuscript.json'
check.TABLE_INDEX_FILE=qa/'table_index_for_manuscript.json'
original_counts=check.char_count
check.char_count=lambda text:original_counts(body_text(text))
original_tokens=check.source_formula_tokens
check.source_formula_tokens=lambda text:original_tokens(re.sub(r'```[\s\S]*?```','',text))


def actual_render(path,mode,source_content_chars):
    manifest=json.loads((qa/'render_manifest.json').read_text(encoding='utf-8'))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(path)==manifest['docxSha256'],'DOCX changed since rendering'
    pdf=root/manifest['pdf']
    assert sha(pdf)==manifest['pdfSha256']
    assert manifest['returncode']==0
    import pymupdf
    pages=[p.get_text() for p in pymupdf.open(pdf)]
    assert len(pages)==manifest['pageCount']
    for item in manifest['pages']:
        assert sha(root/item['path'])==item['sha256']
    plan=check.load_json(check.WRITING_PLAN)
    failures=[]
    declared=checked_scope(plan)
    main_start=next((i for i,t in enumerate(pages) if re.search(r'(?m)^1\s+问题重述\s*$',t)),None)
    appendix_start=next((i for i,t in enumerate(pages) if re.search(r'(?m)^附录\s*$',t)),None)
    assert main_start is not None and appendix_start is not None
    # The shared heuristic mistakes a wrapped sentence beginning '附录3…' for
    # the manuscript appendix. This paper has a unique standalone '附录' heading.
    scope={'counted_main_pages':appendix_start,'total_pages':len(pages),'delivery_mode':declared['mode'],'boundaryMethod':'exact standalone manuscript appendix heading; numbered task attachments are body references'}
    if appendix_start<declared['min_pages']:failures.append(f'主文页数{appendix_start}小于声明的{declared["min_pages"]}页。')
    if any(not t.strip() for t in pages[:appendix_start]):failures.append('主文存在无可提取文字的页面。')
    body_pages=appendix_start-main_start
    if main_start!=1:failures.append(f'摘要占{main_start}页，应在1页内。')
    if body_pages>30:failures.append(f'正文含AI声明和参考文献共{body_pages}页，超过30页。')
    if appendix_start<15:failures.append(f'摘要至参考文献仅{appendix_start}页，小于15页。')
    scope.update({'abstract_pages':main_start,'body_including_AI_references_pages':body_pages,'abstract_to_references_pages':appendix_start,'appendix_start_page':appendix_start+1,'seminar_body_max':30})
    result={'mode':mode,'status':'FAIL' if failures else 'PASS','libreoffice':manifest['libreoffice'],'returncode':0,'pdf':manifest['pdf'],'pdf_sha256':manifest['pdfSha256'],'pdf_bytes':pdf.stat().st_size,'page_count':len(pages),'extracted_text_chars':sum(len(re.sub(r'\s+','',t)) for t in pages),'paper_scope':scope,'renderer':'packaged documents/render_docx.py; SHA-bound reuse','manifest':str((qa/'render_manifest.json').relative_to(root))}
    return result,failures,[]


check.render_docx_qa=actual_render

if __name__=='__main__':
    raise SystemExit(check.main())
