"""Redraw Figures 1, 4 and 7 from archived records without resimulation."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import t
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from inside_labels import arrange_inside

ROOT=Path(__file__).resolve().parent
INPUT=ROOT/'original_plot_inputs';OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'Times New Roman','font.size':8,'axes.labelsize':8,
    'xtick.labelsize':7.2,'ytick.labelsize':7.2,'axes.linewidth':.65,
    'pdf.fonttype':42,'svg.fonttype':'none','savefig.facecolor':'white'})
COL=['#AD332B','#1A6B4D','#3D5294'];MARK=['o','D','s']
NAMES=['Safety-priority cooperation','State-triggered cooperation','Passive merging']
AUDIT=[]
def frame(ax):
    ax.tick_params(direction='in',top=True,right=True,length=2.5,width=.6,pad=2)
    ax.grid(color='#DFE3E8',lw=.4);ax.set_axisbelow(True)
def save(fig,axs,n):
    arrange_inside(fig,axs,n);fig.canvas.draw()
    for ext in ['png','tif','pdf','svg']:
        kw={'dpi':400} if ext=='png' else {'dpi':600,'pil_kwargs':{'compression':'tiff_lzw'}} if ext=='tif' else {}
        fig.savefig(OUT/f'Fig{n}.{ext}',**kw)
    for l,ax in zip('abcdef',axs):
        box=ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted()).expanded(1.02,1.04)
        fig.savefig(OUT/f'Fig{n}{l}.pdf',bbox_inches=box)
    plt.close(fig)

data=pd.read_csv(INPUT/'representative_trajectories.csv')
fig,aa=plt.subplots(3,1,figsize=(6.45,4.85))
fig.subplots_adjust(left=.112,right=.98,bottom=.085,top=.985,hspace=.22)
colors=plt.colormaps['turbo'](np.linspace(0,1,12))
for ax,mode in zip(aa,['COOP','ECO','PASSIVE']):
    for j,color in zip(range(1,13),colors):
        d=data[(data.strategy==mode)&(data.vehicle_id==j)].sort_values('time_s')
        assert len(d)==900 and np.all(np.diff(d.position_m)>=-1e-9)
        ax.plot(d.time_s,d.position_m,color=color,lw=.55)
        AUDIT.append({'figure':1,'mode':mode,'vehicle':j,'time':d.time_s.tolist(),'position':d.position_m.tolist()})
    ax.axhline(750,color='#555',lw=.65,ls='--')
    ax.text(2,765,'Closure',va='bottom',fontsize=7)
    ax.set_ylabel('Longitudinal coordinate (m)');ax.set_xlim(0,90);frame(ax)
aa[-1].set_xlabel('Time (s)');save(fig,list(aa),1)

raw=np.concatenate([np.loadtxt(INPUT/n,delimiter=',',skiprows=1) for n in ['joint_raw.csv','eco_joint_raw.csv']])
fig,aa=plt.subplots(2,2,figsize=(6.45,4.25))
fig.subplots_adjust(left=.095,right=.98,bottom=.12,top=.985,wspace=.31,hspace=.34)
for i,(ax,col,yl) in enumerate(zip(aa.flat,[8,10,12,20],['Fuel (L/100 km)','Speed standard deviation (m/s)','Stopped-vehicle time (veh s)','Mean speed (m/s)'])):
    for mode,c,m,n in zip([1,3,2],COL,MARK,NAMES):
        mu=[];ci=[]
        for pen in [0,.25,.5,.75,1]:
            v=raw[np.isclose(raw[:,1],24)&np.isclose(raw[:,2],pen)&(raw[:,3]==mode),col]
            assert len(v)==20
            mu.append(v.mean());ci.append(t.ppf(.975,19)*v.std(ddof=1)/np.sqrt(20))
        ax.errorbar([0,25,50,75,100],mu,yerr=ci,fmt=m+'-',color=c,mfc='white',ms=3.5,lw=1,capsize=2,elinewidth=.7,label=n)
        AUDIT.append({'figure':4,'panel':chr(97+i),'mode':mode,'mean':mu,'ci95':ci})
    ax.set_xlabel('Target-lane CAV penetration (%)');ax.set_ylabel(yl);ax.set_xticks([0,25,50,75,100]);frame(ax)
aa[0,0].legend(loc='upper left',bbox_to_anchor=(.005,.84),frameon=False,fontsize=7,
    handlelength=1.5,handletextpad=.4,labelspacing=.25,borderaxespad=.1)
save(fig,list(aa.flat),4)

C=pd.read_csv(INPUT/'eco_vs_coop_paired_summary.csv')
selected=[(25,1),(1000/28,.5),(1000/24,.75),(50,1)]
labels=['25.0/100','35.7/50','41.7/75','50.0/100']
keys=['L100','sigma','arms','stop','speed','total_fuel']
values=['L100_saving_pct','sigma_reduction_pct','arms_reduction_pct','stop_reduction_veh_s','speed_gain_pct','total_fuel_saving_pct']
ylabels=['Fuel-intensity saving (%)','Speed-disturbance reduction (%)','Acceleration-RMS reduction (%)',
    'Stopped-time reduction (veh s)','Mean-speed gain (%)','Total-fuel saving (%)']
fig,aa=plt.subplots(3,2,figsize=(6.45,5.05))
fig.subplots_adjust(left=.095,right=.985,bottom=.11,top=.98,wspace=.34,hspace=.42)
for i,(ax,key,value,yl) in enumerate(zip(aa.flat,keys,values,ylabels)):
    rows=[C[np.isclose(C.k1,k)&np.isclose(C.penetration,p)].iloc[0] for k,p in selected]
    means=np.array([r[value] for r in rows]);ci=np.array([r[key+'_ci95'] for r in rows])
    ax.errorbar(range(4),means,yerr=ci,fmt='o',color=COL[1],mfc='white',ms=3.5,lw=.9,capsize=2.5)
    ax.axhline(0,color='#777',ls=':',lw=.6)
    ax.set_xlim(-.30,3.30);ax.set_xticks(range(4),labels,rotation=12);ax.set_ylabel(yl);frame(ax)
    AUDIT.append({'figure':7,'panel':chr(97+i),'mean':means.tolist(),'ci95':ci.tolist()})
fig.supxlabel('Target-lane density (veh/km) / CAV penetration (%)',y=.017,fontsize=8)
save(fig,list(aa.flat),7)
(ROOT/'legacy_plot_audit.json').write_text(json.dumps(AUDIT,indent=2),encoding='utf-8')
print('Generated Figures 1, 4 and 7 from archived trajectories and paired summaries.')
