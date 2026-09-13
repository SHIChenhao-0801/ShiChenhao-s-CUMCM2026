import runpy
import sys
from pathlib import Path

entry = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(entry.parent))
sys.argv = [str(entry), *sys.argv[2:]]
runpy.run_path(str(entry), run_name="__main__")
