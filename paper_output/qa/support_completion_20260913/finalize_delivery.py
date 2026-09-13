from pathlib import Path
import datetime
import hashlib
import json

ROOT = Path.cwd()
assert ROOT.as_posix() == 'D:/Document/数学建模/2026CUMCM'
SUPPORT = ROOT / '支撑材料'
QA = ROOT / 'paper_output/qa/support_completion_20260913'
stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

updates = {
    '00_支撑材料总说明.txt': '''本次提交前补件说明（2026-09-13）
当前支撑材料共137个文件。AI工具使用详情.docx为可编辑附件：已根据论文末尾AI报告填写已知工具和用途；真实交互、精确客户端版本及人工确认等字段须由团队据实补齐。
06_绘图程序与数据包含draw_figures.R、14份CSV、6张PNG及3份说明/校验文件，图像只保留PNG。绘图程序已在隔离目录实际运行。
05_数值检验与实验已补齐两份CSV的预期目录、相对实验根路径、run_checks.py和包含Matplotlib的requirements.txt。网格、时间误差及方法对照的适量检验已实际运行通过；本轮未重跑全部高网格正式计算。命令和范围见该目录“论文采用检验_独立运行说明.txt”。
方法对照原源码仅修正ROOT定位一行；其余原检验源码和历史失败状态保留。原44份源码去注释与沙盒报告属于此前记录，不代表本轮所有文件均通过。
本轮Visual Studio界面复现由用户按Esc中止，未完成，不能以命令行结果替代GUI或团队人工审查。
完整文件路径见00_文件清单.txt；附录用清单见00_可用于论文附录的支撑清单.txt，目录外另提供“支撑材料文件列表_附录用.docx”。后续将AI附件改为PDF或增删文件时须同步清单。

以下为原整理说明，涉及“本轮”的表述指此前源码去注释批次：

''',
    '00_材料来源说明.txt': '''本次新增材料来源（2026-09-13）
AI工具使用详情依据“药材热湿耦合模型与干燥时间计算_附录修订版.docx”第9.3节及用户提供的格式要求制作；未虚构交互记录或人工核验结果。
06绘图CSV和PNG来自paper_output/figures/review_20260913的论文用图输入与图像，交付副本逐字节核对。R程序改为按自身路径读取CSV、仅输出PNG；本机重绘与历史PNG有小幅像素差异，交付保留原论文PNG，详细边界见绘图复现说明.txt。
05新增两份CSV与03中的清洗输入逐字节一致。方法对照程序仅将原绝对ROOT改为由当前脚本位置确定；新增运行入口与依赖清单用于在外部实验目录独立运行。历史废弃试验未修复、未改判。

以下为此前材料来源记录：

''',
    '00_整理验收说明.txt': '''本次补件验收（2026-09-13）
当前137个文件已生成完整清单；01至06及根目录数量依次为10、11、30、12、43、24、7。
03全部30个文件及04全部12个文件保持此前审计字节；四份结果工作簿与final_v6a冻结结果一致。
05在新建虚拟环境中实际安装并检查numpy、scipy、openpyxl、matplotlib；网格Q1 N20/40、时间误差Q1 N20和方法对照quick N100/200均实际退出0并核查内部报告。具体范围和数值见05说明，不将适量重跑等同于重跑全文正式高网格计算。
06的14份CSV、6张PNG已核对来源，R在独立目录实际运行通过。
AI详情DOCX共6页，目录外附录清单DOCX共8页，均已渲染并逐页检查。AI真实交互及团队确认仍待据实填写，论文PDF尚未定稿。
Visual Studio复现未完成：用户按Esc停止Computer Use；命令行验证与人工审查状态分别记录。
本次不生成压缩包，不修改论文正文；论文原附录中的method_comparison.py第11行ROOT定位与当前交付源码存在一行差异，插入最终附录时须同步。新增绘图程序及run_checks.py亦须按最终附录编排处理。

以下为此前源码去注释核验记录，计数及状态对应此前批次：

'''
}
for name, prefix in updates.items():
    p = SUPPORT / name
    old = p.read_text(encoding='utf-8-sig')
    if not old.startswith(prefix.splitlines()[0]):
        p.write_text(prefix + old, encoding='utf-8')

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

files = [{'path': p.relative_to(SUPPORT).as_posix(), 'bytes': p.stat().st_size, 'sha256': digest(p)}
         for p in sorted(SUPPORT.rglob('*')) if p.is_file()]
assert len(files) == 137
assert not any(Path(f['path']).suffix.lower() in {'.md', '.json', '.zip', '.rar'} for f in files)
paper = ROOT / '药材热湿耦合模型与干燥时间计算_附录修订版.docx'
assert digest(paper) == 'b6fbac8fefd87c10497a7c63f3638a7ead1f7e82c9bb0af7e773031a51f6960c'
inventory_path = QA / 'inventory_audit.json'
inventory = json.loads(inventory_path.read_text(encoding='utf-8-sig'))
inventory['final_metadata_refreshed_at_utc'] = stamp
inventory['support_bytes'] = sum(f['bytes'] for f in files)
inventory['final_file_manifest'] = files
inventory_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding='utf-8')
report = {'at_utc': stamp, 'file_count': len(files), 'support_bytes': sum(f['bytes'] for f in files),
          'files': files, 'main_paper_unchanged_sha256': digest(paper),
          'ai_docx': {'sha256': digest(SUPPORT / 'AI工具使用详情.docx'), 'visually_checked_pages': 6},
          'appendix_docx': {'sha256': digest(ROOT / '支撑材料文件列表_附录用.docx'), 'visually_checked_pages': 8},
          'gui': 'User stopped Computer Use with physical Escape; Visual Studio reproduction incomplete.',
          'human_review': 'Pending team confirmation; not substituted by automated checks.',
          'final_pdf': 'Not finalized by user.', 'historical_failed_experiments': 'Preserved without repair or reclassification.'}
(QA / 'final_delivery_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
memory = ROOT / 'memoryskill.md'
with memory.open('a', encoding='utf-8') as f:
    f.write('\n- 2026-09-13提交前补件：依用户四项新指令，支撑材料已增AI详情DOCX（6页，真实交互和团队确认待填）、06绘图R+14CSV+6PNG、05两份输入CSV/相对根路径/Matplotlib依赖和运行入口；三项适量检验实际通过，历史失败保持。完整137文件清单已生成根目录《支撑材料文件列表_附录用.docx》（8页）。论文原DOCX未改、PDF未定稿；方法对照附录需同步一行ROOT。用户按Esc停止Computer Use并催促收尾，本轮VS复现未完成。证据：paper_output/qa/support_completion_20260913/final_delivery_audit.json。\n')
print(json.dumps({'files': len(files), 'bytes': report['support_bytes'], 'paper_unchanged': True}, ensure_ascii=False))
