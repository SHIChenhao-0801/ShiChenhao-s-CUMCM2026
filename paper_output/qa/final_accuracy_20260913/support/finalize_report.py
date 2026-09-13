from pathlib import Path
import json,hashlib,datetime
R=Path('D:/Document/数学建模/2026CUMCM')
Q=R/'paper_output/qa/final_accuracy_20260913/support'
d=json.loads((Q/'support_audit.json').read_text(encoding='utf-8'))
d['status']='ACTION_REQUIRED'
d['metadata_identity_hits']=[{'path':'AI工具使用详情.docx','part':'docProps/core.xml','fields':['dc:creator','cp:lastModifiedBy'],'category':'team_member_name'}]
d['metadata_scope']='All 16 XLSX and 1 DOCX core properties read. Original inputs retain original third-party authors; 4 generated results have blank authors. Only current AI DOCX exposes team author name.'
d['findings']=[
 {'priority':1,'code':'ZIP_CAPACITY','issue':'In-memory DEFLATE-9 estimate exceeds both decimal 20 MB and binary 20 MiB.','bytes':21891321,'archive_written':False},
 {'priority':1,'code':'DOCX_IDENTITY','path':'AI工具使用详情.docx','issue':'Team member name in author and lastModifiedBy metadata; PDF metadata blank.'},
 {'priority':2,'code':'INVENTORY_STALE','issue':'Current 138 files, but both TXT lists and inventory DOCX list 137 and omit AI PDF; explanatory TXT also retains old six-page/three-example/signature status.'},
 {'priority':2,'code':'AI_EXCERPT_WORDING','issue':'Current quoted prompt/reply excerpts differ from stored source_actual_exchange; may be summaries, so label as summaries or restore source wording. No inference of fabrication.'},
 {'priority':2,'code':'AI_DANGLING_EXAMPLE','pdf_page':2,'issue':'References instance 3 after instance 3 was removed.'},
 {'priority':2,'code':'PAPER_SOURCE_MISMATCH','pdf_page':164,'issue':'method_comparison ROOT is old absolute path in appendix and relative to script in current support.'},
 {'priority':1,'code':'OLD_ZIP_STALE','path':'支撑材料临时.zip','issue':'109 files, missing 35 current files, 55 differing common files, six unwanted IDE files; cannot serve as current submission archive.'}
]
d['ai_details']['pdf_pages_visually_checked']=[1,2,3,4,5]
d['ai_details']['visual_result']='No clipped text, overlap, garbled glyphs or broken tables in current five-page PDF. First-page embedded screenshot inspected: no visible team identity, account or absolute path.'
d['ai_details']['pdf_docx_difference_explanation']='The only normalized text differences are five PDF page footers 第1页共5页 through 第5页共5页. Removing them yields exact 2639-character body equality; images separately inspected.'
d['paper_visual_review']={'pdf_sha256':hashlib.sha256((R/'论文.pdf').read_bytes()).hexdigest(),'pages':list(range(145,187)),'method':'11 original-size 4-page montages produced by main agent from current PDF; all images viewed','status':'PASS_VISUAL_WITH_CONTENT_FINDING','content_finding_page':164,'no_clipping_overlap_missing_glyphs':True,'limitations':'Readability check, not a new model verification or user code review.'}
d['finalized_at']=datetime.datetime.now().astimezone().isoformat()
d['snapshot_still_current']=all((R/'支撑材料'/r['path']).exists() and hashlib.sha256((R/'支撑材料'/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in d['files']) and len([p for p in (R/'支撑材料').rglob('*') if p.is_file()])==d['file_count']
(Q/'support_audit.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':d['status'],'file_count':d['file_count'],'snapshot_still_current':d['snapshot_still_current'],'findings':len(d['findings'])},ensure_ascii=False))
