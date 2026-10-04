%% Safety ablation and representative trajectories for the ECO strategy
clear; clc; close all;

P0 = params_merge();
P0.sp1 = 24;                 % 41.7 veh/km: ECO is active
penetration = 0.75;
seeds = 0:19;

rootDir = fileparts(mfilename('fullpath'));
outDir = fullfile(rootDir,'paper_results');
if ~exist(outDir,'dir'), mkdir(outDir); end

jobs = zeros(4*numel(seeds),2);
q = 0;
for variant = 1:4
    for seed = seeds
        q = q + 1;
        jobs(q,:) = [variant seed];
    end
end

fprintf('ECO safety ablation: %d simulations.\n',size(jobs,1));
raw = zeros(size(jobs,1),18);
useParallel = license('test','Distrib_Computing_Toolbox');
if useParallel
    pool = gcp('nocreate');
    if isempty(pool), parpool('local',4); end
    parfor ii = 1:size(jobs,1)
        raw(ii,:) = run_ablation(jobs(ii,:),penetration,P0);
    end
else
    for ii = 1:size(jobs,1)
        raw(ii,:) = run_ablation(jobs(ii,:),penetration,P0);
    end
end

write_matrix_csv(fullfile(outDir,'eco_safety_ablation_raw.csv'),raw, ...
    ['variant,seed,comp,fuelL,L100,sigma_v,a_rms,stop_veh_s,min_gap,n_hard,' ...
     'n_abort,final_gap_violation,pre_gap_violation,n_gap_correction,n_safety,' ...
     'v_mean,n_merged,perveh_mL']);

summary = zeros(4,14);
for variant = 1:4
    x = raw(raw(:,1)==variant,:);
    summary(variant,:) = [variant,size(x,1),mean(x(:,3)),mean(x(:,4)), ...
        mean(x(:,5)),mean(x(:,6)),mean(x(:,7)),mean(x(:,8)),min(x(:,9)), ...
        sum(x(:,11)),sum(x(:,13)),sum(x(:,14)),sum(x(:,12)),mean(x(:,15))];
end
write_matrix_csv(fullfile(outDir,'eco_safety_ablation_summary.csv'),summary, ...
    ['variant,n,comp_mean,fuel_mean,L100_mean,sigma_mean,arms_mean,' ...
     'stop_veh_s_mean,min_gap_min,n_abort_sum,pre_gap_violation_sum,' ...
     'gap_correction_sum,final_gap_violation_sum,safety_mean']);
save(fullfile(outDir,'eco_safety_ablation_results.mat'),'raw','summary','seeds','penetration','P0');

P = P0;
ecoTypical = simulate_merge('ECO',penetration,0,P,true);
coopTypical = simulate_merge('COOP',penetration,0,P,true);
passiveTypical = simulate_merge('PASSIVE',penetration,0,P,true);
save(fullfile(outDir,'eco_typical_trajectory.mat'), ...
    'ecoTypical','coopTypical','passiveTypical','penetration','P');

fprintf('Full ECO constraints: completion %.2f%%, final violations %d, minimum gap %.3f m.\n', ...
    summary(1,3),summary(1,13),summary(1,9));

function row = run_ablation(job,penetration,P0)
variant = job(1); seed = job(2); P = P0;
if variant == 2
    P.use_predictive_gap = false;
elseif variant == 3
    P.use_safety_filter = false;
elseif variant == 4
    P.use_predictive_gap = false;
    P.use_abort = false;
    P.use_safety_filter = false;
    P.use_gap_correction = false;
end
R = simulate_merge('ECO',penetration,seed,P,false);
row = [variant,seed,R.comp_rate,R.fuel_L,R.fuel_L100,R.sigma_v,R.a_rms, ...
    R.stop_steps*P.Ts,R.min_gap,R.n_hard,R.n_abort,R.final_gap_violation_steps, ...
    R.pre_gap_violation_steps,R.n_gap_corrections,R.n_safety,R.v_mean, ...
    R.n_merged,R.fuel_per_veh];
end

function write_matrix_csv(path,x,header)
fid = fopen(path,'w'); fprintf(fid,'%s\n',header); fclose(fid);
writematrix(x,path,'WriteMode','append');
end
