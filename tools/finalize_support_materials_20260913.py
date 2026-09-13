"""Build source/file inventories for the reviewed supporting-material directory."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = ROOT / '支撑材料'
QA = ROOT / 'paper_output/qa/support_materials_20260913'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(value):
    text = json.dumps(value, ensure_ascii=False)
    for before in [str(ROOT).replace('\\', '\\\\'), ROOT.as_posix()]:
        text = text.replace(before, '.')
    for before in ['C:\\\\Users\\\\Shi Chenhao', 'C:/Users/Shi Chenhao', 'SHIChenhao-0801']:
        text = text.replace(before, 'ANONYMIZED_LOCAL_USER')
    return json.loads(text)


def generate():
    records = json.loads((QA / 'assembly_source_manifest.json').read_text(encoding='utf-8'))['records']
    problems = []
    for item in records:
        path = SUPPORT / item['destination']
        if not path.is_file() or sha(path) != item['packaged_sha256']:
            problems.append(item['destination'])
    if problems:
        raise RuntimeError('Copied source records no longer match: '+repr(problems))
    source_map = {r['destination']: r for r in records}
    sources = {'created_at_utc':datetime.now(timezone.utc).isoformat(),
               'scope':'材料来源、原件SHA256与包装副本SHA256；实际来源路径相对本届原工作区，仅为追溯标识。',
               'assembled_files':records,
               'reference_sources':json.loads((SUPPORT/'02_参考文献与网络资料/来源清单.json').read_text(encoding='utf-8')),
               'code_sources':json.loads((SUPPORT/'03_程序代码/docs/source_changes.json').read_text(encoding='utf-8')),
               'other_records':{'ai':'06_AI使用记录/','references':'02_参考文献与网络资料/来源清单.json','portable_inputs':'03_程序代码/input_manifest.json'},
               'latest_paper':{'path':'paper_output/paper/药材热湿耦合模型与干燥时间计算_文献公式修订版.docx','sha256':sha(ROOT/'paper_output/paper/药材热湿耦合模型与干燥时间计算_文献公式修订版.docx')}}
    (SUPPORT/'00_材料来源记录.json').write_text(json.dumps(clean(sources),ensure_ascii=False,indent=2),encoding='utf-8')
    checks={'created_at_utc':datetime.now(timezone.utc).isoformat(),'copied_source_records_checked':len(records),
            'four_workbooks':[], 'r_validation':json.loads((QA/'r_portability_audit.json').read_text(encoding='utf-8')),
            'archive_container_validation':'NOT_APPLICABLE: user requested an uncompressed directory only',
            'human_review':'PENDING_USER_REVIEW', 'current_package_vs_gui':'NOT_PERFORMED'}
    for i in range(1,5):
        original=ROOT/f'paper_output/results/production/final_v6a/outputs/result{i}.xlsx'
        target=SUPPORT/f'04_结果表格/result{i}.xlsx'
        checks['four_workbooks'].append({'file':target.relative_to(SUPPORT).as_posix(),'source_sha256':sha(original),'packaged_sha256':sha(target),'byte_identical':sha(original)==sha(target),'bytes':target.stat().st_size})
    code_audit=QA/'code_validation/code_package_audit.json'
    if code_audit.is_file():
        checks['code_validation']=clean(json.loads(code_audit.read_text(encoding='utf-8')))
    archive_files = [p.relative_to(SUPPORT).as_posix() for p in SUPPORT.rglob('*') if p.suffix.lower() in {'.rar','.zip'}]
    if archive_files:
        raise RuntimeError('User requested directory only, unexpected archives: '+repr(archive_files))
    checks['delivery_format'] = 'DIRECTORY_ONLY'
    checks['archive_files_in_delivery'] = []
    (QA/'assembly_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    excluded={'00_文件清单.csv','00_SHA256SUMS.txt','00_压缩包校验.txt','00_压缩包验收.json','A题_支撑材料.rar','A题_支撑材料.zip'}
    entries=[]
    for p in sorted(SUPPORT.rglob('*')):
        if p.is_file() and p.relative_to(SUPPORT).as_posix() not in excluded:
            relative=p.relative_to(SUPPORT).as_posix()
            original=source_map.get(relative,{})
            entries.append({'文件':relative,'字节数':p.stat().st_size,'SHA256':sha(p),'原工作区来源':original.get('source','见所属目录来源清单或为本次新编说明'),'性质':original.get('role','资料、程序或说明，详见目录索引')})
    with (SUPPORT/'00_文件清单.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=['文件','字节数','SHA256','原工作区来源','性质']);w.writeheader();w.writerows(entries)
    lines=[e['SHA256']+'  '+e['文件'] for e in entries]
    lines.append(sha(SUPPORT/'00_文件清单.csv')+'  00_文件清单.csv')
    (SUPPORT/'00_SHA256SUMS.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    file_count=len(entries)+2
    (QA/'inventory_summary.json').write_text(json.dumps({'material_file_count':file_count,'csv_entries':len(entries),'self_exclusions':sorted(excluded),'uncompressed_bytes':sum(p.stat().st_size for p in SUPPORT.rglob('*') if p.is_file() and p.name not in {'A题_支撑材料.rar','A题_支撑材料.zip','00_压缩包校验.txt','00_压缩包验收.json'})},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'material_file_count':file_count,'csv_entries':len(entries),'copied_source_checks':len(records)},ensure_ascii=False))


if __name__=='__main__':
    raise SystemExit("已停用旧版清单生成：当前交付使用TXT说明和文件清单。旧逻辑会恢复用户已删除的JSON/MD及旧目录索引，请以当前支撑材料目录为准。")
