from pathlib import Path
import sys, json
ROOT=Path(__file__).resolve().parent
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

A=ROOT/'analysis';F=ROOT/'figures';F.mkdir(exist_ok=True)
OLD=ROOT.parent/'analysis_scripts'
d=pd.read_csv(A/'robustness_experiments.csv')
c=pd.read_csv(A/'component_experiments.csv')
settings=pd.read_csv(A/'experiment_settings.csv')
assert len(d)==1020 and not d.duplicated(['condition_id','mode_id','seed']).any()
assert len(c)==120 and not c.duplicated(['component_id','seed']).any()
assert np.isfinite(d.to_numpy()).all() and np.isfinite(c.to_numpy()).all()
assert all(set(g.seed)==set(range(20)) for _,g in d.groupby(['condition_id','mode_id']))
assert all(set(g.seed)==set(range(20)) for _,g in c.groupby('component_id'))
old=json.loads((OLD/'analysis/summary.json').read_text())
modes={1:'COOP',2:'ECO',3:'PASSIVE'}
colors={1:'#AD332B',2:'#1A6B4D',3:'#3D5294'}
markers={1:'o',2:'s',3:'^'}
linestyles={1:'-',2:'--',3:'-.'}
metrics=['completion','fuel_L100','speed_sd','acceleration_rms','stopped_vehicle_s','mean_speed','total_fuel_L','minimum_gap','jerk_rms','hdv_filter_count','cav_filter_count','filter_mean_delta','mean_information_age','maximum_information_age','hold_events','hold_vehicle_s']
def ci(v):
    v=np.asarray(v,float);mu=float(v.mean());sd=float(v.std(ddof=1));half=stats.t.ppf(.975,len(v)-1)*sd/np.sqrt(len(v))
    return {'mean':mu,'low':float(mu-half),'high':float(mu+half),'sd':sd,'n':len(v)}
summ=[]
for (cond,mode),g in d.groupby(['condition_id','mode_id']):
    row={'condition_id':int(cond),'condition':settings.iloc[int(cond)-1]['condition'],'mode':modes[mode], 'mode_id':int(mode),'runs':len(g),'runs_with_overlap':int((g.violations>0).sum()),'negative_gap_samples':int(g.violations.sum()),'minimum_observed_gap':float(g.minimum_gap.min()),'minimum_completion':float(g.completion.min())}
    for met in metrics:
        for k,v in ci(g[met]).items():row[met+'_'+k]=v
    summ.append(row)
s=pd.DataFrame(summ);s.to_csv(A/'robustness_summary.csv',index=False)

contrasts=[]
for cond in range(1,18):
    ec=d[(d.condition_id==cond)&(d.mode_id==2)].sort_values('seed')
    for bm in [1,3]:
        base=d[(d.condition_id==cond)&(d.mode_id==bm)].sort_values('seed')
        for met in metrics[:9]:
            raw=ec[met].to_numpy()-base[met].to_numpy();est=ci(raw)
            p=float(stats.ttest_1samp(raw,0).pvalue) if est['sd']>1e-14 else (1.0 if abs(est['mean'])<1e-12 else np.nan)
            contrasts.append({'condition_id':cond,'baseline':modes[bm],'metric':met,'direction':'ECO minus baseline','mean_difference':est['mean'],'ci_low':est['low'],'ci_high':est['high'],'p_t':p,'dz':est['mean']/est['sd'] if est['sd']>1e-14 else np.nan,'n':20})
contr=pd.DataFrame(contrasts);contr['p_holm']=np.nan
for _,g in contr.groupby(['baseline','metric']):
    vals=g.p_t.fillna(1).to_numpy();order=np.argsort(vals);adjusted=np.minimum(1,np.maximum.accumulate(vals[order]*np.arange(len(vals),0,-1)));res=np.empty_like(adjusted);res[order]=adjusted;contr.loc[g.index,'p_holm']=res
contr.to_csv(A/'robustness_paired_contrasts.csv',index=False)

paired=[]
for cond in range(2,18):
    for mode in range(1,4):
        base=d[(d.condition_id==1)&(d.mode_id==mode)].sort_values('seed')
        alt=d[(d.condition_id==cond)&(d.mode_id==mode)].sort_values('seed')
        for met in ['fuel_L100','jerk_rms','completion','mean_speed']:
            delta=alt[met].to_numpy()-base[met].to_numpy();est=ci(delta)
            row={'condition_id':cond,'mode_id':mode,'metric':met,'mean_difference':est['mean'],'ci_low':est['low'],'ci_high':est['high']}
            if met!='completion':
                q=ci(delta/base[met].to_numpy()*100);row.update(relative_pct=q['mean'],relative_low=q['low'],relative_high=q['high'])
            paired.append(row)
pd.DataFrame(paired).to_csv(A/'robustness_vs_ideal.csv',index=False)

component_names={1:'Ramp timing',2:'Scheduling',3:'Weights and gain',4:'Acceleration limit',5:'Admission',6:'Spacing buffer'}
base=d[(d.condition_id==1)&(d.mode_id==2)].sort_values('seed')
comp=[]
for cid,g in c.groupby('component_id'):
    g=g.sort_values('seed');e=ci((g.fuel_L100.to_numpy()/base.fuel_L100.to_numpy()-1)*100)
    comp.append({'component_id':int(cid),'component':component_names[cid],'fuel_change_pct':e,'minimum_gap':float(g.minimum_gap.min()),'negative_gap_samples':int(g.violations.sum()),'minimum_completion':float(g.completion.min())})

summary={'robustness_runs':len(d),'component_runs':len(c),'conditions':settings.to_dict('records'),'groups':summ,'components':comp,'vs_ideal':paired,'new_negative_gap_runs':int((d.violations>0).sum()),'notes':['Negative net gap denotes simulated longitudinal overlap, not a count of distinct crashes.','CAV broadcast failures are shared per transmitting vehicle per time step, not independently sampled per receiver.','Neighbor identities and lane/role labels use exact discrete states; nominal CAV controllers use delayed noisy longitudinal states.','Fuel outcomes from overlap runs are retained for transparency but do not establish usable performance.','Pointwise intervals are descriptive and do not incorporate model-form or external-population uncertainty.']}
(A/'round2_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')

plt.rcParams.update({'font.family':'Times New Roman','font.size':9,'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,'axes.linewidth':.7,'lines.linewidth':1.2,'savefig.facecolor':'white','axes.unicode_minus':True})
def style(ax):
    ax.tick_params(direction='in',top=True,right=True,length=3,width=.65)
    ax.grid(axis='y',color='#dddddd',linewidth=.45);ax.set_axisbelow(True)
def panel(ax,label):ax.set_title(label,fontsize=9,loc='left',pad=7);style(ax)
def save(fig,n):
    fig.savefig(F/f'Fig{n}.png',dpi=350)
    fig.savefig(F/f'Fig{n}.tif',dpi=600,pil_kwargs={'compression':'tiff_lzw'})
    fig.savefig(F/f'Fig{n}.pdf')
    for i,ax in enumerate(fig.axes):
        bbox=ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted()).expanded(1.015,1.035)
        fig.savefig(F/f'Fig{n}{chr(97+i)}.pdf',bbox_inches=bbox)
    plt.close(fig)
def errors(ax,x,rows,key='mean',lo='low',hi='high',**kwargs):
    y=np.array([r[key] for r in rows]);lower=y-np.array([r[lo] for r in rows]);upper=np.array([r[hi] for r in rows])-y
    ax.errorbar(x,y,yerr=[np.maximum(0,lower),np.maximum(0,upper)],capsize=2,markersize=4,**kwargs)
def series(ax,conds,metric,labels=None):
    numeric=labels is not None and all(str(v).replace('.','',1).isdigit() for v in labels)
    x=np.array(labels,dtype=float) if numeric else np.arange(len(conds))
    for m in [1,2,3]:
        rows=[]
        for cond in conds:
            v=s[(s.condition_id==cond)&(s.mode_id==m)].iloc[0];rows.append({'mean':v[metric+'_mean'],'low':v[metric+'_low'],'high':v[metric+'_high']})
        errors(ax,x,rows,color=colors[m],marker=markers[m],linestyle=linestyles[m],label=modes[m])
    ax.set_xticks(x,labels if labels is not None else [str(v) for v in conds])
    margin=max(.001,float(np.ptp(x))*.07) if numeric else .3
    ax.set_xlim(x[0]-margin,x[-1]+margin);style(ax)

# Figure 9: mechanism attribution, six grouped reversions, and threshold cost.
fig,axs=plt.subplots(2,2,figsize=(6.45,5.15));fig.subplots_adjust(left=.11,right=.98,bottom=.105,top=.95,wspace=.38,hspace=.57)
ax=axs[0,0];x=np.array([25,1000/28,50])
for j,(key,label,col,mk) in enumerate([('fuel_trigger_with_coop','COOP settings',colors[1],'o'),('fuel_trigger_with_eco','ECO settings',colors[2],'s')]):
    errors(ax,x,[r[key] for r in old['factorial']],lo='ci_low',hi='ci_high',color=col,marker=mk,linestyle='-' if j==0 else '--',label=label)
ax.set_xticks(x,['25.0','35.7','50.0']);ax.set_xlabel('Initial density (veh/km)');ax.set_ylabel('Fuel saving from gate (%)');ax.legend(frameon=False,loc='upper right');panel(ax,'(a) Isolated activation gate')
ax=axs[0,1];y=np.arange(6);v=np.array([r['fuel_change_pct']['mean'] for r in comp]);lo=[r['fuel_change_pct']['low'] for r in comp];hi=[r['fuel_change_pct']['high'] for r in comp]
ax.errorbar(v,y,xerr=[v-np.array(lo),np.array(hi)-v],fmt='o',color=colors[2],capsize=2,markersize=4);ax.axvline(0,color='#555555',lw=.7,ls=':');ax.set_yticks(y,['Ramp','Scheduling','Weights/gain','Accel. limit','Admission','Safety buffer']);ax.invert_yaxis();ax.set_xlabel('Fuel change on reversion (%)');panel(ax,'(b) ECO component reversions')
ax=axs[1,0]
for j,density in enumerate([25,1000/28,50]):
    rr=sorted([r for r in old['thresholds'] if abs(r['density']-density)<.01 and r['variant'] in [130,140,145]],key=lambda r:r['variant']);xx=[30,40,45]
    vals=[r['fuel_change_pct'] for r in rr];vals.insert(1,{'mean':0,'ci_low':0,'ci_high':0});xx.insert(1,35)
    errors(ax,xx,vals,lo='ci_low',hi='ci_high',color=colors[j+1],marker=markers[j+1],linestyle=linestyles[j+1],label=f'{density:.1f} veh/km')
ax.set_xlabel('Density threshold (veh/km)');ax.set_ylabel('Fuel change from nominal (%)');ax.legend(frameon=False,loc='lower left');panel(ax,'(c) Density-threshold sensitivity')
ax=axs[1,1];rr=[next(r for r in old['thresholds'] if r['variant']==v) for v in [1250,1550,2015,2040]]
errors(ax,range(4),[r['fuel_change_pct'] for r in rr],lo='ci_low',hi='ci_high',color=colors[2],marker='s',linestyle='none');ax.axhline(0,color='#555555',lw=.7,ls=':');ax.set_xticks(range(4),['Start\n250 m','Start\n550 m','Critical\n15 m','Critical\n40 m']);ax.set_ylabel('Fuel change from nominal (%)');panel(ax,'(d) Distance-threshold sensitivity');save(fig,9)

# Figure 10: original serial timings and success are shown together.
fig,axs=plt.subplots(1,3,figsize=(6.45,2.75));fig.subplots_adjust(left=.09,right=.98,bottom=.23,top=.85,wspace=.42)
tim=pd.read_csv(OLD/'analysis/runtime_summary.csv')
for m in [1,2,3]:
    rows=[r for r in old['runtime'] if r['mode']==m];xx=[r['vehicles'] for r in rows]
    for ax,met in zip(axs[:2],['mean_ms','maximum_ms']):ax.plot(xx,[r[met] for r in rows],color=colors[m],marker=markers[m],ls=linestyles[m],ms=4,label=modes[m])
    yy=[tim[(tim.vehicles==v)&(tim['mode']==m)].completion.mean() for v in xx]
    axs[2].plot(xx,yy,color=colors[m],marker=markers[m],ls=linestyles[m],ms=4)
for ax,lab,ylab in zip(axs,['(a) Mean step time','(b) Maximum step time','(c) Merge completion'],['Time (ms)','Time (ms)','Completion (%)']):panel(ax,lab);ax.set_xticks([38,57,76]);ax.set_xlabel('Vehicles');ax.set_ylabel(ylab)
axs[0].legend(frameon=False,loc='upper left');axs[1].axhline(100,color='#555555',lw=.7,ls=':');axs[1].set_ylim(bottom=0);axs[2].set_ylim(-3,105);save(fig,10)

# Figure 11: delay, loss and observation errors with shared physical metrics.
fig,axs=plt.subplots(3,2,figsize=(6.45,6.5));fig.subplots_adjust(left=.11,right=.96,bottom=.075,top=.96,wspace=.40,hspace=.66)
series(axs[0,0],[1,2,3,4],'fuel_L100',['0','100','300','500']);axs[0,0].set_xlabel('Broadcast delay (ms)');axs[0,0].set_ylabel('Fuel (L/100 km)');panel(axs[0,0],'(a) Delay and fuel intensity')
series(axs[0,1],[1,2,3,4],'completion',['0','100','300','500']);axs[0,1].set_xlabel('Broadcast delay (ms)');axs[0,1].set_ylabel('Completion (%)');axs[0,1].set_ylim(78,103);panel(axs[0,1],'(b) Delay and completion')
series(axs[1,0],[1,5,6,7],'fuel_L100',['0','5','10','20']);axs[1,0].set_xlabel('Independent packet loss (%)');axs[1,0].set_ylabel('Fuel (L/100 km)');panel(axs[1,0],'(c) Loss and fuel intensity')
labs=['Ideal','Control\nnoise','All-layer\nnoise','Combined']
series(axs[1,1],[1,8,9,10],'fuel_L100',labs);axs[1,1].set_ylabel('Fuel (L/100 km)');panel(axs[1,1],'(d) Uncertainty and fuel intensity')
series(axs[2,0],[1,8,9,10],'jerk_rms',labs);axs[2,0].set_ylabel('Jerk RMS (m/s³)');panel(axs[2,0],'(e) Realized motion smoothness')
for m in [1,2,3]:
    vals=[s[(s.condition_id==k)&(s.mode_id==m)].minimum_observed_gap.iloc[0] for k in [1,4,7,8,9,10]]
    axs[2,1].plot(range(6),vals,color=colors[m],marker=markers[m],ls=linestyles[m],ms=4,label=modes[m])
axs[2,1].set_xticks(range(6),['Ideal','500 ms','20%\nloss','Control\nnoise','All-layer\nnoise','Combined'],fontsize=7);axs[2,1].axhline(2,color='#555555',lw=.7,ls=':');axs[2,1].set_xlim(-.35,5.4);axs[2,1].set_ylabel('Minimum observed gap (m)');panel(axs[2,1],'(f) Spacing margin across seeds');axs[0,0].legend(frameon=False,loc='upper left');save(fig,11)

# Figure 12: the unfiltered branch is explicitly a safety diagnostic.
fig,axs=plt.subplots(2,2,figsize=(6.45,4.9));fig.subplots_adjust(left=.11,right=.98,bottom=.12,top=.94,wspace=.4,hspace=.5)
series(axs[0,0],[1,11,12],'fuel_L100',['0','20','40']);axs[0,0].set_xlabel('Bounded IDM parameter variation (%)');axs[0,0].set_ylabel('Fuel (L/100 km)');panel(axs[0,0],'(a) Heterogeneity with shared filtering');axs[0,0].legend(frameon=False,loc='lower left')
series(axs[0,1],[1,11,12],'jerk_rms',['0','20','40']);axs[0,1].set_xlabel('Bounded IDM parameter variation (%)');axs[0,1].set_ylabel('Jerk RMS (m/s³)');panel(axs[0,1],'(b) Smoothness with shared filtering')
for m in [1,2,3]:
    rr=s[(s.mode_id==m)&s.condition_id.isin([11,13])].sort_values('condition_id')
    axs[1,0].plot([0,1],rr.minimum_observed_gap,color=colors[m],marker=markers[m],ls=linestyles[m],ms=4)
    axs[1,1].bar(m,rr.iloc[1].runs_with_overlap,color=colors[m],width=.6,label=modes[m]);axs[1,1].text(m,rr.iloc[1].runs_with_overlap+.25,f"{int(rr.iloc[1].runs_with_overlap)}/20",ha='center',fontsize=8)
axs[1,0].set_xticks([0,1],['All vehicles\nfiltered','CAVs only\nfiltered']);axs[1,0].axhline(0,color='#555555',lw=.7,ls=':');axs[1,0].set_ylabel('Minimum observed gap (m)');panel(axs[1,0],'(c) HDV safety-override diagnostic')
axs[1,1].set_xticks([1,2,3],list(modes.values()));axs[1,1].set_ylabel('Runs with negative gaps');axs[1,1].set_ylim(0,max(5,float(s.runs_with_overlap.max())+2));axs[1,1].yaxis.set_major_locator(plt.MaxNLocator(integer=True));panel(axs[1,1],'(d) Overlaps without HDV filtering');save(fig,12)

# Figure 13: closure position and desired/initial speed vary one factor at a time.
fig,axs=plt.subplots(2,2,figsize=(6.45,4.85));fig.subplots_adjust(left=.11,right=.98,bottom=.12,top=.94,wspace=.36,hspace=.53)
for col,conds,labs in [(0,[14,1,15],['650','750','850']),(1,[16,1,17],['80','100','120'])]:
    series(axs[0,col],conds,'fuel_L100',labs)
    for m in [1,2,3]:
        vals=[s[(s.condition_id==k)&(s.mode_id==m)].minimum_observed_gap.iloc[0] for k in conds]
        axs[1,col].plot(range(3),vals,color=colors[m],marker=markers[m],ls=linestyles[m],ms=4)
    axs[1,col].set_xticks(range(3),labs);axs[1,col].set_xlim(-.3,2.3);axs[1,col].axhline(2,color='#555555',lw=.7,ls=':')
    for row in [0,1]:
        axs[row,col].set_xlabel('Lane-closure coordinate (m)' if col==0 else 'Initial and desired speed scale (%)')
        axs[row,col].set_ylabel('Fuel (L/100 km)' if row==0 else 'Minimum observed gap (m)')
for ax,label in zip(axs.flat,['(a) Closure position and fuel','(b) Speed scale and fuel','(c) Closure position and gap','(d) Speed scale and gap']):panel(ax,label)
axs[0,0].legend(frameon=False,loc='best');save(fig,13)

print('VALIDATED',len(d),'robustness runs and',len(c),'component reversions')
print(s[['condition','mode','fuel_L100_mean','completion_mean','minimum_observed_gap','runs_with_overlap','jerk_rms_mean']].to_string(index=False))
print('COMPONENTS',json.dumps(comp,indent=2))

# Final compact presentation pass; this does not rerun any simulation.
import subprocess
subprocess.run([sys.executable, str(ROOT / "graphics_revision" / "replot.py"), "--output-dir", str(ROOT / "figures")], check=True)
