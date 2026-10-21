"""Aggregate the corrected paired simulations without importing legacy results."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.io import loadmat
from scipy import stats

ROOT=Path(__file__).resolve().parent
A=ROOT/'corrected';OUT=ROOT/'processed';OUT.mkdir(exist_ok=True)
COLS=['family','scale','mode_id','seed','spacing','penetration','variant','gate']
METRICS=['comp_rate','fuel_L100','fuel_L','sigma_v','a_rms','actual_acceleration_rms','v_mean','stopped_vehicle_s','delay_vehicle_s','actual_jerk_rms']
MODES={1:'COOP',2:'ECO',3:'PASSIVE'}

def ci(x):
 a=np.asarray(x,dtype=float);a=a[np.isfinite(a)]
 if len(a)==0:return {'mean':np.nan,'lo':np.nan,'hi':np.nan,'sd':np.nan,'n':0}
 m=float(a.mean());sd=float(a.std(ddof=1)) if len(a)>1 else 0
 h=stats.t.ppf(.975,len(a)-1)*sd/np.sqrt(len(a)) if len(a)>1 else 0
 return {'mean':m,'lo':m-h,'hi':m+h,'sd':sd,'n':len(a)}

def holm(ps):
 p=np.asarray(ps);idx=np.argsort(p);out=np.empty_like(p)
 out[idx]=np.minimum(1,np.maximum.accumulate(p[idx]*(len(p)-np.arange(len(p)))))
 return out

def paired(a,b):
 x=np.asarray(a)-np.asarray(b);x[np.abs(x)<1e-10]=0
 e=ci(x);sd=e['sd'];nz=np.count_nonzero(x)
 p=float(stats.ttest_1samp(x,0).pvalue) if sd>1e-12 else (1. if not nz else 0.)
 # Exact signed-rank enumeration for paired n=20, including tied ranks.
 if nz:
  ranks=stats.rankdata(abs(x[x!=0]));obs=float(ranks[x[x!=0]>0].sum())
  counts=np.array([0.])
  for v in ranks:counts=np.concatenate([counts,counts+v])
  pw=min(1.,2*min(np.mean(counts<=obs+1e-9),np.mean(counts>=obs-1e-9)))
 else:pw=1.
 return dict(e,p=p,p_wilcoxon=pw,dz=e['mean']/sd if sd>1e-12 else (0 if not nz else np.nan))

def main():
 rows=[];runs={}
 expected=pd.concat([pd.read_csv(A/'registered_jobs.csv'),pd.read_csv(A/'evaluation_jobs.csv')],ignore_index=True)
 for idx,j in expected.iterrows():
  fn=A/f'run_{idx+1:04d}.mat';raw=loadmat(fn,simplify_cells=True);s=raw['S'];runs[idx+1]=s
  assert np.allclose(np.array([j[c] for c in COLS]),s['job']),(idx,'job mismatch')
  d=dict(zip(COLS,s['job']));d['run_id']=idx+1
  for k,v in s.items():
   if np.isscalar(v) and k!='residual_queue':d[k]=v
  for k,v in s['qp'].items():d['qp_'+k]=v
  d['residual_at_end']=int(np.asarray(s['residual_queue']).reshape(-1)[-1])
  d['censored_completion_s']=float(np.nan_to_num(np.asarray(s['completion_time']),nan=90).mean())
  d['fuel_per_completed_L']=s['fuel_L']/s['n_merged'] if s['n_merged'] else np.nan
  rows.append(d)
 df=pd.DataFrame(rows);df.to_csv(OUT/'seed_metrics.csv',index=False)
 assert len(df)==3874
 assert np.isfinite(df[['fuel_L','fuel_L100','comp_rate','min_gap']]).all().all()
 main=df[df.family==1].copy();main.to_csv(OUT/'main_grid.csv',index=False)
 robust=pd.concat([main[(main.spacing==24)&(main.penetration==.75)].assign(variant=1),df[df.family==5]])
 robust.to_csv(OUT/'robustness.csv',index=False)
 queue=pd.concat([main[(main.spacing==24)&(main.penetration==.75)],df[df.family==2]])
 queue.to_csv(OUT/'queues.csv',index=False)
 abl=pd.concat([main[(main.spacing==24)&(main.penetration==.75)&(main.mode_id==2)].assign(variant=1),df[df.family==6]])
 abl.to_csv(OUT/'ablation.csv',index=False)
 contrasts=[]
 for family,data,keys in [('main',main,['spacing','penetration']),('robustness',robust,['variant']),('queue',queue,['n'])]:
  for group,g in data.groupby(keys):
   group=(group,) if not isinstance(group,tuple) else group
   e=g[g.mode_id==2].sort_values('seed')
   for bm in [1,3]:
    b=g[g.mode_id==bm].sort_values('seed');assert list(e.seed)==list(b.seed)
    for met in METRICS+['censored_completion_s']:
     p=paired(e[met],b[met]);p['sample_size']=p.pop('n');d=dict(family=family,baseline=MODES[bm],metric=met,**dict(zip(keys,group)),**p)
     if met not in ['comp_rate','stopped_vehicle_s','delay_vehicle_s','censored_completion_s']:
      rel=(1-e[met].to_numpy()/b[met].to_numpy())*100
      if met=='v_mean':rel=-rel
      d.update({f'rel_{k}':v for k,v in ci(rel).items()})
     contrasts.append(d)
 c=pd.DataFrame(contrasts)
 for _,g in c.groupby(['family','baseline','metric']):
  c.loc[g.index,'p_holm']=holm(g.p);c.loc[g.index,'p_wilcoxon_holm']=holm(g.p_wilcoxon)
 c.to_csv(OUT/'paired_contrasts.csv',index=False)
 matched=[]
 for (sp,pen),b in df[df.family==4].groupby(['spacing','penetration']):
  b=b.sort_values('seed');e=main[(main.spacing==sp)&(main.penetration==pen)&(main.mode_id==2)].sort_values('seed')
  for met in METRICS:
   p=paired(e[met],b[met]);rel=ci((1-e[met].to_numpy()/b[met].to_numpy())*100) if np.all(b[met]!=0) else ci([])
   matched.append(dict(spacing=sp,penetration=pen,metric=met,**p,**{f'rel_{k}':v for k,v in rel.items()}))
 m=pd.DataFrame(matched)
 for _,g in m.groupby('metric'):m.loc[g.index,'p_holm']=holm(g.p)
 m.to_csv(OUT/'matched_grid.csv',index=False)
 common=[]
 for (n,seed),g in queue.groupby(['n','seed']):
  count=int(g.n_merged.min())
  for _,row in g.iterrows():
   s=runs[int(row.run_id)]
   if count:
    t=float(np.sort(np.asarray(s['completion_time']).reshape(-1))[count-1]);ix=int(round(t/.1))-1
    fuel=float(s['cumulative_fuel_L'][ix]);delay=float(s['delay_curve'][ix])
   else:t=fuel=delay=np.nan
   common.append(dict(n=n,seed=seed,mode_id=row.mode_id,completed=count,time_s=t,fuel_L=fuel,delay_vehicle_s=delay))
 pd.DataFrame(common).to_csv(OUT/'common_service.csv',index=False)
 summary={'runs':len(df),'main':[],'queue':[],'robustness':[],'ablation':[],'tuning':[],'refinement':[],'hold':[]}
 for typ,data,keys in [('main',main,['spacing','penetration','mode_id']),('queue',queue,['n','mode_id']),('robustness',robust,['variant','mode_id']),('ablation',abl,['variant']),('tuning',df[df.family==11],['gate','spacing'])]:
  for group,g in data.groupby(keys):
   group=(group,) if not isinstance(group,tuple) else group;row=dict(zip(keys,group));row['n_runs']=len(g)
   for met in METRICS+['censored_completion_s','residual_at_end','fuel_per_completed_L']:row[met]=ci(g[met])
   for met in ['min_gap','closure_front_clearance','acceleration_min','minimum_headway_margin','minimum_cap']:row[met]=float(g[met].min())
   for met in ['acceleration_max','jerk_abs_max','qp_residual_max','qp_applied_residual_max']:row[met]=float(g[met].max())
   for met in ['final_gap_violation_steps','standstill_violations','headway_violations','filter_infeasible','filter_infeasible_steps','filter_hdv','filter_cav','closure_interventions','closure_infeasible','closure_boundary_samples','qp_calls','qp_iterations','qp_limit','qp_residual_bad','qp_repair_calls','qp_repair_success','qp_hold_fallback','qp_numerical_fallback','n_abort']:row[met]=int(g[met].sum())
   row['overlap_runs']=int((g.final_gap_violation_steps>0).sum());row['full_completion_runs']=int((g.comp_rate==100).sum())
   summary[typ].append(row)
 for (n,mi,ns),g in df[df.family==10].groupby(['n','mode_id','variant']):
  summary['refinement'].append(dict(n=n,mode_id=mi,substeps=ns,minimum_gap=float(g.min_gap.min()),dense_min_gap=float(g.dense_min_gap.min()),dense_overlap=int(g.dense_overlap.sum()),closure_samples=int(g.closure_boundary_samples.sum()),completion_mean=float(g.comp_rate.mean())))
 for speed in [16,4]:
  r=loadmat(A/f'hold_physical_{speed}.mat',simplify_cells=True)['R']
  rr=np.atleast_2d(r['restart_records'])
  summary['hold'].append(dict(speed=speed,events=int(r['n_abort']),completion_s=float(np.asarray(r['completion_time']).reshape(-1)[0]),restart_s=float(rr[0,0]),minimum_gap_including_initial=float(min(.2,r['min_gap'])),steering_max=float(abs(r['recSteer'][:,0]).max()),yaw_max=float(abs(r['recYaw'][:,0]).max()),state_match_error=float(abs(rr[:,2:5]-rr[:,5:8]).max())))
 (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({'runs':len(df),'queues':[(x['n'],x['mode_id'],x['comp_rate']['mean'],x['min_gap']) for x in summary['queue']],'main_ECO_completion_min':float(main[main.mode_id==2].comp_rate.min()),'main_ECO_gap_min':float(main[main.mode_id==2].min_gap.min()),'closure_boundary_samples':int(df.closure_boundary_samples.sum()),'hold':summary['hold']},indent=2))

if __name__=='__main__':main()
