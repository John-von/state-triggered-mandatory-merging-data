root=fileparts(mfilename('fullpath')); out=fullfile(root,'analysis'); if ~exist(out,'dir'),mkdir(out);end
data=fullfile(root,'..','PLOS_ONE_Mixed_Traffic_Merging_Data','data','raw');
C=readtable(fullfile(data,'joint_raw.csv')); E=readtable(fullfile(data,'eco_joint_raw.csv'));
assert(height(C)==1000 && height(E)==500);
metrics={'perkm_L100','sigma_v','a_rms','stop_veh_s','v_mean','fuelL'};
records=[];
for baseline=1:2
 for sp=[40 34 28 24 20]
  for pen=[0 .25 .5 .75 1]
   b=sortrows(C(C.sp1==sp & C.penetration==pen & C.mode==baseline,:),'seed');
   e=sortrows(E(E.sp1==sp & E.penetration==pen,:),'seed');
   assert(height(b)==20 && height(e)==20 && isequal(b.seed,e.seed));
   for metric=1:6
    x=b.(metrics{metric});y=e.(metrics{metric}); raw=x-y;if metric==5,raw=-raw;end
    diff=100*raw./x;if metric==4,diff=raw;end
    [~,pt,ci,stats]=ttest(diff,0,'Alpha',.05);
    if all(diff==0),pw=1;dz=0;else,pw=signrank(diff,0,'method','exact');dz=mean(diff)/std(diff,0);end
    dzraw=mean(raw)/std(raw,0);
    ci_raw=mean(raw)+[-1 1]*tinv(.975,19)*std(raw,0)/sqrt(20);
    records(end+1,:)=[baseline,1000/sp,sp,pen,metric,20,mean(x),mean(y),mean(diff),ci',pt,pw,dz,mean(raw),ci_raw,dzraw,stats.tstat];
   end
  end
 end
end
names={'baseline','density','spacing','penetration','metric','n','baseline_mean','ECO_mean','effect','ci95_low','ci95_high','p_t','p_wilcoxon_exact','dz_effect','raw_difference','raw_ci95_low','raw_ci95_high','dz_raw','t_statistic'};
T=array2table(records,'VariableNames',names);T.p_t_holm=zeros(height(T),1);T.p_wilcoxon_holm=zeros(height(T),1);
for baseline=1:2
 for metric=1:6
  ix=find(T.baseline==baseline & T.metric==metric);
  T.p_t_holm(ix)=holm(T.p_t(ix));T.p_wilcoxon_holm(ix)=holm(T.p_wilcoxon_exact(ix));
 end
end
writetable(T,fullfile(out,'paired_statistics.csv'));
for baseline=1:2
 for metric=1:6
  x=T(T.baseline==baseline & T.metric==metric & T.penetration>0,:);
  fprintf('baseline=%d metric=%s effect [%.4f,%.4f], positive CI %d/20, Holm t %d/20, Holm Wilcoxon %d/20, dz [%.3f,%.3f]\n',baseline,metrics{metric},min(x.effect),max(x.effect),sum(x.ci95_low>0),sum(x.p_t_holm<.05 & x.effect>0),sum(x.p_wilcoxon_holm<.05 & x.effect>0),min(x.dz_effect),max(x.dz_effect));
 end
end
fprintf('STATISTICS_COMPLETE\n');
function adj=holm(p)
[v,o]=sort(p);m=numel(p);adjusted=min(1,cummax(v.*(m:-1:1)'));adj=zeros(size(p));adj(o)=adjusted;
end
