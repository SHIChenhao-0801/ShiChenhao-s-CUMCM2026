"""Bind actual independent review artifacts to the immutable delivery."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
ROOT = Path.cwd()
assert ROOT.as_posix() == 'D:/Document/数学建模/2026CUMCM'
QA = ROOT/'paper_output/qa/manuscript_20260912'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(QA/'render_manifest.json')
page_hashes={x['page']:x['sha256'] for x in manifest['pages']}
paths=[QA/'visual_pages_001_037.json',QA/'visual_pages_038_100.json',
       ROOT/'paper_output/qa/visual_pages_101_160.json',QA/'visual_pages_161_218.json']
covered=[]
for path in paths:
    value=read(path)
    for p in value['pages']:
        assert p.get('visuallyInspected',p.get('viewedIndividually',p.get('actuallyViewed',False)))
        h=p.get('currentImageSha256',p.get('v5ImageSha256',p.get('sha256')))
        assert h==page_hashes[p['page']]
        covered.append(p['page'])
assert sorted(covered)==list(range(1,219))
struct=read(QA/'docx_structure_build.json')
source=read(QA/'docx_embedded_source_audit.json')
assert struct['docxSha256']==source['docx']['sha256']==manifest['docxSha256']
assert source['status']=='PASS_SOURCE_LINES'
assert source['sourceFileCount']==42 and source['docxSourceLineCount']==9434
assert struct['sourceFrontTextPreserved'] and struct['commentsAdded']==8
assert struct['displayEquationsNumbered']==68 and struct['tables']==12
geometry=read(QA/'layout_geometry.json')
assert not geometry['outsidePage'] and not geometry['unexpectedMathGlyphs']
format_report=read(ROOT/'paper_output/format_check_report.json')
assert format_report['status']=='PASS'
workflow=read(ROOT/'paper_output/qa/workflow_guard_report.json')
assert workflow['current_step']=='S8' and workflow['next_step'] in ('','DONE')
delivery=read(QA/'delivery_file.json')
assert sha(ROOT/delivery['path'])==manifest['docxSha256']
static=QA/'final_docx_static_independent_review.json'
assert static.exists(), 'Final independent static review has not finished.'
static_text=static.read_text(encoding='utf-8')
assert manifest['docxSha256'] in static_text
report={'generatedAtUtc':datetime.now(timezone.utc).isoformat(),
    'status':'PASS_REQUESTED_DOCX_DELIVERY','delivery':delivery,
    'render':{'docxSha256':manifest['docxSha256'],'pdfSha256':manifest['pdfSha256'],
              'pages':218,'abstractPages':1,'bodyIncludingAIReferences':21,'appendixPages':196},
    'visualReview':{'actuallyReviewedPages':218,'missingPages':[],
                   'reports':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in paths]},
    'content':{'preservedSourceBodyAndSymbolTable':True,'wordComments':8,
               'numberedDisplayEquations':68,'nativeWordEquationsIncludingInline':203,'tables':12,
               'textOnlyFigureBriefs':6,'codeFiles':42,'codeLines':9434},
    'staticIndependentReview':{'path':static.relative_to(ROOT).as_posix(),'sha256':sha(static)},
    'formatWarningsDisposition':[
        'No embedded images follows the user request; six drawing briefs are included.',
        'Markdown heading counter includes comments inside fenced complete source; actual section headings are formatted in Word.'
    ],
    'scopeLimits':['No new production PDE computation in this writing task.',
                   'Original source issues preserved with eight comments for team review.',
                   'User produces six figures; layout must be rechecked after insertion.',
                   'Existing submission ZIP portability remains FAIL; this DOCX is not a repaired submission package.',
                   'Team proofreading, scientific approval, and code human signoff remain pending.']}
(QA/'delivery_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(QA/'delivery_review.md').write_text('''# 本轮完整DOCX交付复核

结论：用户要求的完整DOCX（保留原文、交叉验证简写、公式表格、文字绘图说明、完整附录）已生成并完成本轮文件与排版复核。

- 实际渲染218页：摘要1页、正文含AI/参考文献21页、附录196页。
- 218张完整页面图均已实际逐页查看；v3到v5只变更第29、32页，已在v5重新查看，其余216页图像字节完全一致。
- 原非空正文与符号表逐项保留，8处Word批注标出原文问题；68个编号公式、203个原生Word数学对象、12张表及6项文字绘图说明。
- 42份原程序9434行实际从DOCX重新提取并逐行核对，源文件指纹一致。
- 全文实际章节审计、合并及统一改写复核通过；格式检查与当前S8完成。自动图数量建议不适用本轮用户明确要求，标题计数差异来自源码注释的Markdown井号。

本轮没有重新运行生产PDE。原文批注、用户图像制作、核心代码人工签核及旧提交ZIP独立运行问题仍需团队处理；不把本轮成稿或AI审阅等同比赛最终批准。插入图像后须重新检查页数。

交付文件、哈希、独立审查报告与逐页覆盖详见同名JSON。
''',encoding='utf-8')
print('PASS_REQUESTED_DOCX_DELIVERY: 218 reviewed pages, 42 complete source files, immutable delivery SHA matched.')
