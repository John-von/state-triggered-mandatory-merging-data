"""Compute robustness summaries and paired contrasts from saved records."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
import numpy as np
import pandas as pd
from scipy import stats

A=ROOT/'analysis'
d=pd.read_csv(A/'robustness_experiments.csv')
c=pd.read_csv(A/'component_experiments.csv')
settings=pd.read_csv(A/'experiment_settings.csv')
assert len(d)==1020 and not d.duplicated(['condition_id','mode_id','seed']).any()
assert len(c)==120 and not c.duplicated(['component_id','seed']).any()
assert np.isfinite(d.to_numpy()).all() and np.isfinite(c.to_numpy()).all()
assert all(set(g.seed)==set(range(20)) for _,g in d.groupby(['condition_id','mode_id']))
assert all(set(g.seed)==set(range(20)) for _,g in c.groupby('component_id'))
modes={1:'COOP',2:'ECO',3:'PASSIVE'}
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


print('Summarized 1020 robustness runs and 120 component reversions.')
