from pathlib import Path, PurePosixPath
import hashlib
import json
import zipfile

root = Path(__file__).resolve().parents[3]
qa = Path(__file__).resolve().parent
archive = root / '支撑材料临时.zip'
sources = []
with zipfile.ZipFile(archive) as bundle:
    assert bundle.testzip() is None
    for member in bundle.infolist():
        name = PurePosixPath(member.filename)
        assert not name.is_absolute() and '..' not in name.parts
        if member.is_dir() or name.suffix.lower() not in {'.py', '.m', '.mjs', '.ps1'}:
            continue
        assert name.parts[0] == '支撑材料'
        relative = Path(*name.parts[1:])
        data = bundle.read(member)
        before = qa / 'before' / relative
        candidate = qa / 'candidate' / relative
        source = root / '支撑材料' / relative
        digest = lambda value: hashlib.sha256(value).hexdigest()
        sources.append({'path': relative.as_posix(), 'zipSha256': digest(data),
                        'matchesBefore': before.is_file() and data == before.read_bytes(),
                        'matchesCurrentSupport': source.is_file() and data == source.read_bytes(),
                        'matchesCommentFreeCandidate': candidate.is_file() and data == candidate.read_bytes()})
report = {'archive': str(archive), 'bytes': archive.stat().st_size,
          'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'crcPassed': True,
          'sourceCount': len(sources), 'allSourcesMatchBefore': all(x['matchesBefore'] for x in sources),
          'allSourcesMatchCurrentSupport': all(x['matchesCurrentSupport'] for x in sources), 'sources': sources}
(qa / 'user_zip_source_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k != 'sources'}, ensure_ascii=False, indent=2))
