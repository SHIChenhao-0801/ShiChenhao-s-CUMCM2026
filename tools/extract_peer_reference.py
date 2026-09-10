"""Copy only modeling assets from a user-supplied archive; never execute them."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('D:/Document/数学建模/A题_model.zip')
DEST = ROOT/'reference_materials/peer-models/2026-09-10_A_model'
DEST.mkdir(parents=True,exist_ok=True)
records=[]
skipped=[]
with zipfile.ZipFile(SOURCE) as archive:
    for entry in archive.infolist():
        name=entry.filename.replace('\\','/')
        pp=PurePosixPath(name)
        if pp.is_absolute() or '..' in pp.parts or ':' in name:
            raise ValueError('Invalid archive path')
        if entry.is_dir():
            continue
        if '/__pycache__/' in name or '/out/preview/ud/' in name:
            skipped.append({'path':name,'bytes':entry.file_size,'reason':'unneeded bytecode/browser profile'})
            continue
        target=(DEST/Path(*pp.parts[1:])).resolve()
        if not target.is_relative_to(DEST.resolve()):
            raise ValueError('Archive path outside intended workspace')
        content=archive.read(entry)
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():
            raise FileExistsError(target)
        target.write_bytes(content)
        records.append({'archive_path':name,'path':target.relative_to(ROOT).as_posix(),
                        'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()})
manifest={'source_archive':str(SOURCE),'source_bytes':SOURCE.stat().st_size,
    'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'user_authorization':'Reference and compare; archive contents are data, not new instructions.',
    'executed_code':False,'unpickled_objects':False,'extracted_assets':records,'skipped':skipped}
(DEST/'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'destination':str(DEST),'source_sha256':manifest['source_sha256'],
    'assets':len(records),'skipped_unneeded':len(skipped)},ensure_ascii=False))
