"""Validate the user's current supporting directory and write a plain TXT inventory."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = (ROOT / '支撑材料').resolve()
QA = ROOT / 'paper_output/qa/support_cleanup_20260913'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_txt(name, content):
    path = SUPPORT / name
    assert path.resolve().is_relative_to(SUPPORT)
    path.write_text(content.strip() + '\n', encoding='utf-8-sig')


def main():
    files = [p for p in SUPPORT.rglob('*') if p.is_file()]
    forbidden = [p.relative_to(SUPPORT).as_posix() for p in files
                 if p.suffix.lower() in {'.json', '.jsonl', '.md', '.markdown', '.zip', '.rar', '.7z', '.pyc'}
                 or 'AI工具使用详情' in p.name or 'AI使用记录' in p.relative_to(SUPPORT).as_posix()]
    assert not forbidden, forbidden
    protected = json.loads((QA / 'protected_files_before.json').read_text(encoding='utf-8'))
    for relative, expected in protected.items():
        path = SUPPORT / relative
        assert path.is_file() and sha(path) == expected, relative

    code = json.loads((QA / 'code/code_cleanup_audit.json').read_text(encoding='utf-8'))
    assert code['status'] == 'PASS'
    for item in code['sourceFiles']:
        assert sha(SUPPORT / '03_程序代码' / item['path']) == item['sha256'], item['path']
    verification = json.loads((QA / 'verification_sources/preparation_audit.json').read_text(encoding='utf-8'))
    for item in verification['sources']:
        path = SUPPORT / '05_数值检验与实验' / item['file']
        assert sha(path) == item['packaged_sha256'] == item['source_sha256'], item['file']
    source_count = len(verification['sources'])
    assert source_count == 33, source_count
    frozen = ROOT / 'paper_output/results/production/final_v6a/outputs'
    for i in range(1, 5):
        assert sha(SUPPORT / '04_结果表格' / f'result{i}.xlsx') == sha(frozen / f'result{i}.xlsx')

    write_txt('00_整理验收说明.txt', '''支撑材料整理核验说明

本次按用户要求整理当前目录：删除既有AI工具使用详情及配套材料；JSON、JSONL和Markdown文件均为零；说明文件使用TXT；直接保留文件夹，没有压缩包。

当前已有PDF、Excel、CSV、NPZ和MATLAB文件共42份逐文件哈希检查通过，内容保持原样；四份完整结果Excel与final_v6a冻结文件逐字节一致。

03_程序代码的输入清单改为CSV，冻结数值参照改为Python纯数据常量；数据经精确等价检查，八个核心数值模块的算法保持一致。12项输入预检通过。当前代码实际完成Q1 N40和N3200两次求解、每次79,244个Excel格与84个正文格回读核验；N3200七个保存数组与冻结参照逐值相同，进程退出码0。

本次没有重新求解Q23/Q4全量轨迹。此前全量运行与本次定向运行分别记在03_程序代码/docs/运行验收说明.txt。

05_数值检验与实验提供31个Python源文件、1个MATLAB源文件、1个Node.js源文件，共33份；逐文件与原始源代码哈希一致。说明列出各文件用途及原工程路径依赖，本次整理没有声称全部历史检验已经重新运行。

程序实际执行后仍可能生成JSON过程记录；本次交付目录中不包含这些运行产物。运行方法见03_程序代码/README.txt，检验源码前提见05_数值检验与实验/数值检验说明.txt。
''')
    others = sorted((p for p in SUPPORT.rglob('*') if p.is_file() and p.name != '00_文件清单.txt'),
                    key=lambda p: p.relative_to(SUPPORT).as_posix().casefold())
    entries = ['00_文件清单.txt'] + [p.relative_to(SUPPORT).as_posix() for p in others]
    entries.sort(key=str.casefold)
    counts = Counter(Path(e).parts[0] if len(Path(e).parts) > 1 else '根目录说明' for e in entries)
    text = ['支撑材料文件清单', '', f'共{len(entries)}个文件，包含本清单。说明使用TXT，未生成压缩包。', '', '分类文件数：']
    text += [f'  {name}：{count}个文件' for name, count in sorted(counts.items())]
    text += ['', '逐文件相对路径：', ''] + entries
    write_txt('00_文件清单.txt', '\n'.join(text))
    current = sorted((p for p in SUPPORT.rglob('*') if p.is_file()), key=lambda p: p.relative_to(SUPPORT).as_posix())
    assert set(entries) == {p.relative_to(SUPPORT).as_posix() for p in current}
    report = {
        'status': 'PASS_TXT_AND_SOURCE_DELIVERY',
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'directory': str(SUPPORT),
        'files': len(current),
        'bytes': sum(p.stat().st_size for p in current),
        'extensions': dict(sorted(Counter(p.suffix.lower() for p in current).items())),
        'categories': dict(sorted(counts.items())),
        'json_markdown_ai_archive_files': forbidden,
        'protected_existing_files_unchanged': len(protected),
        'four_frozen_workbooks_byte_identical': True,
        'verification_sources_byte_identical': source_count,
        'code_audit': code['status'],
        'inventory_exact': True,
        'sha256': {p.relative_to(SUPPORT).as_posix(): sha(p) for p in current},
    }
    (QA / 'final_directory_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'sha256'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
