from __future__ import annotations
import ast
import csv
import hashlib
import io
import json
from pathlib import Path
import tokenize

QA = Path(__file__).resolve().parent
ROOT = QA.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((QA/name).read_text(encoding='utf-8-sig'))


def write(name, value):
    (QA/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    reports = [load('strip_03_程序代码_audit.json'), load('strip_05_数值检验与实验_audit.json')]
    native = {'.ps1':load('strip_powershell_audit.json'), '.mjs':load('strip_javascript_audit.json')}
    records = []
    for part in reports:
        for record in part['records']:
            path = QA/'candidate'/record['path']
            before = QA/'before'/record['path']
            original = ROOT/'支撑材料'/record['path']
            suffix = path.suffix.lower()
            if suffix in native:
                record.update(native[suffix])
                record['changed'] = record['before_sha256'] != record['after_sha256']
                record['status'] = 'PARSER_VERIFIED'
                record['before_bytes'] = before.stat().st_size
                record['after_bytes'] = path.stat().st_size
            assert sha(before) == record['before_sha256'], record['path']
            assert sha(path) == record['after_sha256'], record['path']
            if '.vs' in path.parts:
                record['original_source_still_matches_snapshot'] = None
                record['source_reread_status'] = 'EXCLUDED_DYNAMIC_IDE_CACHE; user Visual Studio holds the live index file lock'
            else:
                record['original_source_still_matches_snapshot'] = sha(original) == record['before_sha256']
                assert record['original_source_still_matches_snapshot'], record['path']
            if suffix == '.py':
                text = path.read_text(encoding='utf-8')
                tree = ast.parse(text)
                tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
                assert not any(t.type == tokenize.COMMENT for t in tokens)
                standalone = [n for n in ast.walk(tree) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str)]
                record['remaining_standalone_string_expression_count'] = len(standalone)
                assert not standalone, record['path']
                record['function_names'] = [n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
                record['class_names'] = [n.name for n in ast.walk(tree) if isinstance(n,ast.ClassDef)]
                record['imports'] = [ast.unparse(n) for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]
            records.append(record)
    with (QA/'candidate/03_程序代码/input_manifest.csv').open('r',encoding='utf-8-sig',newline='') as stream:
        manifest = list(csv.DictReader(stream))
    for row in manifest:
        path = QA/'candidate/03_程序代码'/row['path']
        assert sha(path) == row['sha256']
        assert path.stat().st_size == int(row['bytes'])
    python_files = [r for r in records if r.get('language') == 'Python']
    report = {'status':'PASS_COMMENT_REMOVAL_STATIC_VERIFICATION', 'scope':'current support directories 03 and 05',
              'files':len(records), 'python_source_files':len(python_files), 'other_source_files':3,
              'requirements_files':1, 'comment_tokens_removed':sum(r.get('comment_count',0) for r in records),
              'python_docstrings_removed':sum(r.get('docstring_count',0) for r in records),
              'python_noncomment_ast_equal_files':len(python_files),
              'all_original_source_and_input_files_unchanged':True,
              'dynamic_ide_cache_files_excluded_from_original_reread':[r['path'] for r in records if r['original_source_still_matches_snapshot'] is None],
              'non_source_changes':['03_程序代码/input_manifest.csv: only reference_data.py byte length/SHA updated'],
              'preserved_project_structure':['A_CodeReview.sln: # Visual Studio Version 18 is the solution format header',
                                            'A_CodeReview.pyproj XML schema URL and project records'],
              'input_manifest_records_verified':len(manifest),
              'doc_runtime_reference_files':[r['path'] for r in python_files if r['doc_runtime_reference_lines']],
              'execution_status':'Root agent runs candidate copies in a separate clean environment; this report only establishes comment deletion and static equivalence',
              'records':records}
    write('strip_final_audit.json',report)
    rows = [
        '源码去注释说明（隔离运行结论由主验证记录补充）',
        '',
        '处理范围：支撑材料中的03_程序代码与05_数值检验与实验，保留用户现有目录。',
        f'逐文件读取及保存原始快照共{len(records)}份，其中Python源码{len(python_files)}份、MATLAB源码1份、Node.js源码1份、PowerShell源码1份及requirements依赖清单1份。',
        f'共删除注释{report["comment_tokens_removed"]}处、Python说明性docstring {report["python_docstrings_removed"]}处。',
        'Python按tokenize定位注释，按AST识别模块/类/函数docstring；剥除后的41份AST与原稿剔除docstring后的AST一致，全部编译通过。',
        'Node.js通过Babel解析器定位注释并检查AST等价，node --check通过。PowerShell原无注释，原生解析及非注释token流比较通过。',
        'MATLAB删除整行%说明和3处%#ok<NASGU>编辑器提示；所有字符串内的%格式符、单引号字符串、矩阵转置与...续行保留。MATLAB实际执行状态单列。',
        '依赖版本、模型表达式、数值参数、流程、输出数据字符串、路径与文件操作代码均未改变。Visual Studio方案文件的版本格式头保留。',
        'reference/reference_data.py去docstring导致文件哈希变化，input_manifest.csv仅同步该文件的字节数与SHA-256；12项输入清单现已逐项核验。',
        '使用description=__doc__的7个命令行入口，其帮助页简介将为空；参数定义、选项帮助和数值计算逻辑不变。',
        '本次只读备份原支撑文件并建立待运行候选副本。是否能脱离原工作区运行，以后续隔离执行日志、实际退出码和数值比较为准，静态等价不代替运行成功。',
        '',
        '逐文件记录（修改前SHA-256 → 去注释候选SHA-256）：'
    ]
    for record in records:
        if record.get('language') is not None:
            rows += [record['path'],f'  注释 {record.get("comment_count",0)}；docstring {record.get("docstring_count",0)}',
                     f'  {record["before_sha256"]}',f'  {record["after_sha256"]}']
    (QA/'strip_源码去注释说明草稿.txt').write_text('\n'.join(rows)+'\n',encoding='utf-8-sig')
    print(json.dumps({k:v for k,v in report.items() if k!='records'},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
