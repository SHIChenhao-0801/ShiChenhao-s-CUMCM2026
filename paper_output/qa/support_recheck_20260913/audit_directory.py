from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import zipfile
import zlib
import fitz

ROOT = Path(__file__).resolve().parents[3]
SUPPORT = ROOT / '支撑材料'
QA = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def is_local(path):
    rel = path.relative_to(SUPPORT)
    return '.vs' in rel.parts or path.name == 'UpgradeLog.htm'

def compression_measure(paths):
    # Count DEFLATE payload and normal UTF-8 ZIP headers without creating an archive.
    total = 22
    rows = []
    for path in paths:
        arcname = '支撑材料/' + path.relative_to(SUPPORT).as_posix()
        raw = path.read_bytes()
        compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
        size = len(compressor.compress(raw)) + len(compressor.flush())
        overhead = 30 + 46 + 2 * len(arcname.encode('utf-8'))
        total += size + overhead
        rows.append({'path':path.relative_to(SUPPORT).as_posix(), 'raw_bytes':len(raw), 'deflate_bytes':size, 'header_bytes':overhead})
    return {'method':'raw DEFLATE level 9 + ordinary UTF-8 ZIP local/central headers; no archive created; no directory entries/extras/comments', 'estimated_bytes':total, 'margin_to_20000000':20000000-total, 'margin_to_20MiB':20*1024*1024-total, 'largest':sorted(rows, key=lambda r:r['deflate_bytes'], reverse=True)[:10]}

def main():
    files = sorted(p for p in SUPPORT.rglob('*') if p.is_file())
    formal = [p for p in files if not is_local(p)]
    local = [p for p in files if is_local(p)]
    prior = json.loads((ROOT/'paper_output/qa/comment_sandbox_20260913/final_delivery_audit.json').read_text('utf-8'))
    prior_rows = prior['formalFiles']
    prior_changed = []
    for row in prior_rows:
        path = SUPPORT / row['path']
        if not path.is_file() or sha(path) != row['sha256']:
            prior_changed.append(row['path'])
    raw_pairs = [(SUPPORT/'01_赛题与原始数据/A题.pdf', ROOT/'problem_files/CUMCM2026Problems/A题/A题.pdf')]
    for p in (SUPPORT/'01_赛题与原始数据/附件').rglob('*.xlsx'):
        raw_pairs.append((p,ROOT/'problem_files/CUMCM2026Problems/A题/附件'/p.relative_to(SUPPORT/'01_赛题与原始数据/附件')))
    checks = [{'path':str(a.relative_to(SUPPORT)), 'source':str(b.relative_to(ROOT)), 'equal':b.is_file() and sha(a)==sha(b)} for a,b in raw_pairs]
    results = []
    for n in range(1,5):
        p=SUPPORT/f'04_结果表格/result{n}.xlsx'
        ref=ROOT/f'paper_output/results/production/final_v6a/outputs/result{n}.xlsx'
        results.append({'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p),'frozen_equal':sha(p)==sha(ref)})
    zip_checks = []
    for p in formal:
        if p.suffix.lower() in {'.xlsx','.npz'}:
            with zipfile.ZipFile(p) as archive:
                bad=archive.testzip()
            zip_checks.append({'path':p.relative_to(SUPPORT).as_posix(),'crc_valid':bad is None,'bad_entry':bad})
    pdfs=[]
    for p in formal:
        if p.suffix.lower()=='.pdf':
            with fitz.open(p) as doc:
                pdfs.append({'path':p.relative_to(SUPPORT).as_posix(),'pages':len(doc),'encrypted':bool(doc.is_encrypted),'metadata':doc.metadata})
    submission=[]
    for p in list(ROOT.glob('*.pdf'))+list((ROOT/'paper_output/submission').glob('*.pdf')):
        with fitz.open(p) as doc:
            submission.append({'path':p.relative_to(ROOT).as_posix(),'mtime':datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat(),'bytes':p.stat().st_size,'sha256':sha(p),'pages':len(doc),'beginning':doc[0].get_text()[:200]})
    report={'at_utc':datetime.now(timezone.utc).isoformat(),'root':str(SUPPORT),'actual_files':len(files),'formal_files':len(formal),'actual_bytes':sum(p.stat().st_size for p in files),'formal_bytes':sum(p.stat().st_size for p in formal),'categories':dict(Counter(p.relative_to(SUPPORT).parts[0] if len(p.relative_to(SUPPORT).parts)>1 else '根目录说明' for p in formal)),'extensions':dict(Counter(p.suffix.lower() for p in formal)),'local_files':[p.relative_to(SUPPORT).as_posix() for p in local],'formal_json_markdown_archives':[p.relative_to(SUPPORT).as_posix() for p in formal if p.suffix.lower() in {'.json','.jsonl','.md','.markdown','.zip','.rar','.7z'}],'all_empty_files':[p.relative_to(SUPPORT).as_posix() for p in files if p.stat().st_size==0],'prior_formal_count':len(prior_rows),'prior_changed':prior_changed,'raw_inputs':checks,'frozen_results':results,'xlsx_npz_crc':zip_checks,'pdfs':pdfs,'current_compression_measurement':compression_measure(formal),'existing_submission_pdfs':submission,'files':[{'path':p.relative_to(SUPPORT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'local_only':is_local(p)} for p in files]}
    out=QA/'directory_initial_audit.json'
    if out.exists():out=QA/'directory_final_audit.json'
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in {'files','pdfs','xlsx_npz_crc','raw_inputs'}},ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
