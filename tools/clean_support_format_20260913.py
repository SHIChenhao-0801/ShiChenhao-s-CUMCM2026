"""Apply the user's TXT/source-code delivery format to currently retained materials."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DEST = (ROOT/'支撑材料').resolve()
QA = ROOT/'paper_output/qa/support_cleanup_20260913'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(relative, text):
    p=DEST/relative
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(text.strip()+'\n',encoding='utf-8-sig')


def main():
    QA.mkdir(parents=True,exist_ok=True)
    protected={p.relative_to(DEST).as_posix():sha(p) for p in DEST.rglob('*')
               if p.is_file() and p.suffix.lower() in {'.xlsx','.pdf','.html','.csv','.npz','.m'}
               and p.name not in {'AI工具使用详情.pdf','00_文件清单.csv'}}
    (QA/'protected_files_before.json').write_text(json.dumps(protected,ensure_ascii=False,indent=2),encoding='utf-8')
    deleted=[]
    for p in list(DEST.rglob('*')):
        if not p.is_file():
            continue
        rel=p.relative_to(DEST)
        if rel.parts[0] in {'03_程序代码','05_数值检验与实验'}:
            continue  # Other agents own these two directories during cleanup.
        remove=p.suffix.lower() in {'.md','.json','.jsonl'} or rel.as_posix() in {'AI工具使用详情.pdf','00_文件清单.csv'}
        if not remove:
            continue
        assert p.resolve().is_relative_to(DEST)
        if p.name=='AI工具使用详情.pdf':
            assert sha(p)=='d996b6aab3be25fe000d2e0f6572c43a6c47d59212d4451e5dc2f96e32010b7a', 'AI file changed after the previous delivery; preserve for review.'
        deleted.append({'file':rel.as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
        p.unlink()
    write('00_支撑材料总说明.txt','''A题《药材的烘干问题》支撑材料

本目录按当前文件夹结构整理，说明使用TXT，数值检验提供实际源代码。

1. 01_赛题与原始数据
   A题题面、附件1/2、四份空白结果模板及清洗后的两份CSV。

2. 02_参考文献与网络资料
   当前保留的四份正文参考PDF，以及补充网页和Shampine扫描资料。
   文献实际范围见该目录“参考文献文件说明.txt”。

3. 03_程序代码
   核心Python程序、Visual Studio工程、依赖、原始输入及冻结参照。
   从README.txt开始；数值结果由runDelivery.py的quick/final入口复现。

4. 04_结果表格
   result1.xlsx至result4.xlsx为四问完整结果。
   Referrence Table Files内为正文七份结果CSV。

5. 05_数值检验与实验
   Python检验源码、必要模型依赖、MATLAB交叉实现及对照源码。
   具体源码用途及历史运行前提见该目录TXT说明。

当前四个Excel与final_v6a冻结文件逐字节一致。问题三严格报告时刻为57.4724 h，问题四为51.0906 h；这些是给定模型假设下的计算结果。

03是当前独立生产计算入口。05保存检验所用完整源码，部分脚本依赖原工程的数据和目录，具体运行前提另有说明。代码的命令行数值复现与团队人工审查分别记录。

逐文件列表见00_文件清单.txt。本次直接交付文件夹。
''')
    write('00_可用于论文附录的支撑清单.txt','''支撑材料文件列表

1. 01_赛题与原始数据/A题.pdf及附件目录：题面、原始环境/半径数据和空白模板。
2. 01_赛题与原始数据/清洗后数据：实际输入的两份CSV。
3. 02_参考文献与网络资料：现存参考文献PDF、补充网页及资料范围说明。
4. 03_程序代码：完整生产程序、运行入口、必要输入、固定依赖与数值参照。
5. 04_结果表格/result1.xlsx：问题一完整结果。
6. 04_结果表格/result2.xlsx：问题二完整时空大表。
7. 04_结果表格/result3.xlsx：问题三完整结果。
8. 04_结果表格/result4.xlsx：问题四完整结果。
9. 04_结果表格/Referrence Table Files：正文七份结果CSV。
10. 05_数值检验与实验：网格、时间、解析、方法对照、阈值、守恒、参数情景等检验的实际源码及MATLAB交叉实现。
11. 00_文件清单.txt：按当前目录生成的完整文件列表。

这份清单供论文附录整理使用，最终以团队实际采用的内容为准。
''')
    write('00_材料来源说明.txt','''材料来源说明

原始输入：本届A题题面及官方附件。01中的原始PDF/Excel保持现有字节；两份CSV由附件1/2转换取得。

计算结果：04中的四份工作簿和七份正文CSV来自final_v6a冻结计算。本次只整理文件形式和代码读取方式。

程序：03源于本届review_delivery生产代码，输入清单和参照数据按当前无JSON的目录格式调整。模型方程、物性与求解方法沿用此前已核验版本。

数值检验：05提供检验实际采用的源代码及必要依赖。每份源码的具体来源与用途见该目录TXT说明；不以机器审计报告替代程序。

参考文献：02按用户当前保留的PDF/网页整理。两份中文综述的实际PDF分别为28页和8页；英文干燥书为5页节选，数值分析文件为254页Finite Volume Methods作者更新稿。具体文件名与范围见参考文献文件说明.txt。

文件夹未包含本机虚拟环境、稠密求解缓存或压缩交付文件。
''')
    write('01_赛题与原始数据/数据说明.txt','''数据说明

A题.pdf：官方题面。
附件/附件1.xlsx：环境观测，共241条，0至4小时。
附件/附件2.xlsx：半径观测，共145条，0至72小时。
附件/附件3/result1.xlsx至result4.xlsx：官方空白结果模板。

清洗后数据/A_environment_observed.csv字段：
time_s（秒）、time_h（小时）、temperature_C（摄氏度）、temperature_K（开尔文）、air_moisture_kg_per_kg（空气水分指标）。

清洗后数据/A_radius_observed.csv字段：
time_s（秒）、time_h（小时）、radius_cm（厘米）、radius_m（米）。

两份CSV保存实际输入值。已有读取检查未发现缺失数值、非有限值或重复时间。

4小时后的50°C、0.05 kg/kg平台是模型延拓假设。气相水分指标映射为材料平衡含水率是闭合假设，不能将其当成额外材料实测数据。

已填好的四问完整结果在04_结果表格，不能与本目录空白模板混淆。
''')
    write('02_参考文献与网络资料/参考文献文件说明.txt','''参考文献文件说明

本说明按当前实际保留的PDF核对题名和页数，不因文件名写有Handbook就认定为整部书。

1. 中药材干燥技术与装备研究现状.pdf
   王乐意、李长河、刘明政等，农业工程学报，2024，40(2)：1-28。
   DOI：10.11975/j.issn.1002-6819.202306104。
   当前PDF共28页，为该篇综述。用于中药材干燥技术和装备背景。

2. 数值模拟仿真研究现状及其在中药干燥领域应用展望_王晓辉.pdf
   王晓辉、王学成、唐培渝等，中国中药杂志，2023，48(13)：3440-3447。
   DOI：10.19540/j.cnki.cjcmm.20230331.301。
   当前用户保留的PDF共8页，首页题名、作者、卷期相符；不再沿用此前未取得全文的旧说明。

3. Handbook of Industrial Drying.pdf
   Arun S. Mujumdar编，Handbook of Industrial Drying，第4版，2014。
   当前文件共5页，包含题名、版权及正文13-15页的公开预览节选，不是全书。

4. Handbook of numerical analysis.pdf
   文件实际题名为Finite Volume Methods，作者Robert Eymard、Thierry Gallouët、Raphaèle Herbin。
   当前共254页，首页明确为2019年1月作者更新稿；不是Handbook of Numerical Analysis整部书，也不是2000年刊方排印本。

补充网络资料包含FAO干燥原理网页、SciPy solve_ivp官方文档和Shampine的MATLAB ODE Suite扫描。各自说明见补充网络资料/补充资料说明.txt。
''')
    write('02_参考文献与网络资料/补充网络资料/补充资料说明.txt','''补充网络资料说明

1. FAO Grain storage techniques中的Drying principles and general considerations章节。
   保存官方网页及离线文本，用于核查平衡含水率与环境湿度、温度关系。原资料对象为粮食，其经验参数没有直接移植到本题药材。

2. SciPy solve_ivp官方文档。
   保存官方API网页及离线文本，用于BDF、Jacobian、事件等接口核查。网页展示的版本不能替代实际计算环境版本。

3. Shampine L F, Reichelt M W. The MATLAB ODE Suite.
   SIAM Journal on Scientific Computing, 1997, 18(1):1-22.
   DOI：https://doi.org/10.1137/S1064827594276424
   扫描来源：https://www.et.byu.edu/~beard/papers/library/MatlabOdeSuite.pdf
   当前扫描文件35页，扫描页数与期刊页码1-22含义不同。曾核对题名摘要首页和末页书目，不声称逐页通读。

这些材料保留实际使用范围，不自动增加论文正文引用编号。
''')
    write('04_结果表格/结果表说明.txt','''四问结果表说明

result1.xlsx：问题一完整结果，附录2物性、固定半径、N=3200。
result2.xlsx：问题二完整时空大表，附录3物性、固定半径、N=3200。
result3.xlsx：问题三完整结果，与问题二共享从t=0开始的Q23轨迹；严格报告时刻57.4724小时。
result4.xlsx：问题四完整结果，附录4物性、径向收缩、N=6400；严格报告时刻51.0906小时。

Referrence Table Files内七份q*_paper_*.csv是正文表格数据。

四份工作簿均为final_v6a冻结原件，问题二文件29,210,086字节，完整保留大表。四位小数显示不等于数值精度，严格达标使用未舍入全域最大含水率。问题四域外留空，表面列独立。

源代码在03_程序代码；独立检验源码在05_数值检验与实验。
''')
    for relative,old in protected.items():
        p=DEST/relative
        assert p.is_file() and sha(p)==old, 'Retained data changed: '+relative
    (QA/'main_cleanup_actions.json').write_text(json.dumps({'deleted':deleted,'protected_files_unchanged':len(protected)},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'deleted_files':len(deleted),'retained_data_unchanged':len(protected)},ensure_ascii=False))


if __name__=='__main__':
    main()
