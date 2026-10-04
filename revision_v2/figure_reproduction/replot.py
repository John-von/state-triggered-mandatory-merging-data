"""Reproduce Figs 9–13 from archived results, without running simulations.

Usage: python replot.py
Input and output paths are relative to this file. See README.txt for statistics.
"""
from pathlib import Path
import json, argparse
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from inside_labels import arrange_inside
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / 'plot_inputs'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir', type=Path, default=ROOT/'figures')
OUT = parser.parse_args().output_dir.resolve()
OUT.mkdir(exist_ok=True)
original = json.loads((INPUT / 'first_round_summary.json').read_text(encoding='utf-8'))
round2 = json.loads((INPUT / 'round2_summary.json').read_text(encoding='utf-8'))
raw = pd.read_csv(INPUT / 'robustness_experiments.csv')
summary = pd.read_csv(INPUT / 'robustness_summary.csv')
timing = pd.read_csv(INPUT / 'runtime_summary.csv')
assert len(raw) == 1020 and len(timing) == 27
assert not raw.duplicated(['condition_id', 'mode_id', 'seed']).any()

# Stable strategy hues: COOP red, ECO green, PASSIVE blue.
COL = {1: '#AD332B', 2: '#1A6B4D', 3: '#3D5294'}
MARK={1:'o',2:'D',3:'s'}
LINE={1:'-',2:'-',3:'-'}
NAME = {1: 'COOP', 2: 'ECO', 3: 'PASSIVE'}
LEGEND_NAME={1:'Safety-priority cooperation',2:'State-triggered cooperation',3:'Passive merging'}
ACCENT = ['#3784CA', '#E89132', '#9162C1', '#16A1AA', '#CF617D', '#AE850E']
METHODS = [1, 2, 3]
SIZE = {9: (6.45, 3.95), 10: (6.45, 2.35), 11: (6.45, 4.85),
        12: (6.45, 3.95), 13: (6.45, 3.55)}
plt.rcParams.update({'font.family': 'Times New Roman', 'font.size': 8,
    'axes.labelsize': 8, 'axes.titlesize': 8.3, 'xtick.labelsize': 7.2,
    'ytick.labelsize': 7.2, 'legend.fontsize': 7.4, 'axes.linewidth': .65,
    'savefig.facecolor': 'white', 'axes.unicode_minus': True,
    'pdf.fonttype': 42, 'ps.fonttype': 42, 'svg.fonttype': 'none'})
AUDIT = []

def record(fig, panel, label, statistic, value):
    arr = np.asarray(value, dtype=float)
    assert np.isfinite(arr).all(), (fig, panel, label)
    AUDIT.append({'figure': fig, 'panel': panel, 'label': label,
                  'statistic': statistic, 'value': arr.tolist()})

def estimate(v):
    v = np.asarray(v, float)
    assert len(v) == 20 and np.isfinite(v).all()
    mean = float(v.mean())
    half = stats.t.ppf(.975, 19) * v.std(ddof=1) / np.sqrt(20)
    return mean, float(mean - half), float(mean + half)

def group(cid, mode):
    g = raw[(raw.condition_id == cid) & (raw.mode_id == mode)].sort_values('seed')
    assert len(g) == 20 and g.seed.tolist() == list(range(20))
    return g

def row(cid, mode):
    return summary[(summary.condition_id == cid) & (summary.mode_id == mode)].iloc[0]

def frame(ax, title, grid='y'):
    ax.set_title(title, loc='left', pad=5, fontweight='normal')
    ax.tick_params(direction='in', top=True, right=True, length=2.5, width=.6, pad=2)
    if grid:
        ax.grid(axis=grid, color='#DFE3E8', lw=.4, zorder=0)
    ax.set_axisbelow(True)

def legend(ax, loc='upper left', kind='line', ncol=1):
    handles = ([Line2D([0],[0],color=COL[m],marker=MARK[m],mfc='white',ls=LINE[m],lw=1.0,ms=3.5) for m in METHODS]
               if kind=='line' else [Patch(facecolor=COL[m],edgecolor=COL[m],alpha=.5) for m in METHODS])
    if ax.figure.legends:return
    lg=ax.figure.legend(handles,[LEGEND_NAME[m] for m in METHODS],loc='upper center',
              bbox_to_anchor=(.53,.995),ncol=3,frameon=True,fancybox=False,
              facecolor='white',edgecolor='#333333',handlelength=2.0,
              columnspacing=1.0,handletextpad=.5,fontsize=7.4,borderpad=.3)
    lg.get_frame().set_linewidth(.5)

def series(ax,cids,x,metric,n,letter):
    for m in METHODS:
        vals=np.array([estimate(group(cid,m)[metric]) for cid in cids])
        for cid,v in zip(cids,vals):
            check=row(cid,m)
            assert np.allclose(v,[check[metric+'_mean'],check[metric+'_low'],check[metric+'_high']],rtol=1e-10)
            record(n,letter,f'{cid}/{NAME[m]}','mean and pointwise 95% t interval',v)
        ax.errorbar(x,vals[:,0],yerr=[vals[:,0]-vals[:,1],vals[:,2]-vals[:,0]],
                    color=COL[m],marker=MARK[m],mfc='white',ls=LINE[m],lw=1.0,ms=3.5,capsize=2,elinewidth=.7)
    ax.set_xticks(x)


def save(fig, axes, n):
    arrange_inside(fig, axes, n)
    fig.canvas.draw()
    fig.savefig(OUT / f'Fig{n}.png', dpi=400)
    fig.savefig(OUT / f'Fig{n}.tif', dpi=600, pil_kwargs={'compression': 'tiff_lzw'})
    fig.savefig(OUT / f'Fig{n}.pdf')
    fig.savefig(OUT / f'Fig{n}.svg')
    # Explicit panel list excludes colorbars and preserves a/b/c/d naming.
    for letter, ax in zip('abcdef', axes):
        box = ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted()).expanded(1.02, 1.04)
        fig.savefig(OUT / f'Fig{n}{letter}.pdf', bbox_inches=box)
    plt.close(fig)

def boxes(ax, cids, labels, metric, ylabel, n, letter):
    offsets = {1: -.24, 2: 0, 3: .24}
    # Horizontal offsets only separate individual seed points; y values are unchanged.
    jitter = np.random.default_rng(736).permutation(np.linspace(-.060, .060, 20))
    for k, cid in enumerate(cids):
        for m in METHODS:
            vals = group(cid, m)[metric].to_numpy()
            mu, low, high = estimate(vals)
            check = row(cid, m)
            assert np.allclose([mu, low, high], [check[metric+'_mean'], check[metric+'_low'], check[metric+'_high']], rtol=1e-10)
            xpos = k + offsets[m]
            b = ax.boxplot(vals, positions=[xpos], widths=.19, manage_ticks=False,
                           patch_artist=True, showfliers=False, whis=1.5,
                           boxprops={'facecolor': COL[m], 'alpha': .25, 'edgecolor': COL[m], 'linewidth': .7},
                           medianprops={'color': COL[m], 'linewidth': 1.1},
                           whiskerprops={'color': COL[m], 'linewidth': .6},
                           capprops={'color': COL[m], 'linewidth': .6})
            ax.scatter(xpos+jitter, vals, s=4.5, color=COL[m], alpha=.5, linewidths=0, zorder=3)
            ax.errorbar(xpos, mu, yerr=[[mu-low], [high-mu]], fmt='D',
                        markersize=2.6, mfc='white', mec=COL[m], mew=.65,
                        ecolor=COL[m], elinewidth=.75, capsize=1.5, zorder=5)
            record(n, letter, f'{cid}/{NAME[m]}', 'seed values; mean and pointwise 95% t interval', [*vals, mu, low, high])
    ax.set_xticks(range(len(cids)), labels)
    ax.set_xlim(-.55, len(cids)-.45)
    ax.set_ylabel(ylabel)
    ax.margins(y=.14)

GAP_CMAP = LinearSegmentedColormap.from_list('gap_margin', ['#CA665C', '#FFF9F3', '#1F968B'])
def heat(ax, values, cols, title, vmin, vmax, cmap='YlGnBu', fmt='.2f', norm=None, flag_below=None):
    a = np.asarray(values, float)
    kwargs = {'norm': norm} if norm is not None else {'vmin': vmin, 'vmax': vmax}
    ax.imshow(a, aspect='auto', cmap=cmap, interpolation='nearest', **kwargs)
    ax.set_xticks(range(a.shape[1]), cols)
    ax.set_yticks(range(3), [NAME[m] for m in METHODS])
    for tick, m in zip(ax.get_yticklabels(), METHODS): tick.set_color(COL[m])
    for i in range(a.shape[0]):
        for j in range(a.shape[1]):
            val = a[i,j]
            normalized = float(norm(val)) if norm is not None else (val-vmin)/(vmax-vmin)
            textcolor = 'white' if normalized > .76 or (norm is not None and normalized < .19) else '#202020'
            ax.text(j, i, format(val, fmt), ha='center', va='center', fontsize=7.3, color=textcolor)
            if flag_below is not None and val < flag_below-1e-6:
                ax.add_patch(Rectangle((j-.5,i-.5),1,1,fill=False,edgecolor='#A33131',lw=1.1))
    ax.set_xticks(np.arange(-.5,a.shape[1]), minor=True)
    ax.set_yticks(np.arange(-.5,a.shape[0]), minor=True)
    ax.grid(which='minor',color='white',lw=1)
    ax.tick_params(which='minor', length=0)
    frame(ax,title,grid=None)

# Figure 9 preserves all original paired comparisons.
fig, aa = plt.subplots(2,2,figsize=SIZE[9]); axes=list(aa.flat)
fig.subplots_adjust(left=.095,right=.98,bottom=.12,top=.925,wspace=.49,hspace=.59)
ax=aa[0,0]
for key,label,m in [('fuel_trigger_with_coop','COOP settings',1),('fuel_trigger_with_eco','ECO settings',2)]:
    x=[];v=[]
    for r in original['factorial']:
        q=r[key];x.append(r['density']);v.append([q['mean'],q['ci_low'],q['ci_high']])
        record(9,'a',f'{r["density"]}/{label}','paired mean saving and 95% interval',v[-1])
    v=np.array(v)
    ax.errorbar(x,v[:,0],yerr=[v[:,0]-v[:,1],v[:,2]-v[:,0]],color=COL[m],marker=MARK[m],mfc='white',ls=LINE[m],lw=1.0,ms=3.5,capsize=2,label=label)
ax.set_xticks(x,['25.0','35.7','50.0']);ax.set_xlabel('Initial density (veh/km)');ax.set_ylabel('Fuel saving (%)');ax.set_ylim(-.3,6.4)
ax.legend(frameon=False,loc='upper right',fontsize=7.4,handlelength=2)
frame(ax,'(a) Isolated activation gate')
ax=aa[0,1]
for i,r in enumerate(round2['components']):
    q=r['fuel_change_pct']; mu,lo,hi=q['mean'],q['low'],q['high']
    ax.errorbar(mu,i,xerr=[[mu-lo],[hi-mu]],fmt='o',ms=3.7,color=ACCENT[i],elinewidth=1.1,capsize=2,zorder=3)
    record(9,'b',r['component'],'paired mean change and 95% interval',[mu,lo,hi])
ax.set_yticks(range(6),['Ramp timing','Scheduling','Weights/gain','Accel. limit','Admission','Safety buffer']);ax.invert_yaxis()
ax.axvline(0,color='#555',ls=':',lw=.65);ax.set_xlim(-.7,1.45);ax.set_xlabel('Fuel change on reversion (%)');frame(ax,'(b) Component reversions',grid='x')
ax=aa[1,0]
grid=np.zeros((3,4)); cells={}
for i,density in enumerate([25,1000/28,50]):
    for j,thr in enumerate([30,35,40,45]):
        q={'mean':0.,'ci_low':0.,'ci_high':0.} if thr==35 else next(r['fuel_change_pct'] for r in original['thresholds'] if abs(r['density']-density)<.01 and int(r['variant'])==100+thr)
        grid[i,j]=q['mean'];cells[(i,j)]=q
        record(9,'c',f'{density}/{thr}','paired mean change and 95% interval',[q['mean'],q['ci_low'],q['ci_high']])
cm=LinearSegmentedColormap.from_list('threshold_change',['#2C999A','#F4FBFA'])
ax.imshow(grid,cmap=cm,vmin=-4.3,vmax=0,aspect='auto',interpolation='nearest')
for (i,j),q in cells.items():
    col='white' if q['mean'] < -2 else '#20363C'
    ax.text(j,i-.12,f"{q['mean']:.2f}",ha='center',va='center',fontsize=7.3,color=col)
    ax.text(j,i+.17,f"[{q['ci_low']:.2f}, {q['ci_high']:.2f}]",ha='center',va='center',fontsize=5.9,color=col)
ax.set_xticks(range(4),['30','35','40','45']);ax.set_yticks(range(3),['25.0','35.7','50.0'])
ax.set_xlabel('Density threshold (veh/km)');ax.set_ylabel('Initial density (veh/km)')
ax.set_xticks(np.arange(-.5,4),minor=True);ax.set_yticks(np.arange(-.5,3),minor=True);ax.grid(which='minor',color='white',lw=1);ax.tick_params(which='minor',length=0)
frame(ax,'(c) Fuel change (%) and 95% CI',grid=None)
ax=aa[1,1]
for i,(variant,label) in enumerate(zip([1250,1550,2015,2040],['Start 250 m','Start 550 m','Critical 15 m','Critical 40 m'])):
    q=next(r['fuel_change_pct'] for r in original['thresholds'] if int(r['variant'])==variant)
    mu,lo,hi=q['mean'],q['ci_low'],q['ci_high']
    ax.barh(i,mu,height=.49,color=ACCENT[i+2],zorder=3)
    ax.errorbar(mu,i,xerr=[[mu-lo],[hi-mu]],fmt='o',ms=2.2,color=ACCENT[i+2],ecolor='#333',capsize=2,elinewidth=.6,zorder=4)
    record(9,'d',label,'paired mean change and 95% interval',[mu,lo,hi])
ax.set_yticks(range(4),['Start 250 m','Start 550 m','Critical 15 m','Critical 40 m']);ax.invert_yaxis();ax.set_xlabel('Fuel change from nominal (%)');ax.axvline(0,color='#555',ls=':',lw=.65);frame(ax,'(d) Distance thresholds',grid='x')
save(fig,axes,9)

# Figure 10: use pooled step means and observed maxima, not means of seed maxima.
fig,aa=plt.subplots(1,3,figsize=SIZE[10],gridspec_kw={'width_ratios':[1,1,1.03]});axes=list(aa)
fig.subplots_adjust(left=.074,right=.985,bottom=.20,top=.81,wspace=.42)
for p,metric,title in [(0,'mean_ms','(a) Mean step time'),(1,'maximum_ms','(b) Observed maximum')]:
    ax=aa[p]
    for m in METHODS:
        vals=[]
        for count in [38,57,76]:
            r=next(r for r in original['runtime'] if int(r['vehicles'])==count and int(r['mode'])==m)
            vals.append(r[metric]);g=timing[(timing.vehicles==count)&(timing['mode']==m)]
            expected=g.mean_ms.mean() if metric=='mean_ms' else g.maximum_ms.max()
            assert np.isclose(vals[-1],expected,rtol=1e-10)
            record(10,chr(97+p),f'{count}/{NAME[m]}',metric,vals[-1])
        ax.plot([38,57,76],vals,color=COL[m],marker=MARK[m],mfc='white',ls=LINE[m],lw=1.0,ms=3.5)
    ax.set_xticks([38,57,76]);ax.set_xlabel('Vehicles');ax.set_ylabel('Time (ms)');frame(ax,title)
legend(aa[0],loc='upper left');aa[0].set_ylim(0,26);aa[1].set_ylim(0,107);aa[1].axhline(100,color='#555',ls=':',lw=.7)
completion=np.array([[timing[(timing.vehicles==v)&(timing['mode']==m)].completion.mean() for v in [38,57,76]] for m in METHODS])
record(10,'c','rows COOP/ECO/PASSIVE; columns 38/57/76','three-seed mean completion percent',completion)
ax=aa[2]
for j,m in enumerate(METHODS):
    xx=np.arange(3)+(j-1)*.24
    ax.bar(xx,completion[j],width=.215,color=COL[m],zorder=3)
    for x,y in zip(xx,completion[j]):
        if 0<y<100:ax.text(x,y+3,f'{y:.1f}',ha='center',va='bottom',fontsize=6.9,color=COL[m])
ax.set_xticks(range(3),['38','57','76']);ax.set_xlabel('Vehicles')
ax.set_ylabel('Completion (%)');ax.set_ylim(0,112);ax.set_yticks([0,50,100])
ax.text(0,103,'100% (all)',ha='center',fontsize=6.7)
ax.text(2,4,'0% (all)',ha='center',fontsize=6.7)
frame(ax,'(c) Merge completion')
save(fig,axes,10)

# Figure 11: empirical seed distributions, summary heatmaps, and jerk means.
fig,aa=plt.subplots(3,2,figsize=SIZE[11]);axes=list(aa.flat)
fig.subplots_adjust(left=.093,right=.985,bottom=.09,top=.91,wspace=.31,hspace=.68)
series(aa[0,0],[1,2,3,4],[0,100,300,500],'fuel_L100',11,'a');aa[0,0].set_ylabel('Fuel (L/100 km)');aa[0,0].set_xlabel('Broadcast delay (ms)');frame(aa[0,0],'(a) Delay and fuel');legend(aa[0,0])
vals=np.array([[row(cid,m).completion_mean for cid in [1,2,3,4]] for m in METHODS]);record(11,'b','delay 0/100/300/500 ms','20-seed mean completion percent',vals)
ax=aa[0,1]
# Vertical offsets separate method markers within each delay category; the
# completion axis remains unshifted. Intervals come from the 20 actual seeds.
for j,m in enumerate(METHODS):
    for k,cid in enumerate([1,2,3,4]):
        mu,lo,hi=estimate(group(cid,m).completion)
        assert np.isclose(mu,vals[j,k])
        y=k+(j-1)*.19
        ax.errorbar(mu,y,xerr=[[mu-lo],[hi-mu]],fmt=MARK[m],mfc='white',mec=COL[m],
                    ecolor=COL[m],ms=4,elinewidth=.8,capsize=2,zorder=3)
        record(11,'b',f'{cid}/{NAME[m]}','mean completion and pointwise 95% t interval',[mu,lo,hi])
ax.set_yticks(range(4),['0','100','300','500']);ax.invert_yaxis()
ax.set_ylabel('Broadcast delay (ms)');ax.set_xlabel('Completion (%)')
ax.set_xlim(83,103);ax.set_xticks([85,90,95,100])
ax.axvline(100,color='#9B9B9B',ls=':',lw=.65)
ax.text(93.75,2.53,'93.75%',ha='center',va='bottom',fontsize=7,color=COL[1])
ax.set_ylim(3.50,-.50)
frame(ax,'(b) Merge completion',grid='x')
series(aa[1,0],[1,5,6,7],[0,5,10,20],'fuel_L100',11,'c');aa[1,0].set_ylabel('Fuel (L/100 km)');aa[1,0].set_xlabel('Independent packet loss (%)');frame(aa[1,0],'(c) Packet loss and fuel')
labels=['Ideal','Control\nnoise','All-layer\nnoise','Combined']
boxes(aa[1,1],[1,8,9,10],labels,'fuel_L100','Fuel (L/100 km)',11,'d');frame(aa[1,1],'(d) State uncertainty and fuel');legend(aa[1,1],loc='upper left',kind='box',ncol=3);aa[1,1].set_ylim(top=9.18)
ax=aa[2,0]
for k,cid in enumerate([1,8,9,10]):
    for m in METHODS:
        mu,lo,hi=estimate(group(cid,m).jerk_rms)
        x=k+(m-2)*.23
        ax.bar(x,mu,width=.215,color=COL[m],zorder=3)
        ax.errorbar(x,mu,yerr=[[mu-lo],[hi-mu]],fmt='none',ecolor='#303030',elinewidth=.6,capsize=1.5,zorder=4)
        record(11,'e',f'{cid}/{NAME[m]}','mean jerk and pointwise 95% t interval',[mu,lo,hi])
ax.set_xticks(range(4),labels);ax.set_ylabel('Jerk RMS (m/s³)');ax.set_ylim(0,2.2);frame(ax,'(e) Realized smoothness')
vals=np.array([[row(cid,m).minimum_observed_gap for cid in [1,4,7,8,9,10]] for m in METHODS])
record(11,'f','ideal/delay500/loss20/control-noise/all-noise/combined','minimum observed gap over seeds',vals)
heat(aa[2,1],vals,['Ideal','500\nms','20%\nloss','Control\nnoise','All-layer\nnoise','Comb.'],'(f) Minimum gap (m)',1.8,2.12,cmap=GAP_CMAP,norm=TwoSlopeNorm(2,1.8,2.12),fmt='.3f',flag_below=2)
save(fig,axes,11)

# Figure 12: show the distribution and the actual failed seed identities.
fig,aa=plt.subplots(2,2,figsize=SIZE[12]);axes=list(aa.flat)
fig.subplots_adjust(left=.09,right=.982,bottom=.13,top=.895,wspace=.34,hspace=.64)
boxes(aa[0,0],[1,11,12],['0','±20','±40'],'fuel_L100','Fuel (L/100 km)',12,'a');aa[0,0].set_xlabel('Bounded IDM variation (%)');frame(aa[0,0],'(a) Fuel under heterogeneity');legend(aa[0,0],loc='upper left',kind='box',ncol=3);aa[0,0].set_ylim(7.60,9.05)
boxes(aa[0,1],[1,11,12],['0','±20','±40'],'jerk_rms','Jerk RMS (m/s³)',12,'b');aa[0,1].set_xlabel('Bounded IDM variation (%)');frame(aa[0,1],'(b) Smoothness under heterogeneity')
ax=aa[1,0]
for i,m in enumerate(METHODS):
    filtered=row(11,m).minimum_observed_gap;unfiltered=row(13,m).minimum_observed_gap
    ax.plot([unfiltered,filtered],[i,i],color=COL[m],lw=1.1,zorder=2)
    ax.plot(filtered,i,'o',mfc='white',mec=COL[m],ms=4,zorder=4)
    ax.plot(unfiltered,i,'o',color=COL[m],ms=4,zorder=3)
    if unfiltered<0: ax.text(unfiltered+.10,i+.22,f'{unfiltered:.2f}',ha='left',va='top',fontsize=7,color=COL[m])
    record(12,'c',NAME[m],'minimum gaps: all vehicles filtered; CAVs only filtered',[filtered,unfiltered])
ax.set_yticks(range(3),[NAME[m] for m in METHODS]);ax.set_ylim(2.55,-.45);ax.set_xlim(-3.3,2.6);ax.set_xlabel('Minimum observed gap (m)');ax.axvline(0,color='#555',ls=':',lw=.65);frame(ax,'(c) Removing the HDV filter',grid='x')
ax.legend([Line2D([0],[0],marker='o',ls='none',mfc='white',mec='#333',ms=4),Line2D([0],[0],marker='o',ls='none',color='#333',ms=4)],['All vehicles','CAVs only'],loc='lower left',frameon=False,ncol=2,fontsize=6.8,handletextpad=.4,columnspacing=1.2)
ax=aa[1,1]
for i,m in enumerate(METHODS):
    overlap=(group(13,m).violations.to_numpy()>0)
    for seed,failed in enumerate(overlap):
        ax.add_patch(Rectangle((seed-.40,i-.27),.8,.54,facecolor=COL[m] if failed else '#E9EDF1',edgecolor='white',lw=.35))
    ax.text(20.1,i,f'{int(overlap.sum())}/20',va='center',ha='left',fontsize=7.6,color=COL[m])
    record(12,'d',NAME[m],'negative-gap indicator for seeds 0 to 19',overlap.astype(int))
ax.set_xlim(-.8,23);ax.set_ylim(2.8,-.55);ax.set_yticks(range(3),[NAME[m] for m in METHODS]);ax.set_xticks([0,5,10,15,19]);ax.set_xlabel('Random seed');frame(ax,'(d) Runs with negative gaps',grid=None)
ax.legend([Patch(color='#666'),Patch(color='#E9EDF1')],['Negative gap','No negative gap'],loc='lower left',frameon=False,ncol=2,fontsize=6.8,handlelength=.9,columnspacing=.9)
save(fig,axes,12)

# Figure 13: fuel distributions and aligned spacing maps use a common gap scale.
fig,aa=plt.subplots(2,2,figsize=SIZE[13],gridspec_kw={'height_ratios':[1.4,1]});axes=list(aa.flat)
fig.subplots_adjust(left=.093,right=.98,bottom=.135,top=.885,wspace=.33,hspace=.62)
for col,cids,labs in [(0,[14,1,15],['650','750','850']),(1,[16,1,17],['80','100','120'])]:
    x=[float(v) for v in labs]
    series(aa[0,col],cids,x,'fuel_L100',13,chr(97+col));aa[0,col].set_ylabel('Fuel (L/100 km)')
    frame(aa[0,col],'(a) Closure position and fuel' if col==0 else '(b) Speed scale and fuel')
    aa[0,col].set_xlabel('Closure coordinate (m)' if col==0 else 'Initial/desired speed scale (%)')
    vals=np.array([[row(cid,m).minimum_observed_gap for cid in cids] for m in METHODS])
    record(13,chr(99+col),'COOP/ECO/PASSIVE by '+str(labs),'minimum gap over seeds',vals)
    heat(aa[1,col],vals,labs,'(c) Minimum gap (m)' if col==0 else '(d) Minimum gap (m)',1.3,2.12,cmap=GAP_CMAP,norm=TwoSlopeNorm(2,1.3,2.12),fmt='.3f',flag_below=2)
    aa[1,col].set_xlabel('Closure coordinate (m)' if col==0 else 'Initial/desired speed scale (%)')
legend(aa[0,0],loc='upper left');aa[0,0].set_ylim(top=8.95)
save(fig,axes,13)

(ROOT/'plot_audit.json').write_text(json.dumps({'sizes_inches':SIZE,'plotted_values':AUDIT},indent=2),encoding='utf-8')
print('Verified figure values and generated mixed-style Figs 9–13:', len(AUDIT), 'plotted groups')
