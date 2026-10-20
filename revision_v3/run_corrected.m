% Registered paired experiments for the corrected simulator.
root=fileparts(mfilename('fullpath'));addpath(fullfile(root,'code'));
out=fullfile(root,'corrected');if ~isfolder(out),mkdir(out);end
jobs=[];
% Columns: family, scale, mode, seed, spacing, penetration, variant, gate.
% Queue and training results are produced first for early diagnostic review.
for scale=2:3
 for mode=1:3
  for seed=0:19,jobs(end+1,:)=[2 scale mode seed 24 .75 0 0];end
 end
end
for candidate=1:4
 for gate=0:1
  for sp=[28 24 20]
   for seed=100:104,jobs(end+1,:)=[3 1 2 seed sp .75 candidate gate];end
  end
 end
end
for sp=[40 34 28 24 20]
 for pen=[0 .25 .5 .75 1]
  for mode=1:3
   for seed=0:19,jobs(end+1,:)=[1 1 mode seed sp pen 0 0];end
  end
 end
end
for sp=[40 34 28 24 20]
 for pen=[0 .25 .5 .75 1]
  for seed=0:19,jobs(end+1,:)=[4 1 2 seed sp pen 0 0];end
 end
end
for condition=2:17
 for mode=1:3
  for seed=0:19,jobs(end+1,:)=[5 1 mode seed 24 .75 condition 0];end
 end
end
for variant=2:4
 for seed=0:19,jobs(end+1,:)=[6 1 2 seed 24 .75 variant 0];end
end
for variant=1:6
 for seed=0:19,jobs(end+1,:)=[7 1 2 seed 24 .75 variant 0];end
end
for threshold=[30 40 45]
 for sp=[40 28 20]
  for seed=0:19,jobs(end+1,:)=[8 1 2 seed sp .75 100+threshold 0];end
 end
end
for dist=[250 550]
 for seed=0:19,jobs(end+1,:)=[8 1 2 seed 24 .75 1000+dist 0];end
end
for crit=[15 40]
 for seed=0:19,jobs(end+1,:)=[8 1 2 seed 24 .75 2000+crit 0];end
end
for sp=[40 28 20]
 for seed=0:19,jobs(end+1,:)=[9 1 1 seed sp .75 0 0];end
end
for scale=1:3
 for mode=1:3
  for seed=0:2
   for ns=[10 20],jobs(end+1,:)=[10 scale mode seed 24 .75 ns 0];end
  end
 end
end
names={'family','scale','mode_id','seed','spacing','penetration','variant','gate'};
writetable(array2table(jobs,'VariableNames',names),fullfile(out,'registered_jobs.csv'));
fprintf('REGISTERED %d corrected experiments.\n',size(jobs,1));
pool=gcp('nocreate');if isempty(pool),parpool('local',5);end
parfor ji=1:size(jobs,1)
 run_one(root,jobs(ji,:),ji);
end
fprintf('CORRECTED_GRID_COMPLETE\n');
% Select each activation policy using the same training objective and budget.
% Priorities: overlap-free candidate, highest completion, lowest fuel intensity.
scores=[];chosen=zeros(1,2);
for gate=0:1
 for candidate=1:4
  ids=find(jobs(:,1)==3 & jobs(:,7)==candidate & jobs(:,8)==gate);
  vals=zeros(numel(ids),3);
  for q=1:numel(ids)
   d=load(fullfile(out,sprintf('run_%04d.mat',ids(q))),'S');
   vals(q,:)=[d.S.final_gap_violation_steps,d.S.comp_rate,d.S.fuel_L100];
  end
  scores(end+1,:)=[gate candidate sum(vals(:,1)) mean(vals(:,2)) mean(vals(:,3))];
 end
 sub=scores(scores(:,1)==gate,:);
 [~,order]=sortrows([sub(:,3)>0,-sub(:,4),sub(:,5),sub(:,2)],[1 2 3 4]);
 chosen(gate+1)=sub(order(1),2);
end
writetable(array2table(scores,'VariableNames',{'gate','candidate','overlap_samples','completion','fuel_L100'}),fullfile(out,'tuning_training.csv'));
evaluation=[];
for gate=0:1
 for sp=[28 24 20]
  for seed=0:19,evaluation(end+1,:)=[11 1 2 seed sp .75 chosen(gate+1) gate];end
 end
end
writetable(array2table(evaluation,'VariableNames',names),fullfile(out,'evaluation_jobs.csv'));
offset=size(jobs,1);
parfor ji=1:size(evaluation,1)
 run_one(root,evaluation(ji,:),offset+ji);
end
delete(gcp('nocreate'));
% Targeted state-matching tests. The initial 0.2 m gap is deliberately unsafe.
for speed=[16 4]
 P=params_merge();P.n0=1;P.n1=2;P.T_end=12;P.sp1=24;
 P.hold_probe=true;P.physical_probe=true;P.probe_speed=speed;P.v0=speed;P.v1=speed;
 R=simulate_final('ECO',1,0,P,false);
 assert(R.n_abort>=1 && ~isempty(R.restart_records) && R.n_merged==1);
 assert(max(abs(R.restart_records(:,3:5)-R.restart_records(:,6:8)),[],'all')<1e-8);
 save(fullfile(out,sprintf('hold_physical_%d.mat',speed)),'R','P');
 fprintf('HOLD speed%d events%d completion%d gap%.5f\n',speed,R.n_abort,R.n_merged,R.min_gap);
end
fprintf('ALL_CORRECTED_EXPERIMENTS_COMPLETE\n');

function run_one(root,job,ji)
fn=fullfile(root,'corrected',sprintf('run_%04d.mat',ji));
if isfile(fn),return;end
maxNumCompThreads(1);clear simulate_final
P=params_merge();P.sp1=job(5);P.n0=12+6*(job(2)-1);P.n1=26+13*(job(2)-1);
switch job(1)
 case {3,11}
  P.revision_no_trigger=~logical(job(8));P=tuning_candidate(P,job(7));
 case 4
  P.revision_no_trigger=true;
 case 5
  P=robustness_setting(P,job(7));
 case 6
  if job(7)==2,P.use_predictive_gap=false;end
  if job(7)>=3,P.use_safety_filter=false;end
  if job(7)==4,P.use_predictive_gap=false;P.use_abort=false;end
 case 7
  P=component_setting(P,job(7));
 case 8
  v=job(7);
  if v<1000,P.eco_density_min=v-100;elseif v<2000,P.eco_trigger_dist=v-1000;else,P.D_crit=v-2000;end
 case 9
  P.revision_trigger_only=true;
 case 10
  P.n_sub=job(7);P.dense_samples=job(7);
end
if (job(1)==1 && job(5)==24 && job(6)==.75 || job(1)==2) && job(4)<=2
 P.dense_samples=P.n_sub;
end
modes={'COOP','ECO','PASSIVE'};
R=simulate_final(modes{job(3)},job(6),job(4),P,false);
assert(all(isfinite(R.recX),'all') && all(isfinite(R.recV),'all') && all(R.recV>=0,'all'));
assert(min(R.recA,[],'all')>=P.a_emg-1e-8);
S=compact_result(R,P,job);save(fn,'S','P','job');
if job(4)==0 && (job(1)==2 || job(1)==1 && job(5)==24 && job(6)==.75 || job(1)==5 || job(1)==10)
 save(fullfile(root,'corrected',sprintf('trajectory_%04d.mat',ji)),'R','P','job');
end
fprintf('DONE %04d family%d %s n%d seed%d comp%.2f gap%.4f closure%d\n',ji,job(1),R.mode,P.n0+P.n1,job(4),R.comp_rate,R.min_gap,R.closure_boundary_samples);
end

function P=robustness_setting(P,c)
switch c
 case 2,P.delay_s=.1;
 case 3,P.delay_s=.3;
 case 4,P.delay_s=.5;
 case 5,P.drop_probability=.05;
 case 6,P.drop_probability=.10;
 case 7,P.drop_probability=.20;
 case 8,P.position_sigma=.2;P.speed_sigma=.1;
 case 9,P.position_sigma=.2;P.speed_sigma=.1;P.noisy_safety=true;
 case 10,P.delay_s=.3;P.drop_probability=.1;P.position_sigma=.2;P.speed_sigma=.1;
 case 11,P.hdv_variation=.2;
 case 12,P.hdv_variation=.4;
 case 13,P.hdv_variation=.2;P.cav_only_safety=true;
 case 14,P.X_drop=650;
 case 15,P.X_drop=850;
 case 16,P.v0=P.v0*.8;P.v1=P.v1*.8;
 case 17,P.v0=P.v0*1.2;P.v1=P.v1*1.2;
end
end

function P=component_setting(P,c)
switch c
 case 1,P.eco_T_ramp=P.T_ramp;P.global_ramp_clock=true;
 case 2,P.eco_N_prep=P.N_prep;P.eco_N_lc_active=P.N_lc_active;
 case 3,P.eco_qv=P.qv;P.eco_qa=P.qa;P.eco_ru=P.ru;P.eco_qg=P.qg;P.eco_qr=P.qr;P.eco_qc=P.qc;P.eco_kp_gap=P.kp_c;P.eco_kd_gap=P.kd_c;
 case 4,P.eco_a_max=P.a_max;P.eco_a_min=P.a_min;
 case 5,P.eco_k_pred=P.k_pred;P.eco_tau_gap=P.tau_h;
 case 6,P.eco_safety_buffer=P.safety_buffer;
end
end
