from pathlib import Path
import csv, hashlib, json, shutil, sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path.cwd()
assert ROOT.as_posix() == 'D:/Document/数学建模/2026CUMCM'
OUT = ROOT / 'paper_output/handoff/six_figures_20260912'
QA = ROOT / 'paper_output/qa/figure_package_20260912'
CACHE = ROOT / 'tmp/cache/figure_package_20260912'
for p in (OUT, QA, CACHE): p.mkdir(parents=True, exist_ok=True)
PROD = 'paper_output/results/production/final_v6a/'
old = json.loads((ROOT / 'paper_output/qa/figure_guide_20260912/build_manifest.json').read_text(encoding='utf-8'))
source_paths = [s['path'] for s in old['sources']] + [PROD + 'Q4/summary.json']
copied = {}
sources = []
for src in source_paths:
    p = Path(src)
    if p.name in ('sampled_solution.npz', 'summary.json'):
        rel = Path('原始数据') / p.parent.name / p.name
    elif 'outputs' in p.parts:
        rel = Path('原始数据/正文核对表') / p.name
    else:
        rel = Path('原始数据') / p.name
    dest = OUT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / src, dest)
    sha = hashlib.sha256(dest.read_bytes()).hexdigest()
    prior = next((s for s in old['sources'] if s['path'] == src), None)
    if prior: assert sha == prior['sha256']
    copied[src] = rel.as_posix()
    sources.append({'file': rel.as_posix(), 'source': src, 'sha256': sha})

sheets = []
def add(fig, filename, name, title, note, source, columns, rows):
    rows = [[v.item() if isinstance(v, np.generic) else v for v in row] for row in rows]
    rel = f'CSV/图{fig}/{filename}.csv'
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f); w.writerow(columns); w.writerows(rows)
    sheets.append({'figure': fig, 'name': name, 'title': title, 'note': note,
                   'source': source, 'columns': columns, 'rows': rows, 'csv': rel})

q1src = PROD + 'figures/fig_q1_profiles_data.npz'
with np.load(ROOT / q1src) as a:
    times = a['times_s']; radii = a['radii_m'] * 100
    for field, tag, title, prefix in [('temperature_C', 'temperature', '温度', 'T'), ('C', 'moisture', '含水率', 'C')]:
        columns = ['r_cm'] + [f'{prefix}_{t:g}s' for t in times]
        rows = np.column_stack([radii, a[field].T]).tolist()
        add(1, tag, '图1' + title, '图1 径向' + title + '剖面',
            '首列为物理半径cm；其余七列对应100、300、600、900、1200、1500、1800 s。温度单位°C，含水率为kg水/kg干物质。N3200。',
            copied[q1src] + '；radii_m×100，' + field + '转置', columns, rows)

envsrc = 'paper_output/data_cleaned/A_environment_observed.csv'
with (ROOT / envsrc).open(encoding='utf-8-sig', newline='') as f: env = list(csv.DictReader(f))
add(2, 'observed_0_4h', '图2观测', '图2 环境观测数据 0至4小时',
    '241条真实观测。t=4h末点为50.165°C和0.04986，必须保留。相邻观测点连直线即为分段线性插值。水分指标不是相对湿度%。',
    copied[envsrc], ['time_h', 'temperature_C', 'air_moisture_kg_per_kg'],
    [[float(r[k]) for k in ['time_h', 'temperature_C', 'air_moisture_kg_per_kg']] for r in env])
q23src = PROD + 'Q23/sampled_solution.npz'
q23json = PROD + 'Q23/summary.json'
summary = json.loads((ROOT / q23json).read_text(encoding='utf-8'))
completion = summary['completion']; event = completion['critical_event_s']
assert summary['settings']['tail_temperature_C'] == 50
assert summary['settings']['tail_equilibrium'] == 0.05
add(2, 'assumed_platform_4_60h', '图2假设平台', '图2 4小时后的假设平台',
    '两行是水平线的绘图端点，不是实测。4h仅表示右侧极限，左端开放；60h为展示终点。虚线无实测标记，与观测系列分开。',
    copied[q23json] + '；settings名义延拓，展示终点60h',
    ['time_h', 'temperature_C', 'boundary_moisture_kg_per_kg', 'endpoint_included'],
    [[4.0, 50.0, 0.05, 0], [60.0, 50.0, 0.05, 1]])

with np.load(ROOT / q23src) as a:
    for field, tag, title, limit in [('T_K', 'temperature_0_4h', '温度', 14400.), ('C', 'moisture_to_event', '含水率', event)]:
        mask = a['times_s'] <= limit
        vals = a[field][mask][:, [0, -1]]
        if field == 'T_K': vals = vals - 273.15
        columns = ['time_h', 'centre_T_C', 'surface_T_C'] if field == 'T_K' else ['time_h', 'centre_C_kg_per_kg', 'surface_C_kg_per_kg']
        add(3, tag, '图3' + title, '图3 中心与表面' + title + '响应',
            '采用Q23从0时刻起算的同一轨迹。centre表示中心，surface表示表面；已换算小时和°C，含水率为干基kg/kg。N3200。',
            copied[q23src] + '；times_s/3600，' + field + '首末列', columns,
            np.column_stack([a['times_s'][mask] / 3600, vals]).tolist())
    mask = (a['times_s'] >= event - 120) & (a['times_s'] <= event + 2)
    centre_zoom = np.column_stack([a['times_s'][mask], a['times_s'][mask] - event,
                                  a['C'][mask, 0], a['C'][mask, 0] - 0.15]).tolist()

q3src = PROD + 'figures/fig_q3_drying_data.npz'
with np.load(ROOT / q3src) as a:
    add(4, 'drying_main', '图4主曲线', '图4 全域达标过程',
        'max_C取生产全体节点最大值；中心与最大值重合时不人为错开。threshold_C=0.15。实际曲线止于206902s，之后留空。',
        copied[q3src] + '；times_s/3600，centre_C、surface_C、max_C',
        ['time_h', 'centre_C', 'surface_C', 'max_C', 'threshold_C'],
        np.column_stack([a['times_s']/3600, a['centre_C'], a['surface_C'], a['max_C'], np.full(len(a['times_s']), .15)]).tolist())
    mask = a['times_s'] >= event - 120
    add(4, 'maximum_near_event', '图4全域放大', '图4 临界附近全域最大值保存点',
        '仅两个已保存全域最大值点，含临界根及计算终点。横轴秒差，纵轴max_C_minus_threshold；严格报告点另见图4事件标记。',
        copied[q3src] + '；仅筛选已有点，未新增求解',
        ['time_s', 'delta_time_s', 'max_C', 'max_C_minus_threshold'],
        np.column_stack([a['times_s'][mask], a['times_s'][mask]-event, a['max_C'][mask], a['max_C'][mask]-.15]).tolist())
add(4, 'centre_near_event', '图4中心放大', '图4 临界附近中心含水率保存点',
    '供观察根前走势。这里是中心样点，不应改名为全节点最大值曲线；全域最大值与严格标记请取另外两表。横轴秒差，纵轴centre_C_minus_threshold。',
    copied[q23src] + '；C首列，根前120s至实际终点',
    ['time_s', 'delta_time_s', 'centre_C', 'centre_C_minus_threshold'], centre_zoom)
add(4, 'event_markers', '图4事件标记', '图4 临界根与严格报告点',
    '临界根浓度0.15为等号定义；严格报告点的最大浓度来自实际核验记录，不能用四位舍入替代。kind与strictly_below用于区分标记。',
    copied[q23json] + '；completion',
    ['kind', 'time_s', 'time_h', 'delta_time_s', 'max_C', 'max_C_minus_threshold', 'strictly_below'],
    [['critical_equality', event, completion['critical_event_h'], 0., .15, 0., 0],
     ['strict_report', completion['reported_time_s'], completion['reported_drying_time_h'],
      completion['reported_time_s']-event, completion['max_C_at_reported_time'], completion['max_C_at_reported_time']-.15, 1]])

radsrc = 'paper_output/data_cleaned/A_radius_observed.csv'
with (ROOT / radsrc).open(encoding='utf-8-sig', newline='') as f: rad = list(csv.DictReader(f))
add(5, 'radius_observed', '图5半径', '图5 半径观测序列',
    '145条观测，0至72h，每0.5h一条。横轴小时、纵轴cm；连接相邻点为模型的线性插值。',
    copied[radsrc], ['time_h', 'radius_cm'], [[float(r['time_h']), float(r['radius_cm'])] for r in rad])
q4src = PROD + 'Q4/sampled_solution.npz'
q4json = PROD + 'Q4/summary.json'
q4event = json.loads((ROOT / q4json).read_text(encoding='utf-8'))['completion']['critical_event_s']
with np.load(ROOT / q4src) as a:
    wanted = [0., 6*3600., 12*3600., 24*3600., 48*3600., q4event]
    labels = ['0h', '6h', '12h', '24h', '48h', 'event']
    pairs = []; cols = []; selected = []
    for t, label in zip(wanted, labels):
        idx = np.flatnonzero(a['times_s'] == t)
        assert len(idx) == 1, (t, idx)
        i = int(idx[0]); radius = float(a['radius_m'][i]*100)
        cols += ['r_' + label + '_cm', 'C_' + label]
        pairs += [a['material_x']*radius, a['C'][i]]
        selected.append([label, float(a['times_s'][i]), float(a['times_s'][i]/3600), radius])
    add(5, 'moisture_profiles_xy_pairs', '图5含水率剖面', '图5 六时刻物理半径与含水率',
        '每相邻两列是一组X和Y，共六组，各21点。r已乘各时刻真实R。C为干基kg/kg；各曲线到自身表面结束，域外留空。event的精确时刻见选定时刻表。',
        copied[q4src] + '；r=material_x×radius_m×100，C原值；N6400', cols,
        np.column_stack(pairs).tolist())
    add(5, 'selected_times_and_radii', '图5选定时刻', '图5 六条剖面的时刻与半径',
        '可作为半径曲线上的标记；event为临界根51.09057478683054h。半径已换算cm。',
        copied[q4src] + '；精确匹配保存时刻', ['curve', 'time_s', 'time_h', 'radius_cm'], selected)

isosrc = 'paper_output/results/crossvalidation/isotherm_closure_v1/isotherm_closure.json'
scenarios = json.loads((ROOT / isosrc).read_text(encoding='utf-8'))['scenarios']
assert len(scenarios) == 6
rows = []
for p in [1, 2, 4]:
    vals = []
    for q in ['Q23', 'Q4']:
        matches = [s for s in scenarios if s['scenario'] == f'iso_p{p}_{q}']
        assert len(matches) == 1
        s = matches[0]
        assert s['intervals'] == 800 and s['latentFraction'] == 0 and s['status'] == 'computed_event_only'
        vals.append(s['event_h'])
    rows.append([p, *vals])
add(6, 'scenario_comparison', '图6情景对比', '图6 经验边界阻力情景对比',
    '三行共六点，全部N800且latentFraction=0，使用临界等号事件小时。p=1不能替换为正文生产结果；不加误差棒或置信带。',
    copied[isosrc] + '；六条scenarios的顶层event_h',
    ['p', 'Q23_event_h', 'Q4_event_h'], rows)

payload = {'sheets': sheets}
(CACHE / 'workbook_data.json').write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False), encoding='utf-8')
tables = [{k:v for k,v in s.items() if k != 'rows'} | {'data_rows': len(s['rows'])} for s in sheets]
manifest = {'purpose':'Six-figure plotting handoff with actual data', 'new_model_runs':0,
            'sources': sources, 'tables': tables, 'total_data_rows':sum(len(s['rows']) for s in sheets),
            'source_root_note':'source字段仅作来源追踪；绘图只使用包内file/CSV/Excel，无需原工作区。'}
(OUT / '数据清单.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
(QA / 'export_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
readme = ['A题六图绘图资料包', '',
    '先打开“六图绘图数据.xlsx”，按图号选择工作表。每张表第6行为字段名、第7行起为数值。',
    'Word“六图绘图说明.docx”逐图写明坐标、选列、线型、标记及图注。',
    'CSV目录提供同一套数值，UTF-8 BOM编码，Excel/WPS或Origin可直接导入。',
    '原始数据目录保留15份来源副本，供复核或自定义绘图；普通作图不必读取NPZ或JSON。',
    '所有路径均相对解压后的本文件夹。无需作者电脑、D盘路径、工作区或额外下载。', '',
    '数据精度：CSV保留Python双精度往返表示；Excel单元格为数值，显示小数位不代表数据已舍入。',
    '本包是冻结结果的导出，未重跑模型。图1/3/4为N3200，图5为N6400，图6均为N800。',
    '图2观测与4h后平台必须分开。平台表的4h表示开放左端的右侧极限，不是新的观测点。',
    '图4中心放大表只标中心样点；全域最大值与严格达标点使用对应数据表。',
    '图5每两列一组XY，横轴半径随时刻变化，不可给六条曲线套同一半径列。', '', '文件与工作表对应：']
readme += [f"图{s['figure']} | Excel：{s['name']} | {s['csv']} | {len(s['rows'])}条" for s in sheets]
(OUT / '请先阅读.txt').write_text('\n'.join(readme)+'\n', encoding='utf-8-sig')
print(json.dumps({'out':OUT.relative_to(ROOT).as_posix(), 'tables':len(sheets), 'rows':manifest['total_data_rows'], 'original_sources':len(sources)}, ensure_ascii=False))
