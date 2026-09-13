from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import hashlib
import json
import shutil

manifest=json.loads(Path('C:/Evidence/published_support_manifest.json').read_text(encoding='utf-8'))
assert manifest['status']=='FINALIZED'
source=Path('C:/PublishedSupport')
destination=Path('C:/Users/WDAGUtilityAccount/Desktop/支撑材料_去注释核查版')
destination.mkdir(exist_ok=False)
copied=[]
for entry in manifest['formalFiles']:
    relative=PurePosixPath(entry['path'])
    assert not relative.is_absolute() and '..' not in relative.parts
    original=source/Path(*relative.parts)
    target=destination/Path(*relative.parts)
    assert hashlib.sha256(original.read_bytes()).hexdigest()==entry['sha256']
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(original,target)
    assert hashlib.sha256(target.read_bytes()).hexdigest()==entry['sha256']
    copied.append(entry)
record={'status':'COPIED_AND_SHA_VERIFIED','utc':datetime.now(timezone.utc).isoformat(),
        'destination':str(destination),'fileCount':len(copied),'files':copied,
        'originalDesktopZipPreserved':Path('C:/Users/WDAGUtilityAccount/Desktop/支撑材料临时.zip').is_file(),
        'originalExtractedFolderPreserved':Path('C:/Users/WDAGUtilityAccount/Desktop/支撑材料临时').is_dir(),
        'excludedMachineCaches':True,'publishedHostFolderWasMappedOnlyAfterAllRuns':True}
Path('C:/Evidence/desktop_delivery.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':record['status'],'destination':str(destination),'fileCount':len(copied)},ensure_ascii=False),flush=True)
