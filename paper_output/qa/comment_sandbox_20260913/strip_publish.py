from __future__ import annotations
import argparse
import ast
import copy
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tokenize
import traceback

QA = Path(__file__).resolve().parent
ROOT = QA.parents[2]
SUPPORT = ROOT/'支撑材料'
SOURCE_EXTENSIONS = {'.py', '.m', '.mjs', '.ps1'}
NODE = Path('C:/Users/Shi Chenhao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
BABEL = Path('C:/Users/Shi Chenhao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/lib/transform/babelBundle.js')


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def utc():
    return datetime.now(timezone.utc).isoformat()


def save_log(path, report):
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def safe_file(base, relative):
    rel = Path(relative)
    if rel.is_absolute() or '..' in rel.parts or rel.parts[0] not in {'03_程序代码', '05_数值检验与实验'}:
        raise RuntimeError('Unexpected publication path: ' + relative)
    path = base/rel
    if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(base.resolve()):
        raise RuntimeError('Missing, linked, or out-of-bound file: ' + str(path))
    ancestor = path.parent
    while ancestor != base:
        if ancestor.is_symlink():
            raise RuntimeError('Symlinked parent is not a publication destination: ' + str(ancestor))
        ancestor = ancestor.parent
    return path


def verify_python(original, current, relative):
    from strip_sources import DropDocs, doc_node
    old = ast.parse(original.decode('utf-8-sig'),filename=relative)
    text = current.decode('utf-8-sig')
    new = ast.parse(text,filename=relative)
    comments = [t for t in tokenize.generate_tokens(io.StringIO(text).readline) if t.type == tokenize.COMMENT]
    docs = [n for n in ast.walk(new) if doc_node(n) is not None]
    standalone = [n for n in ast.walk(new) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str)]
    if comments or docs or standalone:
        raise AssertionError('Python comments/docstrings remain: ' + relative)
    expected = ast.dump(DropDocs().visit(copy.deepcopy(old)),include_attributes=False)
    actual = ast.dump(new,include_attributes=False)
    if expected != actual:
        raise AssertionError('Non-comment Python AST changed: ' + relative)
    compile(text,relative,'exec')
    return {'parser':'Python tokenize/ast/compile', 'comment_count':0, 'docstring_count':0,
            'standalone_string_expression_count':0, 'noncomment_ast_equivalent':True,
            'normalized_ast_sha256':sha_bytes(actual.encode()), 'syntax':'PASS'}


def verify_javascript(original, current):
    payload = {'before':original.decode('utf-8-sig'),'after':current.decode('utf-8-sig'),'babel':str(BABEL)}
    script = """
const fs=require('node:fs');
const p=JSON.parse(fs.readFileSync(0,'utf8'));
const {babelParse}=require(p.babel);
const a=babelParse(p.before,'before.mjs',true), b=babelParse(p.after,'after.mjs',true);
function strip(x) {
 if(Array.isArray(x)) return x.map(strip);
 if(!x || typeof x!=='object') return x;
 const y={}; for(const [k,v] of Object.entries(x)) {
  if(!['comments','leadingComments','trailingComments','innerComments','loc','start','end','extra','tokens'].includes(k)) y[k]=strip(v);
 } return y;
}
if(b.comments.length) throw Error('Comments remain');
if(JSON.stringify(strip(a))!==JSON.stringify(strip(b))) throw Error('Non-comment AST changed');
console.log(JSON.stringify({parser:'Babel',comment_count:0,noncomment_ast_equivalent:true,syntax:'PASS'}));
"""
    process = subprocess.run([str(NODE),'-e',script],input=json.dumps(payload,ensure_ascii=False),
                             text=True,encoding='utf-8',capture_output=True,cwd=ROOT,check=False)
    if process.returncode:
        raise RuntimeError('JavaScript parser failure: ' + process.stderr)
    return json.loads(process.stdout)


def verify_powershell(before, target):
    interpreter = shutil.which('pwsh')
    if interpreter is None:
        raise RuntimeError('PowerShell 7 parser is unavailable; refusing unverifiable publication')
    process = subprocess.run([interpreter,'-NoProfile','-File',str(QA/'strip_publish_pscheck.ps1'),
                              '-Before',str(before),'-Current',str(target)],text=True,encoding='utf-8',
                             capture_output=True,cwd=ROOT,check=False)
    if process.returncode:
        raise RuntimeError('PowerShell parser failure: ' + process.stderr)
    return json.loads(process.stdout)


def verify_entry(record, target):
    original = (QA/'before'/record['path']).read_bytes()
    current = target.read_bytes()
    if sha_bytes(current) != record['after_sha256']:
        raise AssertionError('Published bytes differ from frozen candidate: ' + record['path'])
    suffix = target.suffix.lower()
    if suffix == '.py':
        checks = verify_python(original,current,record['path'])
    elif suffix == '.mjs':
        checks = verify_javascript(original,current)
    elif suffix == '.ps1':
        checks = verify_powershell(QA/'before'/record['path'],target)
    elif suffix == '.m':
        from strip_sources import strip_matlab
        expected, detail = strip_matlab(original.decode('utf-8-sig'),record['path'])
        if expected.encode('utf-8') != current:
            raise AssertionError('MATLAB non-comment bytes changed: ' + record['path'])
        checks = {'parser':'Observed MATLAB comment-form lexical validation','comment_count':0,
                  'noncomment_content_matches_frozen_candidate':True,
                  'quoted_percent_format_strings_preserved':detail['format_strings_with_percent_preserved'],
                  'runtime':'NOT_PERFORMED_BY_PUBLISHER'}
    elif target.name == 'requirements.txt':
        expected = [v for v in original.decode('utf-8-sig').splitlines() if not v.lstrip().startswith('#')]
        actual = current.decode('utf-8-sig').splitlines()
        if expected != actual or any(v.lstrip().startswith('#') for v in actual):
            raise AssertionError('Dependencies changed beyond comment removal')
        checks = {'parser':'requirements line comparison','comment_count':0,'dependencies_unchanged':True}
    else:
        checks = {'role':'input_manifest','check':'Frozen CSV copied; 12 referenced inputs verified separately'}
    return {'path':record['path'],'sha256':sha_bytes(current),'bytes':len(current),'checks':checks}


def main():
    parser = argparse.ArgumentParser(description='Publish only frozen comment-stripped support sources after exact before-SHA checks.')
    parser.add_argument('--apply',action='store_true',help='Perform the restricted publication. Without this flag only preflight and candidate parser checks run.')
    args = parser.parse_args()
    audit = read_json(QA/'strip_final_audit.json')
    records = [r for r in audit['records'] if Path(r['path']).suffix.lower() in SOURCE_EXTENSIONS
               or r['path'] in {'03_程序代码/requirements.txt','03_程序代码/input_manifest.csv'}]
    records.sort(key=lambda r:(r['path'].endswith('/input_manifest.csv'),r['path']))
    sources = [r for r in records if Path(r['path']).suffix.lower() in SOURCE_EXTENSIONS]
    if len(records) != 46 or len(sources) != 44:
        raise AssertionError('Expected exactly 44 source files, requirements, and input_manifest.csv')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    log_path = QA/('strip_publish_'+('apply_' if args.apply else 'preflight_')+stamp+'.json')
    report = {'mode':'APPLY' if args.apply else 'PREFLIGHT_ONLY','startedAtUtc':utc(),'status':'CHECKING',
              'allowedFileCount':46,'sourceFileCount':44,'sourceAuditSha256':sha_bytes((QA/'strip_final_audit.json').read_bytes()),
              'scope':'Only frozen comment-stripped candidate files; no ROOT adaptations or new algorithms',
              'beforeShaRequired':True,'preflight':[],'published':[],'postChecks':[],
              'excludedFromMutation':['All TXT descriptions','Visual Studio project/solution/metadata','Every other support file'],
              'numericalRuntimeClaim':'NONE; runtime results are independently recorded elsewhere'}
    save_log(log_path,report)
    try:
        for r in records:
            candidate = safe_file(QA/'candidate',r['path'])
            before = safe_file(QA/'before',r['path'])
            target = safe_file(SUPPORT,r['path'])
            for label,path,expected in [('candidate',candidate,r['after_sha256']),('before snapshot',before,r['before_sha256']),
                                        ('current support',target,r['before_sha256'])]:
                actual = sha_bytes(path.read_bytes())
                if actual != expected:
                    raise RuntimeError(label+' SHA changed; no overwrite permitted: '+r['path']+
                                       ' expected='+expected+' actual='+actual)
            check = verify_entry(r,candidate)
            report['preflight'].append({'path':r['path'],'beforeSha256':r['before_sha256'],
                                        'candidateSha256':r['after_sha256'],'candidateCheck':check['checks']})
        report['status'] = 'PREFLIGHT_PASS'
        save_log(log_path,report)
        if args.apply:
            for r in records:
                target = safe_file(SUPPORT,r['path'])
                payload = safe_file(QA/'candidate',r['path']).read_bytes()
                if sha_bytes(payload) != r['after_sha256']:
                    raise RuntimeError('Candidate changed during publication: '+r['path'])
                if sha_bytes(target.read_bytes()) != r['before_sha256']:
                    raise RuntimeError('User file changed after preflight; refusing overwrite: '+r['path'])
                changed = r['before_sha256'] != r['after_sha256']
                if changed:
                    temp_path = None
                    try:
                        with tempfile.NamedTemporaryFile(mode='wb',prefix='.comment_publish_',suffix='.tmp',
                                                         dir=target.parent,delete=False) as stream:
                            temp_path = Path(stream.name)
                            stream.write(payload)
                            stream.flush()
                            os.fsync(stream.fileno())
                        if sha_bytes(target.read_bytes()) != r['before_sha256']:
                            raise RuntimeError('User file changed immediately before replacement: '+r['path'])
                        os.replace(temp_path,target)
                    finally:
                        if temp_path is not None and temp_path.exists():
                            temp_path.unlink()
                report['published'].append({'path':r['path'],'rewritten':changed,'afterSha256':sha_bytes(target.read_bytes())})
                save_log(log_path,report)
            for r in records:
                report['postChecks'].append(verify_entry(r,safe_file(SUPPORT,r['path'])))
            with (SUPPORT/'03_程序代码/input_manifest.csv').open('r',encoding='utf-8-sig',newline='') as stream:
                inputs = list(csv.DictReader(stream))
            if len(inputs) != 12:
                raise AssertionError('Input manifest no longer contains 12 entries')
            for entry in inputs:
                rel = Path(entry['path'])
                if rel.is_absolute() or '..' in rel.parts:
                    raise RuntimeError('Invalid manifest input path')
                path = SUPPORT/'03_程序代码'/rel
                if not path.resolve().is_relative_to((SUPPORT/'03_程序代码').resolve()):
                    raise RuntimeError('Manifest reference escapes package')
                data = path.read_bytes()
                if sha_bytes(data)!=entry['sha256'] or len(data)!=int(entry['bytes']):
                    raise AssertionError('Published input manifest mismatch: '+entry['path'])
            report['inputManifestVerifiedEntries'] = len(inputs)
            report['status'] = 'PUBLISHED_AND_POST_VERIFIED'
        report['finishedAtUtc'] = utc()
        save_log(log_path,report)
        print(json.dumps({'status':report['status'],'log':str(log_path),'published':len(report['published']),
                          'postVerified':len(report['postChecks'])},ensure_ascii=False))
    except BaseException as error:
        report.update(status='REFUSED_OR_PARTIAL_PUBLICATION_FAILURE',finishedAtUtc=utc(),
                      error=repr(error),traceback=traceback.format_exc(),
                      recovery='No automated rollback: do not overwrite possible user edits; use per-file journal and before snapshot')
        save_log(log_path,report)
        raise


if __name__ == '__main__':
    main()
