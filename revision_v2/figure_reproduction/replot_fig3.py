from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import t
from inside_labels import arrange_inside
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'figures'
OUT.mkdir(exist_ok=True)
raw=np.concatenate([np.loadtxt(ROOT/'original_plot_inputs'/n,delimiter=',',skiprows=1) for n in ['joint_raw.csv','eco_joint_raw.csv']])
plt.rcParams.update({'font.family':'Times New Roman','font.size':8,'axes.labelsize':8,'xtick.labelsize':7.2,'ytick.labelsize':7.2,'axes.linewidth':.65,'pdf.fonttype':42,'svg.fonttype':'none'})
fig,aa=plt.subplots(2,2,figsize=(6.45,4.25))
fig.subplots_adjust(left=.095,right=.98,bottom=.12,top=.98,wspace=.31,hspace=.34)
spacing=[40,34,28,24,20];density=1000/np.array(spacing)
colors=['#AD332B','#1A6B4D','#3D5294'];markers=['o','D','s']
names=['Safety-priority cooperation','State-triggered cooperation','Passive merging']
for ax,col,yl in zip(aa.flat,[8,10,12,20],['Fuel (L/100 km)','Speed standard deviation (m/s)','Stopped-vehicle time (veh s)','Mean speed (m/s)']):
 for mode,c,m,n in zip([1,3,2],colors,markers,names):
  mu=[];ci=[]
  for sp in spacing:
   v=raw[np.isclose(raw[:,1],sp)&np.isclose(raw[:,2],.75)&(raw[:,3]==mode),col]
   assert len(v)==20
   mu.append(v.mean());ci.append(t.ppf(.975,19)*v.std(ddof=1)/np.sqrt(20))
  ax.errorbar(density,mu,yerr=ci,fmt=m+'-',color=c,mfc='white',ms=3.5,lw=1,capsize=2,elinewidth=.7,label=n)
 ax.set_xlabel('Target-lane density (veh/km)');ax.set_ylabel(yl)
 ax.tick_params(direction='in',top=True,right=True,length=2.5,width=.6)
 ax.grid(color='#DFE3E8',lw=.4);ax.set_axisbelow(True)
fig.legend(*aa[0,0].get_legend_handles_labels())
arrange_inside(fig,list(aa.flat),3)
fig.canvas.draw()
for ext in ['png','pdf','svg','tif']:
 kw={'dpi':400} if ext=='png' else {'dpi':600,'pil_kwargs':{'compression':'tiff_lzw'}} if ext=='tif' else {}
 fig.savefig(OUT/f'Fig3.{ext}',**kw)
for letter,ax in zip('abcd',aa.flat):
 box=ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted()).expanded(1.02,1.04)
 fig.savefig(OUT/f'Fig3{letter}.pdf',bbox_inches=box)
print('Reproduced Figure 3 with its legend inside.')
