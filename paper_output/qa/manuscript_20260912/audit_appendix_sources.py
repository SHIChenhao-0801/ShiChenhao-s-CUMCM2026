"""Static appendix checks and current legacy/camel AST comparison; no model import."""
import ast
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
report_path = ROOT/'paper_output/code/review_delivery/tools/coreRenameReport.json'
report = json.loads(report_path.read_text(encoding='utf-8-sig'))
builder_path = ROOT/'paper_output/code/review_delivery/tools/buildCamelCopies.py'
builder_tree = ast.parse(builder_path.read_text(encoding='utf-8-sig'))
normalizer_ast = next(n for n in builder_tree.body if isinstance(n,ast.ClassDef) and n.name=='NormalizeTree')
ns = {'ast':ast, 'renameMap':report['identifierMap'], 'pathMap':report['pathMap']}
exec(compile(ast.Module(body=[normalizer_ast],type_ignores=[]),str(builder_path),'exec'),ns)
normalizer = ns['NormalizeTree']
checks = []
for item in report['files']:
    original = ROOT/item['originalPath']
    review = ROOT/item['reviewPath']
    a, b = original.read_bytes(), review.read_bytes()
    original_ast = ast.parse(a.decode('utf-8-sig'))
    normalized = normalizer().visit(ast.parse(b.decode('utf-8-sig')))
    same = ast.dump(original_ast,include_attributes=False)==ast.dump(normalized,include_attributes=False)
    checks.append({'originalPath':item['originalPath'],'reviewPath':item['reviewPath'],
        'originalSha256':hashlib.sha256(a).hexdigest(),'reviewSha256':hashlib.sha256(b).hexdigest(),
        'normalizedAstIdentical':same,
        'originalHashMatchesExistingReport':hashlib.sha256(a).hexdigest()==item['originalSha256'],
        'reviewHashMatchesExistingReport':hashlib.sha256(b).hexdigest()==item['reviewSha256']})
draft_path = OUT/'appendix_derivation_research.md'
text = draft_path.read_text(encoding='utf-8')
chinese = len(re.findall(r'[\u4e00-\u9fff]',text))
math_only_removed = re.sub(r'\$\$.*?\$\$','',text,flags=re.S)
checks_summary = {'status':'PASS' if all(x['normalizedAstIdentical'] for x in checks) else 'FAIL',
    'scope':'static AST comparison and document structure only; no model imported or solved',
    'generatedAtUtc':datetime.now(timezone.utc).isoformat(),'sourcePairs':checks,
    'draft':{'path':draft_path.relative_to(ROOT).as_posix(),
       'sha256':hashlib.sha256(draft_path.read_bytes()).hexdigest(),
       'unicodeChineseCharacterCount':chinese,
       'chineseOutsideDisplayMath':len(re.findall(r'[\u4e00-\u9fff]',math_only_removed)),
       'displayMathPairs':text.count('$$')//2,
       'balancedDisplayMathDelimiters':text.count('$$')%2==0,
       'sections':re.findall(r'^## (.+)$',text,flags=re.M)},
    'knownNonComputationalCorrections':['The old camel loadInputs comment confuses air dry-basis humidity with material dry-basis moisture. The appendix uses the actual CSV field definition.',
        'No mathematical or numerical branch differs after the registered identifier/path normalization.']}
(OUT/'appendix_source_audit.json').write_text(json.dumps(checks_summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':checks_summary['status'],'chineseCharacters':chinese,
    'chineseOutsideMath':checks_summary['draft']['chineseOutsideDisplayMath'],
    'displayMathPairs':checks_summary['draft']['displayMathPairs'],
    'equalModules':sum(x['normalizedAstIdentical'] for x in checks)},ensure_ascii=False))
assert checks_summary['status']=='PASS'
