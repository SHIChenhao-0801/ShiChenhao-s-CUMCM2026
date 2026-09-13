from __future__ import annotations
import hashlib
import importlib.util
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import zipfile

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
jread=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
spec=importlib.util.spec_from_file_location('verified_strip',ROOT/'paper_output/qa/comment_sandbox_20260913/strip_sources.py')
strip=importlib.util.module_from_spec(spec)
spec.loader.exec_module(strip)
manifest=jread(OUT/'source_manifest.json')
manifest['entries']=manifest['entries'][:44]
extras=[
 ('paper_output/code/data/prepare_a_data.py','Python','从官方附件1/2核查字段、时间及有限性，换算单位并导出正式观测CSV和原始观测图','正式输入预处理；原始观测图不是本稿最终六图'),
 ('tools/export_six_figure_package_20260912.py','Python','从冻结NPZ/JSON与观测CSV导出六图14张数据表，保留原精度、实际半径、事件与情景口径','正式六图数据预处理；不重新积分'),
 ('paper_output/figures/review_20260913/draw_figures.R','R','读取六图14张CSV，核验坐标范围和关键值，绘制六张PNG/PDF/SVG及合并PDF','当前正文六图绘图实现；不重新积分')]
checks=[]
for number,(relative,language,purpose,scope) in enumerate(extras,45):
    path=ROOT/relative
    original=path.read_bytes().decode('utf-8-sig')
    destination=OUT/'extra_sources'/path.name
    if language=='Python':
        clean,audit=strip.strip_python(original,relative)
        destination.write_text(clean,encoding='utf-8')
    else:
        clean=destination.read_text(encoding='utf-8-sig')
        audit={'language':'R','native_parse':'PASS','parse_expression_equal_without_source':True,'comment_count':3,'remaining_comment_count':0,'proof':str(OUT/'r_strip_check.txt')}
        assert 'parse_expression_equal_without_source=TRUE' in (OUT/'r_strip_check.txt').read_text(encoding='utf-8')
    audit.update(original_path=str(path),original_sha256=sha(path),appendix_source_sha256=sha(destination),original_bytes=path.stat().st_size,appendix_source_bytes=destination.stat().st_size)
    checks.append(audit)
    evidence=[]
    if number==45:
        record_path=ROOT/'paper_output/data_cleaned/A_data_run_record.json'
        record=jread(record_path)
        assert record['status']=='PASS' and record['source_code_sha256']==sha(path)
        evidence.append({'path':str(record_path),'sha256':sha(record_path),'original_source_sha_verified':True,'status':record['status']})
        execution='原版脚本历史实跑PASS，运行记录源码SHA与现文件一致；本附录去注释副本仅重新做语法及非注释AST等价检查'
        limitation='保留原工作区层级及input_manifest.json依赖；不属于03独立入口，未对该副本执行Windows Sandbox重跑'
    elif number==46:
        record_path=ROOT/'paper_output/qa/figure_package_20260912/final_package_audit.json'
        record=jread(record_path)
        evidence.append({'path':str(record_path),'sha256':sha(record_path),'historical_artifact_audit':True})
        execution='原版数据包已历史导出并核对14表、4627行和15689数据格；本附录去注释副本语法及非注释AST等价PASS'
        limitation='依赖原项目路径、冻结结果和build_manifest.json来源索引；旧记录未保存该导出脚本SHA，不能把产物审计表述为当前源码逐字节实跑证据；未在Windows Sandbox重跑'
    else:
        record_path=ROOT/'paper_output/figures/review_20260913/R_run.log'
        evidence.append({'path':str(record_path),'sha256':sha(record_path),'historical_figure_run':True})
        execution='R4.6.1原版已实际生成六图，既有数值与轴范围检查PASS；本附录副本R原生解析和去注释表达式等价PASS'
        limitation='依赖原项目绘图目录、14张CSV及Windows中文字体；旧运行日志未绑定原脚本SHA，本次未重画或在Windows Sandbox执行R'
    entry={'id':f'SRC{number:03d}','relative_path':relative,'display_path':'补充源码/'+relative,
           'language':language,'sha256':sha(destination),'bytes':destination.stat().st_size,'lines':len(clean.splitlines()),
           'purpose':purpose,'adoption_scope':scope,'execution_scope':execution,'limitations':limitation,
           'absolute_path':str(destination),'original_absolute_path':str(path),'original_sha256':sha(path),
           'appendix_source_path':str(destination),'source_text_encoding':'utf-8-sig','complete_source':True,
           'in_current_support':False,'verification':audit,'existing_evidence':evidence}
    manifest['entries'].append(entry)

figure_root=ROOT/'paper_output/figures/review_20260913'
paper=ROOT/'paper_output/paper/药材热湿耦合模型与干燥时间计算_格式与语言修订版.docx'
figure_hashes={sha(p):p for p in figure_root.glob('图*') if p.suffix.lower() in {'.svg','.png'}}
media=[]
with zipfile.ZipFile(paper) as z:
    for member in z.namelist():
        if member.startswith('word/media/'):
            raw=z.read(member);digest=hashlib.sha256(raw).hexdigest();match=figure_hashes.get(digest)
            media.append({'docx_member':member,'sha256':digest,'bytes':len(raw),'matched_r_output':str(match) if match else None})
matched_figures=sorted({Path(m['matched_r_output']).stem for m in media if m['matched_r_output']})
csv_records=[]
for p in sorted((figure_root/'input_data/CSV').rglob('*.csv')):
    relative=p.relative_to(figure_root/'input_data/CSV')
    predecessor=ROOT/'paper_output/handoff/six_figures_20260912/CSV'/relative
    assert sha(p)==sha(predecessor)
    csv_records.append({'file':str(p),'sha256':sha(p),'matches_exported_csv':True})
assert len(csv_records)==14
figure_binding={'paper_path':str(paper),'paper_sha256':sha(paper),'media':media,'matched_figure_stems':matched_figures,'input_csv_count':14,'input_csvs':csv_records}
(OUT/'figure_source_binding.json').write_text(json.dumps(figure_binding,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'extra_comment_removal_audit.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest.update(status='READY',finalized_utc=datetime.now(timezone.utc).isoformat(),source_count=len(manifest['entries']),total_source_lines=sum(e['lines'] for e in manifest['entries']),languages=dict(Counter(e['language'] for e in manifest['entries'])),extra_figure_sources=[e['id'] for e in manifest['entries'][44:]])
manifest['coverage']={'base':'全部当前44份正式支撑源码，逐文件完整读取，与已去注释冻结候选SHA相同','extras':'追加原始输入预处理、冻结六图CSV导出和最终R绘图3份；不改变正式支撑106文件','excludes':'旧版本副本、Word排版和资料包Excel展示工具未作为建模源码追加；未将失败检验改写成成功','latest_paper_media_direct_match_count':len(matched_figures),'complete_code_count':47,'extra_strip_validation':'两份Python非注释AST相同，R原生parse去源位置信息后的表达式相同；算法与字符串不改动'}
(OUT/'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'READY','sources':len(manifest['entries']),'lines':manifest['total_source_lines'],'languages':manifest['languages'],'direct_figure_matches':matched_figures},ensure_ascii=False))
