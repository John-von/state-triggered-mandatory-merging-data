"""Create publication figures from the corrected experiment records."""
from pathlib import Path
import json,sys
import numpy as np
import pandas as pd
from scipy.io import loadmat
from scipy.stats import t
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import Rectangle

ROOT=Path(__file__).resolve().parent;P=ROOT/'processed';A=ROOT/'corrected';OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
from inside_labels import overlaps_data
D=pd.read_csv(P/'seed_metrics.csv');M=D[D.family==1];Q=pd.read_csv(P/'queues.csv');R=pd.read_csv(P/'robustness.csv');C=pd.read_csv(P/'paired_contrasts.csv');G=pd.read_csv(P/'matched_grid.csv')
COL=['#AD332B','#1A6B4D','#3D5294'];NAM=['COOP','ECO','PASSIVE'];MK=['o','D','s'];LS=['-','--','-.']
plt.rcParams.update({'font.family':'Times New Roman','font.size':8,'axes.labelsize':8,'xtick.labelsize':7.2,'ytick.labelsize':7.2,'axes.linewidth':.65,'legend.fontsize':7.2,'pdf.fonttype':42,'svg.fonttype':'none','savefig.facecolor':'white'})

def frame(ax):
 ax.tick_params(direction='in',top=True,right=True,length=2.5,width=.6,pad=2)
 ax.grid(color='#DFE3E8',lw=.4);ax.set_axisbelow(True)

def err(x):
 x=np.asarray(x);return x.mean(),t.ppf(.975,len(x)-1)*x.std(ddof=1)/np.sqrt(len(x))

def panels(nr,nc,h):
 f,axs=plt.subplots(nr,nc,figsize=(6.45,h),squeeze=False)
 f.subplots_adjust(left=.105,right=.98,bottom=.11,top=.985,wspace=.34,hspace=.38)
 for ax in axs.flat:frame(ax)
 return f,list(axs.flat)

def legend(ax):
 ax.legend(loc='best',frameon=False,ncol=3,handlelength=1.3,columnspacing=.8,handletextpad=.35,fontsize=7)

def save(fig,axes,n):
 fig.canvas.draw();renderer=fig.canvas.get_renderer();positions=[]
 for i,ax in enumerate(axes):
  label=ax.text(.018,.975,f'({chr(97+i)})',transform=ax.transAxes,ha='left',va='top',fontsize=8.1,zorder=30)
  if ax.images:
   box=label.get_window_extent(renderer).expanded(1.05,1.08)
   for txt in ax.texts:
    if txt is not label and box.overlaps(txt.get_window_extent(renderer)):
     x,y=txt.get_position();txt.set_position((x,y+(.17 if ax.yaxis_inverted() else -.17)))
  else:
   candidates=[(.018,.975,'left','top'),(.98,.975,'right','top'),(.98,.035,'right','bottom'),(.018,.035,'left','bottom'),(.5,.975,'center','top')]
   candidates += [(x,y,'left','top') for y in [.9,.75,.6,.45,.3,.15] for x in [.02,.3,.6,.85]]
   best=None
   for x,y,ha,va in candidates:
    label.set_position((x,y));label.set_ha(ha);label.set_va(va)
    score=overlaps_data(ax,label.get_window_extent(renderer),renderer,label)
    if best is None or score<best[0]:best=(score,x,y,ha,va)
    if score==0:break
   score,x,y,ha,va=best;label.set_position((x,y));label.set_ha(ha);label.set_va(va)
   positions.append((i,score,x,y))
  label.set_gid('panel-letter')
 fig.canvas.draw()
 for ext in ['png','pdf','tif']:
  kw={'dpi':300} if ext=='png' else {'dpi':600,'pil_kwargs':{'compression':'tiff_lzw'}} if ext=='tif' else {}
  fig.savefig(OUT/f'Fig{n}.{ext}',**kw)
 plt.close(fig);print(f'Figure {n} rendered; label checks {positions}')

def traj(row):return loadmat(A/f'trajectory_{int(row.run_id):04d}.mat',simplify_cells=True)['R']

def main_figures():
 reps=[traj(M[(M.spacing==24)&(M.penetration==.75)&(M.seed==0)&(M.mode_id==mi)].iloc[0]) for mi in [1,2,3]]
 times=np.arange(1,901)*.1
 f,axs=panels(3,1,4.7);f.subplots_adjust(hspace=.16,bottom=.09)
 for ax,r in zip(axs,reps):
  for i,col in enumerate(plt.colormaps['turbo'](np.linspace(0,1,12))):ax.plot(times,r['recX'][:,i],color=col,lw=.6)
  ax.axhline(750,color='#555',ls='--',lw=.65);ax.set_xlim(0,90);ax.set_ylabel('Longitudinal position (m)')
 axs[-1].set_xlabel('Time (s)');save(f,axs,1)
 f,axs=panels(2,2,4.1)
 for i,r in enumerate(reps):
  series=[r['recV'].mean(axis=1),(r['recV']<1).sum(axis=1),r['cumulative_fuel_L'],(r['recX']-r['initial']['x']).sum(axis=1)/1000]
  for ax,y in zip(axs,series):ax.plot(times,y,color=COL[i],ls=LS[i],lw=1,label=NAM[i])
 for ax,ylabel in zip(axs,['Fleet mean speed (m/s)','Stopped vehicles','Cumulative fuel (L)','Cumulative distance (veh km)']):ax.set(xlabel='Time (s)',ylabel=ylabel,xlim=(0,90))
 legend(axs[0]);save(f,axs,2)
 c=C[(C.family=='main')&(C.baseline=='COOP')]
 f,axs=panels(2,2,3.8);f.subplots_adjust(right=.87,left=.09,wspace=.3,hspace=.32)
 for ax,met in zip(axs,['fuel_L100','sigma_v','actual_acceleration_rms','v_mean']):
  z=c[c.metric==met].pivot(index='penetration',columns='spacing',values='rel_mean').reindex(index=[0,.25,.5,.75,1],columns=[40,34,28,24,20]).to_numpy()
  im=ax.imshow(z,origin='lower',aspect='auto',cmap='RdYlGn',vmin=-25,vmax=25)
  ax.grid(False);ax.set_xticks(range(5),['25.0','29.4','35.7','41.7','50.0']);ax.set_yticks(range(5),['0','25','50','75','100']);ax.set(xlabel='Initial density (veh/km)',ylabel='CAV penetration (%)')
  for (i,j),v in np.ndenumerate(z):ax.text(j,i,f'{v:.1f}',ha='center',va='center',fontsize=7.1,color='white' if abs(v)>17 else '#222')
 cb=f.colorbar(im,cax=f.add_axes([.91,.18,.018,.65]));cb.set_label('Relative improvement (%)');save(f,axs,3)
 f,axs=panels(1,3,2.35);f.subplots_adjust(right=.87,left=.085,bottom=.26,wspace=.46)
 for ax,bm,ym in zip(axs,['COOP','PASSIVE','COOP'],['v_mean','v_mean','fuel_L']):
  x=C[(C.family=='main')&(C.baseline==bm)&(C.metric=='fuel_L100')&(C.penetration>0)].sort_values(['spacing','penetration'])
  y=C[(C.family=='main')&(C.baseline==bm)&(C.metric==ym)&(C.penetration>0)].sort_values(['spacing','penetration'])
  im=ax.scatter(x.rel_mean,y.rel_mean,c=1000/x.spacing,cmap='viridis',vmin=25,vmax=50,s=23,edgecolors='#444',linewidths=.3,zorder=3)
  ax.axvline(0,color='#777',ls=':',lw=.6);ax.axhline(0,color='#777',ls=':',lw=.6)
  ax.set_xlabel(f'Fuel-intensity saving\nvs {bm} (%)');ax.set_ylabel('Mean-speed gain (%)' if ym=='v_mean' else 'Total-fuel saving (%)')
 cb=f.colorbar(im,cax=f.add_axes([.91,.28,.018,.65]));cb.set_label('Initial density (veh/km)');save(f,axs,4)

def attribution():
 f,axs=panels(2,2,4.1);f.subplots_adjust(hspace=.45,wspace=.42)
 z=G[G.metric=='fuel_L100'].pivot(index='penetration',columns='spacing',values='rel_mean').reindex(index=[0,.25,.5,.75,1],columns=[40,34,28,24,20]).to_numpy()
 ax=axs[0];im=ax.imshow(z,origin='lower',aspect='auto',cmap='YlGnBu',vmin=0,vmax=6);ax.grid(False);ax.set_xticks(range(5),['25.0','29.4','35.7','41.7','50.0']);ax.set_yticks(range(5),['0','25','50','75','100']);ax.set(xlabel='Initial density (veh/km)',ylabel='CAV penetration (%)')
 for (i,j),v in np.ndenumerate(z):ax.text(j,i,f'{v:.2f}',ha='center',va='center',fontsize=6.7,color='white' if v>3.5 else '#222')
 b=M[(M.spacing==24)&(M.penetration==.75)&(M.mode_id==2)].sort_values('seed');labels=['Ramp/clock','Scheduling','Weights/gain','Accel. limits','Admission','Gap buffer']
 for i in range(6):
  g=D[(D.family==7)&(D.variant==i+1)].sort_values('seed');mu,hs=err((g.fuel_L100.to_numpy()/b.fuel_L100.to_numpy()-1)*100)
  axs[1].errorbar(mu,i,xerr=hs,fmt='o',color=plt.colormaps['tab10'](i),ms=3,capsize=2,lw=.8)
 axs[1].set_yticks(range(6),labels);axs[1].invert_yaxis();axs[1].axvline(0,color='#666',ls=':',lw=.6);axs[1].set_xlabel('Fuel change on reversion (%)')
 z=np.zeros((3,4))
 for i,sp in enumerate([40,28,20]):
  base=M[(M.spacing==sp)&(M.penetration==.75)&(M.mode_id==2)].sort_values('seed')
  for j,v in enumerate([130,135,140,145]):
   g=base if v==135 else D[(D.family==8)&(D.spacing==sp)&(D.variant==v)].sort_values('seed')
   z[i,j]=(1-g.fuel_L100.to_numpy()/base.fuel_L100.to_numpy()).mean()*100
 ax=axs[2];ax.imshow(z,aspect='auto',cmap='RdYlGn',vmin=-6,vmax=6);ax.grid(False);ax.set_xticks(range(4),['30','35','40','45']);ax.set_yticks(range(3),['25.0','35.7','50.0']);ax.set(xlabel='Density threshold (veh/km)',ylabel='Initial density (veh/km)')
 for (i,j),v in np.ndenumerate(z):ax.text(j,i,f'{v:.2f}%',ha='center',va='center',fontsize=7)
 for i,v in enumerate([1250,1550,2015,2040]):
  g=D[(D.family==8)&(D.variant==v)].sort_values('seed');mu,hs=err((1-g.fuel_L100.to_numpy()/b.fuel_L100.to_numpy())*100)
  axs[3].barh(i,mu,xerr=hs,color=['#8E6BB0','#B09ACB','#D8879F','#C35178'][i],height=.5,capsize=2,error_kw={'linewidth':.6})
 axs[3].set_yticks(range(4),['Start 250 m','Start 550 m','Critical 15 m','Critical 40 m']);axs[3].invert_yaxis();axs[3].axvline(0,color='#777',lw=.6);axs[3].set_xlabel('Fuel-intensity saving (%)');save(f,axs,5)

def boxes(ax,groups,positions,colors,width=.18):
 for x,g,col in zip(positions,groups,colors):
  a=np.asarray(g);bp=ax.boxplot(a,positions=[x],widths=width,patch_artist=True,showfliers=False,manage_ticks=False,medianprops={'color':col,'linewidth':1},boxprops={'facecolor':col+'30','edgecolor':col,'linewidth':.7},whiskerprops={'color':col,'linewidth':.7},capprops={'color':col,'linewidth':.7})
  ax.scatter(x+np.linspace(-width*.32,width*.32,len(a)),a,s=7,color=col,alpha=.45,linewidths=0,zorder=3);ax.scatter([x],[a.mean()],marker='D',s=14,facecolors='white',edgecolors=col,linewidths=.7,zorder=4)

def queue_fig():
 f,axs=panels(3,2,5.25);f.subplots_adjust(hspace=.46,bottom=.09)
 for i in range(3):
  g=Q[Q.mode_id==i+1];vals=[err(g[g.n==n].comp_rate) for n in [38,57,76]]
  axs[0].errorbar(np.array([0,1,2])+(i-1)*.16,[v[0] for v in vals],yerr=[v[1] for v in vals],fmt=MK[i],color=COL[i],mfc='white',capsize=2,ms=3,label=NAM[i])
  ids=g[g.n==57].run_id.astype(int);curves=[loadmat(A/f'run_{j:04d}.mat',simplify_cells=True)['S']['completion_curve'] for j in ids]
  axs[1].plot(np.arange(1,901)*.1,np.mean(curves,axis=0)*100,color=COL[i],ls=LS[i],lw=1)
 axs[0].set_xticks([0,1,2],['38','57','76']);axs[0].set(xlabel='Vehicles',ylabel='Merge completion (%)',ylim=(-5,116));legend(axs[0])
 axs[1].set(xlabel='Time (s)',ylabel='Completed by time t (%)',xlim=(0,90),ylim=(-4,100))
 com=pd.read_csv(P/'common_service.csv');g=Q[Q.n==57]
 for ax,data,met,yl in [(axs[2],g,'delay_vehicle_s','Fleet delay (veh s)'),(axs[3],g,'fuel_L','Total fleet fuel (L)'),(axs[4],com[com.n==57],'fuel_L','Fuel to common service (L)')]:
  boxes(ax,[data[data.mode_id==i+1][met] for i in range(3)],[0,1,2],COL,.42);ax.set_xticks([0,1,2],NAM);ax.set_ylabel(yl)
 for i in range(3):
  g=Q[Q.mode_id==i+1];vals=[err(g[g.n==n].residual_at_end) for n in [38,57,76]]
  axs[5].errorbar(np.arange(3)+(i-1)*.16,[v[0] for v in vals],yerr=[v[1] for v in vals],fmt=MK[i],color=COL[i],mfc='white',capsize=2,ms=3)
 axs[5].set_xticks([0,1,2],['38','57','76']);axs[5].set(xlabel='Vehicles',ylabel='Residual queue at 90 s');save(f,axs,6)

def heat(ax,condition_ids,labels):
 z=np.array([[R[(R.mode_id==mi)&(R.variant==v)].min_gap.min() for v in condition_ids] for mi in [1,2,3]])
 ax.imshow(z,aspect='auto',cmap='RdYlGn',norm=TwoSlopeNorm(vmin=1,vcenter=2,vmax=3));ax.grid(False);ax.set_xticks(range(len(labels)),labels,fontsize=6.8);ax.set_yticks(range(3),NAM)
 for (i,j),v in np.ndenumerate(z):
  ax.text(j,i,f'{v:.3f}',ha='center',va='center',fontsize=6.6)
  if v<2-1e-8:ax.add_patch(Rectangle((j-.49,i-.49),.98,.98,fill=False,ec=COL[0],lw=.8))

def robust_figures():
 f,axs=panels(3,2,5.15);f.subplots_adjust(hspace=.48,bottom=.08)
 for ax,ids,x,met,yl,xl in [(axs[0],[1,2,3,4],[0,100,300,500],'fuel_L100','Fuel (L/100 km)','Broadcast delay (ms)'),(axs[1],[1,2,3,4],[0,100,300,500],'comp_rate','Merge completion (%)','Broadcast delay (ms)'),(axs[2],[1,5,6,7],[0,5,10,20],'fuel_L100','Fuel (L/100 km)','Packet loss (%)')]:
  for i in range(3):
   vals=[err(R[(R.mode_id==i+1)&(R.variant==v)][met]) for v in ids];ax.errorbar(x,[v[0] for v in vals],yerr=[v[1] for v in vals],fmt=MK[i]+LS[i],color=COL[i],mfc='white',ms=3,lw=.85,capsize=2,label=NAM[i])
  ax.set(xlabel=xl,ylabel=yl)
 legend(axs[0]);axs[1].set_ylim(-5,110)
 for ax,met,yl in [(axs[3],'fuel_L100','Fuel (L/100 km)'),(axs[4],'actual_jerk_rms','Realized jerk RMS (m/s³)')]:
  for j,v in enumerate([1,8,9,10]):boxes(ax,[R[(R.mode_id==i+1)&(R.variant==v)][met] for i in range(3)],[j-.22,j,j+.22],COL,.17)
  ax.set_xticks(range(4),['Ideal','Control\nnoise','All-layer\nnoise','Combined']);ax.set_ylabel(yl)
 heat(axs[5],[1,3,4,7,8,9,10],['Ideal','300\nms','500\nms','20%\nloss','Control\nnoise','All-layer\nnoise','Comb.']);save(f,axs,7)
 f,axs=panels(2,2,3.85);f.subplots_adjust(hspace=.4,bottom=.15)
 for ax,met,yl in [(axs[0],'fuel_L100','Fuel (L/100 km)'),(axs[1],'actual_jerk_rms','Realized jerk RMS (m/s³)')]:
  for j,v in enumerate([1,11,12]):boxes(ax,[R[(R.mode_id==i+1)&(R.variant==v)][met] for i in range(3)],[j-.22,j,j+.22],COL,.17)
  ax.set_xticks(range(3),['0','±20','±40']);ax.set(xlabel='Bounded IDM variation (%)',ylabel=yl)
 for i in range(3):axs[0].plot([],[],color=COL[i],marker=MK[i],ls='none',label=NAM[i])
 legend(axs[0])
 for i in range(3):
  a=R[(R.mode_id==i+1)&(R.variant==11)].min_gap.min();b=R[(R.mode_id==i+1)&(R.variant==13)].min_gap.min()
  axs[2].plot([a,b],[i,i],color=COL[i],lw=1);axs[2].scatter([a,b],[i,i],color=COL[i],s=22,marker=MK[i]);axs[2].text(min(a,b)-.1,i+.15,f'{b:.2f}',color=COL[i],fontsize=7)
  bad=R[(R.mode_id==i+1)&(R.variant==13)].sort_values('seed').final_gap_violation_steps>0
  for j,x in enumerate(bad):axs[3].bar(j,1,bottom=i-.5,width=.72,color=COL[0] if x else '#DDE2E5')
  axs[3].text(20,i,f'{sum(bad)}/20',va='center',fontsize=7)
 axs[2].axvline(2,color='#777',ls=':',lw=.65);axs[2].axvline(0,color='#777',ls=':',lw=.65);axs[2].set_yticks(range(3),NAM);axs[2].set(xlabel='Minimum net gap (m)',xlim=(-4.3,2.6),ylim=(2.4,-.3))
 axs[3].set_yticks(range(3),NAM);axs[3].set_xticks([0,5,10,15,19]);axs[3].set(xlabel='Random seed',xlim=(-.8,22),ylim=(2.6,-.6));axs[3].grid(False);save(f,axs,8)
 f,axs=panels(2,2,3.75)
 for ax,ids,x,xl in [(axs[0],[14,1,15],[650,750,850],'Closure coordinate (m)'),(axs[1],[16,1,17],[80,100,120],'Initial/desired speed scale (%)')]:
  for i in range(3):
   vals=[err(R[(R.mode_id==i+1)&(R.variant==v)].fuel_L100) for v in ids];ax.errorbar(x,[v[0] for v in vals],yerr=[v[1] for v in vals],fmt=MK[i]+LS[i],color=COL[i],mfc='white',ms=3,lw=.9,capsize=2,label=NAM[i])
  ax.set(xlabel=xl,ylabel='Fuel (L/100 km)')
 legend(axs[0]);heat(axs[2],[14,1,15],['650','750','850']);heat(axs[3],[16,1,17],['80','100','120']);axs[2].set_xlabel('Closure coordinate (m)');axs[3].set_xlabel('Speed scale (%)');save(f,axs,9)

def hold_fig():
 f,axs=panels(3,2,5.0);f.subplots_adjust(hspace=.4,bottom=.09)
 for speed,col,ls in [(16,COL[1],'-'),(4,COL[2],'--')]:
  r=loadmat(A/f'hold_physical_{speed}.mat',simplify_cells=True)['R'];initial=r['initial'];tt=np.arange(121)*.1
  y=np.r_[initial['y'][0],r['recY'][:,0]];yd=r['recV'][:,0]*np.sin(r['recPsi'][:,0])+r['recVy'][:,0]*np.cos(r['recPsi'][:,0]);yd=np.r_[initial['vx'][0]*np.sin(initial['psi'][0])+initial['vy'][0]*np.cos(initial['psi'][0]),yd]
  if speed==4:yd=np.r_[yd[0],np.diff(y)/.1]
  series=[y,yd,np.r_[0,r['recSteer'][:,0]],np.r_[initial['om'][0],r['recYaw'][:,0]],np.r_[39,r['front_gaps']],np.r_[.2,r['rear_gaps']]]
  for j,(ax,yy) in enumerate(zip(axs,series)):
   if speed==4 and j in [2,3]:continue
   ax.plot(tt,yy,color=col,ls=ls,lw=1,label=f'{speed} m/s')
  restart=float(np.atleast_2d(r['restart_records'])[0,0])
  for ax in axs:ax.axvline(restart,color=col,ls=':',lw=.55,alpha=.8)
 for ax,yl in zip(axs,['Lateral position (m)','Inertial lateral speed (m/s)','Steering command (rad)','Yaw rate (rad/s)','Front net gap (m)','Rear net gap (m)']):ax.set(xlim=(0,5),xlabel='Time (s)',ylabel=yl)
 legend(axs[0]);axs[5].axhline(2,color='#888',lw=.65,ls='--');save(f,axs,10)

if __name__=='__main__':
 main_figures();attribution();queue_fig();robust_figures();hold_fig()
