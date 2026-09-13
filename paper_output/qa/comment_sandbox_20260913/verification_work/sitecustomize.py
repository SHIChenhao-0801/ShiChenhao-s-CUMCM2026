import json
import os
from pathlib import Path
import sys


_root = Path(os.environ['VERIFICATION_SANDBOX_ROOT']).resolve()
_stdlib = Path(sys.base_prefix).resolve()
_venv = Path(sys.prefix).resolve()
_fonts = Path('C:/Windows/Fonts').resolve()
_guard = Path(__file__).resolve().parent
_log = _root / 'blocked_access.jsonl'
_reads = (_root, _stdlib, _venv, _fonts, _guard)


def _path(value):
    if value is None:
        return Path.cwd().resolve()
    if isinstance(value, int):
        return None
    return Path(os.fsdecode(value)).resolve()


def _check(value, write, event):
    path = _path(value)
    if path is None or str(path).lower() in ('nul', '\\\\.\\nul'):
        return
    allowed = path.is_relative_to(_root) if write else any(path.is_relative_to(p) for p in _reads)
    if not allowed:
        entry = {'pid': os.getpid(), 'event': event, 'path': str(path), 'write': write}
        with _log.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(entry, ensure_ascii=False) + '\n')
        raise PermissionError('Independent verification sandbox denied ' + str(path))


def _audit(event, args):
    if event == 'open':
        mode = args[1] or ''
        flags = args[2] or 0
        writing = any(x in mode for x in ('w', 'a', '+', 'x')) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        _check(args[0], writing, event)
    elif event in ('os.listdir', 'os.scandir', 'os.chdir'):
        _check(args[0] if args else None, False, event)
    elif event in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.chmod', 'os.utime'):
        _check(args[0], True, event)
    elif event in ('os.rename', 'os.replace'):
        _check(args[0], True, event)
        _check(args[1], True, event)
    elif event in ('socket.connect', 'socket.getaddrinfo'):
        raise PermissionError('Network unavailable during independent verification')


sys.addaudithook(_audit)
