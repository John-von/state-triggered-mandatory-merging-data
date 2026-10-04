root=fileparts(mfilename('fullpath'));addpath(fullfile(root,'code'));
out=fullfile(root,'analysis');
P=params_merge();P.sp1=24;
A=simulate_robust('ECO',.75,0,P,false);
B=simulate_components('ECO',.75,0,P,false);
assert(isequal(A.recX,B.recX)&&isequal(A.recV,B.recV)&&isequal(A.recA,B.recA));
names={'ramp_timing','scheduling','objective_and_gain','acceleration_limit','admission','spacing_buffer'};
jobs=[];for ci=1:6,for seed=0:19,jobs(end+1,:)=[ci,seed];end,end
writetable(array2table(jobs,'VariableNames',{'component_id','seed'}),fullfile(out,'component_registered_jobs.csv'));
pool=gcp('nocreate');if isempty(pool),parpool('local',4);end
raw=zeros(size(jobs,1),13);
parfor ji=1:size(jobs,1)
 fn=fullfile(out,sprintf('component_%04d.mat',ji));
 if isfile(fn),item=load(fn,'row');raw(ji,:)=item.row;continue;end
 ci=jobs(ji,1);seed=jobs(ji,2);P=params_merge();P.sp1=24;
 switch ci
  case 1,P.eco_T_ramp=P.T_ramp;P.global_ramp_clock=true;
  case 2,P.eco_N_prep=P.N_prep;P.eco_N_lc_active=P.N_lc_active;
  case 3,P.eco_qv=P.qv;P.eco_qa=P.qa;P.eco_ru=P.ru;P.eco_qg=P.qg;P.eco_qr=P.qr;P.eco_qc=P.qc;P.eco_kp_gap=P.kp_c;P.eco_kd_gap=P.kd_c;
  case 4,P.eco_a_max=P.a_max;P.eco_a_min=P.a_min;
  case 5,P.eco_k_pred=P.k_pred;P.eco_tau_gap=P.tau_h;
  case 6,P.eco_safety_buffer=P.safety_buffer;
 end
 R=simulate_components('ECO',.75,seed,P,false);
 row=[ci,seed,R.comp_rate,R.fuel_L100,R.sigma_v,R.a_rms,R.stop_steps*P.Ts,R.v_mean,R.fuel_L,R.min_gap,R.final_gap_violation_steps,R.jerk_rms,R.n_abort];
 raw(ji,:)=row;save_row(fn,row);fprintf('Component %d/%d %s seed%d\n',ji,size(jobs,1),names{ci},seed);
end
writetable(array2table(raw,'VariableNames',{'component_id','seed','completion','fuel_L100','speed_sd','acceleration_rms','stopped_vehicle_s','mean_speed','total_fuel_L','minimum_gap','violations','jerk_rms','hold_events'}),fullfile(out,'component_experiments.csv'));
delete(gcp('nocreate'));fprintf('COMPONENT_EXPERIMENTS_COMPLETE\n');
function save_row(fn,row),save(fn,'row');end
