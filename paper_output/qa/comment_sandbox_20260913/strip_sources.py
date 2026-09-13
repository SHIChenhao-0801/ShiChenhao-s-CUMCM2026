from __future__ import annotations
import argparse
import ast
import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import tokenize

ROOT = Path(__file__).resolve().parents[3]
QA = Path(__file__).resolve().parent
PARTS = ['03_程序代码', '05_数值检验与实验']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def blank(value):
    return ''.join(c if c in '\r\n' else ' ' for c in value)


def clean_space(value):
    value = '\n'.join(line.rstrip() for line in value.splitlines()) + '\n'
    return re.sub(r'\n{4,}', '\n\n\n', value).lstrip('\n')


def doc_node(node):
    body = getattr(node, 'body', [])
    if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and body:
        first = body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
            return first
    return None


class DropDocs(ast.NodeTransformer):
    def generic_visit(self, node):
        doc = doc_node(node)
        if doc is not None:
            node.body = node.body[1:]
            if not node.body and not isinstance(node, ast.Module):
                node.body = [ast.Pass()]
        return super().generic_visit(node)


def strip_python(text, label):
    tree = ast.parse(text, filename=label)
    lines = text.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))

    def offset(line, col, byte_col=False):
        if byte_col:
            col = len(lines[line-1].encode('utf-8')[:col].decode('utf-8'))
        return starts[line-1] + col

    spans = []
    comments = []
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type == tokenize.COMMENT:
            first = offset(*token.start)
            last = offset(*token.end)
            spans.append((first, last, blank(text[first:last])))
            comments.append({'line': token.start[0], 'characters': len(token.string)})
    docs = []
    for owner in ast.walk(tree):
        node = doc_node(owner)
        if node is not None:
            first = offset(node.lineno, node.col_offset, True)
            last = offset(node.end_lineno, node.end_col_offset, True)
            replacement = blank(text[first:last])
            needs_pass = len(owner.body) == 1 and not isinstance(owner, ast.Module)
            if needs_pass:
                replacement = 'pass' + replacement[4:]
            else:
                tail = re.match(r'[ \t]*;', text[last:])
                if tail:
                    last += tail.end()
                    replacement = blank(text[first:last])
            spans.append((first, last, replacement))
            docs.append({'line': node.lineno, 'end_line': node.end_lineno, 'owner': getattr(owner, 'name', '<module>'),
                         'empty_suite_pass': needs_pass})
    spans.sort(reverse=True)
    for first, last, replacement in spans:
        text = text[:first] + replacement + text[last:]
    result = clean_space(text)
    actual = ast.parse(result, filename=label)
    expected = DropDocs().visit(copy.deepcopy(tree))
    expected_dump = ast.dump(expected, include_attributes=False)
    actual_dump = ast.dump(actual, include_attributes=False)
    if expected_dump != actual_dump:
        raise AssertionError('Non-comment Python AST differs: ' + label)
    compile(result, label, 'exec')
    remaining_comments = [t for t in tokenize.generate_tokens(io.StringIO(result).readline) if t.type == tokenize.COMMENT]
    remaining_docs = [n for n in ast.walk(actual) if doc_node(n) is not None]
    if remaining_comments or remaining_docs:
        raise AssertionError('Residual comment/docstring: ' + label)
    uses_doc = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == '__doc__']
    return result, {'language': 'Python', 'comment_count': len(comments), 'comments': comments,
                    'docstring_count': len(docs), 'docstrings': docs, 'ast_equal_without_docstrings': True,
                    'normalized_ast_sha256': sha(expected_dump.encode()), 'compile': 'PASS',
                    'remaining_comment_count': 0, 'remaining_docstring_count': 0,
                    'doc_runtime_reference_lines': uses_doc,
                    'doc_runtime_effect': 'argparse description becomes None; CLI options and numerical execution unchanged' if uses_doc else None}


def strip_matlab(text, label):
    lines = text.splitlines(keepends=True)
    result = []
    comments = []
    percent_values = []
    for number, line in enumerate(lines, 1):
        # The actual file has only whole-line comments and three trailing %#ok directives.
        # Restrict stripping to those observed forms; never guess whether an apostrophe is a transpose.
        if re.match(r'^\s*%', line):
            comments.append({'line': number, 'kind': 'whole_line'})
            result.append('\n' if line.endswith('\n') else '')
            continue
        match = re.search(r';[ \t]+(%#ok<NASGU>)[ \t]*(?:\r?\n)?$', line)
        if match:
            comments.append({'line': number, 'kind': 'code_analyzer_directive'})
            line = line[:match.start(1)] + ('\n' if line.endswith('\n') else '')
        if '%' in line:
            # Every other percent is in a MATLAB single-quoted printf/error format string.
            strings = re.findall(r"'(?:[^'\r\n]|'')*'", line)
            if sum(s.count('%') for s in strings) != line.count('%'):
                raise AssertionError('Unclassified MATLAB percent: ' + label + ':' + str(number))
            percent_values.extend(s for s in strings if '%' in s)
        result.append(line)
    result = clean_space(''.join(result))
    if re.search(r'^\s*%', result, flags=re.M) or '%#ok' in result:
        raise AssertionError('MATLAB comments remain')
    return result, {'language': 'MATLAB', 'comment_count': len(comments), 'comments': comments,
                    'docstring_count': 0, 'remaining_comment_count': 0,
                    'verification': 'Only known whole-line comments and trailing %#ok<NASGU> removed; every other percent is inside a preserved quoted format string',
                    'format_strings_with_percent_preserved': percent_values,
                    'matlab_parser_check': 'PENDING_ROOT_RUNTIME_CHECK'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--part', choices=PARTS, required=True)
    args = parser.parse_args()
    part = args.part
    source = ROOT/'支撑材料'/part
    before = QA/'before'/part
    candidate = QA/'candidate'/part
    if before.exists() or candidate.exists():
        raise RuntimeError('Snapshots already exist; refusing to overwrite: ' + part)
    shutil.copytree(source, before)
    shutil.copytree(before, candidate)
    records = []
    for path in sorted(candidate.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(candidate)
        original = (before/relative).read_bytes()
        detail = {'language': None, 'comment_count': 0, 'docstring_count': 0, 'status': 'UNCHANGED_NON_SOURCE'}
        if path.suffix.lower() == '.py':
            text, detail = strip_python(original.decode('utf-8-sig'), str(relative))
            path.write_bytes(text.encode('utf-8'))
        elif path.suffix.lower() == '.m':
            text, detail = strip_matlab(original.decode('utf-8-sig'), str(relative))
            path.write_bytes(text.encode('utf-8'))
        elif path.name == 'requirements.txt':
            lines = original.decode('utf-8-sig').splitlines()
            removed = [i for i, line in enumerate(lines, 1) if line.lstrip().startswith('#')]
            clean = [line for line in lines if not line.lstrip().startswith('#')]
            path.write_bytes(('\n'.join(clean)+'\n').encode('utf-8'))
            detail = {'language': 'pip requirements', 'comment_count': len(removed), 'docstring_count': 0,
                      'comments': removed, 'dependency_lines_identical': True, 'remaining_comment_count': 0}
        elif path.suffix.lower() in ['.ps1', '.mjs']:
            detail = {'language': path.suffix.lower(), 'status': 'PENDING_NATIVE_PARSER'}
        updated = path.read_bytes()
        records.append({'path': f'{part}/{relative.as_posix()}', 'before_bytes': len(original), 'after_bytes': len(updated),
                        'before_sha256': sha(original), 'after_sha256': sha(updated), 'changed': original != updated, **detail})
    if part == '03_程序代码':
        manifest = candidate/'input_manifest.csv'
        with manifest.open('r', encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.DictReader(stream))
        modifications = []
        for row in rows:
            path = candidate/row['path']
            data = path.read_bytes()
            if row['sha256'] != sha(data):
                if row['path'] != 'reference/reference_data.py':
                    raise AssertionError('Unexpected input change: ' + row['path'])
                modifications.append({'path': row['path'], 'old': dict(row)})
                row.update(bytes=str(len(data)), sha256=sha(data))
                modifications[-1]['new'] = dict(row)
        with manifest.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=['path','bytes','sha256'])
            writer.writeheader()
            writer.writerows(rows)
        entry = next(r for r in records if r['path'].endswith('/input_manifest.csv'))
        data = manifest.read_bytes()
        entry.update(after_bytes=len(data), after_sha256=sha(data), changed=entry['before_sha256'] != sha(data),
                     status='REFERENCE_SOURCE_HASH_UPDATED', reference_hash_changes=modifications)
    write_json(QA/('strip_'+part+'_audit.json'), {'scope': part, 'records': records,
                'original_source_modified': False, 'all_files_read': True, 'algorithm_changes': False,
                'runtime_testing': 'PENDING_ROOT_SANDBOX', 'comments_total':sum(r.get('comment_count',0) for r in records),
                'docstrings_total':sum(r.get('docstring_count',0) for r in records)})
    print(json.dumps({'part': part, 'files': len(records), 'python_files': sum(r.get('language')=='Python' for r in records),
                      'comments': sum(r.get('comment_count',0) for r in records), 'docstrings':sum(r.get('docstring_count',0) for r in records),
                      'pending_parsers':[r['path'] for r in records if r.get('status')=='PENDING_NATIVE_PARSER']},ensure_ascii=False))


if __name__ == '__main__':
    main()
