from pathlib import Path
from datetime import datetime, timezone
import json
import shutil
import subprocess

work = Path('C:/Work')
files = []
for base in [work/'03/results', work/'03/tmp/cache/runtime', work/'extra_entries/03_wrapper/results', work/'wrapper_stable/results']:
    if base.exists():
        files += [{'path': str(p), 'bytes': p.stat().st_size, 'mtime': p.stat().st_mtime}
                  for p in base.rglob('*') if p.is_file()]
ps = ['C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe', '-NoProfile', '-Command',
      'Get-Process python | Select-Object Id,CPU,WorkingSet64,StartTime | ConvertTo-Json']
proc = subprocess.run(ps, capture_output=True, text=True)
report = {'utc': datetime.now(timezone.utc).isoformat(), 'files': files,
          'disk': dict(zip(['total','used','free'],shutil.disk_usage('C:/'))),
          'pythonProcesses': proc.stdout, 'processProbeExit': proc.returncode}
Path('C:/Evidence/progress_snapshot.json').write_text(json.dumps(report,ensure_ascii=False,indent=2), encoding='utf-8')
