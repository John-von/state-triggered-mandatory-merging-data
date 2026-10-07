root=fileparts(mfilename('fullpath')); addpath(fullfile(root,'code'));
out=fullfile(root,'analysis'); if ~exist(out,'dir'),mkdir(out);end
P=params_merge(); P.sp1=24;
R0=simulate_merge('ECO',0.75,0,P,false);
R1=simulate_revision('ECO',0.75,0,P,false);
assert(isequal(R0.recX,R1.recX) && isequal(R0.recV,R1.recV) && isequal(R0.recA,R1.recA),'Instrumentation changed baseline');
fprintf('Instrumentation baseline is bit-for-bit identical.\n');
fprintf('Filter applications CAV %d HDV %d; mean adjustment %.3f max %.3f\n',R1.filter_cav,R1.filter_hdv,R1.filter_delta_mean,R1.filter_delta_max);
save(fullfile(out,'instrumentation_validation.mat'),'R1');

% Three densities at 75% nominal target-lane penetration, twenty paired seeds.
% Two missing cells of a 2x2 design: COOP parameters with trigger;
% ECO parameters without the trigger. The archived COOP and ECO are retained.
jobs=[];
for sp=[40 28 20]
 for variant=1:2
  for seed=0:19, jobs(end+1,:)=[sp variant seed]; end
 end
end
% Threshold sensitivity at the representative density; all other ECO values fixed.
% Density thresholds are also examined across the three densities.
for threshold=[30 40 45]
 for sp=[40 28 20]
  for seed=0:19,jobs(end+1,:)=[sp 100+threshold seed];end
 end
end
for dist=[250 550]
 for seed=0:19,jobs(end+1,:)=[24 1000+dist seed];end
end
for critical=[15 40]
 for seed=0:19,jobs(end+1,:)=[24 2000+critical seed];end
end
fprintf('Revision simulations: %d\n',size(jobs,1));
pool=gcp('nocreate'); if isempty(pool),parpool('local',4);end
raw=zeros(size(jobs,1),17);
parfor ii=1:size(jobs,1)
 fn=fullfile(out,sprintf('job_%04d.mat',ii));
 if isfile(fn),item=load(fn,'row');raw(ii,:)=item.row;continue;end
 row=runjob(jobs(ii,:),P); raw(ii,:)=row; parsave(fn,row);
 fprintf('Completed revision job %d/%d\n',ii,size(jobs,1));
end
T=array2table(raw,'VariableNames',{'spacing','variant','seed','completion','fuel_L100','speed_sd','acceleration_rms','stopped_vehicle_s','mean_speed','total_fuel_L','minimum_gap','violations','filter_count','hdv_filter_count','cav_filter_count','filter_mean_delta','filter_max_delta'});
writetable(T,fullfile(out,'revision_experiments.csv'));
delete(gcp('nocreate'));

% Warm each configuration, then profile serial simulation steps without parfor.
% The timed scope includes the controller, dynamics, safety checks and logging.
times=[]; perstep=[];
for scale=1:3
 P=params_merge(); P.sp1=24; P.n0=12+6*(scale-1); P.n1=26+13*(scale-1);
 for modeIndex=1:3
  modes={'COOP','ECO','PASSIVE'}; mode=modes{modeIndex};
  simulate_revision(mode,0.75,999,P,false);
  for seed=0:2
   R=simulate_revision(mode,0.75,seed,P,false); t=R.step_seconds*1000;
   times(end+1,:)=[P.n0+P.n1,modeIndex,seed,mean(t),prctile(t,95),max(t),sum(t>100),R.comp_rate,R.final_gap_violation_steps,R.min_gap];
   perstep=[perstep;[repmat([P.n0+P.n1,modeIndex,seed],numel(t),1),(1:numel(t))',t]];
   writematrix(times,fullfile(out,'timing_progress.csv'));
   fprintf('Timing n=%d %s seed=%d mean=%.3f max=%.3f ms\n',P.n0+P.n1,mode,seed,mean(t),max(t));
  end
 end
end
writetable(array2table(times,'VariableNames',{'vehicles','mode','seed','mean_ms','p95_ms','maximum_ms','steps_over_100ms','completion','violations','min_gap'}),fullfile(out,'runtime_summary.csv'));
writetable(array2table(perstep,'VariableNames',{'vehicles','mode','seed','step','milliseconds'}),fullfile(out,'runtime_steps.csv'));
fprintf('REVISION_EXPERIMENTS_COMPLETE\n');

function row=runjob(job,P)
P.sp1=job(1); v=job(2); seed=job(3); mode='ECO';
if v==1,P.revision_trigger_only=true;mode='COOP';
elseif v==2,P.revision_no_trigger=true;
elseif v<1000,P.eco_density_min=v-100;
elseif v<2000,P.eco_trigger_dist=v-1000;
else,P.D_crit=v-2000;end
R=simulate_revision(mode,0.75,seed,P,false);
row=[P.sp1,v,seed,R.comp_rate,R.fuel_L100,R.sigma_v,R.a_rms,R.stop_steps*P.Ts,R.v_mean,R.fuel_L,R.min_gap,R.final_gap_violation_steps,R.n_safety,R.filter_hdv,R.filter_cav,R.filter_delta_mean,R.filter_delta_max];
end
function parsave(fn,row),save(fn,'row');end
