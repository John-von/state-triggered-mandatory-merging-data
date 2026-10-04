from pathlib import Path
import csv,json,sys,math
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parent;A=ROOT/'analysis'; D=ROOT.parent/'PLOS_ONE_Mixed_Traffic_Merging_Data/data/raw'
def read(p):
 with p.open(encoding='utf-8-sig') as f:return [{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]
def group(rows,**kv):return sorted([r for r in rows if all(abs(r[k]-v)<1e-8 for k,v in kv.items())],key=lambda r:r['seed'])
def stats(x):
 x=np.asarray(x);m=float(x.mean());se=float(x.std(ddof=1)/math.sqrt(len(x)));return {'mean':m,'ci_low':m-2.093024054408263*se,'ci_high':m+2.093024054408263*se}
def summary(rows,mapping):return {label:float(np.mean([r[col] for r in rows])) for label,col in mapping.items()}
c=read(D/'joint_raw.csv');e=read(D/'eco_joint_raw.csv');new=read(A/'revision_experiments.csv')
out={'factorial':[],'thresholds':[]}
cols={'fuel':'perkm_L100','speed':'v_mean','arms':'a_rms','sigma':'sigma_v','stop':'stop_veh_s','totalfuel':'fuelL'}
newcols={'fuel':'fuel_L100','speed':'mean_speed','arms':'acceleration_rms','sigma':'speed_sd','stop':'stopped_vehicle_s','totalfuel':'total_fuel_L'}
for sp in [40,28,20]:
 original_c=group(c,sp1=sp,penetration=.75,mode=1);original_e=group(e,sp1=sp,penetration=.75)
 t=group(new,spacing=sp,variant=1);u=group(new,spacing=sp,variant=2)
 rec={'density':1000/sp,'spacing':sp,'COOP':summary(original_c,cols),'trigger_only':summary(t,newcols),'config_only':summary(u,newcols),'ECO':summary(original_e,cols)}
 for field,label in [('perkm_L100','fuel'),('v_mean','speed'),('a_rms','arms')]:
  nc=newcols[label]; sign=-1 if label=='speed' else 1
  b=np.array([r[field] for r in original_c]);z=np.array([r[field] for r in original_e]);x=np.array([r[nc] for r in t]);y=np.array([r[nc] for r in u]);
  rec[label+'_trigger_with_coop']=stats(100*sign*(b-x)/b)
  rec[label+'_trigger_with_eco']=stats(100*sign*(y-z)/y)
  rec[label+'_config_without_trigger']=stats(100*sign*(b-y)/b)
  rec[label+'_config_with_trigger']=stats(100*sign*(x-z)/x)
 rec['completion_min']=min(r['completion'] for r in t+u);rec['min_gap']=min(r['minimum_gap'] for r in t+u);rec['violations']=sum(r['violations'] for r in t+u)
 out['factorial'].append(rec)
for sp,v in sorted({(r['spacing'],r['variant']) for r in new if r['variant']>2}):
 base=group(e,sp1=sp,penetration=.75);cur=group(new,spacing=sp,variant=v)
 b=np.array([r['perkm_L100'] for r in base]);z=np.array([r['fuel_L100'] for r in cur])
 out['thresholds'].append({'density':1000/sp,'spacing':sp,'variant':v,'fuel_change_pct':stats(100*(z-b)/b),'completion_min':min(r['completion'] for r in cur),'min_gap':min(r['minimum_gap'] for r in cur),'violations':sum(r['violations'] for r in cur),'speed':float(np.mean([r['mean_speed'] for r in cur]))})
out['new_runs']=len(new);out['completion_min']=min(r['completion'] for r in new);out['violations']=sum(r['violations'] for r in new);out['min_gap']=min(r['minimum_gap'] for r in new)
if (A/'runtime_steps.csv').exists():
 rr=read(A/'runtime_steps.csv');out['runtime']=[]
 for n,m in sorted({(r['vehicles'],r['mode']) for r in rr}):
  xx=[r['milliseconds'] for r in rr if r['vehicles']==n and r['mode']==m]
  out['runtime'].append({'vehicles':n,'mode':m,'steps':len(xx),'mean_ms':float(np.mean(xx)),'p95_ms':float(np.percentile(xx,95)),'maximum_ms':float(max(xx)),'steps_over_100ms':sum(x>100 for x in xx)})
(A/'summary.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
