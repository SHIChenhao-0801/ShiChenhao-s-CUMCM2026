"""Correct explanatory scope only; preserve every displayed model equation and result."""
from pathlib import Path
import hashlib,json,re
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[3]
assert Path.cwd().resolve()==ROOT
OUT=Path(__file__).resolve().parent
BASE=ROOT/'notes/A-modeling/2026-09-10'
changes=[]
for name in ['A题_完整建模与公式推导.md','A题_建模浓缩交接.md']:
    p=BASE/name
    original=p.read_text(encoding='utf-8')
    text=original
    pairs=[]
    if '完整' in name:
        pairs=[
        ('推导：随材料运动薄壳的显热积累取B D_tT；净传导热流由M07/M08得到。这里假设忽略机械功、辐射、化学热、湿分迁移携带显焓、显式相变潜热。固定骨架u=0；收缩骨架u另行给出。题给B作为有效热物性闭合，不能称为完整多相能量守恒。',
         '推导与闭合应分两步：M07/M08给出净传导项；若从M21的组分显焓守恒出发，实际热容量为ρd(cd+Ccw)，且保留水分携焓梯度项。只有另行忽略该项并采用B=ρeff cp作为有效容量约定，才得到M09。固定骨架u=0；收缩骨架u另行给出。机械功、辐射、化学热与显式相变潜热也未纳入。B随C变化本身不构成推导错误，但B等于真实组分容量并未由题给数据证明，不能把M09称为完整多相能量守恒的无条件结论。'),
        ('附件首个低于该必要界的记录在19.5h。',
         '将附件打印值视为精确数时，首个低于该必要界的采样点在19.5h；这不是已确定的真实不相容起始时刻。'),
        ('因此仅凭C≥0、初始干质量与输入半径，19.5h就已能确认不相容。',
         '因此将经验式与附件打印值均视为精确时，该采样点已违反联合模型的必要条件。不过1.211cm距界仅约2.03μm；若三位小数半径是四舍五入值，其半个显示单位为5μm，题目又未给实测/拟合误差，不能把19.5h认作已确定的真实物理不相容起始时刻。'),
        ('常系数有限圆柱可由径向Bessel解乘轴向平板解作廉价尺度核查；完整非线性二维才可直接量化所选模型端面差异。',
         '常系数、均匀初值、恒定阶跃环境并具有可分离齐次Robin边界时，有限圆柱的归一化齐次衰减响应可写成径向Bessel响应与轴向平板响应的乘积。任意时变环境应对这个联合阶跃响应作Duhamel卷积，不能把两个分别受迫的时变解直接相乘；完整非线性二维才可直接量化本次所选模型的端面差异。')]
    else:
        pairs=[
        ('水守恒减去C倍干守恒，再取u=0、ρd均匀恒定即得水方程。热方程省略显式潜热、迁移携焓、辐射及机械功。',
         '水守恒减去C倍干守恒，再取u=0、ρd均匀恒定即得水方程。热方程采用题给ρeff cp作为有效热容量，并省略显式潜热、迁移携焓、辐射及机械功；从完整组分显焓守恒推到此式还需要这一容量约定，不能把它当作由所有题给密度含义无条件推出。'),
        ('附件首个低于必要半径界的记录是19.5h、R=1.211cm；72h即使全干也最多容纳初始97.831743%的干质量。',
         '将打印值与经验式视为精确时，首个违反必要半径界的采样点为19.5h、R=1.211cm；该点距界仅约2.03μm，小于三位小数半径可能的5μm半个显示单位，不能认作真实不相容的精确起点。72h按字面给定模型，即使全干也最多容纳初始97.831743%的干质量；真实测量和经验式误差仍未给出。')]
    for old,new in pairs:
        count=text.count(old)
        if count!=1:
            raise ValueError((name,count,old[:65]))
        text=text.replace(old,new)
        changes.append({'document':name,'old':old,'new':new})
    before_eq=re.findall(r'\\\[(.*?)\\\]',original,re.S)
    after_eq=re.findall(r'\\\[(.*?)\\\]',text,re.S)
    assert before_eq==after_eq
    p.write_text(text,encoding='utf-8')
(OUT/'explanatory_corrections.json').write_text(json.dumps({'created_at_utc':datetime.now(timezone.utc).isoformat(),'changes':changes,'changed_equations':False,'changed_solver':False,'changed_numerical_results':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'corrected_passages':len(changes),'display_equations_preserved':True,'solver_and_results_changed':False},ensure_ascii=False))
