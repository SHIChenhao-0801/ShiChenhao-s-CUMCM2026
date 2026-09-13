"""Write actual prose notes and audit the final delivered code directory."""
from pathlib import Path
import ast
import csv
from datetime import datetime, timezone
import hashlib
import json
import xml.etree.ElementTree as ET

QA = Path(__file__).resolve().parent
ROOT = QA.parents[3]
PACKAGE = ROOT/'支撑材料/03_程序代码'
before = QA/'before_current_03'
static = json.loads((QA/'migration_static.json').read_text(encoding='utf-8'))
process = json.loads((QA/'process_result.json').read_text(encoding='utf-8'))
test = json.loads((QA/'targeted_result.json').read_text(encoding='utf-8'))
assert process['actualExitCode'] == 0 and test['status'] == 'PASS'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

source_lines = [
    '源码与输入格式变更说明', '',
    '本次整理以用户当前03_程序代码目录为输入，没有恢复已删除或重排的其他目录。', '',
    '本次修改：',
    '1. 输入完整性清单改用input_manifest.csv，12项路径、字节数、SHA256以真实CSV字段保存。',
    '2. 冻结数值参照改用reference/reference_data.py中的REFERENCE_DATA纯数据常量。',
    '   全部字典、列表和标量类型保持一致；每个浮点数的十六进制值均与转换前一致。',
    '3. runDelivery.py只改两处输入读取方式并增加CSV导入；反向规范化这几处改动后AST一致。',
    '4. 八个核心模块只改说明文件名引用；模型、参数、离散、Jacobian、BDF及导出算法未改。',
    '5. Visual Studio工程内的说明文件引用改为README.txt。',
    '6. 删除冗余审计JSON和旧Markdown说明，重新编写可直接阅读的TXT说明。',
    '7. 原始Excel、清洗CSV、四份原模板和三份NPZ均保持原字节。', '',
    '导出器内部生成和回读的JSON协议保留，以保持原有全表验证链条；当前交付目录不含JSON文件。',
    '本次未重新求解Q23/Q4全量轨迹，实际定向核验范围见运行验收说明.txt。', '',
    '源码SHA256（整理前 -> 本次交付）：', '']
for item in static['coreModules']:
    source_lines += [item['path'], '  前：'+item['beforeSha256'], '  后：'+item['afterSha256'], '']
source_lines += ['runDelivery.py', '  前：'+static['runnerBeforeSha256'],
                '  后：'+static['runnerAfterSha256'], '',
                'reference/reference_data.py（新增纯数据文件）', '  SHA256：'+sha(PACKAGE/'reference/reference_data.py'), '']
(PACKAGE/'docs/源码变更说明.txt').write_text('\n'.join(source_lines), encoding='utf-8')

notes = f'''程序运行与格式整理验收说明

一、本次实际核验

本次仅调整输入保存格式与说明文件，不修改数学模型或生产数值。

输入清单：CSV的12项输入/模板/参照全部通过文件与哈希预检。
冻结参照：新的Python纯数据常量与转换前数据逐类型、逐浮点十六进制值完全一致。
核心源码：八个模块在说明路径规范化后AST一致。
主入口：仅CSV清单读取和Python数据常量读取发生改变，规范化后AST一致。

从当前源码复制到独立QA目录后，实际运行：
  Q1，N40：求解完成；Excel回读79,244格，正文表live Run核验84格，通过。
  Q1，N3200：求解完成；Excel回读79,244格，正文表live Run核验84格，通过。
  Q1，N3200：冻结参照检查通过，七个保存数组逐值完全相同。
  外部监督进程实际退出码：0。
  本次定向运行总耗时：{process['elapsedSeconds']:.3f}秒。

本次没有重新运行Q23/Q4全量轨迹；它们的数值参照数据经精确等价检查，算法源码经AST检查。
本次运行生成的记录和结果保存在独立QA目录，没有混入交付的03_程序代码。

二、此前全量运行事实

在本次文件格式整理前，同机隔离环境曾实际完成：
  N40三轨迹及四题完整导出/回读：退出0，454.516秒。
  N3200/N3200/N6400正式网格：退出0，989.547秒。
  四份工作簿9,335,598格回读、297正文格live Run核验通过。
  三轨迹21个保存数组逐值相同。
  四份原精度gzip解压后的全部CSV字节、七份正文CSV字节均与final_v6a一致。
  严格报告时间仍为Q3 57.4724 h、Q4 51.0906 h。

以上是整理前版本的全量运行记录，不冒充本次又进行了一次全量计算。

三、适用范围

实际环境为Windows AMD64、Python3.14.7、NumPy2.5.2、SciPy1.18.1、openpyxl3.1.5。
当前证据不覆盖第二台物理电脑或其他操作系统，也不证明条件模型的真实预测精度。
新版Visual Studio工程仅完成静态检查，GUI打开、断点和运行未在本次实测；用户人工审查仍待本人完成。
运行后会产生JSON格式校验记录；当前交付目录已清除JSON和Markdown文件，说明统一为TXT。
'''
(PACKAGE/'docs/运行验收说明.txt').write_text(notes, encoding='utf-8')

with (PACKAGE/'input_manifest.csv').open(encoding='utf-8-sig', newline='') as stream:
    items = list(csv.DictReader(stream))
assert len(items) == 12
for item in items:
    path = PACKAGE/item['path']
    assert path.stat().st_size == int(item['bytes']) and sha(path) == item['sha256']
python_files = []
for path in sorted(PACKAGE.rglob('*.py')):
    ast.parse(path.read_text(encoding='utf-8'))
    python_files.append({'path':path.relative_to(PACKAGE).as_posix(), 'sha256':sha(path)})
for item in process['sourceFiles']:
    assert sha(PACKAGE/item['path']) == item['sha256']
ET.parse(PACKAGE/'A_CodeReview.pyproj')
assert 'README.txt' in (PACKAGE/'A_CodeReview.pyproj').read_text(encoding='utf-8')
for path in [PACKAGE/'README.txt', PACKAGE/'numerical_design.txt', *sorted((PACKAGE/'docs').glob('*.txt'))]:
    content = path.read_text(encoding='utf-8')
    assert not content.lstrip().startswith(('{','['))
for path in sorted(PACKAGE.rglob('*')):
    assert path.suffix.lower() not in {'.json','.md'}
    assert path.name not in {'.venv','.vs','__pycache__'}
files = [p for p in PACKAGE.rglob('*') if p.is_file()]
report = {'status':'PASS', 'createdAtUtc':datetime.now(timezone.utc).isoformat(),
          'scope':'Current code-folder JSON/Markdown cleanup with equivalent input formats and focused Q1 execution',
          'deliveryFiles':len(files), 'deliveryBytes':sum(p.stat().st_size for p in files),
          'jsonFiles':0, 'markdownFiles':0, 'plainTextNotes':4,
          'inputManifestFormat':'CSV', 'inputManifestRows':12,
          'referenceFormat':'Python pure-data constant', 'referenceExactTypeAndFloatEquality':True,
          'unchangedAlgorithmCoreModules':8, 'pythonFilesSyntaxChecked':len(python_files),
          'actualExitCode':process['actualExitCode'], 'targetedElapsedSeconds':process['elapsedSeconds'],
          'q1IntervalsTested':[40,3200], 'workbookCellsCheckedPerRun':79244,
          'paperCellsCheckedPerRun':84, 'q1FinalArraysExactlyMatchFrozen':7,
          'fullQ23Q4RerunThisCleanup':False, 'runtimeStillGeneratesJsonRecords':True,
          'newVisualStudioGui':'NOT_PERFORMED', 'humanReview':'PENDING_USER_REVIEW',
          'sourceFiles':python_files, 'removedFromDelivery':static['removedFromDelivery'],
          'detailedEvidence':['migration_static.json','process_result.json','targeted_result.json']}
(QA/'code_cleanup_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({key:report[key] for key in ['status','deliveryFiles','deliveryBytes','jsonFiles',
      'markdownFiles','actualExitCode','targetedElapsedSeconds']}, ensure_ascii=False))
