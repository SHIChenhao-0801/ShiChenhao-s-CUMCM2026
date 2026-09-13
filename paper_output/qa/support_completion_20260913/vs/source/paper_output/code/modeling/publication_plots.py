from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[3]
SOURCE=Path(__file__).resolve()
LOADED_PLOT_SHA256=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'tmp/cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
from matplotlib import font_manager
from matplotlib.colors import Normalize
from matplotlib.ticker import NullLocator
import matplotlib.pyplot as plt

FONT_PATH=Path('C:/Windows/Fonts/msyh.ttc')
if not FONT_PATH.exists():
    raise RuntimeError('Verified Chinese font Microsoft YaHei is unavailable')
font_manager.fontManager.addfont(str(FONT_PATH))
FONT_NAME=font_manager.FontProperties(fname=str(FONT_PATH)).get_name()
STYLE={'font.family':FONT_NAME,'font.size':10,'axes.titlesize':11,'axes.labelsize':10,
       'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False,
       'legend.frameon':False,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'path',
       'savefig.facecolor':'white','figure.facecolor':'white','axes.facecolor':'white'}
COLOURS={'centre':'#2563A6','mean':'#C76829','surface':'#218573','threshold':'#51555D'}


def _sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def _record(path):
    p=Path(path).resolve()
    return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':_sha(p),'exists':True}


def _directory(directory):
    p=Path(directory).resolve()
    if not p.is_relative_to(ROOT) or p.is_relative_to(ROOT/'problem_files'):
        raise ValueError('Write figures only inside the competition workspace outside original inputs')
    p.mkdir(parents=True,exist_ok=True)
    return p


def _run_source(run):
    module=sys.modules[run.model.__class__.__module__]
    path=Path(inspect.getfile(run.model.__class__)).resolve()
    if getattr(module,'LOADED_CODE_SHA256',_sha(path))!=_sha(path):
        raise RuntimeError('Core changed after import; regenerate figure from a consistent Run')
    records=[_record(path)]
    jac=path.with_name('analytic_jacobian.py')
    if jac.exists():records.append(_record(jac))
    for rec in run.model.input_records:
        if _sha(ROOT/rec['path'])!=rec['sha256']:
            raise RuntimeError('Run input changed: '+rec['path'])
        records.append(rec)
    return {'kind':'live_Run','settings':asdict(run.model.settings),'files':records,
            'event_s':None if run.event_s is None else float(run.event_s),'end_s':float(run.end_s)}


def _unchanged(sources):
    if _sha(SOURCE)!=LOADED_PLOT_SHA256:
        raise RuntimeError('Plot module changed after import')
    for source in sources:
        for rec in source.get('files',[]):
            if _sha(ROOT/rec['path'])!=rec['sha256']:
                raise RuntimeError('Source changed during figure generation: '+rec['path'])


def _save(fig,figure_id,qid,title,caption,directory,sources,data,extra=None):
    directory=_directory(directory)
    _unchanged(sources)
    data_path=directory/(figure_id+'_data.npz')
    np.savez_compressed(data_path,**data)
    artifacts={}
    for ext in ['png','svg','pdf']:
        path=directory/(figure_id+'.'+ext)
        fig.savefig(path,dpi=210 if ext=='png' else 160,bbox_inches='tight',pad_inches=.14)
        artifacts[ext]=_record(path)
    plt.close(fig)
    _unchanged(sources)
    record={'figure_id':figure_id,'question_id':qid,'title':title,'caption':caption,
            'purpose':caption,'path':artifacts['png']['path'],
            'bytes':artifacts['png']['bytes'],'sha256':artifacts['png']['sha256'],
            'status':'computed','ok':True,'placeholder':False,'exists':True,
            'artifacts':artifacts,'plot_data':_record(data_path),'sources':sources,
            'generated_by':'paper_output/code/modeling/publication_plots.py',
            'source_code_sha256':LOADED_PLOT_SHA256,
            'generated_at':datetime.now(timezone.utc).isoformat(),
            'font':{'name':FONT_NAME,'file':str(FONT_PATH)},
            'visual_review':'pending','human_review':'pending','visual_studio_gui':'pending'}
    if extra:record.update(extra)
    metadata=directory/(figure_id+'.json')
    metadata.write_text(json.dumps(record,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    record['metadata']=_record(metadata)
    return record


def _footer(fig,text):
    fig.text(.5,.015,text,ha='center',va='bottom',fontsize=8.1,color='#52565E',linespacing=1.45)


def _environment_note(run):
    s=run.model.settings
    if s.boundary_extension=='nominal':
        return f'4 h 后环境延拓为 {s.tail_temperature_C:g} °C、等效平衡含水率 {s.tail_equilibrium*s.equilibrium_scale:g} kg/kg'
    if s.boundary_extension=='tail_mean':return '4 h 后环境按末 1 h 观测均值延拓'
    return '4 h 后环境按最后观测值延拓'


def _profiles(run,qid,directory):
    source=_run_source(run)
    if qid=='Q1':
        ts=np.array([100.,300.,600.,900.,1200.,1500.,1800.])
        labels=[f'{t:g} s' for t in ts]
        title='第一问：预热阶段的径向温湿分布'
    else:
        ts=np.arange(1,7,dtype=float)*1800
        labels=[f'{t/3600:g} h' for t in ts]
        title='第二问：前三小时的径向温湿分布'
    if run.end_s<ts[-1]-1e-7:
        raise ValueError('Run does not cover all question-specific plot times')
    rs=np.linspace(0,.02,121)
    T,C=run.fields(ts,radii_m=rs);T=T-273.15
    with plt.rc_context(STYLE):
        fig,axes=plt.subplots(1,2,figsize=(11.8,4.8))
        fig.subplots_adjust(left=.075,right=.97,bottom=.245,top=.82,wspace=.28)
        colours=plt.get_cmap('viridis')(np.linspace(.08,.9,len(ts)))
        handles=[]
        for i,(label,colour) in enumerate(zip(labels,colours)):
            handle,=axes[0].plot(rs*100,T[i],color=colour,lw=1.7,label=label)
            handles.append(handle)
            axes[1].plot(rs*100,C[i],color=colour,lw=1.7,label=label)
        for ax in axes:
            ax.set_xlim(0,2);ax.set_xticks([0,.5,1,1.5,2]);ax.set_xlabel('到药材中心的距离 / cm')
            ax.grid(alpha=.2,lw=.7)
        axes[0].set(title='（a）温度',ylabel='温度 / °C')
        axes[1].set(title='（b）干基含水率',ylabel='干基含水率 / (kg/kg)')
        fig.suptitle(title,y=.97,fontsize=14,fontweight='bold')
        fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.5,.075),ncol=len(labels),fontsize=9)
        _footer(fig,'一维径向有效模型的条件性数值结果；忽略端面与显式潜热，环境水分按等效平衡边界处理。')
        return _save(fig,f'fig_{qid.lower()}_profiles',qid,title,
            '各曲线对应题目指定时刻。温度采用摄氏度，水分采用干基；曲线来自同一live Run的物理径向点值。',
            directory,[source],{'times_s':ts,'radii_m':rs,'temperature_C':T,'C':C},
            {'sample_time_count':len(ts),'sample_radius_count':len(rs)})


def _drying(run,qid,directory):
    source=_run_source(run)
    if run.event_s is None:
        raise ValueError('Full drying figure requires an actual threshold event')
    if qid=='Q4' and not run.model.settings.shrink:
        raise ValueError('Q4 primary figure must show the shrinking-domain run')
    radius_knots=run.model.rad['time_s'] if qid=='Q4' else np.array([])
    radius_knots=radius_knots[radius_knots<=run.end_s]
    ts=np.unique(np.r_[np.linspace(0,run.end_s,241),
                       np.arange(0,min(run.end_s,14400)+1,600),
                       radius_knots,run.event_s,run.end_s])
    rs=np.linspace(0,.02,121)
    _,C=run.fields(ts,radii_m=rs)
    R=np.asarray(run.model.radius(ts))
    inside=rs[None,:] <= R[:,None]+1e-12
    C=np.where(inside,C,np.nan)
    _,ends=run.fields(ts,material_x=[0.,1.])
    state=run.state(ts)
    mean=2*run.model.w@state[1:-1:2]
    max_C=np.max(state[1:-1:2],axis=0)
    del state
    t_h=ts/3600;event_h=run.event_s/3600
    title=('第三问：固定半径下的全程水分迁移' if qid=='Q3' else '第四问：收缩域内的全程水分迁移')
    with plt.rc_context(STYLE):
        fig,axes=plt.subplots(1,2,figsize=(12,5.1),gridspec_kw={'width_ratios':[1.08,1]})
        fig.subplots_adjust(left=.065,right=.965,bottom=.21,top=.83,wspace=.31)
        cmap=plt.get_cmap('YlGnBu').copy();cmap.set_bad('white')
        mesh=axes[0].pcolormesh(t_h,rs*100,np.ma.masked_invalid(C.T),shading='auto',
                              cmap=cmap,norm=Normalize(vmin=.05,vmax=2.55),rasterized=True)
        cb=fig.colorbar(mesh,ax=axes[0],pad=.025,fraction=.05)
        cb.set_label('干基含水率 / (kg/kg)',fontsize=9)
        if qid=='Q4':


            axes[0].fill_between(t_h,R*100,2,color='white',zorder=3)
            axes[0].plot(t_h,R*100,color='#202631',lw=1.8,label='药材表面 R(t)',zorder=4)
            axes[0].text(.65*t_h[-1],1.88,'域外（非药材）',ha='center',va='center',fontsize=9,color='#62666D')
            axes[0].legend(loc='lower right',fontsize=8.5,facecolor='white',framealpha=.85,frameon=True)
        axes[0].set(xlim=(0,t_h[-1]),ylim=(0,2),xlabel='烘干时间 / h',
                    ylabel='物理径向距离 / cm',title='（a）物理空间中的含水率')
        for series,name,colour in [(ends[:,0],'中心',COLOURS['centre']),
                                  (mean,'干质量加权均值',COLOURS['mean']),
                                  (ends[:,1],'表面',COLOURS['surface'])]:
            axes[1].plot(t_h,series,lw=1.8,label=name,color=colour)
        axes[1].axhline(.15,color=COLOURS['threshold'],ls='--',lw=1.25,label='阈值 0.15 kg/kg')
        axes[1].axvline(event_h,color='#6D6473',ls=':',lw=1.2)
        axes[1].annotate(f'全域临界时刻\n{event_h:.3f} h',xy=(event_h,.15),
                         xytext=(.67*t_h[-1],.64),arrowprops={'arrowstyle':'->','color':'#625A6A'},
                         fontsize=9,ha='center',va='center',color='#514956')
        axes[1].set(xlim=(0,t_h[-1]*1.015),ylim=(0,2.66),xlabel='烘干时间 / h',
                    ylabel='干基含水率 / (kg/kg)',title='（b）中心、均值与表面的变化')
        axes[1].legend(loc='upper right',fontsize=8.8);axes[1].grid(alpha=.18)
        if t_h[-1]>4:
            axes[0].axvline(4,color='#666A73',ls=':',lw=.85,alpha=.8)
            axes[0].text(4+.025*t_h[-1],.13,'4 h',fontsize=8,color='#52545A')
        fig.suptitle(title,y=.97,fontsize=14,fontweight='bold')
        footer='一维径向有效模型；均值按干物质质量加权，达标条件取全域最大值。\n'+_environment_note(run)+'。'
        if qid=='Q4' and run.end_s>259200:
            footer+=' 半径超过 72 h 后采用末值延拓。'
        _footer(fig,footer)
        return _save(fig,f'fig_{qid.lower()}_drying',qid,title,
                     '左图为物理半径与时间的水分场；第四问域外留白，黑线为实测半径轨迹的插值。右图显示中心、干质量加权均值、表面及全域阈值事件。',
                     directory,[source],{'times_s':ts,'radii_m':rs,'radius_m':R,'C':C,
                         'centre_C':ends[:,0],'mean_C':mean,'surface_C':ends[:,1],'max_C':max_C},
                     {'event_s':float(run.event_s),'post_verification_s':float(run.end_s),
                      'masked_outside_count':int(np.count_nonzero(~inside)),
                      'sample_time_count':len(ts),'sample_radius_count':len(rs),
                      'mean_definition':'2*sum(material_dual_cell_weights*C); dry-solid mass weighting'})


def make_plots(runs,directory):

    run1=runs['Q1'];run23=runs.get('Q23',runs.get('Q2'));run4=runs['Q4']
    if run23 is None:raise ValueError('Provide the shared Q2/Q3 Run under Q23 or Q2')
    return [_profiles(run1,'Q1',directory),_profiles(run23,'Q2',directory),
            _drying(run23,'Q3',directory),_drying(run4,'Q4',directory)]


def _saved_summary(path):
    path=Path(path).resolve()
    content=path.read_bytes()
    rec=_record(path)
    if hashlib.sha256(content).hexdigest()!=rec['sha256']:
        raise RuntimeError('Evidence file changed while being read')
    data=json.loads(content)
    diag=data['diagnostics']
    if not diag.get('solver_success') or not diag.get('strictly_dry_at_end') or diag.get('event_h') is None:
        raise ValueError('Comparison requires a completed successful drying run')


    src={'kind':'saved_completed_run_summary','files':[rec],
         'recorded_solver_code':data.get('code'),'settings':data['settings'],
         'current_solver_equivalence_not_assumed':True}
    return data,src


def make_shrinkage_comparison(fixed_summary_path,shrunk_summary_path,directory):
    fixed,sf=_saved_summary(fixed_summary_path);shrunk,ss=_saved_summary(shrunk_summary_path)
    a,b=fixed['settings'],shrunk['settings']
    if a['question']!='Q4' or b['question']!='Q4' or a['shrink'] or not b['shrink']:
        raise ValueError('Require matched appendix-4 fixed and shrinking runs')
    differences={k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
    if differences!={'shrink'} or fixed.get('code',{}).get('sha256')!=shrunk.get('code',{}).get('sha256'):
        raise ValueError('A pure shrinkage comparison needs identical settings/source except shrink')
    values=np.array([fixed['diagnostics']['event_h'],shrunk['diagnostics']['event_h']])
    N=a['intervals'];reduction=100*(1-values[1]/values[0])
    title='同附录4物性下的固定半径与收缩对照'
    with plt.rc_context(STYLE):
        fig,ax=plt.subplots(figsize=(8.2,4.7));fig.subplots_adjust(left=.2,right=.92,bottom=.22,top=.81)
        ax.barh([1,0],values,color=['#8894A3','#218573'],height=.5)
        ax.set_yticks([1,0],['固定半径 2 cm','采用附件2收缩'])
        ax.set_xlim(0,values.max()*1.25);ax.set_xlabel('全域临界烘干时间 / h');ax.grid(axis='x',alpha=.18)
        for y,v in zip([1,0],values):ax.text(v+values.max()*.02,y,f'{v:.3f} h',va='center',fontsize=10)
        ax.text(.98,.12,f'本对照缩短 {reduction:.2f}%',transform=ax.transAxes,ha='right',color='#246653',fontsize=11)
        fig.suptitle(title,y=.95,fontsize=14,fontweight='bold')
        _footer(fig,f'同一已保存计算版本，N={N}，除收缩开关外设置一致；这是有效模型中的尺寸效应。\n不可把第三、四问同时改变物性的时长差直接归因于收缩。')
        return _save(fig,'fig_q4_shrinkage_control','Q4',title,
                     f'已保存同物性、同参数、同源码版本N={N}对照；读取来源原始哈希，未假设与后续细网格正式结果相同。',
                     directory,[sf,ss],{'event_hours':values},
                     {'intervals':N,'same_property_control':True,'reduction_percent':float(reduction)})


def make_convergence_plot(report_paths,directory):

    sources=[];groups=[]
    for path in report_paths:
        path=Path(path).resolve();content=path.read_bytes();data=json.loads(content);rec=_record(path)
        if hashlib.sha256(content).hexdigest()!=rec['sha256']:raise RuntimeError('Changing convergence report')
        if not data.get('finished_at') or not str(data.get('status','')).startswith('computed'):
            raise ValueError('Select only finished convergence reports; in-progress reports are not plotted')
        groups.append(data);sources.append({'kind':'finished_convergence_report','files':[rec]})
    if not groups:raise ValueError('At least one finished convergence report is required')
    labels={'Q1':'第一问','Q23':'第二、三问','Q4':'第四问'}
    colours={'Q1':'#2563A6','Q23':'#C76829','Q4':'#218573'}
    title='相邻网格结果差异与临界时刻收敛'
    plotted={}
    with plt.rc_context(STYLE):
        fig,axes=plt.subplots(1,2,figsize=(11.5,4.8));fig.subplots_adjust(left=.08,right=.965,bottom=.21,top=.82,wspace=.32)
        for group in groups:
            q=group['question'];comp=group['comparisons']
            x=np.array([c['fine_N'] for c in comp],dtype=float)
            y=np.array([c['max_absolute_difference']['C'] for c in comp],dtype=float)
            axes[0].loglog(x,y,'o-',color=colours.get(q),label=labels.get(q,q),lw=1.6)
            timed=[c for c in comp if c.get('event_difference_s') is not None]
            if timed:
                axes[1].loglog([c['fine_N'] for c in timed],[abs(c['event_difference_s']) for c in timed],
                               'o-',color=colours.get(q),label=labels.get(q,q),lw=1.6)
            plotted[q+'_fine_N']=x;plotted[q+'_C_difference']=y
        axes[0].set(title='（a）共同物理采样点的最大含水率差',xlabel='较细网格的区间数 N',ylabel='相邻网格最大差 / (kg/kg)')
        axes[1].set(title='（b）全域临界时刻的变化',xlabel='较细网格的区间数 N',ylabel='相邻网格临界时刻差的绝对值 / s')
        all_ticks=sorted({c['fine_N'] for g in groups for c in g['comparisons']})
        time_ticks=sorted({c['fine_N'] for g in groups for c in g['comparisons'] if c.get('event_difference_s') is not None})
        axes[0].set_xticks(all_ticks,[str(n) for n in all_ticks])
        if time_ticks:axes[1].set_xticks(time_ticks,[str(n) for n in time_ticks])
        for ax in axes:
            ax.xaxis.set_minor_locator(NullLocator())
            ax.grid(which='both',alpha=.2);ax.legend(fontsize=9)
        fig.suptitle(title,y=.97,fontsize=14,fontweight='bold')
        _footer(fig,'读取已完成检验报告并记录来源哈希；相邻网格差用于数值收敛检验，不是实测预测误差。')
        return _save(fig,'fig_model_grid_convergence','Q3',title,
                     '横轴为相邻比较中较细网格的区间数；所画为实际计算的最大含水率差和阈值时刻差，不把相邻差直接称作严格误差上界。',
                     directory,sources,plotted,{'question_ids':[g['question'] for g in groups]})


def make_sensitivity_plot(summary_paths,directory,question_id='Q4',baseline_label='基准'):

    if baseline_label not in summary_paths:raise ValueError('An explicit baseline label is required')
    labels=list(summary_paths);rows=[];sources=[]
    for label,path in summary_paths.items():
        data,source=_saved_summary(path);rows.append(data);sources.append(source)
    if len({r['settings']['intervals'] for r in rows})!=1 or len({r['settings']['question'] for r in rows})!=1:
        raise ValueError('Sensitivity cases must have a common question and grid size')
    expected={'Q4'} if question_id=='Q4' else {'Q2','Q3','Q23'}
    if rows[0]['settings']['question'] not in expected:
        raise ValueError('Sensitivity figure label does not match the saved physical question')
    if len({r.get('code',{}).get('sha256') for r in rows})!=1:
        raise ValueError('Sensitivity cases must use the same saved source version')
    values=np.array([r['diagnostics']['event_h'] for r in rows]);baseline=values[labels.index(baseline_label)]
    delta=100*(values/baseline-1);N=rows[0]['settings']['intervals']
    title=('第四问' if question_id=='Q4' else '第二、三问')+'：物理假设与参数情景比较'
    with plt.rc_context(STYLE):
        fig,ax=plt.subplots(figsize=(9.4,max(4.7,.48*len(labels)+1.8)))
        fig.subplots_adjust(left=.25,right=.93,bottom=.2,top=.82)
        pos=np.arange(len(labels));colours=['#8A949F' if x==baseline_label else '#218573' for x in labels]
        ax.barh(pos,values,color=colours,height=.58);ax.set_yticks(pos,labels);ax.invert_yaxis()
        ax.set_xlim(0,values.max()*1.33);ax.set_xlabel('全域临界烘干时间 / h');ax.grid(axis='x',alpha=.18)
        for y,v,d in zip(pos,values,delta):ax.text(v+values.max()*.015,y,f'{v:.3f} h（{d:+.2f}%）',va='center',fontsize=9)
        fig.suptitle(title,y=.95,fontsize=14,fontweight='bold')
        _footer(fig,f'同一已保存求解版本，N={N}；百分比相对“{baseline_label}”。这些是指定情景的模型变化，不是统计置信区间。')
        return _save(fig,f'fig_{question_id.lower()}_physical_sensitivity',question_id,title,
                     '读取明确列出的已完成情景，并记录每份摘要哈希、设置和原计算版本；不将情景差异当作观测误差。',
                     directory,sources,{'event_hours':values,'relative_change_percent':delta},
                     {'scenario_labels':labels,'baseline_label':baseline_label,'intervals':N})


def make_question_plot(run, question_id, directory):

    if question_id in ('Q1', 'Q2'):
        return _profiles(run, question_id, _directory(directory))
    if question_id in ('Q3', 'Q4'):
        return _drying(run, question_id, _directory(directory))
    raise ValueError('A question plot requires Q1, Q2, Q3 or Q4')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--selfcheck',action='store_true')
    parser.add_argument('--output-dir',default='paper_output/results/plot_selfcheck');args=parser.parse_args()
    if not args.selfcheck:parser.error('Use make_plots with live Runs or --selfcheck')
    if Path.cwd().resolve()!=ROOT:raise RuntimeError('Run from the competition workspace')
    from drying_core import Settings,solve_case
    runs={}
    for q in ['Q1','Q23','Q4']:
        print('Selfcheck: solving '+q+' with N=40',flush=True)
        runs[q]=solve_case(Settings(question=q,intervals=40,face_scheme='kirchhoff',shrink=q=='Q4',
                                  rtol=1e-7,atol_temperature=1e-7,atol_moisture=1e-9))
    output=_directory(ROOT/args.output_dir)
    records=make_plots(runs,output)
    fixed=ROOT/'paper_output/results/experiments/physical_Q4_fixed_N200_K/summary.json'
    shrunk=ROOT/'paper_output/results/experiments/grids_Q4_N200_K/summary.json'
    if fixed.exists() and shrunk.exists():records.append(make_shrinkage_comparison(fixed,shrunk,output))
    reports=[ROOT/f'paper_output/results/convergence/{q}_K_analytic_J_v3/convergence_report.json' for q in ['Q1','Q23']]
    if all(p.exists() for p in reports):records.append(make_convergence_plot(reports,output))
    scenario_root=ROOT/'paper_output/results/experiments'
    scenarios={'基准':shrunk,'4 h 后环境 49 °C':scenario_root/'physical_Q4_T49_N200_K/summary.json',
               '4 h 后环境 51 °C':scenario_root/'physical_Q4_T51_N200_K/summary.json',
               '潜热能量负荷压力测试':scenario_root/'physical_Q4_latent_N200_K/summary.json'}
    if all(p.exists() for p in scenarios.values()):records.append(make_sensitivity_plot(scenarios,output))
    report={'scope':'N40 live-run plot selfcheck; primary plots are not final numerical results. Optional comparisons preserve their independent N200/finished-report sources.',
            'status':'GENERATED_PENDING_VISUAL_REVIEW','figures':records}
    (output/'plot_selfcheck_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'figure_count':len(records),'output':str(output)},ensure_ascii=False),flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
