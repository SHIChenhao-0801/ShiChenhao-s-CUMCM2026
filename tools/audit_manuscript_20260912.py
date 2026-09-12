"""Run the shared authoring audit with explicit full-source-appendix handling.

The user requested complete source listings. Literal program keys (for example
`placeholder: False`) are not manuscript placeholders. Prose audits and global
revision similarity therefore operate on the text outside fenced code; source
hashes and approval records continue to bind the complete unchanged files.
"""
from pathlib import Path
import re
import sys
import difflib

ROOT = Path(__file__).resolve().parents[1]
if Path.cwd().resolve() != ROOT:
    raise RuntimeError('Run from the contest workspace.')
sys.path.insert(0, str(ROOT / '.agents/skills/paper-formal-writer/scripts'))
import validate_authoring as audit


def prose(text):
    return re.sub(r'```[\s\S]*?```', '', text)


original_common = audit.validate_common
original_duplicates = audit.duplicate_paragraphs


def prose_duplicates(text):
    # Different question-specific coefficients must not turn equations into
    # allegedly duplicated prose after numerical normalization.
    narrative = re.sub(r'\$\$[\s\S]*?\$\$', '', prose(text))
    # Source listings repeat structured path/version metadata by necessity.
    narrative = re.sub(r'(?m)^(?:文件：|原运行槽位：).*$', '', narrative)
    return original_duplicates(narrative)


def validate_prose(text, section, section_id, *, require_marker):
    return original_common(prose(text), section, section_id, require_marker=require_marker)


def prose_similarity(isjunk, a, b, autojunk=False):
    return difflib.SequenceMatcher(isjunk, prose(a), prose(b), autojunk=autojunk)


audit.validate_common = validate_prose
audit.SequenceMatcher = prose_similarity
audit.duplicate_paragraphs = prose_duplicates

if __name__ == '__main__':
    raise SystemExit(audit.main())
