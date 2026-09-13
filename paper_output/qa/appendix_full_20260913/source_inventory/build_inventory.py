from __future__ import annotations
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import tokenize

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
SUPPORT=ROOT/'支撑材料'
COMMENT_QA=ROOT/'paper_output/qa/comment_sandbox_20260913'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read_json=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
frozen=read_json(COMMENT_QA/'final_delivery_audit.json')
strip=read_json(COMMENT_QA/'strip_final_audit.json')
vm=read_json(COMMENT_QA/'verification_work/windows_sandbox_verification_matrix.json')
vm_rows={r['file']:r for r in vm['files']}
strip_rows={r['path']:r for r in strip['records']}
purpose03={
 'runDelivery.py':'独立生产入口：输入预检、三条轨迹调度、四题结果导出、完整回读及冻结数值参照对照',
 'q1Model.py':'问题一的附录2物性与1800秒求解设置',
 'q2Model.py':'问题二与问题三共用的附录3物性及固定半径轨迹设置',
 'q3Model.py':'连续全域阈值事件、0.0001小时格点上的严格达标时刻与原精度核验',
 'q4Model.py':'问题四的附录4物性、观测半径收缩及正式网格设置',
 'dryingCore.py':'材料坐标径向控制体、热湿物性、Kirchhoff水通量、BDF积分、状态查询、诊断及保存',
 'analyticJacobian.py':'非线性径向模型的解析稀疏Jacobian及有限差分自检',
 'diskDense.py':'原精度BDF稠密多项式磁盘缓存、查询及释放',
 'exportOutputs.py':'按题目模板生成四问工作簿、原精度归档、正文表，并进行完整回读校验',
 'reference/reference_data.py':'final_v6a冻结数值参照的Python纯数据常量',
 'runLogged.ps1':'独立入口的Windows辅助监督与真实退出码留存'
}
purpose05={}
original05={}
text=(SUPPORT/'05_数值检验与实验/源码文件与校验值.txt').read_text(encoding='utf-8-sig')
for block in re.split(r'(?=^\d+\. )',text,flags=re.M):
    match=re.match(r'^\d+\. ([^\r\n]+)',block)
    if match:
        purpose05[match.group(1)]=re.search(r'^用途：([^\r\n]+)',block,re.M).group(1)
        original05[match.group(1)]=re.search(r'^来源：([^\r\n]+)',block,re.M).group(1)
files=[]
for record in frozen['formalFiles']:
    path=SUPPORT/record['path']
    if not path.is_file() or sha(path)!=record['sha256'] or path.stat().st_size!=record['bytes']:
        raise AssertionError('Formal material changed: '+record['path'])
    files.append({**record,'absolute_path':str(path),'group':Path(record['path']).parts[0] if len(Path(record['path']).parts)>1 else '根目录说明'})
assert len(files)==106
order03=list(purpose03)
source_records=[r for r in frozen['formalFiles'] if Path(r['path']).suffix.lower() in {'.py','.m','.mjs','.ps1'}]
source_records.sort(key=lambda r:(0,order03.index(r['path'].removeprefix('03_程序代码/'))) if r['path'].startswith('03_程序代码/') else (1,r['path']))
entries=[]
for number,record in enumerate(source_records,1):
    relative=record['path'];path=SUPPORT/relative
    raw=path.read_bytes();text=raw.decode('utf-8-sig');language={'.py':'Python','.m':'MATLAB','.mjs':'JavaScript','.ps1':'PowerShell'}[path.suffix]
    assert sha(path)==strip_rows[relative]['after_sha256']
    checks={'matches_comment_stripped_frozen_candidate':True}
    if language=='Python':
        tree=ast.parse(text,filename=relative)
        tokens=list(tokenize.generate_tokens(io.StringIO(text).readline))
        assert not any(t.type==tokenize.COMMENT for t in tokens)
        assert not any(isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str) for n in ast.walk(tree))
        compile(text,relative,'exec')
        checks.update(python_compile='PASS',comment_tokens=0,standalone_string_expressions=0,
                      function_count=sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) for n in ast.walk(tree)),
                      class_count=sum(isinstance(n,ast.ClassDef) for n in ast.walk(tree)))
    if relative.startswith('03_程序代码/'):
        key=relative.removeprefix('03_程序代码/')
        purpose=purpose03[key]
        role='正式采用：生产求解、导出或数值参照'
        execution='Windows Sandbox正式Q1/Q23 N3200、Q4 N6400，全量程序内部PASS；本文件与运行版本SHA一致'
        if path.suffix=='.ps1':
            role='复现辅助入口'
            execution='Windows Sandbox Windows PowerShell5.1原脚本quick三轨迹及四题导出/回读，稳定重试真实退出0、内部PASS'
        limitation='数值复现不代表真实物理预测精度；Visual Studio只完成打开、断点及单步，团队人工审查另行完成'
        original=str(path)
    else:
        key=relative.removeprefix('05_数值检验与实验/')
        purpose=purpose05[key];original=str(ROOT/original05[key])
        row=vm_rows[path.name]
        execution=row['windowsSandboxStatus']
        limitation=row['windowsSandboxScope']
        role='检验与历史诊断'
        if '失败' in execution or '未全通过' in execution or '不符合' in execution or '未执行' in execution:
            role='保留用于追溯的未通过、受限或未执行检验'
        checks['tested_path_adaptation_required']=row.get('windowsSandboxTestedSha256') not in {None,record['sha256']}
        checks['vm_tested_source_sha256']=row.get('windowsSandboxTestedSha256')
    entry={'id':f'SRC{number:03d}','relative_path':relative,'display_path':relative,'language':language,
           'sha256':record['sha256'],'bytes':len(raw),'lines':len(text.splitlines()),
           'purpose':purpose,'adoption_scope':role,'execution_scope':execution,'limitations':limitation,
           'absolute_path':str(path),'original_absolute_path':original,
           'appendix_source_path':str(path),'source_text_encoding':'utf-8-sig','complete_source':True,
           'in_current_support':True,'verification':checks}
    entries.append(entry)
assert len(entries)==44
manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'status':'BASE44_READY_EXTRA_FIGURE_SOURCES_UNDER_REVIEW',
          'current_support_root':str(SUPPORT),'current_formal_support_count':len(files),
          'base_source_count':44,'source_count':len(entries),'total_source_lines':sum(e['lines'] for e in entries),
          'languages':dict(Counter(e['language'] for e in entries)),
          'basis':{'formal_delivery_audit':str(COMMENT_QA/'final_delivery_audit.json'),
                   'formal_delivery_audit_sha256':sha(COMMENT_QA/'final_delivery_audit.json'),
                   'windows_sandbox_matrix':str(COMMENT_QA/'verification_work/windows_sandbox_verification_matrix.json'),
                   'windows_sandbox_matrix_sha256':sha(COMMENT_QA/'verification_work/windows_sandbox_verification_matrix.json')},
          'entries':entries,'formal_support_files':files,'extra_figure_sources':[],
          'not_included':['用户另行编写的AI工具使用详情','本机VS缓存与升级日志','稿件排版工具','未采用的历史62份源码整包'],
          'reading_scope':'Every current source file fully read, SHA-bound and parsed where applicable; no new numerical solve'}
(OUT/'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':manifest['status'],'source_count':len(entries),'source_lines':manifest['total_source_lines'],'support_files':len(files)},ensure_ascii=False))
