root=fileparts(mfilename('fullpath'));addpath(fullfile(root,'code'));
data=fullfile(root,'..','PLOS_ONE_Mixed_Traffic_Merging_Data','data','raw');
C=readtable(fullfile(data,'joint_raw.csv'));E=readtable(fullfile(data,'eco_joint_raw.csv'));
P=params_merge();P.sp1=24;modes={'COOP','PASSIVE','ECO'};diagnostics=zeros(3,5);
for j=1:3
 R=simulate_merge(modes{j},.75,0,P,false);
 if j<3,b=C(C.sp1==24&C.penetration==.75&C.seed==0&C.mode==j,:);else,b=E(E.sp1==24&E.penetration==.75&E.seed==0,:);end
 actual=[R.fuel_L100 R.v_mean R.a_rms R.comp_rate R.final_gap_violation_steps];
 expected=[b.perkm_L100 b.v_mean b.a_rms b.comp b.final_gap_violation];
 assert(all(abs(actual(1:3)-expected(1:3))<1e-5),'Archived continuous-metric mismatch');
 assert(all(actual(4:5)==expected(4:5)),'Archived completion/violation mismatch');
 diagnostics(j,:)=[j,max(abs(actual-expected)),b.n_safety,R.n_safety,R.n_safety-b.n_safety];
 fprintf('%s: performance metrics agree within CSV precision (maximum difference %.8g); completion and violations match exactly.\n',modes{j},max(abs(actual-expected)));
 fprintf('  Legacy safety count: archived %d, rerun %d, difference %+d. This strict floating-point comparison includes arbitrarily small corrections.\n',b.n_safety,R.n_safety,R.n_safety-b.n_safety);
end
out=fullfile(root,'analysis');if ~exist(out,'dir'),mkdir(out);end
writetable(array2table(diagnostics,'VariableNames',{'legacy_mode','maximum_metric_difference','archived_safety_count','rerun_safety_count','safety_count_difference'}),fullfile(out,'quick_reproduction_diagnostics.csv'));
fprintf('QUICK_REPRODUCTION_CHECK_PASSED\n');
