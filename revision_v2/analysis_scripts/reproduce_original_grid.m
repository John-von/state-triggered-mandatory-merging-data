% Rebuild the original 1500-run grid without overwriting the archived records.
root=fileparts(mfilename('fullpath'));addpath(fullfile(root,'code'));
out=fullfile(root,'reproduced_main');if ~exist(out,'dir'),mkdir(out);end
jobs=[];
for sp=[40 34 28 24 20]
 for pen=[0 .25 .5 .75 1]
  for mode=1:3
   for seed=0:19,jobs(end+1,:)=[sp pen mode seed];end
  end
 end
end
if license('test','Distrib_Computing_Toolbox') && isempty(gcp('nocreate')),parpool('local',4);end
raw=zeros(size(jobs,1),22);P0=params_merge();
parfor i=1:size(jobs,1)
 P=P0;P.sp1=jobs(i,1);pen=jobs(i,2);m=jobs(i,3);seed=jobs(i,4);modes={'COOP','PASSIVE','ECO'};
 R=simulate_merge(modes{m},pen,seed,P,false);
 raw(i,:)=[1000/P.sp1,P.sp1,pen,m,seed,R.comp_rate,R.fuel_L,R.fuel_per_veh,R.fuel_L100,R.co2_gkm,R.sigma_v,R.a_rms,R.stop_steps*P.Ts,R.min_gap,R.n_hard,R.n_abort,R.final_gap_violation_steps,R.pre_gap_violation_steps,R.n_gap_corrections,R.n_safety,R.v_mean,R.n_merged];
end
names={'k1','sp1','penetration','mode','seed','comp','fuelL','perveh_mL','perkm_L100','co2_gkm','sigma_v','a_rms','stop_veh_s','min_gap','n_hard','n_abort','final_gap_violation','pre_gap_violation','n_gap_correction','n_safety','v_mean','n_merged'};
writetable(array2table(raw,'VariableNames',names),fullfile(out,'main_grid.csv'));
