from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re

QA=Path(__file__).resolve().parent
ROOT=QA.parents[2]
SUPPORT=ROOT/'支撑材料'
OUT=QA/'strip_txt_drafts'
audit=json.loads((QA/'strip_final_audit.json').read_text(encoding='utf-8-sig'))
by_path={r['path']:r for r in audit['records']}
drafts=[]


def read(relative):
    return (SUPPORT/relative).read_text(encoding='utf-8-sig')


def draft(relative,text):
    destination=OUT/relative
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(text.rstrip()+'\n',encoding='utf-8-sig')
    source=SUPPORT/relative
    drafts.append({'target':relative,'currentTargetSha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                   'draft':str(destination),'draftSha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
                   'applyStatus':'NOT_APPLIED; root must review after final runtime result and package scope',
                   'noVmSuccessClaim':True})


source_note=[
    '源码去注释与输入格式说明','',
    '当前版本在已有独立生产工程上删除Python注释和说明性docstring，并删除requirements中的说明行；模型方程、物性、参数、离散、Jacobian、BDF、导出和校验流程保持原有计算语句。',
    '本目录10份Python的非注释AST逐项等价并编译通过。runLogged.ps1原无注释，内容未改。Visual Studio工程、方案及用户IDE状态不由本轮源码发布覆盖。',
    'input_manifest.csv包含12项输入、模板和数值参照。reference/reference_data.py的数值常量不变；删除模块docstring后只同步该文件在清单内的字节数和SHA256。',
    'Python语义上的__doc__随说明性docstring删除而为空，因此使用description=__doc__的帮助页不再显示模块简介；命令行选项和数值执行逻辑不变。',
    '两份原始Excel、两份清洗CSV、四份空白模板和三份NPZ没有因去注释发生改变。',
    '此前已完成的CSV清单与Python纯数据常量转换保留。当前源码SHA与去注释前不同，不再声称源码与来源逐字节相同。',
    '运行会继续生成JSON过程记录；这些记录属于实际运行产物。独立运行结果及对应版本见运行验收说明。',
    '05历史检验中仅用于隔离实验的根目录路径适配没有写回本次去注释候选源码。','',
    'SHA256（去注释前 → 当前去注释版本）：',''
]
for r in audit['records']:
    if r['path'].startswith('03_程序代码/') and (Path(r['path']).suffix in {'.py','.ps1'} or Path(r['path']).name in {'requirements.txt','input_manifest.csv'}):
        source_note += [r['path'].removeprefix('03_程序代码/'),
                        f'  去注释前：{r["before_sha256"]}',
                        f'  当前版本：{r["after_sha256"]}',
                        f'  当前大小：{r["after_bytes"]} 字节','']
draft('03_程序代码/docs/源码变更说明.txt','\n'.join(source_note))

note=read('05_数值检验与实验/源码文件与校验值.txt')
note=note.replace('以下33项均为真实源代码。新复制文件与所列本届来源逐字节一致；runCrossCheck.m与整理前的现有文件逐字节一致。',
                  '以下33项均为真实源代码的去注释版本。来源路径用于追溯；删除注释及Python说明性docstring后文件字节已改变，当前SHA256以本表为准。没有修改计算语句、模型参数或输出数据字符串。')
blocks=re.split(r'(?=^\d+\. )',note,flags=re.M)
count=0
for i,block in enumerate(blocks):
    match=re.match(r'^\d+\. ([^\r\n]+)',block)
    if not match:
        continue
    key='05_数值检验与实验/'+match.group(1)
    r=by_path[key]
    assert r['before_sha256'] in block
    block=re.sub(r'^大小：\d+ 字节$',f'大小：{r["after_bytes"]} 字节',block,flags=re.M)
    block=block.replace('SHA256：'+r['before_sha256'],
                        'SHA256：'+r['after_sha256']+'\n去注释前SHA256：'+r['before_sha256'])
    blocks[i]=block
    count+=1
assert count==33
draft('05_数值检验与实验/源码文件与校验值.txt',''.join(blocks))

note=read('05_数值检验与实验/数值检验说明.txt')
note=note.replace('本目录保存本题实际使用的数值检验源代码，供阅读和追溯。',
                  '本目录保存本题数值检验源代码的去注释版本，供阅读和追溯。')
note=note.replace('相互调用的本地Python源码已经补齐，文件名和代码内容保持原样。',
                  '相互调用的本地Python源码已经补齐，文件名保留；已删除注释及说明性docstring，非注释AST与去注释前等价。')
note=note.replace('原位保留；未改任何字节，未移回原工作区。',
                  '位置保留；已删除整行说明及代码分析器提示，格式化字符串、矩阵转置和计算语句保留。')
note=note.replace('这些是实际使用过的原检验源码，仍保留当时的路径、输出结构和数据读取约定。',
                  '这些源码已去注释，仍保留当时的路径、输出结构和数据读取约定。')
note=note.replace('本轮保留原文件，不自动修补它或恢复用户移走的原路径。',
                  '本轮去注释未修补该路径推导，也未恢复用户移走的原路径。')
note=note.replace('本轮只复制与静态核对源码，没有重新求解PDE、运行全部实验或代替核心代码人工审查。',
                  '本轮已完成去注释、逐文件SHA和Python非注释AST检查，并在另设的实验副本中开展入口或函数级隔离验证。该副本对14处旧根目录路径作了适配，补入两CSV、四模板及描述性序列所用Q23参考NPZ；这些路径适配没有混入本目录候选源码。当前不能概括为所有历史源码都能原样独立运行，也没有运行全部默认高网格批次。实际环境、命令、异常和数值判定以本轮独立运行核查说明为准；HOST受限venv与Windows Sandbox虚拟机分别记录。')
note=note.replace('原本届paper_output内的源程序和证据没有修改；runCrossCheck.m保留用户当前放置位置及原字节。',
                  '原本届paper_output中的生产源程序及历史证据保持各自版本；本目录交付去注释副本。runCrossCheck.m保留用户当前放置位置，当前字节及SHA以源码文件与校验值为准。')
draft('05_数值检验与实验/数值检验说明.txt',note)

note=read('03_程序代码/docs/运行验收说明.txt')
current=[
    '程序运行与去注释验收说明','',
    '一、当前去注释版本的静态核验','',
    '当前交付源码删除注释和Python说明性docstring；计算语句、参数及导出/回读协议未变。10份Python非注释AST等价并编译通过，PowerShell非注释token流等价。',
    '12项输入清单逐项回读一致，reference_data.py只发生说明性docstring删除及清单SHA同步，数值常量不变。',
    '当前入口SHA256：'+by_path['03_程序代码/runDelivery.py']['after_sha256'],
    '本说明以下两节是去注释前各版本的历史运行事实，不能代替当前去注释源码的运行证明。',
    '当前版本的正式独立运行结论应由本轮实际运行记录单列，包含环境、实际退出码、内部检查状态和源码SHA；本静态说明不代填尚未完成的运行结果。','',
    '二、去注释前的文件格式调整及定向核验（历史）',''
]
note=note.split('一、本次实际核验',1)[1].lstrip()
note=note.replace('二、此前全量运行事实','三、去注释前的更早全量运行事实（历史）')
note=note.replace('三、适用范围','四、上述历史证据的适用范围')
draft('03_程序代码/docs/运行验收说明.txt','\n'.join(current)+note)

note=read('03_程序代码/README.txt')
note=note.replace('八个核心模块的模型、数值方法、参数和四题导出规则保持不变。',
                  '八个核心模块的模型、数值方法、参数和四题导出规则保持不变。本轮已删除源码注释和Python说明性docstring，并完成非注释AST核对。')
note=note.replace('docs/源码变更说明.txt：本次文件格式调整及源码前后SHA256。',
                  'docs/源码变更说明.txt：当前去注释规则、输入清单同步及源码前后SHA256。')
note=note.replace('docs/运行验收说明.txt：此前全量运行和本次定向核验的区别。',
                  'docs/运行验收说明.txt：当前源码版本、静态检查和按版本区分的实际运行记录。')
draft('03_程序代码/README.txt',note)

note=read('00_材料来源说明.txt')
note=note.replace('本次只整理文件形式和代码读取方式。',
                  '本轮源码去注释不修改这些冻结结果，独立重算和检查记录另行保存。')
note=note.replace('模型方程、物性与求解方法沿用此前已核验版本。',
                  '模型方程、物性与求解方法沿用此前版本；本轮删除注释及说明性docstring，当前源码SHA另列，非注释AST已经检查。')
note=note.replace('05提供检验实际采用的源代码及必要依赖。',
                  '05提供检验源码的去注释副本及必要模型依赖；历史接口、原绝对路径和未通过的诊断也保留供追溯，不能把所有文件概称为已独立通过。')
draft('00_材料来源说明.txt',note)

note=[
    '支撑材料整理与源码去注释核验说明','',
    '当前说明使用TXT；程序与IDE在运行后可能生成额外过程文件，实际交付清单应在最终发布后重新生成。',
    '本轮共处理44份源码（41份Python、1份MATLAB、1份Node.js、1份PowerShell）及requirements清单，删除274处词法注释和106处Python说明性docstring。',
    '41份Python非注释AST与去注释前相同，全部编译通过；Node.js用Babel核对非注释AST，PowerShell用原生解析器核对token流。MATLAB只删除已辨认的整行说明和3个编辑器提示，字符串、格式符、转置及计算表达式保留。',
    'reference/reference_data.py删除说明性docstring后，input_manifest.csv只同步它的字节数和SHA。12项输入/模板/参照经实际回读检查。',
    '原始PDF、Excel、CSV、NPZ及四份冻结结果不因源码去注释改变。MATLAB源码的字节已改变，不能再包含在“原字节不变”的旧42文件计数中。',
    '03和05的当前源码SHA见各目录TXT。05的33份源码与原来源之间是可追溯的去注释关系，不再逐字节相同。',
    '实际运行可否通过须同时检查进程退出码与程序内部数值报告。HOST受限venv、Windows Sandbox虚拟机、MATLAB/Visual Studio GUI及用户人工审查分别记录，不能互相替代。',
    '当前目录中的05历史源码有路径依赖、旧接口错误或未通过的诊断。数值方法和模型参数未因这些运行问题而被本轮去注释发布擅自改变。',
    '本说明不填入尚未结束的虚拟机成功声明；最终实际运行范围与结果由对应记录补充。'
]
draft('00_整理验收说明.txt','\n'.join(note))

issues=[
    'TXT过期文字复核与替换草稿说明','',
    '这些只是QA草稿，没有修改真实支撑材料或candidate；最终运行状态、VS状态及目录/压缩交付口径需由根代理结合最新用户要求定稿。',
    '1. 03/docs/源码变更说明.txt：旧“本次只改两处读取”“八模块只改说明文件名”及末尾10份源码SHA已过期。完整替换草稿已生成，列本轮去注释前后SHA。',
    '2. 05/源码文件与校验值.txt：33份“逐字节一致”失效；全部大小及SHA需换成去注释版本，保留原来源与去注释前SHA。完整草稿已生成。',
    '3. 05/数值检验说明.txt：代码内容原样、MATLAB未改任何字节、本轮只复制静态未求解等表述已过期。草稿改为去注释事实与独立实验适配边界；未填入VM成功。',
    '4. 03/docs/运行验收说明.txt：此前11.031s Q1定向运行与989.547s全量运行仅绑定历史SHA。草稿保留原事实，但显式标成去注释前历史；当前VM运行需根代理补入实际退出码/原精度核验。',
    '5. 00_整理验收说明.txt：旧42份含MATLAB“内容原样”、33源码原始SHA一致、当前只Q1未Q23/Q4均不宜保留为现状。已生成保守替换稿。',
    '6. 00_材料来源说明.txt及03/README.txt：补充去注释与SHA版本说明，避免“本次只整理文件形式”误导。草稿已生成。',
    '7. 00_文件清单.txt：103总数/03为30文件已经受用户VS升级产物影响，不能手改固定数；最终交付前按实际清单重新生成，.vs动态缓存、UpgradeLog和压缩包是否纳入由根代理按最新要求确定。',
    '8. 支撑目录存在用户VS新生成的.vs/DocumentLayout.json，所以“JSON/MD均为零”不能未经最终扫描继续声称。保留用户IDE状态与正式交付清单的范围应明确。',
    '9. 用户最新ZIP安排由根代理处理；所有“不压缩/没有压缩包/直接交付文件夹”等旧措辞需在其最终口径确定后统一。',
    '10. numerical_design.txt及赛题/文献TXT未发现与去注释直接冲突的算法、数据或来源描述，无需为了本轮源码格式修改改写。',
    '',
    '发布脚本只发布44份源码、requirements和input_manifest，共46份，不会发布本目录TXT草稿。',
    '草稿清单及写入前真实TXT的SHA见strip_txt_drafts_manifest.json。'
]
(QA/'strip_TXT过期说明与替换草稿索引.txt').write_text('\n'.join(issues)+'\n',encoding='utf-8-sig')
(QA/'strip_txt_drafts_manifest.json').write_text(json.dumps(drafts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'drafts':len(drafts),'files':[r['target'] for r in drafts],'real_support_modified':False},ensure_ascii=False,indent=2))
