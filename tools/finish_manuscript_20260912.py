"""Record completed image observations and prepare the reviewed DOCX delivery."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path.cwd()
assert ROOT.as_posix() == 'D:/Document/数学建模/2026CUMCM'
QA = ROOT / 'paper_output/qa/manuscript_20260912'
def read(name):
    return json.loads((QA/name).read_text(encoding='utf-8'))
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name, value):
    (QA/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

manifest = read('render_manifest.json')
previous = read('render_manifest_v3.json')
assert manifest['pageCount'] == previous['pageCount'] == 218
assert digest(ROOT/manifest['docx']) == manifest['docxSha256']
assert digest(ROOT/manifest['pdf']) == manifest['pdfSha256']
changes = []
for old, new in zip(previous['pages'],manifest['pages']):
    assert old['page'] == new['page']
    assert digest(ROOT/old['path']) == old['sha256']
    assert digest(ROOT/new['path']) == new['sha256']
    if old['sha256'] != new['sha256']:
        changes.append(new['page'])
assert changes == [29,32]
notes = {
    1:'摘要完整占一页；标题、正文、关键词及页码可读。',
    4:'符号表跨页，表头正常。',
    5:'符号表续页正常；原文后的口径说明可读。',
    16:'问题四表格跨页，续页重复表头。',
    17:'结果表续页及收缩说明正常。',
    22:'参考文献页留白较多，六条文献及页码完整。',
    23:'附录从本页开始，支撑文件列表清楚。',
    29:'最终 v5 实际复看，密度导数已统一为 rho_eff；式49–55完整可读。',
    30:'较长 BDF 公式靠近正文宽度边界，仍完整未裁切。',
    32:'最终 v5 实际复看，极限符号异常字符已消失；式63–66可读。',
    33:'v5 实际查看，Bessel 展开与长式68完整，附录C衔接正常。',
    34:'v5 实际查看，保留/舍弃表完整，内容换行可读。',
    35:'v5 实际查看，数值求解、误差及事件报告过程可读。',
    36:'v5 实际查看，运行前提与代码清单第一页可读。',
    37:'v5 实际查看，代码清单续表表头正常，长文件名换行完整。',
}
pages = []
for p in manifest['pages'][:37]:
    number = p['page']
    direct = number in [29,32,33,34,35,36,37]
    pages.append({'page':number,'visuallyInspected':True,
        'inspectedVersion':'v5' if direct else 'v3',
        'currentImage':p['path'],'sha256':p['sha256'],
        'inheritedByIdenticalImageBytes':not direct,
        'blockingVisualDefects':[],
        'observation':notes.get(number,'实际逐页查看，正文/公式/表格按本页内容完整可读；无阻断裁切、重叠、乱码。')})
visual = {'status':'PASS_VISUAL_SCOPE','reviewer':'Codex root',
    'generatedAtUtc':datetime.now(timezone.utc).isoformat(),
    'scope':'Pages 1–37 actually viewed as individual complete PNGs; changed pages re-viewed in v5.',
    'docxSha256':manifest['docxSha256'],'pdfSha256':manifest['pdfSha256'],
    'pages':pages,'remainingHumanReview':'Team proofreading and approval remain pending.'}
save('visual_pages_001_037.json',visual)
(QA/'visual_pages_001_037.md').write_text('# 第1—37页实际视觉审查\n\n'
    '状态：本范围无阻断视觉缺陷。全部页面均以完整 PNG 实际逐页查看；第29、32页修订后在 v5 重看，第33—37页直接查看 v5，其余页面与已查看 v3 的 PNG 字节相同。\n\n'
    f"最终 DOCX SHA256：{manifest['docxSha256']}。\n\n"
    +'\n'.join(f"- 第 {p['page']} 页：{p['observation']}" for p in pages)
    +'\n\n本记录不代替团队人工审查及比赛提交批准。\n',encoding='utf-8')

contract = QA/'artifact.md'
contract.write_text(contract.read_text(encoding='utf-8').replace('Seven known factual/reference issues','Eight known factual/reference issues').replace('concise chapter6, chapter7,','concise chapter6, additions to preserved chapter7,'),encoding='utf-8')

delivery = ROOT/'paper_output/paper/A题_完整论文_保留原文_含附录.docx'
delivery.parent.mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/manifest['docx'],delivery)
assert digest(delivery) == manifest['docxSha256']
save('delivery_file.json',{'path':delivery.relative_to(ROOT).as_posix(),'sha256':digest(delivery),
    'bytes':delivery.stat().st_size,'identicalToCanonical':True,
    'userRequestedFormat':'DOCX','finalCompetitionSubmission':False})

memory = ROOT/'memoryskill.md'
old = memory.read_text(encoding='utf-8')
if '## 完整DOCX论文交付（2026-09-12，当前）' not in old:
    with (ROOT/'memory_archive.md').open('a',encoding='utf-8') as f:
        f.write('\n\n# 完整DOCX编撰完成前的记忆快照 — '+datetime.now(timezone.utc).isoformat()+'\n\n'+old+'\n')
    principles = old.split('## 建模与交叉验证核实')[0]
    retained = old[old.index('## 提交代码可移植性核验'):]
    update = '''## 完整DOCX论文交付（2026-09-12，当前）

- 用户已明确要求直接完整编撰DOCX及附录，覆盖此前“只给大纲/先逐项确认”的任务范围；保留单独提供的Word原内容，交叉验证点到即可，图只给绘图说明，由用户制作。
- 交付入口 `paper_output/paper/A题_完整论文_保留原文_含附录.docx`；规范源文件 `paper_output/final_paper_source.md`、`paper_output/final_paper.docx`。不覆盖旧submission PDF/ZIP。
- 用户Word原件SHA256 8244c3e9b54c407a12169a25e1cd7c8bfde61e22558c3d5196cd91725f407484，原非空正文及22行符号表全部保留（含模型评价及两条原参考文献）；原标题编入章节、去空白垫行。8处原文问题以Word批注标出，后续模型正文按正确定义写作，原文未获用户同意前不静默改写。
- 本次按Standard2.2实际逐节审计、合并、7处全局实质改写、再审计、真实生成渲染；最终guard S8→DONE。QA与构建脚本在 `paper_output/qa/manuscript_20260912/` 和 `tools/*manuscript*20260912.py`。该阶段通过只表示本DOCX写作/排版合同完成，不表示旧ZIP修复、真实物理验证或用户已签核。
- 最终v5 DOCX SHA256 3c0edfdf5946019ac8129afee637880954c86561a6440adc6dc0553483185013；渲染218页＝摘要1＋正文含AI/参考文献21＋附录196，第23页开始附录。68编号公式、203原生可编辑OMML、12张表、6项文字绘图说明，无嵌入图，符合本轮用户约定。
- 42份完整源码共9434行嵌入附录，含11生产文件与31检验/历史依赖文件；独立逐行核验与源SHA比对PASS。附录A物理推导、B离散/Jacobian/BDF/事件/Bessel推导、C实际数值计算与复现前提、D/E完整程序。全部218页实际查看；修订只改变29/32页并复看，其他v3/v5图像逐页SHA相同。
- 本轮只审计/编撰与渲染，未重新积分生产PDE、未新增VS GUI或用户人工签核。正文7张结果表297数据格与冻结CSV完全一致；无内部实测T/C，不能写预测准确率。交叉验证正文简写且保留实际网格/样本范围，详细过程放附录。
- 模型勘误已体现在新增正文：空气kg/kg映射为Ceq仍假设；有效显热通量自洽不等于整体能量变化100%解释；经验边界Kp族未标定、不构成真实时长下界。旧M-K常数伪越界、Morris D无效注入及未完成Sobol均不采纳。文献1原引文问题保留批注并给刊方更正；文献2末页3447已核实、作者须等。
- 用户指定“atuoresponse”，已搜索当前安装未找到该名；已说明并用现有 autoresearch 的历史实验审阅模式，把42条trial保留/舍弃及预算故障写入附录，不声称新跑GPU实验。
- 用户另明确要求所有部分结束后用Computer Use打开Apple Music播放音乐提醒。文稿检查完成；播放尚待执行，成功须以界面暂停按钮及时间推进核实，不凭打开应用声称已播放。
- 此次正式交付仍由团队核实原文8条批注、6张图及核心代码；AI声明如实保留人工审查未完成。旧提交ZIP独立运行FAIL保持有效，详见下一节，不将本DOCX当作最终比赛提交包。

'''
    memory.write_text(principles+update+retained,encoding='utf-8')
    assert len(memory.read_text(encoding='utf-8').splitlines()) <= 100
print(json.dumps({'delivery':str(delivery),'sha256':digest(delivery),'changedPages':changes,'rootVisualPages':37},ensure_ascii=False))
