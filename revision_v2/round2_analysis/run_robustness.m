root=fileparts(mfilename('fullpath'));addpath(fullfile(root,'code'));
out=fullfile(root,'analysis');modes={'COOP','ECO','PASSIVE'};
P=params_merge();P.sp1=24;
for mi=1:3
    A=simulate_revision(modes{mi},.75,0,P,false);
    B=simulate_robust(modes{mi},.75,0,P,false);
    assert(isequal(A.recX,B.recX)&&isequal(A.recV,B.recV)&&isequal(A.recA,B.recA),['Ideal baseline mismatch: ' modes{mi}]);
    save(fullfile(out,['baseline_' modes{mi} '.mat']),'B');
    fprintf('Exact ideal baseline verified: %s\n',modes{mi});
end
% Settings registered before execution. Fixed 90 s horizon, 38 vehicles,
% 41.7 veh/km and 75% nominal penetration except explicitly varied factors.
% Noise means independent zero-mean Gaussian position/speed observation error.
specs={
 'ideal',0,0,0,0,0,0,0,750,1;
 'delay_100ms',.1,0,0,0,0,0,0,750,1;
 'delay_300ms',.3,0,0,0,0,0,0,750,1;
 'delay_500ms',.5,0,0,0,0,0,0,750,1;
 'loss_5pct',0,.05,0,0,0,0,0,750,1;
 'loss_10pct',0,.10,0,0,0,0,0,750,1;
 'loss_20pct',0,.20,0,0,0,0,0,750,1;
 'measurement_nominal',0,0,.20,.10,0,0,0,750,1;
 'measurement_all_layers',0,0,.20,.10,1,0,0,750,1;
 'combined',.3,.10,.20,.10,0,0,0,750,1;
 'hdv_variation_20pct',0,0,0,0,0,.20,0,750,1;
 'hdv_variation_40pct',0,0,0,0,0,.40,0,750,1;
 'hdv_unfiltered',0,0,0,0,0,.20,1,750,1;
 'closure_650m',0,0,0,0,0,0,0,650,1;
 'closure_850m',0,0,0,0,0,0,0,850,1;
 'speed_80pct',0,0,0,0,0,0,0,750,.8;
 'speed_120pct',0,0,0,0,0,0,0,750,1.2};
spec_table=cell2table(specs,'VariableNames',{'condition','delay_s','drop_probability','position_sigma','speed_sigma','noisy_safety','hdv_variation','cav_only_safety','closure_m','speed_factor'});
writetable(spec_table,fullfile(out,'experiment_settings.csv'));
jobs=[];
for condition=1:size(specs,1)
 for mi=1:3
  for seed=0:19,jobs(end+1,:)=[condition mi seed];end
 end
end
writetable(array2table(jobs,'VariableNames',{'condition_id','mode_id','seed'}),fullfile(out,'registered_jobs.csv'));
fprintf('Registered %d robustness and transfer jobs.\n',size(jobs,1));
pool=gcp('nocreate');if isempty(pool),parpool('local',4);end
raw=zeros(size(jobs,1),23);
parfor ji=1:size(jobs,1)
 fn=fullfile(out,sprintf('robust_%04d.mat',ji));
 if isfile(fn),item=load(fn,'row');raw(ji,:)=item.row;continue;end
 job=jobs(ji,:);spec=specs(job(1),:);Pj=params_merge();Pj.sp1=24;
 Pj.delay_s=spec{2};Pj.drop_probability=spec{3};Pj.position_sigma=spec{4};Pj.speed_sigma=spec{5};Pj.noisy_safety=spec{6};Pj.hdv_variation=spec{7};Pj.cav_only_safety=spec{8};Pj.X_drop=spec{9};Pj.v0=Pj.v0*spec{10};Pj.v1=Pj.v1*spec{10};
 R=simulate_robust(modes{job(2)},.75,job(3),Pj,false);
 row=[job,R.comp_rate,R.fuel_L100,R.sigma_v,R.a_rms,R.stop_steps*Pj.Ts,R.v_mean,R.fuel_L,R.min_gap,R.final_gap_violation_steps,R.n_safety,R.filter_hdv,R.filter_cav,R.filter_delta_mean,R.filter_delta_max,R.mean_information_age,R.maximum_information_age,R.realized_packet_loss,R.jerk_rms,R.n_abort,sum(R.hold_steps)*Pj.Ts];
 raw(ji,:)=row;save_row(fn,row);
 if job(3)==0,save_run(fullfile(out,sprintf('representative_c%02d_m%d.mat',job(1),job(2))),R);end
 fprintf('Robustness completed %d/%d %s %s seed%d\n',ji,size(jobs,1),spec{1},modes{job(2)},job(3));
end
names={'condition_id','mode_id','seed','completion','fuel_L100','speed_sd','acceleration_rms','stopped_vehicle_s','mean_speed','total_fuel_L','minimum_gap','violations','legacy_filter_count','hdv_filter_count','cav_filter_count','filter_mean_delta','filter_max_delta','mean_information_age','maximum_information_age','realized_packet_loss','jerk_rms','hold_events','hold_vehicle_s'};
writetable(array2table(raw,'VariableNames',names),fullfile(out,'robustness_experiments.csv'));
delete(gcp('nocreate'));fprintf('ROBUSTNESS_EXPERIMENTS_COMPLETE\n');
function save_row(fn,row),save(fn,'row');end
function save_run(fn,R),save(fn,'R');end
