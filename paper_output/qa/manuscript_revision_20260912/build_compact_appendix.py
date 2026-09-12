"""Build a prose-and-excerpts QA draft; never import or run production models."""
from pathlib import Path
import ast
import hashlib
import io
import json
import re
import tokenize
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
QA = Path(__file__).resolve().parent
ORIGINAL_MANIFEST = ROOT / 'paper_output/qa/manuscript_20260912/code_appendix_manifest.json'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def ranges(numbers):
    result = []
    for number in sorted(numbers):
        if result and number == result[-1][1] + 1:
            result[-1][1] = number
        else:
            result.append([number, number])
    return result

definitions = [
    {'id': 'D.1', 'title': '题给物性', 'file': 'drying_core.py',
     'ranges': [[108, 126], [131, 131]], 'context': 'RadialModel.properties',
     'omission': '省略第127—130行仅供验证使用的constant_D与constant_thermal覆盖；第110行只删除行尾注释。其余物性关键语句按原文保留。'},
    {'id': 'D.2', 'title': '环形权重与内部面通量', 'file': 'drying_core.py',
     'ranges': [[76, 80], [133, 135], [145, 145], [150, 157], [159, 159]],
     'context': 'RadialModel.__init__ 的网格段、harmonic、water_internal_flux 的Kirchhoff段',
     'omission': '所列三处上下文分段合列；省略第81—132行其他初始化与物性、第136—144行稀疏模式、第146—149行调和水通量/模式分支和第158行注释。仅展示已选Kirchhoff路径。'},
    {'id': 'D.3', 'title': '材料控制体的守恒右端', 'file': 'drying_core.py',
     'ranges': [[161, 161], [164, 173], [180, 184]], 'context': 'RadialModel.rhs',
     'omission': '省略第162行docstring、第163行调用计数和第174—179行可选表面潜热情景；基线surface_latent_fraction=0。中心通量由零数组直接表示。'},
    {'id': 'D.4', 'title': '稀疏装配与容量导数', 'file': 'analytic_jacobian.py',
     'ranges': [[76, 77], [138, 139], [145, 145], [157, 164]], 'context': 'jacobian 的容量、几何尺度和稀疏行列装配段',
     'omission': '只摘四处关键装配语句；rho_c、cp_c按式(29)前后给出的物性导数，heat_deriv、water_deriv按式(25)—(28)，heat_g按式(24)边界构造。省略其余面偏导构造、add_face辅助函数、边界行、CSC转换及全部自检；相应公式和边界偏导在附录B保留。'},
    {'id': 'D.5', 'title': 'BDF 分段、事件与真实后延伸', 'file': 'drying_core.py',
     'ranges': [[306, 318], [320, 333], [336, 337], [339, 342], [345, 346], [349, 350]],
     'context': '_solve_case_impl 的求解主体',
     'omission': '省略第319、338行注释，第334—335、343—344、347—348行缓存存储或断点整理，及主体之后的Run封装与诊断。保留首次BDF断点整理以显示DiskBDF上下文；该类保存原始BDF稠密系数，不改变方程。所有存储与断点整理仍在完整生产实现执行。'},
    {'id': 'D.6', 'title': '四位小时上取并核对严格达标', 'file': 'q3_model.py',
     'ranges': [[6, 8], [11, 20]], 'context': 'completion 的候选报告时刻循环',
     'omission': '省略第1—5行说明、导入及空行，第9—10行注释，以及第21—27行结果字典；循环所得report_h为严格报告小时，values仍为原精度含水率。'}
]

def main():
    prior = json.loads(ORIGINAL_MANIFEST.read_text(encoding='utf-8-sig'))
    original = {item['path']: item for item in prior['files']}
    sources = {}
    excerpts = []
    sections = []
    for definition in definitions:
        relative = 'paper_output/code/modeling/' + definition['file']
        source_path = ROOT / relative
        raw = source_path.read_bytes()
        digest = sha(raw)
        if digest != original[relative]['sha256'] or digest != original[relative]['frozenProductionSha256']:
            raise ValueError('Production hash mismatch: ' + relative)
        source = raw.decode('utf-8-sig')
        lines = source.splitlines()
        sources[relative] = {'path': relative, 'absolutePath': source_path.as_posix(),
            'sha256': digest, 'frozenProductionSha256': original[relative]['frozenProductionSha256'],
            'matchesFrozenProduction': True, 'originalLineCount': len(lines)}
        tree = ast.parse(source)
        banned = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                banned.update(range(node.lineno, node.end_lineno + 1))
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                body = node.body
                if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                    banned.update(range(body[0].lineno, body[0].end_lineno + 1))
        comments = {token.start[0]: token.start[1] for token in tokenize.generate_tokens(io.StringIO(source).readline) if token.type == tokenize.COMMENT}
        selected = [n for left, right in definition['ranges'] for n in range(left, right + 1)]
        mappings = []
        for number in selected:
            text = lines[number - 1]
            if number in banned or not text.strip():
                raise ValueError(f'Forbidden blank/import/docstring line selected: {relative}:{number}')
            removed_comment = number in comments
            if removed_comment:
                text = text[:comments[number]].rstrip()
            if not text.strip():
                raise ValueError('Comment-only line selected')
            mappings.append({'originalLine': number, 'originalText': lines[number - 1],
                             'withoutComment': text, 'inlineCommentRemoved': removed_comment})
        indentation = min(len(item['withoutComment']) - len(item['withoutComment'].lstrip(' ')) for item in mappings)
        snippet_lines = []
        for index, item in enumerate(mappings, 1):
            text = item.pop('withoutComment')[indentation:]
            item.update({'snippetLine': index, 'text': text})
            snippet_lines.append(text)
        snippet = '\n'.join(snippet_lines) + '\n'
        excerpt = {**definition, 'sourcePath': relative, 'sourceAbsolutePath': source_path.as_posix(),
                   'sourceSha256': digest, 'selectedOriginalRanges': definition['ranges'],
                   'omittedOriginalRanges': ranges(set(range(1, len(lines) + 1)) - set(selected)),
                   'lineCount': len(snippet_lines), 'snippetSha256Utf8Lf': sha(snippet.encode()),
                   'commonLeadingSpacesRemoved': indentation, 'lineMap': mappings,
                   'independentlyRunnable': False, 'localDependenciesRequired': True}
        excerpts.append(excerpt)
        line_label = '、'.join(str(a) if a == b else f'{a}—{b}' for a, b in definition['ranges'])
        sections.append(f"### {definition['id']} {definition['title']}\n\n"
                        f"来源：{definition['file']}，原始行 {line_label}；共 {len(snippet_lines)} 行，SHA-256 见表D1。上下文：{definition['context']}。\n\n"
                        f"{definition['omission']}\n\n```python\n{snippet}```\n")
    total = sum(item['lineCount'] for item in excerpts)
    if not 100 <= total <= 150:
        raise ValueError(f'Snippet line count outside requested range: {total}')
    source_table = '\n'.join(['表D1 算法片段来源；三份源文件均位于 paper_output/code/modeling。', '',
        '| 源文件 | 原始文件 SHA-256 |', '|---|---|'] +
        [f"| {Path(key).name} | {item['sha256']} |" for key, item in sources.items()])
    prose_path = QA / 'compact_appendix_prose.md'
    prose = prose_path.read_text(encoding='utf-8')
    manuscript = prose.replace('{{SOURCE_TABLE}}', source_table).replace('{{SNIPPETS}}', '\n'.join(sections))
    final_path = QA / 'compact_appendix.md'
    final_path.write_text(manuscript, encoding='utf-8', newline='\n')
    equation_numbers = [int(number) for number in re.findall(r'\\mathrm\{\((\d+)\)\}', manuscript)]
    if equation_numbers != list(range(20, 36)):
        raise ValueError('Appendix equation sequence mismatch: ' + repr(equation_numbers))
    references = [int(number) for number in re.findall(r'式\((\d+)\)', manuscript)]
    if any(number not in range(1, 36) for number in references):
        raise ValueError('Invalid equation reference')
    report = {
        'generatedAtUtc': datetime.now(timezone.utc).isoformat(),
        'status': 'PASS_STATIC_EXCERPT_FIDELITY',
        'scope': 'User-requested compact appendix draft; physical/numerical derivations and selected core algorithm statements only.',
        'outputs': {'markdown': final_path.as_posix(), 'markdownSha256': sha(final_path.read_bytes())},
        'sourcePolicy': 'Current original production files; each whole-file byte hash matches frozen final_v6a entry in prior production appendix manifest.',
        'supersedesPriorFullListingRequirement': True,
        'policyReason': 'Current user explicitly requests necessary algorithm excerpts rather than complete files.',
        'sourceManifest': {'path': ORIGINAL_MANIFEST.as_posix(), 'sha256': sha(ORIGINAL_MANIFEST.read_bytes())},
        'writingEvidence': [
            'paper_output/final_paper_source.md: original verified appendices A-C and body equations 1-19',
            'paper_output/qa/manuscript_20260912/appendix_derivation_research.md',
            'paper_output/qa/manuscript_20260912/appendix_numerical_process.md',
            'paper_output/qa/manuscript_20260912/independent_numbers_formula_audit.md'],
        'bodyUnchangedByThisTask': True, 'modelsRerun': False,
        'equationNumbers': equation_numbers,
        'requiredCrossReferences': {'A.2': 'Effective density/current volume incompatibility', 'A': 'Material derivative cancellation and dry mass integral', 'B': 'Residual, sparse matrix, boundary derivatives', 'C': 'Grid/time settings, Bessel benchmark and sampling, strict report and error scope'},
        'sources': list(sources.values()), 'snippetCount': len(excerpts), 'codeLineCount': total,
        'transformationsAllowed': ['Select documented original line ranges', 'Remove comments/docstrings/imports/blank lines', 'Remove uniform leading indentation within each snippet'],
        'notChanged': ['Identifiers', 'Numerical constants', 'Operators', 'Order of selected original statements'],
        'fidelityVerified': True, 'allWholeSourceHashesMatchFrozenProduction': True,
        'pageBudget': {'targetTotal': [8, 10], 'derivations': [3, 4], 'processAndError': [1, 2], 'algorithm': [2, 3], 'renderedHere': False, 'limitation': 'Content budget only; actual page count requires integration and DOCX/PDF rendering.'},
        'notes': ['Excerpts require original context and are not standalone programs.', 'No complete validation, plotting, export or historical source file is embedded.', 'Complete source package remains separate supporting material.'],
        'snippets': excerpts
    }
    (QA / 'snippet_manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'snippets': len(excerpts), 'codeLines': total,
                      'equations': equation_numbers, 'cjkCharacters': len(re.findall('[\u4e00-\u9fff]', manuscript)),
                      'markdownSha256': report['outputs']['markdownSha256']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
