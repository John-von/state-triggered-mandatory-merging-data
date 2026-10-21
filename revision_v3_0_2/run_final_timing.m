% Serial end-to-end timing after the experiment workers have stopped.
root=fileparts(mfilename('fullpath'));addpath(fullfile(root,'code'));
assert(isempty(gcp('nocreate')),'Close the worker pool before timing.');
out=fullfile(root,'corrected');modes={'COOP','ECO','PASSIVE'};rows=[];steps=[];
for scale=1:3
 P=params_merge();P.sp1=24;P.n0=12+6*(scale-1);P.n1=26+13*(scale-1);
 for mi=1:3
  clear simulate_final
  simulate_final(modes{mi},.75,999,P,false);
  for seed=0:2
   R=simulate_final(modes{mi},.75,seed,P,false);t=R.step_seconds*1000;
   rows(end+1,:)=[P.n0+P.n1 mi seed mean(t) prctile(t,95) max(t) sum(t>100) R.comp_rate];
   steps=[steps;repmat([P.n0+P.n1 mi seed],numel(t),1),(1:numel(t))',t];
   fprintf('TIMING n%d %s seed%d mean%.3f p95%.3f max%.3f exceed%d\n',P.n0+P.n1,modes{mi},seed,mean(t),prctile(t,95),max(t),sum(t>100));
  end
 end
end
writetable(array2table(rows,'VariableNames',{'vehicles','mode_id','seed','mean_ms','p95_ms','maximum_ms','steps_over_100ms','completion'}),fullfile(out,'runtime_summary.csv'));
writetable(array2table(steps,'VariableNames',{'vehicles','mode_id','seed','step','milliseconds'}),fullfile(out,'runtime_steps.csv'));
fprintf('FINAL_TIMING_COMPLETE\n');
